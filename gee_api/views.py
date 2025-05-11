from typing import Dict, Any
from venv import logger
from django.http import HttpResponse, JsonResponse, HttpRequest
from rest_framework import viewsets
import ee
from rest_framework.views import APIView
from rest_framework.response import Response
from .constants import ee_assets, shrug_dataset, shrug_fields
from datetime import datetime
import json
from django.views.decorators.csrf import csrf_exempt


from .utils import initialize_earth_engine
from .ee_processing import (
    compare_village, 
    district_boundary, 
    IndiaSAT_lulc, 
    IMD_precipitation, 
    village_boundary, 
    FarmBoundary_lulc, 
    subdistrict_boundary,
    Bhuvan_lulc
)
import ee

from .polygon_processing import (
    process_custom_polygon,
    get_lulc_for_region,
    lulc_area_stats
)
import ee

from gee_api.models import State, District, SubDistrict, Village
from gee_api.serializers import StateSerializer, DistrictSerializer, SubDistrictSerializer, VillageSerializer
from gee_api.models import District, SubDistrict, Village
from typing import List, Dict

# Initialize Earth Engine credentials
email = "admin-133@ee-papnejaanmol.iam.gserviceaccount.com"
key_file = "./creds/ee-papnejaanmol-23b4363dc984.json"
credentials = ee.ServiceAccountCredentials(email=email, key_file=key_file)
ee.Initialize(credentials)


def district_list(request, state_id: int) -> JsonResponse:
    """
    Fetches a list of districts for a given state.

    Args:
        request: The HTTP request object.
        state_id (int): The ID of the state for which districts are fetched.

    Returns:
        JsonResponse: A JSON response containing a list of districts.
    """
    districts = District.objects.filter(state__id=state_id)
    data: List[Dict[str, str]] = [{"id": district.id, "name": district.name} for district in districts]
    return JsonResponse(data, safe=False)


def subdistrict_list(request, district_id: int) -> JsonResponse:
    """
    Fetches a list of subdistricts for a given district.

    Args:
        request: The HTTP request object.
        district_id (int): The ID of the district for which subdistricts are fetched.

    Returns:
        JsonResponse: A JSON response containing a list of subdistricts.
    """
    subdistricts = SubDistrict.objects.filter(district__id=district_id)
    data: List[Dict[str, str]] = [{"id": subdistrict.id, "name": subdistrict.name} for subdistrict in subdistricts]
    return JsonResponse(data, safe=False)


def village_list(request, subdistrict_id: int) -> JsonResponse:
    """
    Fetches a list of villages for a given subdistrict.

    Args:
        request: The HTTP request object.
        subdistrict_id (int): The ID of the subdistrict for which villages are fetched.

    Returns:
        JsonResponse: A JSON response containing a list of villages with their IDs.
    """
    villages = Village.objects.filter(subdistrict__id=subdistrict_id)
    data = [
        {
            "id": village.id,            # Database ID (for internal use)
            "name": village.name,        # Village name
            "village_id": village.village_id,  # Census village ID (pc11_tv_id)
            "display_name": f"{village.name} - {village.village_id}" if village.village_id else village.name
        } 
        for village in villages
    ]
    return JsonResponse(data, safe=False)

def health_check(request: HttpRequest) -> HttpResponse:
    """
    Perform necessary health check logic and return HTTP 200 OK.

    :param request: HttpRequest object
    :return: HttpResponse with status "OK"
    """
    return HttpResponse("OK")


def get_karauli_raster(
        request: HttpRequest,
        district_name: str) -> JsonResponse:
    """
    Get the raster image for a specified district and return a URL for the map tiles.

    :param request: HttpRequest object
    :param district_name: Name of the district to get the raster for
    :return: JsonResponse containing the URL for the map tiles or an error message
    """
    ee.Initialize(credentials)

    try:
        # Access the ImageCollection for Karauli
        district_fc = ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/hackathon_dists').filter(
            ee.Filter.eq('district_n', district_name)).geometry().centroid()

        image_collection = ee.ImageCollection('users/jaltolwelllabs/LULC/hackathon').filterBounds(
            district_fc).filterDate('2022-07-01', '2023-06-30').first()

        image = ee.Image(image_collection)

        valuesToKeep = [6, 8, 9, 10, 11, 12]
        targetValues = [6, 8, 8, 10, 10, 12]
        remappedImage = image.remap(valuesToKeep, targetValues, 0)
        mask = remappedImage.gte(6).And(remappedImage.lte(12))
        remappedImage = remappedImage.updateMask(mask)

        # Define visualization parameters
        vis_params = {
            'bands': ['remapped'],  # Update with the correct band names
            'min': 0,
            'max': 12,
            'palette': [
                '#b2df8a', '#6382ff', '#d7191c', '#f5ff8b', '#dcaa68',
                '#397d49', '#50c361', '#8b9dc3', '#dac190', '#222f5b',
                '#38c5f9', '#946b2d'
            ]
        }

        # Get the map ID and token
        map_id_dict = remappedImage.getMapId(vis_params)

        # Construct the tiles URL template
        tiles_url = map_id_dict['tile_fetcher'].url_format

        return JsonResponse({'tiles_url': tiles_url})
    except Exception as e:
        logger.error('Failed to get Karauli raster', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


def get_rainfall_data(request: HttpRequest) -> JsonResponse:
    """
    Fetch rainfall data for a given location.

    :param request: HttpRequest object
    :return: JsonResponse containing rainfall data or an error message
    """
    ee.Initialize(credentials)

    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()
    subdistrict_name = request.GET.get('subdistrict_name', '').lower()
    village_name = request.GET.get('village_name', '').lower()
    village_id = request.GET.get('village_id', '')

    # Clean up village name if it contains an ID part
    if ' - ' in village_name and not village_id:
        parts = village_name.split(' - ')
        village_name = parts[0].strip()
        if len(parts) > 1:
            village_id = parts[1].strip()

    if not (state_name and district_name):
        return JsonResponse(
            {'error': 'Parameters state_name and district_name are required.'}, 
            status=400)

    try:
        # Get the village boundary - prioritize searching by ID if available
        if village_id:
            # Directly query for the village using the ID
            shrug = shrug_dataset()
            village_fc = shrug.filter(
                ee.Filter.And(
                    ee.Filter.eq(shrug_fields['state_field'], state_name),
                    ee.Filter.eq(shrug_fields['district_field'], district_name),
                    ee.Filter.eq(shrug_fields['subdistrict_field'], subdistrict_name),
                    ee.Filter.eq('pc11_tv_id', village_id)
                )
            )
            
            # Verify we found exactly one village
            count = village_fc.size().getInfo()
            if count == 0:
                return JsonResponse({'error': f"No village found with ID {village_id}"}, status=404)
            
        else:
            # Search by name if no ID
            village_fc = village_boundary(state_name, district_name, subdistrict_name, village_name)
            
            # Check if we have any results
            count = village_fc.size().getInfo()
            if count == 0:
                return JsonResponse({'error': f"No village found with name {village_name}"}, status=404)
            elif count > 1:
                # If multiple villages found, get just the first one
                first_feature = ee.Feature(village_fc.first())
                village_fc = ee.FeatureCollection([first_feature])
                print(f"Warning: Found {count} villages named '{village_name}', using the first one")

        # Now we have a single village feature collection, proceed with rainfall calculation
        village_geometry = village_fc.geometry()
        
        # Set year range based on state
        if state_name in ['maharashtra', 'uttar pradesh', 'jharkhand']:
            # For Bhuvan LULC states, use 2005-2024 excluding 2019
            start_year = 2005
            end_year = 2024
            # We'll handle the exclusion of 2019 in the IMD_precipitation function
        else:
            # For other states, use the default range
            start_year = 2014
            end_year = 2022
        
        # Import the IMD_precipitation function from ee_processing
        # This will handle the rainfall calculation using yearly_sum internally
        rainfall_data = IMD_precipitation(
            start_year,
            end_year,
            state_name,
            district_name,
            subdistrict_name,
            village_name if not village_id else None,  # Use original village name if no ID
            village_id  # Pass the village ID
        )
        
        return rainfall_data
        
    except Exception as e:
        print(f"Error in get_rainfall_data: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def get_boundary_data(request: HttpRequest) -> JsonResponse:
    """
    Get the boundary data for a specified state, district, subdistrict, and village.
    When a village is specified with an ID, use the ID for more precise boundary selection.

    :param request: HttpRequest object
    :return: JsonResponse containing the boundary GeoJSON data or an error message
    """
    ee.Initialize(credentials)

    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()
    subdistrict_name = request.GET.get('subdistrict_name', '').lower()
    village_name = request.GET.get('village_name', '').lower()
    village_id = request.GET.get('village_id', '')

    if not (state_name and district_name):
        return JsonResponse(
            {'error': 'All parameters (state_name, district_name) are required.'}, status=400)

    try:
        # If we have a village name and subdistrict
        if subdistrict_name and village_name:
            # Extract village ID if it's in the format "name - id" and no specific village_id is provided
            if ' - ' in village_name and not village_id:
                parts = village_name.split(' - ')
                village_name = parts[0]  # Use just the village name part
                if len(parts) > 1:
                    village_id = parts[1]  # Extract ID if present
            
            # Get the village boundary, passing both name and ID if available
            village_fc = village_boundary(
                state_name, district_name, subdistrict_name, village_name, village_id)
            geojson = village_fc.getInfo()
            return JsonResponse(geojson)
        elif subdistrict_name:
            # Get subdistrict boundary
            subdistrict_fc = subdistrict_boundary(state_name, district_name, subdistrict_name)
            geojson = subdistrict_fc.getInfo()
            return JsonResponse(geojson)
        else:
            # Get district boundary
            geojson = district_boundary(state_name, district_name).getInfo()
            return JsonResponse(geojson)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_lulc_raster(request: HttpRequest) -> JsonResponse:
    """
    Get the Land Use Land Cover (LULC) raster for a specified location.

    :param request: HttpRequest object
    :return: JsonResponse containing the URL for the LULC raster or an error message
    """
    ee.Initialize(credentials)

    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()
    subdistrict_name = request.GET.get('subdistrict_name', '').lower()
    village_name = request.GET.get('village_name', '').lower()
    village_id = request.GET.get('village_id', '')
    year = request.GET.get('year')

    if not year:
        return JsonResponse({'error': 'Year parameter is required.'}, status=400)

    # Extract village ID if it's in the format "name - id" and no specific village_id is provided
    if ' - ' in village_name and not village_id:
        parts = village_name.split(' - ')
        village_name_only = parts[0]
        if len(parts) > 1:
            village_id = parts[1]
    else:
        village_name_only = village_name
    
    print(f"Processing LULC for: {village_name_only}, ID: {village_id}")

    try:
        if not all((state_name, district_name)):
            raise ValueError(
                'parameters (state_name, district_name) are required.')

        # Choose the correct image based on state and district
        if state_name in ['maharashtra', 'uttar pradesh', 'jharkhand']:
            print(f"Using Bhuvan LULC for state: {state_name}")
            image = Bhuvan_lulc(
                year,
                state_name,
                district_name,
                subdistrict_name,
                village_name_only,
                village_id)
            
            # For Bhuvan LULC, we need to remap classes
            # Tree/Forests: 7,8,9 -> 6
            # Single cropping: 2,3,4 -> 8
            # Double cropping: 5 -> 10
            # Shrub/Scrub: 10 -> 12
            # Remap Bhuvan classes to match our visualization classes
            valuesToKeep = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
            targetValues = [0, 8, 8, 8, 10, 0, 6, 6, 6, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            remappedImage = image.select('b1').remap(valuesToKeep, targetValues, 0)
            
            # Create mask to only show the classes we want (6, 8, 10, 12)
            mask = remappedImage.eq(6).Or(remappedImage.eq(8)).Or(remappedImage.eq(10)).Or(remappedImage.eq(12))
            remappedImage = remappedImage.updateMask(mask)
            
            # Define visualization parameters for Bhuvan
            vis_params = {
                'min': 0,
                'max': 12,
                'palette': [
                    '#b2df8a', '#6382ff', '#d7191c', '#f5ff8b', '#dcaa68',
                    '#397d49', '#50c361', '#8b9dc3', '#dac190', '#222f5b',
                    '#38c5f9', '#946b2d'
                ]
            }
            
        elif district_name in ['vadodara']:
            print("Using Farmboundary_NDVI asset for district:", district_name)
            image = FarmBoundary_lulc(
                year,
                state_name,
                district_name,
                subdistrict_name,
                village_name_only,
                village_id)
                
            # For FarmBoundary, use original remapping
            valuesToKeep = [6, 8, 9, 10, 11, 12]
            targetValues = [6, 8, 8, 10, 10, 12]
            remappedImage = image.remap(valuesToKeep, targetValues, 0)
            mask = remappedImage.gte(6).And(remappedImage.lte(12))
            remappedImage = remappedImage.updateMask(mask)
            
            # Define visualization parameters for FarmBoundary
            vis_params = {
                'bands': ['remapped'],
                'min': 0,
                'max': 12,
                'palette': [
                    '#b2df8a', '#6382ff', '#d7191c', '#f5ff8b', '#dcaa68',
                    '#397d49', '#50c361', '#8b9dc3', '#dac190', '#222f5b',
                    '#38c5f9', '#946b2d'
                ]
            }
            
        else:
            print(f"Using IndiaSAT for state: {state_name}, district: {district_name}")
            image = IndiaSAT_lulc(
                year,
                state_name,
                district_name,
                subdistrict_name,
                village_name_only)
                
            # For IndiaSAT, use original remapping
            valuesToKeep = [6, 8, 9, 10, 11, 12]
            targetValues = [6, 8, 8, 10, 10, 12]
            remappedImage = image.remap(valuesToKeep, targetValues, 0)
            mask = remappedImage.gte(6).And(remappedImage.lte(12))
            remappedImage = remappedImage.updateMask(mask)
            
            # Define visualization parameters for IndiaSAT
            vis_params = {
                'bands': ['remapped'],
                'min': 0,
                'max': 12,
                'palette': [
                    '#b2df8a', '#6382ff', '#d7191c', '#f5ff8b', '#dcaa68',
                    '#397d49', '#50c361', '#8b9dc3', '#dac190', '#222f5b',
                    '#38c5f9', '#946b2d'
                ]
            }

        # Ensure we have image bands before proceeding
        band_names = remappedImage.bandNames().getInfo()
        print(f"Band names for LULC: {band_names}")
        
        if not band_names:
            return JsonResponse({'error': 'No data available for the selected area and year'}, status=404)

        # Get the map ID and token
        map_id_dict = remappedImage.getMapId(vis_params)

        # Construct the tiles URL template
        tiles_url = map_id_dict['tile_fetcher'].url_format
        
        print(f"LULC tiles URL: {tiles_url}")
        return JsonResponse({'tiles_url': tiles_url})
    except Exception as e:
        logger.error('Failed to get LULC raster', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

def calculate_class_area(
        image: ee.Image,
        class_value: int,
        geometry: ee.Geometry,
        district_name: str,
        state_name: str) -> float:
    """
    Calculate the area of a specific land cover class within a given geometry.

    :param image: Earth Engine Image representing the land cover data
    :param class_value: Integer representing the land cover class
    :param geometry: Earth Engine Geometry defining the area to calculate within
    :param district_name: Name of the district
    :param state_name: Name of the state
    :return: Area of the specified class in hectares
    """
    area_image = image.eq(class_value).multiply(ee.Image.pixelArea())
    area_calculation = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=10,
        maxPixels=1e10
    )
    
    # Check available bands
    area_value = area_calculation.getInfo()
    print(f"Available bands: {area_value}")
    
    # Determine band name based on what's available in the image
    if 'remapped' in area_value:
        band_name = 'remapped'
    elif 'NDVI' in area_value:
        band_name = 'NDVI'
    elif 'b1' in area_value:
        band_name = 'b1'
    else:
        # If none of the expected bands are found, raise an error
        raise ValueError(f"No expected bands found in the image data. Available bands: {area_value}")
    
    # Get the area value for the determined band
    if band_name not in area_value:
        raise ValueError(f"Band '{band_name}' is missing in the image data for district '{district_name}'.")
    
    return area_value[band_name] / 1e4

def get_area_change(request: HttpRequest) -> JsonResponse:
    """
    Calculate the area change for single and double cropping cropland over multiple years.

    :param request: HttpRequest object
    :return: JsonResponse containing the area change data or an error message
    """
    ee.Initialize(credentials)

    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()
    subdistrict_name = request.GET.get('subdistrict_name', '').lower()
    village_name = request.GET.get('village_name', '').lower()
    village_id = request.GET.get('village_id', '')
    
    # Extract the village ID from the name if in format "name - id" and no explicit ID provided
    if ' - ' in village_name and not village_id:
        parts = village_name.split(' - ')
        village_name = parts[0].strip()
        if len(parts) > 1:
            village_id = parts[1].strip()

    if not (state_name and district_name):
        return JsonResponse(
            {'error': 'All parameters (state_name, district_name) are required.'}, status=400)

    try:
        # Get precise village boundary using ID if available
        if village_id:
            # Try to get the specific village by ID
            shrug = shrug_dataset()
            village_fc = shrug.filter(
                ee.Filter.And(
                    ee.Filter.eq(shrug_fields['state_field'], state_name),
                    ee.Filter.eq(shrug_fields['district_field'], district_name),
                    ee.Filter.eq(shrug_fields['subdistrict_field'], subdistrict_name),
                    ee.Filter.eq('pc11_tv_id', village_id)
                )
            )
            
            # Check if we got the village
            count = village_fc.size().getInfo()
            if count == 0:
                print(f"No village found with ID {village_id}, falling back to name search")
                # Fall back to normal village boundary search if ID not found
                village_fc = village_boundary(state_name, district_name, subdistrict_name, village_name)
            else:
                print(f"Successfully found village with ID {village_id} for area change calculation")
        else:
            # If no ID, use the normal village boundary function
            village_fc = village_boundary(state_name, district_name, subdistrict_name, village_name)
        
        # Check if we have village features
        count = village_fc.size().getInfo()
        if count == 0:
            return JsonResponse({'error': f"No village found with name {village_name}"}, status=404)
        elif count > 1:
            print(f"Warning: Found {count} features for {village_name}, using the first one for area change")
            # Get the first feature to be very explicit
            first_feature = ee.Feature(village_fc.first())
            village_fc = ee.FeatureCollection([first_feature])
        
        village_geometry = village_fc.geometry()

        # Choose the correct image collection based on state and district
        is_bhuvan = False
        if state_name in ['maharashtra', 'uttar pradesh', 'jharkhand']:
            print(f"Using Bhuvan LULC for state: {state_name}")
            image_collection = ee.ImageCollection(ee_assets['bhuvan_lulc']).filterBounds(village_geometry)
            year_range = range(2005, 2024)  # Bhuvan data range
            is_bhuvan = True
        elif district_name in ['vadodara']:
            image_collection = ee.ImageCollection('users/jaltolwelllabs/LULC/Farmboundary_NDVI_Tree').filterBounds(village_geometry)
            print(f"Using Farmboundary_NDVI asset for district: {district_name}")
            year_range = range(2017, 2024)
            is_bhuvan = False
        else:
            image_collection = ee.ImageCollection('users/jaltolwelllabs/LULC/IndiaSAT_V2_draft').filterBounds(village_geometry)
            year_range = range(2017, 2023)
            is_bhuvan = False
        
        area_change_data = {}
        
        # Batch area calculations more efficiently
        for year in year_range:
            try:
                if year == 2019 and is_bhuvan:
                    print(f"Skipping 2019 for Bhuvan LULC states")
                    continue
                    
                start_date = ee.Date.fromYMD(year, 6, 1)
                end_date = start_date.advance(1, 'year')
                year_filtered = image_collection.filterDate(start_date, end_date)
                
                # Skip years with no data
                if year_filtered.size().getInfo() == 0:
                    print(f"No data for year {year}, skipping")
                    continue
                    
                year_image = year_filtered.mosaic()

                # Apply appropriate remapping based on the data source
                if is_bhuvan:
                    # For Bhuvan LULC, apply remapping specific to Bhuvan classes
                    valuesToKeep = [2, 3, 4, 5, 7, 8, 9, 10, 12]
                    targetValues = [8, 8, 8, 10, 6, 6, 6, 12, 12]
                    remapped_image = year_image.select('b1').remap(valuesToKeep, targetValues, 0)
                else:
                    # For IndiaSAT and FarmBoundary, use original remapping approach
                    remapped_image = year_image
                
                # Optimize: Calculate all areas at once instead of separately
                # Create a single image with different bands for each class
                class_image = ee.Image.cat([
                    remapped_image.eq(8).rename('single_crop'),  # Single cropping (class 8)
                    remapped_image.eq(10).rename('double_crop'), # Double cropping (class 10)
                    remapped_image.eq(6).rename('tree_cover')    # Tree cover (class 6)
                ]).multiply(ee.Image.pixelArea())
                
                # Calculate all areas in a single reduceRegion call
                areas = class_image.reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=village_geometry,
                    scale=10,
                    maxPixels=1e10
                ).getInfo()
                
                # Convert from sq m to hectares
                area_change_data[year] = {
                    'Single cropping cropland': areas.get('single_crop', 0) / 1e4,
                    'Double cropping cropland': areas.get('double_crop', 0) / 1e4,
                    'Tree Cover Area': areas.get('tree_cover', 0) / 1e4
                }
            except Exception as e:
                print(f"Error processing year {year}: {e}")
                # Continue with other years if one fails

        if not area_change_data:
            return JsonResponse({'error': 'No area change data available for any year'}, status=404)

        return JsonResponse(area_change_data)

    except Exception as e:
        print(f"Error in get_area_change: {e}")
        return JsonResponse({'error': str(e)}, status=500)



def get_control_village(request: HttpRequest) -> JsonResponse:
    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()
    subdistrict_name = request.GET.get('subdistrict_name', '').lower()
    village_name = request.GET.get('village_name', '').lower()
    
    # Extract just the village name if it's in the format "name - id"
    if ' - ' in village_name:
        village_name = village_name.split(' - ')[0]

    try:
        control_village = compare_village(
            state_name, district_name, subdistrict_name, village_name)
        geo_json = control_village.getInfo()

        return JsonResponse(geo_json)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
def custom_polygon_comparison(request: HttpRequest) -> JsonResponse:
    """
    Process custom polygons uploaded as GeoJSON and compare with generated circles in control village.
    
    :param request: HttpRequest object with GeoJSON data and village parameters
    :return: JsonResponse with comparison results
    """
    ee.Initialize(credentials)
    
    # Extract parameters from request
    state_name = request.POST.get('state_name', '').lower()
    district_name = request.POST.get('district_name', '').lower()
    subdistrict_name = request.POST.get('subdistrict_name', '').lower()
    village_name = request.POST.get('village_name', '').lower()
    village_id = request.POST.get('village_id', '')
    control_village_name = request.POST.get('control_village_name', '')
    control_village_id = request.POST.get('control_village_id', '')
    year = request.POST.get('year')
    
    # Check required parameters
    if not all([state_name, district_name, subdistrict_name, village_name, year]):
        return JsonResponse(
            {'error': 'Required parameters missing (state, district, subdistrict, village, year)'}, 
            status=400
        )
    
    try:
        # Parse JSON data from request
        geojson_data = json.loads(request.POST.get('geojson', '{}'))
        if not geojson_data or 'features' not in geojson_data:
            return JsonResponse({'error': 'Invalid GeoJSON data'}, status=400)
        
        # Clean village name and ID if in combined format
        if ' - ' in village_name and not village_id:
            parts = village_name.split(' - ')
            village_name = parts[0].strip()
            if len(parts) > 1:
                village_id = parts[1].strip()
        
        # Get the intervention village boundary
        intervention_village = village_boundary(
            state_name, district_name, subdistrict_name, village_name, village_id
        )
        
        # Get or find control village
        if control_village_name:
            # If control village is explicitly specified
            if ' - ' in control_village_name and not control_village_id:
                parts = control_village_name.split(' - ')
                control_village_name = parts[0].strip()
                if len(parts) > 1:
                    control_village_id = parts[1].strip()
                    
            control_village = village_boundary(
                state_name, district_name, subdistrict_name, control_village_name, control_village_id
            )
        else:
            # Find control village automatically using the existing comparison function
            control_village_feature = compare_village(
                state_name, district_name, subdistrict_name, village_name
            )
            control_village = ee.FeatureCollection([control_village_feature])
        
        # Number of points/circles to generate
        num_points = 10
        
        # Process the polygon and generate circles
        result = process_custom_polygon(geojson_data, control_village, num_points)
        circles = result['circles']
        
        # Get appropriate LULC image based on state/district
        year_int = int(year)
        
        # Get LULC for analyzing polygon and circles
        lulc_image = get_lulc_for_region(
            year_int, state_name, district_name, intervention_village.geometry().buffer(1000)
        )
        
        # Define LULC class mappings based on the data source
        if state_name.lower() in ['maharashtra', 'uttar pradesh', 'jharkhand']:
            # Bhuvan LULC classes
            class_mapping = {
                'single_crop': [2, 3, 4],  # Single cropping classes
                'double_crop': [5],        # Double cropping classes
                'tree_cover': [7, 8, 9]    # Tree cover classes
            }
        else:
            # IndiaSAT/FarmBoundary classes
            class_mapping = {
                'single_crop': [8],        # Single cropping class
                'double_crop': [10],       # Double cropping class 
                'tree_cover': [6]          # Tree cover class
            }
        
        # Calculate area statistics for the custom polygon
        custom_polygon_stats = lulc_area_stats(
            lulc_image, ee.FeatureCollection(geojson_data).geometry(), class_mapping
        )
        
        # Calculate area statistics for the circles
        circles_stats = lulc_area_stats(
            lulc_image, circles.geometry(), class_mapping
        )
        
        # Prepare response with comparison results
        response_data = {
            'intervention': {
                'name': village_name,
                'id': village_id,
                'custom_polygon_area_ha': result['polygon_area'] / 10000,  # Convert to hectares
                'crop_stats': custom_polygon_stats
            },
            'control': {
                'name': control_village_name or control_village_feature.get('village_na').getInfo(),
                'id': control_village_id or control_village_feature.get('pc11_tv_id', '').getInfo(),
                'circles_area_ha': circles.geometry().area().getInfo() / 10000,  # Convert to hectares
                'radius_meters': result['radius'],
                'num_circles': num_points,
                'crop_stats': circles_stats
            },
            'year': year
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        import traceback
        print(f"Error in custom_polygon_comparison: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)
