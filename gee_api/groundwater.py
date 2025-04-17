"""
Module for retrieving groundwater level data from I-WRIS.
"""
import requests
# import aiohttp
# import asyncio
import time
import json
from urllib.parse import urlencode
from math import radians, sin, cos, sqrt, atan2
import ee
from typing import Dict, List, Any, Optional, Tuple, Union


# URLs and constants
STATION_URL = 'https://arc.indiawris.gov.in/server/rest/services/NWIC/GroundwaterLevel_Stations/MapServer/0/query'
DATA_URL = 'https://indiawris.gov.in/gwldnlddata'
MAX_DISTANCE_KM = 10  # Maximum distance in km for considering stations
# MAX_RETRIES = 3  # Maximum retries for failed requests
# RETRY_DELAY = 1  # Delay between retries in seconds


def encode_url(base_url: str, params: Dict[str, Any]) -> str:
    """
    Encode parameters into a URL string.
    
    Args:
        base_url: Base URL
        params: Parameters to encode
    
    Returns:
        Encoded URL string
    """
    query_string = urlencode(params)
    return f"{base_url}?{query_string}"


def fetch_data(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Fetch data from a URL using GET request.
    
    Args:
        url: URL to fetch data from
        headers: Request headers
    
    Returns:
        JSON response or empty dict if request failed
    """
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else {}


def fetch_data_post(url: str, headers: Dict[str, str], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Fetch data from a URL using POST request.
    
    Args:
        url: URL to fetch data from
        headers: Request headers
        data: POST request payload
    
    Returns:
        JSON response or None if request failed
    """
    response = requests.post(url, headers=headers, json=data, verify=False)
    return response.json() if response.status_code == 200 else None


# Commenting out async implementation due to I-WRIS API compatibility issues
"""
async def fetch_data_post_async(url: str, headers: Dict[str, str], data: Dict[str, Any], year: int) -> Dict[int, Any]:
    # Implement with retries due to potential I-WRIS issues with async
    for attempt in range(MAX_RETRIES):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        return {year: await response.json()}
                    else:
                        # If I-WRIS rejects async request, we'll hit this and retry
                        await asyncio.sleep(RETRY_DELAY)
        except Exception as e:
            # If there's any other exception, log it and retry
            print(f"Error in async request (attempt {attempt+1}): {e}")
            await asyncio.sleep(RETRY_DELAY)
    
    # If all retries fail, fall back to synchronous request
    print(f"Falling back to synchronous request for year {year}")
    result = fetch_data_post(url, headers, data)
    return {year: result}
"""


def distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculate distance between two coordinates in kilometers using Haversine formula.
    
    Args:
        coord1: First coordinate (latitude, longitude)
        coord2: Second coordinate (latitude, longitude)
    
    Returns:
        Distance in kilometers
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371.0  # Radius of the Earth in kilometers

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def gen_data_payload(start_date: str, end_date: str, state_name: str) -> Dict[str, Any]:
    """
    Generate payload for groundwater level data request.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        state_name: Name of the state
    
    Returns:
        Payload dictionary for data request
    """
    return {
        "stnVal": {
            "Agency_name": "CGWB",
            "Child": "All",
            "Startdate": start_date,
            "Enddate": end_date,
            "Parent": f"\"'{state_name}'\"",
            "Reporttype": "GWL data",
            "Station": "All",
            "Timestep": "Daily",
            "View": "Admin",
            "file_name": "Sample"
        }
    }


def station_location(coordinates: List[List[float]]) -> Tuple[Dict[str, List[float]], set]:
    """
    Get groundwater monitoring stations within specified coordinates.
    
    Args:
        coordinates: List of coordinates defining a polygon
    
    Returns:
        Tuple of (station_dict, state_set) where:
            - station_dict: Dictionary mapping station names to coordinates
            - state_set: Set of state names covered by the stations
    """
    long, lat = zip(*coordinates)
    min_long, max_long, min_lat, max_lat = min(long), max(long), min(lat), max(lat)
    
    payload = {
        "where": "agency_name='CGWB'",
        "geometry": f'{{"spatialReference":{{"latestWkid":4326,"wkid":4326}},"xmin":{min_long},"ymin":{min_lat},"xmax":{max_long},"ymax":{max_lat}}}',
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "units": "esriSRUnit_Foot",
        "inSR": 4326,
        "outFields": "*",
        "returnGeometry": True,
        "returnTrueCurves": False,
        "outSR": 4326,
        "returnIdsOnly": False,
        "returnCountOnly": False,
        "orderByFields": "objectid ASC",
        "returnZ": False,
        "returnM": False,
        "returnDistinctValues": False,
        "featureEncoding": "esriDefault",
        "f": "geojson"
    }
    
    encoded_url = encode_url(STATION_URL, payload)
    response = fetch_data(encoded_url, headers={'Content-Type': 'application/json'})
    
    stations = {}
    state_set = set()
    
    if 'features' in response:
        for feat in response['features']:
            stations[feat['properties']['station_name']] = feat['geometry']['coordinates']
            state_set.add(feat['properties']['state_name'])
    
    return stations, state_set


def close_stations(roi_centroid: List[float], stations: Dict[str, List[float]]) -> List[str]:
    """
    Find closest stations to a point of interest.
    
    Args:
        roi_centroid: Center point [longitude, latitude]
        stations: Dictionary mapping station names to coordinates
    
    Returns:
        List of station names sorted by distance
    """
    dist_stations = {}
    for station, station_coord in stations.items():
        # Convert [longitude, latitude] to (latitude, longitude) for distance calculation
        dist = distance((roi_centroid[1], roi_centroid[0]), (station_coord[1], station_coord[0]))
        dist_stations[dist] = station
    
    return [dist_stations[k] for k in sorted(dist_stations.keys())]


# Commenting out async implementation
"""
async def fetch_GWL_data_async(years: List[int], state_set: set) -> List[Dict[int, Any]]:
    tasks = []
    headers = {'Content-Type': 'application/json'}
    
    # Create tasks for all year/state combinations
    for year in years:
        for statename in state_set:
            payload = gen_data_payload(f'{year}-07-01', f'{year+1}-07-01', statename)
            tasks.append(fetch_data_post_async(DATA_URL, headers, payload, year))
    
    # Run all tasks concurrently
    return await asyncio.gather(*tasks)
"""


# Using synchronous version only
def fetch_GWL_data(years: List[int], state_set: set) -> List[Dict[int, Any]]:
    """
    Fetch groundwater level data synchronously.
    
    Args:
        years: List of years to fetch data for
        state_set: Set of state names to fetch data for
    
    Returns:
        List of dictionaries with year as key and data as value
    """
    result = []
    headers = {'Content-Type': 'application/json'}
    
    for year in years:
        for statename in state_set:
            payload = gen_data_payload(f'{year}-07-01', f'{year+1}-07-01', statename)
            response = fetch_data_post(DATA_URL, headers, payload)
            result.append({year: response})
    
    return result


# Commenting out async implementation
"""
async def get_groundwater_level_async(
    village_fc: ee.FeatureCollection, 
    buffer_dist: int = 10000,  # 10km buffer
    start_year: int = 2017, 
    end_year: int = 2022
) -> Dict[int, Dict[str, Optional[float]]]:
    # Disable SSL warnings temporarily due to I-WRIS requirements
    requests.packages.urllib3.disable_warnings()
    
    # Get village buffer coordinates
    buffer = village_fc.geometry().buffer(buffer_dist).getInfo()
    if not buffer or 'coordinates' not in buffer:
        raise ValueError("Invalid village geometry or buffer")
    
    # Get village centroid
    roi_centroid = village_fc.geometry().centroid().getInfo()['coordinates']
    
    # Find stations in the area
    stations, state_set = station_location(buffer['coordinates'][0])
    
    # If no stations found within the buffer
    if not stations:
        return {year: {'min': None, 'max': None} for year in range(start_year, end_year+1)}
    
    # Get closest stations
    stations_queue = close_stations(roi_centroid, stations)
    
    # Filter stations by maximum distance
    filtered_stations = []
    for station_name in stations_queue:
        station_coord = stations[station_name]
        # Convert [longitude, latitude] to (latitude, longitude) for distance calculation
        dist = distance((roi_centroid[1], roi_centroid[0]), (station_coord[1], station_coord[0]))
        if dist <= MAX_DISTANCE_KM:
            filtered_stations.append(station_name)
    
    # If no stations within MAX_DISTANCE_KM
    if not filtered_stations:
        return {year: {'min': None, 'max': None} for year in range(start_year, end_year+1)}
    
    # Prepare data structure
    years = range(start_year, end_year+1)
    year_values = {k: [] for k in years}
    
    try:
        # Try async fetch first
        gwl_data = await fetch_GWL_data_async(list(years), state_set)
    except Exception as e:
        # Fall back to synchronous if async fails completely
        print(f"Async fetch failed: {e}, falling back to synchronous")
        gwl_data = fetch_GWL_data(list(years), state_set)
    
    # Process the data
    processed_years = []
    for station in filtered_stations:
        # Skip years that already have data
        processed_years = [year for year, val_list in year_values.items() if val_list]
        
        for result in gwl_data:
            for year, data in result.items():
                if year in processed_years or not data:
                    continue
                
                for entry in data:
                    if entry['Station_name'] == station:
                        for item in entry['Data']:
                            year_values[year].append(item['level'])
    
    # Return min/max values for each year
    return {
        k: {
            'min': min(v, default=None), 
            'max': max(v, default=None)
        } 
        for k, v in year_values.items()
    }
"""


# Using only the synchronous implementation
def get_groundwater_level(
    village_fc: ee.FeatureCollection, 
    buffer_dist: int = 10000,  # 10km buffer
    start_year: int = 2017, 
    end_year: int = 2022
) -> Dict[int, Dict[str, Optional[float]]]:
    """
    Get groundwater level data for a village.
    
    Args:
        village_fc: Earth Engine FeatureCollection for the village
        buffer_dist: Buffer distance in meters around village (default: 10000)
        start_year: Start year for data (default: 2017)
        end_year: End year for data (default: 2022)
    
    Returns:
        Dictionary with years as keys and min/max groundwater levels as values
    """
    # Disable SSL warnings temporarily due to I-WRIS requirements
    requests.packages.urllib3.disable_warnings()
    
    # Get village buffer coordinates
    buffer = village_fc.geometry().buffer(buffer_dist).getInfo()
    if not buffer or 'coordinates' not in buffer:
        raise ValueError("Invalid village geometry or buffer")
    
    # Get village centroid
    roi_centroid = village_fc.geometry().centroid().getInfo()['coordinates']
    
    # Find stations in the area
    stations, state_set = station_location(buffer['coordinates'][0])
    
    # If no stations found within the buffer
    if not stations:
        return {year: {'min': None, 'max': None} for year in range(start_year, end_year+1)}
    
    # Get closest stations
    stations_queue = close_stations(roi_centroid, stations)
    
    # Filter stations by maximum distance
    filtered_stations = []
    for station_name in stations_queue:
        station_coord = stations[station_name]
        # Convert [longitude, latitude] to (latitude, longitude) for distance calculation
        dist = distance((roi_centroid[1], roi_centroid[0]), (station_coord[1], station_coord[0]))
        if dist <= MAX_DISTANCE_KM:
            filtered_stations.append(station_name)
    
    # If no stations within MAX_DISTANCE_KM
    if not filtered_stations:
        return {year: {'min': None, 'max': None} for year in range(start_year, end_year+1)}
    
    # Prepare data structure
    years = range(start_year, end_year+1)
    year_values = {k: [] for k in years}
    
    # Use synchronous fetch only
    gwl_data = fetch_GWL_data(list(years), state_set)
    
    # Process the data
    processed_years = []
    for station in filtered_stations:
        # Skip years that already have data
        processed_years = [year for year, val_list in year_values.items() if val_list]
        
        for result in gwl_data:
            for year, data in result.items():
                if year in processed_years or not data:
                    continue
                
                for entry in data:
                    if entry['Station_name'] == station:
                        for item in entry['Data']:
                            year_values[year].append(item['level'])
    
    # Return min/max values for each year
    return {
        k: {
            'min': min(v, default=None), 
            'max': max(v, default=None)
        } 
        for k, v in year_values.items()
    } 