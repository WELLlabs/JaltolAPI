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

# Constants Import

from .constants import ee_assets, shrug_dataset, shrug_fields, compare_village_buffer


email = "admin-133@ee-papnejaanmol.iam.gserviceaccount.com"
key_file = "./creds/ee-papnejaanmol-23b4363dc984.json"
credentials = ee.ServiceAccountCredentials(email=email, key_file=key_file)

from django.http import HttpResponse
ee.Initialize(credentials)


def district_boundary(state_name, district_name):    
    try:
        shrug = shrug_dataset()
       
        return shrug.filter(ee.Filter.And(ee.Filter.eq(shrug_fields['state_field'], state_name), ee.Filter.eq(shrug_fields['district_field'], district_name)))
    except Exception as e:
        raise ValueError(f"Error in fetching district boundary: {e}")


def village_boundary(state_name, district_name, subdistrict_name, village_name):
    try:
        shrug = shrug_dataset()
        return shrug.filter(ee.Filter.And(ee.Filter.eq(shrug_fields['state_field'], state_name), ee.Filter.eq(shrug_fields['district_field'], district_name), ee.Filter.eq(shrug_fields['subdistrict_field'], subdistrict_name), ee.Filter.eq(shrug_fields['village_field'], village_name)))
    except Exception as e:
        raise ValueError(f"Error in fetching village boundary: {e}")

def srtm_slope():
    try:
        return ee.Terrain.slope(ee.Image(ee_assets['srtm']).select('elevation'))
    except Exception as e:
        raise ValueError(f"Error in fetching srtm slope: {e}")

def compute_slope(feature):
    slope = srtm_slope()
    std_dev = slope.reduceRegion(
        reducer=ee.Reducer.stdDev(),
        geometry=feature.geometry(),
        scale=30
        )
    return feature.set('slope_std_dev', std_dev.getNumber('slope'))

def get_buffer(feature):
    return feature.geometry().buffer(compare_village_buffer)


def compare_village(state_name, district_name, subdistrict_name, village_name):
    try:
        village = village_boundary(state_name, district_name, subdistrict_name, village_name)
        intervention_slope = compute_slope(village)
        null_filter = ee.Filter.eq(shrug_fields['village_field'], '').Not()
        spatial_filter = ee.Filter.eq(shrug_fields['village_field'], village_name).Not()
        buffer_fc = district_boundary(state_name, district_name).filterBounds(get_buffer(village)).filter(spatial_filter).filter(null_filter).map(compute_slope)
        value_to_subtract = ee.Number(intervention_slope.get('slope_std_dev'))
        def subtract_value(feature):
           property_value = ee.Number(feature.get('slope_std_dev'))
           new_property_value = ee.Number(((property_value.subtract(value_to_subtract)).divide(value_to_subtract)).multiply(100)).abs()
           return feature.set('slope_diff', new_property_value)
        selected_village = buffer_fc.map(subtract_value).sort('slope_diff').first()
        return selected_village
        
    except Exception as e:
        raise ValueError(f"Error in comparing villages: {e}")
    
def IndiaSAT_lulc(year, state_name, district_name, subdistrict_name = None, village_name=None):
    try:
        indiasat = ee.ImageCollection(ee_assets['indiasat'])
        
        start_date = f'{year}-07-01'
        end_date = f'{int(year) + 1}-06-30' 
        
        if subdistrict_name and village_name:
            village_fc = village_boundary(state_name, district_name, subdistrict_name, village_name)
            return indiasat.filterBounds(village_fc).filterDate(start_date,end_date).mosaic().clipToCollection(village_fc)
        else:
            district_fc = district_boundary(state_name, district_name)
            return indiasat.filterBounds(district_fc).filterDate(start_date,end_date).mosaic().clipToCollection(district_fc)
        
    except Exception as e:
        raise ValueError(f"Error in fetching IndiaSAT: {e}")


def yearly_sum(year: int) -> ee.Image:
    ee.Initialize(credentials)
    # Your provided yearly_sum function here
    precipitation_collection =  ee.ImageCollection(ee_assets['imd_rain'])
    filter = precipitation_collection.filterDate(ee.Date.fromYMD(year, 6, 1),
                                                 ee.Date.fromYMD(ee.Number(year).add(1), 6, 1))
    date = filter.first().get('system:time_start')
    return filter.sum().set('system:time_start', date)

# Function to get statistics for an image
def getStats(image: ee.Image, geometry: ee.Geometry) -> ee.Image:
    # Your provided getStats function here
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=1000
    )
    return image.setMulti(stats)

def IMD_precipitation(start_year, end_year, state_name, district_name, subdistrict_name, village_name):
    try:
        
        village_geometry = village_boundary(state_name, district_name, subdistrict_name, village_name).geometry()
        year_list = list(range(start_year, end_year + 1))
        hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year)))
        collection_with_stats = hyd_yr_col.map(lambda image: getStats(image, village_geometry))

        # Extract rainfall values and dates
        rain_values = collection_with_stats.aggregate_array('b1').getInfo()  
        dates = collection_with_stats.aggregate_array('system:time_start').getInfo()
        dates = [datetime.fromtimestamp(date / 1000).strftime('%Y') for date in dates]
        print(rain_values)
        print(dates)

        # Combine dates and rain values for the response
        rainfall_data = list(zip(dates, rain_values))
        return JsonResponse({'rainfall_data': rainfall_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



