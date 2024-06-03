# gee_api/views.py
from datetime import datetime
from venv import logger  
from django.http import JsonResponse
from .utils import initialize_earth_engine
import ee
from django.conf import settings
import json
from django.shortcuts import render
from pathlib import Path
from django.views.decorators.http import require_http_methods

from .ee_processing import compare_village, district_boundary, IndiaSAT_lulc, IMD_precipitation, village_boundary

email = "admin-133@ee-papnejaanmol.iam.gserviceaccount.com"
key_file = "./creds/ee-papnejaanmol-23b4363dc984.json"
credentials = ee.ServiceAccountCredentials(email=email, key_file=key_file)

from django.http import HttpResponse
ee.Initialize(credentials)

def health_check(request):
    # Perform necessary health check logic here
    return HttpResponse("OK")


def get_karauli_raster(request, district_name):
    ee.Initialize(credentials)
    
    try:
        # Access the ImageCollection for Karauli
        district_fc = ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/hackathon_dists').filter(ee.Filter.eq('district_n', district_name)).geometry().centroid()
        
        image_collection = ee.ImageCollection('users/jaltolwelllabs/LULC/hackathon').filterBounds(district_fc).filterDate('2022-07-01','2023-06-30').first()
        
        # Here you might want to select a specific image by date or other criteria.
        # For example, to get the first image:
        # image = ee.Image(image_collection.filterDate('2022-07-01', '2023-06-30').first())
        image = ee.Image(image_collection)
        
        valuesToKeep = [6, 8, 9, 10,11,12]
        targetValues = [6,8,8,10,10,12]
        remappedImage = image.remap( valuesToKeep, targetValues,0 )
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


# View function to fetch rainfall data
def get_rainfall_data(request):
    ee.Initialize(credentials)
     
    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()
    subdistrict_name = request.GET.get('subdistrict_name', '').lower()
    village_name = request.GET.get('village_name', '').lower()

    if not (state_name and district_name ):
        return JsonResponse({'error': 'All parameters (state_name, district_name) are required.'}, status=400)
    
    
    try:
        rainfall_data = IMD_precipitation(2014, 2022, state_name, district_name, subdistrict_name, village_name)
       

        return rainfall_data
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    
def get_boundary_data(request):
    ee.Initialize(credentials)
    # Extract the parameters from the query string
    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()


    if not (state_name and district_name ):
        return JsonResponse({'error': 'All parameters (state_name, district_name) are required.'}, status=400)

    try:
        # if __name__ == '__main__':
        geojson = district_boundary(state_name, district_name).getInfo()
        return JsonResponse(geojson)        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    
    
def get_lulc_raster(request):
    ee.Initialize(credentials)
    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()
    subdistrict_name = request.GET.get('subdistrict_name', '').lower()
    village_name = request.GET.get('village_name', '').lower()
    year = request.GET.get('year')
    
    try: 
        if not all((state_name, district_name)): 
            raise ValueError('parameters (state_name, district_name) are required.')      
        image = IndiaSAT_lulc(year, state_name, district_name, subdistrict_name, village_name)        
        
        valuesToKeep = [6, 8, 9, 10,11,12]
        targetValues = [6,8,8,10,10,12]
        remappedImage = image.remap( valuesToKeep, targetValues,0 )
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
        logger.error('Failed to get LULC raster', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
 


def calculate_class_area(image, class_value, geometry):
    area_image = image.eq(class_value).multiply(ee.Image.pixelArea())
    area_calculation = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=10,
        maxPixels=1e10
    )
    return area_calculation.get('b1').getInfo()/1e4

def get_area_change(request):
    # Initialize your Earth Engine credentials if not already initialized
    ee.Initialize(credentials)
    
    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()
    subdistrict_name = request.GET.get('subdistrict_name', '').lower()
    village_name = request.GET.get('village_name', '').lower()

    if not (state_name and district_name ):
        return JsonResponse({'error': 'All parameters (state_name, district_name) are required.'}, status=400)

    try:
        # Get the geometry for the specific village
        village_geometry = village_boundary(state_name, district_name,subdistrict_name,village_name).geometry()
         # Define the ImageCollection for Karauli LandUseLandCover
        image_collection = ee.ImageCollection('users/jaltolwelllabs/LULC/IndiaSAT_V2_draft').filterBounds(village_geometry)

    # Define the labels for the classes (only include the specified two classes)
        class_labels = {
            '8': 'Single cropping cropland',
            '9': 'Single cropping cropland',
            '10': 'Double cropping cropland',
            '11': 'Double cropping cropland',
        }

    # Compute the area for each class over the years
        area_change_data = {}
        for year in range(2014, 2023):  # Assuming you have data from 2014 to 2022
            # Filter the ImageCollection for the specific year
            start_date = ee.Date.fromYMD(year, 6, 1)
            end_date = start_date.advance(1, 'year')
            year_image = image_collection.filterDate(start_date, end_date).mosaic()

            # Calculate the area for single cropping cropland
            single_cropping_area = sum(calculate_class_area(year_image, int(class_value), village_geometry)
                                       for class_value in ['8', '9'])

            # Calculate the area for double cropping cropland
            double_cropping_area = sum(calculate_class_area(year_image, int(class_value), village_geometry)
                                       for class_value in ['10', '11'])

            if year not in area_change_data:
                area_change_data[year] = {}

            area_change_data[year]['Single cropping cropland'] = single_cropping_area
            area_change_data[year]['Double cropping cropland'] = double_cropping_area

        return JsonResponse(area_change_data)

    except Exception as e:
        logger.error('Failed to get area change', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
    
    
def get_control_village(request):
    
    state_name = request.GET.get('state_name', '').lower()
    district_name = request.GET.get('district_name', '').lower()
    subdistrict_name = request.GET.get('subdistrict_name', '').lower()
    village_name = request.GET.get('village_name', '').lower()
    
    try:
        control_village = compare_village(state_name, district_name, subdistrict_name, village_name)
        geo_json = control_village.getInfo()
        
        return JsonResponse(geo_json)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    