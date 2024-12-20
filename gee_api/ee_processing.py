from django.http import HttpResponse, JsonResponse, HttpRequest
from datetime import datetime
from venv import logger
import ee
from django.conf import settings
from django.shortcuts import render
from pathlib import Path
from django.views.decorators.http import require_http_methods
from typing import Optional, Dict, Any

# Constants Import
from .constants import ee_assets, shrug_dataset, shrug_fields, compare_village_buffer

# Initialize Earth Engine credentials
email = "admin-133@ee-papnejaanmol.iam.gserviceaccount.com"
key_file = "./creds/ee-papnejaanmol-23b4363dc984.json"
credentials = ee.ServiceAccountCredentials(email=email, key_file=key_file)
ee.Initialize(credentials)


def district_boundary(
        state_name: str,
        district_name: str) -> ee.FeatureCollection:
    """
    Retrieve the boundary for a specified district within a state.

    :param state_name: Name of the state
    :param district_name: Name of the district
    :return: Earth Engine FeatureCollection representing the district boundary
    :raises: ValueError if there is an error fetching the district boundary
    """
    try:
        shrug = shrug_dataset()
        return shrug.filter(
            ee.Filter.And(
                ee.Filter.eq(shrug_fields['state_field'], state_name),
                ee.Filter.eq(shrug_fields['district_field'], district_name)
            )
        )
    except Exception as e:
        raise ValueError(f"Error in fetching district boundary: {e}")
    
def subdistrict_boundary(
        state_name: str,
        district_name: str, 
        subdistrict_name: str ) -> ee.FeatureCollection:
    
    """
    Retrieve the boundary for a specified district within a state.

    :param state_name: Name of the state
    :param district_name: Name of the district
    :return: Earth Engine FeatureCollection representing the district boundary
    :raises: ValueError if there is an error fetching the district boundary
    """
    try:
        shrug = shrug_dataset()
        return shrug.filter(
            ee.Filter.And(
                ee.Filter.eq(shrug_fields['state_field'], state_name),
                ee.Filter.eq(shrug_fields['district_field'], district_name),
                ee.Filter.eq(shrug_fields['subdistrict_field'], subdistrict_name),
            )
        )
    except Exception as e:
        raise ValueError(f"Error in fetching district boundary: {e}")


def village_boundary(
        state_name: str,
        district_name: str,
        subdistrict_name: str,
        village_name: str) -> ee.FeatureCollection:
    """
    Retrieve the boundary for a specified village within a subdistrict, district, and state.

    :param state_name: Name of the state
    :param district_name: Name of the district
    :param subdistrict_name: Name of the subdistrict
    :param village_name: Name of the village
    :return: Earth Engine FeatureCollection representing the village boundary
    :raises: ValueError if there is an error fetching the village boundary
    """
    try:
        shrug = shrug_dataset()
        return shrug.filter(
            ee.Filter.And(
                ee.Filter.eq(shrug_fields['state_field'], state_name),
                ee.Filter.eq(shrug_fields['district_field'], district_name),
                ee.Filter.eq(shrug_fields['subdistrict_field'], subdistrict_name),
                ee.Filter.eq(shrug_fields['village_field'], village_name)
            )
        )
    except Exception as e:
        raise ValueError(f"Error in fetching village boundary: {e}")


def srtm_slope() -> ee.Image:
    """
    Retrieve the slope from the SRTM dataset.

    :return: Earth Engine Image representing the slope
    :raises: ValueError if there is an error fetching the SRTM slope
    """
    try:
        return ee.Terrain.slope(
            ee.Image(ee_assets['srtm']).select('elevation'))
    except Exception as e:
        raise ValueError(f"Error in fetching SRTM slope: {e}")


def compute_slope(feature: ee.Feature) -> ee.Feature:
    """
    Compute the slope standard deviation for a given feature.

    :param feature: Earth Engine Feature for which to compute the slope
    :return: Feature with added slope standard deviation property
    """
    slope = srtm_slope()
    std_dev = slope.reduceRegion(
        reducer=ee.Reducer.stdDev(),
        geometry=feature.geometry(),
        scale=30
    )
    return feature.set('slope_std_dev', std_dev.getNumber('slope'))


def get_buffer(feature: ee.Feature) -> ee.Geometry:
    """
    Generate a buffered geometry for the given feature.

    :param feature: Earth Engine Feature to buffer
    :return: Buffered geometry of the feature
    """
    return feature.geometry().buffer(compare_village_buffer)


def compare_village(
        state_name: str,
        district_name: str,
        subdistrict_name: str,
        village_name: str) -> ee.Feature:
    """
    Compare a village's slope with other villages within the district.

    :param state_name: Name of the state
    :param district_name: Name of the district
    :param subdistrict_name: Name of the subdistrict
    :param village_name: Name of the village
    :return: Feature representing the selected village after comparison
    :raises: ValueError if there is an error in the comparison process
    """
    try:
        village = village_boundary(
            state_name,
            district_name,
            subdistrict_name,
            village_name)
        intervention_slope = compute_slope(village)
        null_filter = ee.Filter.eq(shrug_fields['village_field'], '').Not()
        spatial_filter = ee.Filter.eq(
            shrug_fields['village_field'],
            village_name).Not()
        # being changed for jaltol testing purpose from district_boundary to subdistrict_boundary
        buffer_fc = subdistrict_boundary(state_name, district_name, subdistrict_name).filterBounds(
            get_buffer(village)).filter(spatial_filter).filter(null_filter).map(compute_slope)
        value_to_subtract = ee.Number(intervention_slope.get('slope_std_dev'))

        def subtract_value(feature: ee.Feature) -> ee.Feature:
            property_value = ee.Number(feature.get('slope_std_dev'))
            new_property_value = ee.Number(((property_value.subtract(
                value_to_subtract)).divide(value_to_subtract)).multiply(100)).abs()
            return feature.set('slope_diff', new_property_value)

        selected_village = buffer_fc.map(
            subtract_value).sort('slope_diff').first()
        return selected_village

    except Exception as e:
        raise ValueError(f"Error in comparing villages: {e}")


def IndiaSAT_lulc(
        year: int,
        state_name: str,
        district_name: str,
        subdistrict_name: Optional[str] = None,
        village_name: Optional[str] = None) -> ee.Image:
    """
    Retrieve the Land Use Land Cover (LULC) data for a specified area and year.

    :param year: Year for which to retrieve the LULC data
    :param state_name: Name of the state
    :param district_name: Name of the district
    :param subdistrict_name: Optional name of the subdistrict
    :param village_name: Optional name of the village
    :return: Earth Engine Image representing the LULC data
    :raises: ValueError if there is an error fetching the LULC data
    """
    try:
        indiasat = ee.ImageCollection(ee_assets['indiasat'])

        start_date = f'{year}-07-01'
        end_date = f'{int(year) + 1}-06-30'

        if subdistrict_name and village_name:
            village_fc = village_boundary(
                state_name, district_name, subdistrict_name, village_name)
            return indiasat.filterBounds(village_fc).filterDate(
                start_date, end_date).mosaic().clipToCollection(village_fc)
        else:
            district_fc = district_boundary(state_name, district_name)
            return indiasat.filterBounds(district_fc).filterDate(
                start_date, end_date).mosaic().clipToCollection(district_fc)

    except Exception as e:
        raise ValueError(f"Error in fetching IndiaSAT: {e}")

def FarmBoundary_lulc(
        year: int,
        state_name: str,
        district_name: str,
        subdistrict_name: Optional[str] = None,
        village_name: Optional[str] = None) -> ee.Image:
    """
    Retrieve the Land Use Land Cover (LULC) data for a specified area and year.

    :param year: Year for which to retrieve the LULC data
    :param state_name: Name of the state
    :param district_name: Name of the district
    :param subdistrict_name: Optional name of the subdistrict
    :param village_name: Optional name of the village
    :return: Earth Engine Image representing the LULC data
    :raises: ValueError if there is an error fetching the LULC data
    """
    try:
        farmboundary = ee.ImageCollection(ee_assets['farmboundary'])

        start_date = f'{year}-07-01'
        end_date = f'{int(year) + 1}-06-30'

        if subdistrict_name and village_name:
            village_fc = village_boundary(
                state_name, district_name, subdistrict_name, village_name)
            return farmboundary.filterBounds(village_fc).filterDate(
                start_date, end_date).mosaic().clipToCollection(village_fc)
        else:
            district_fc = district_boundary(state_name, district_name)
            return farmboundary.filterBounds(district_fc).filterDate(
                start_date, end_date).mosaic().clipToCollection(district_fc)

    except Exception as e:
        raise ValueError(f"Error in fetching FarmBoundary: {e}")

def yearly_sum(year: int) -> ee.Image:
    """
    Calculate the yearly sum of precipitation for a given year.

    :param year: The year for which to calculate the precipitation sum
    :return: Earth Engine Image representing the sum of precipitation for the year
    """
    ee.Initialize(credentials)
    precipitation_collection = ee.ImageCollection(ee_assets['imd_rain'])
    filter = precipitation_collection.filterDate(
        ee.Date.fromYMD(
            year, 6, 1), ee.Date.fromYMD(
            ee.Number(year).add(1), 6, 1))
    date = filter.first().get('system:time_start')
    return filter.sum().set('system:time_start', date)


def getStats(image: ee.Image, geometry: ee.Geometry) -> ee.Image:
    """
    Calculate statistics (e.g., mean) for a given image over a specified geometry.

    :param image: Earth Engine Image to calculate statistics for
    :param geometry: Earth Engine Geometry over which to calculate statistics
    :return: Image with added statistics as properties
    """
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=1000
    )
    return image.setMulti(stats)


def IMD_precipitation(
        start_year: int,
        end_year: int,
        state_name: str,
        district_name: str,
        subdistrict_name: Optional[str],
        village_name: Optional[str]) -> JsonResponse:
    """
    Retrieve the IMD precipitation data for a specified time range and location.

    :param start_year: The start year for the precipitation data
    :param end_year: The end year for the precipitation data
    :param state_name: Name of the state
    :param district_name: Name of the district
    :param subdistrict_name: Optional name of the subdistrict
    :param village_name: Optional name of the village
    :return: JsonResponse containing the precipitation data or an error message
    """
    try:
        village_geometry = village_boundary(
            state_name,
            district_name,
            subdistrict_name,
            village_name).geometry()
        year_list = list(range(start_year, end_year + 1))
        hyd_yr_col = ee.ImageCollection(
            ee.List(year_list).map(lambda year: yearly_sum(year)))
        collection_with_stats = hyd_yr_col.map(
            lambda image: getStats(image, village_geometry))

        # Extract rainfall values and dates
        rain_values = collection_with_stats.aggregate_array('b1').getInfo()
        dates = collection_with_stats.aggregate_array(
            'system:time_start').getInfo()
        dates = [datetime.fromtimestamp(
            date / 1000).strftime('%Y') for date in dates]

        # Combine dates and rain values for the response
        rainfall_data = list(zip(dates, rain_values))
        return JsonResponse({'rainfall_data': rainfall_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
