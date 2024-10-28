from typing import Dict, Any
from venv import logger
from django.http import HttpResponse, JsonResponse, HttpRequest
from rest_framework import viewsets
import ee
from rest_framework.views import APIView
from rest_framework.response import Response


from .utils import initialize_earth_engine
from .ee_processing import compare_village, district_boundary, IndiaSAT_lulc, IMD_precipitation, village_boundary, FarmBoundary_lulc
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
        JsonResponse: A JSON response containing a list of villages.
    """
    villages = Village.objects.filter(subdistrict__id=subdistrict_id)
    data: List[Dict[str, str]] = [{"id": village.id, "name": village.name} for village in villages]
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

    if not (state_name and district_name):
        return JsonResponse(
            {'error': 'All parameters (state_name, district_name) are required.'}, status=400)

    try:
        rainfall_data = IMD_precipitation(
            2014,
            2022,
            state_name,
            district_name,
            subdistrict_name,
            village_name)

        return rainfall_data
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_boundary_data(request: HttpRequest) -> JsonResponse:
    """
    Get the boundary data for a specified state and district.

    :param request: HttpRequest object
    :return: JsonResponse containing the boundary GeoJSON data or an error message
    """
    ee.Initialize(credentials)

    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()

    if not (state_name and district_name):
        return JsonResponse(
            {'error': 'All parameters (state_name, district_name) are required.'}, status=400)

    try:
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
    year = request.GET.get('year')

    try:
        if not all((state_name, district_name)):
            raise ValueError(
                'parameters (state_name, district_name) are required.')

        # Choose the correct image based on district name
        # added for jaltol testing purposes the if statement below
        if district_name in ["chitrakoot", "saraikela kharsawan", "aurangabad", "nashik"]:
            print("Using Farmboundary_NDVI asset for district:", district_name)
            

            image = FarmBoundary_lulc(
                year,
                state_name,
                district_name,
                subdistrict_name,
                village_name)
        else:
            image = IndiaSAT_lulc(
                year,
                state_name,
                district_name,
                subdistrict_name,
                village_name)

        valuesToKeep = [6, 8, 9, 10, 11, 12]
        targetValues = [6, 8, 8, 10, 10, 12]
        remappedImage = image.remap(valuesToKeep, targetValues, 0)
        mask = remappedImage.gte(6).And(remappedImage.lte(12))
        remappedImage = remappedImage.updateMask(mask)

        # Define visualization parameters
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

        # Get the map ID and token
        map_id_dict = remappedImage.getMapId(vis_params)

        # Construct the tiles URL template
        tiles_url = map_id_dict['tile_fetcher'].url_format

        return JsonResponse({'tiles_url': tiles_url})
    except Exception as e:
        logger.error('Failed to get LULC raster', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


def calculate_class_area(
        image: ee.Image,
        class_value: int,
        geometry: ee.Geometry,
        district_name: str) -> float:
    """
    Calculate the area of a specific land cover class within a given geometry.

    :param image: Earth Engine Image representing the land cover data
    :param class_value: Integer representing the land cover class
    :param geometry: Earth Engine Geometry defining the area to calculate within
    :return: Area of the specified class in hectares
    """
    area_image = image.eq(class_value).multiply(ee.Image.pixelArea())
    area_calculation = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=10,
        maxPixels=1e10
    )
    # Use 'NDVI' band for 'chitrakoot' district and 'b1' for others
    band_name = 'NDVI' if district_name in ["chitrakoot", "saraikela kharsawan", "aurangabad", "nashik"] else 'b1'
    
    area_value = area_calculation.getInfo()
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

    if not (state_name and district_name):
        return JsonResponse(
            {'error': 'All parameters (state_name, district_name) are required.'}, status=400)

    try:
        village_geometry = village_boundary(
            state_name,
            district_name,
            subdistrict_name,
            village_name).geometry()

        # Choose the correct image collection based on district name
        # added for jaltol testing purposes the if statement below
        if district_name in ["chitrakoot", "saraikela kharsawan", "aurangabad", "nashik"]:
            image_collection = ee.ImageCollection('users/jaltolwelllabs/LULC/Farmboundary_NDVI').filterBounds(village_geometry)
            print("Using Farmboundary_NDVI asset for area change for district:", district_name)
            print("band names",ee.Image(image_collection.first()).bandNames().getInfo())

        else:
            image_collection = ee.ImageCollection('users/jaltolwelllabs/LULC/IndiaSAT_V2_draft').filterBounds(village_geometry)

        class_labels = {
            '8': 'Single cropping cropland',
            '9': 'Single cropping cropland',
            '10': 'Double cropping cropland',
            '11': 'Double cropping cropland',
        }

        area_change_data: Dict[int, Dict[str, float]] = {}
        for year in range(2017, 2023):
            start_date = ee.Date.fromYMD(year, 6, 1)
            end_date = start_date.advance(1, 'year')
            year_image = image_collection.filterDate(start_date, end_date).mosaic()

            single_cropping_area = sum(
                calculate_class_area(year_image, int(class_value), village_geometry, district_name)
                for class_value in ['8', '9']
            )

            double_cropping_area = sum(
                calculate_class_area(year_image, int(class_value), village_geometry, district_name)
                for class_value in ['10', '11']
            )

            area_change_data[year] = {
                'Single cropping cropland': single_cropping_area,
                'Double cropping cropland': double_cropping_area
            }

        return JsonResponse(area_change_data)

    except Exception as e:
        logger.error('Failed to get area change', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)



def get_control_village(request: HttpRequest) -> JsonResponse:
    """
    Fetch control village data by comparing it with another village.

    :param request: HttpRequest object
    :return: JsonResponse containing the control village GeoJSON data or an error message
    """
    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()
    subdistrict_name = request.GET.get('subdistrict_name', '').lower()
    village_name = request.GET.get('village_name', '').lower()

    try:
        control_village = compare_village(
            state_name, district_name, subdistrict_name, village_name)
        geo_json = control_village.getInfo()

        return JsonResponse(geo_json)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
