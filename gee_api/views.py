# gee_api/views.py
from datetime import datetime
from venv import logger  
from django.http import JsonResponse
from .utils import initialize_earth_engine
import ee
from django.conf import settings

email = "admin-133@ee-papnejaanmol.iam.gserviceaccount.com"
key_file = "./creds/ee-papnejaanmol-23b4363dc984.json"
credentials = ee.ServiceAccountCredentials(email=email, key_file=key_file)

from django.http import HttpResponse
ee.Initialize(credentials)

def health_check(request):
    # Perform necessary health check logic here
    return HttpResponse("OK")

def fetch_village_analysis(request, village_name):
    # initialize_earth_engine()
    ee.Initialize(credentials)
    try:
        # Filter the VillageLevel table for Karauli villages
        village_level_table = ee.FeatureCollection("users/jaltolwelllabs/RJ_2001_2011_final_proj32644").filter(ee.Filter.eq('Dist_N_11', 'Karauli'))
        village_data = village_level_table.filter(ee.Filter.eq('name', village_name)).first()

        # Filter the ImageCollection by date range
        lulc_data = ee.ImageCollection("users/jaltolwelllabs/LULC/IndiaSAT_V2_draft").filterDate('2016-06-01', '2017-07-31')
        
        # Perform additional processing as required
        # Note: Depending on what analysis or data you want to return, you'll need to add your specific Earth Engine processing logic here

        # Example: Serialize the result for response (This is a placeholder - adapt as needed)
        serialized_data = village_data.getInfo()  # This is a basic example; adapt as per your requirements

        return JsonResponse({'data': serialized_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def list_districts(request):
    # List of districts
    districts = [
       'anantapur' , 'dhamtari', 'uttar bastar kanker', 'karauli', 'koppal','thane', 'raichur' 
    ]
    return JsonResponse({'districts': districts})

def karauli_villages_geojson(request,district_name):
    # initialize_earth_engine()
    ee.Initialize(credentials)
    try:
        # Fetch the Karauli village features
        district_level_table = ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/hackathon_dists').filter(ee.Filter.eq('district_n', district_name))
        
        # Convert features to GeoJSON
        geojson = district_level_table.getInfo()  # This will be a dictionary that includes GeoJSON data
        
        return JsonResponse(geojson)
    except Exception as e:
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

def area_change_karauli(request,district_name ,village_name):
    # Initialize your Earth Engine credentials if not already initialized
    ee.Initialize(credentials)

    # Define the FeatureCollection for Karauli villages
    district_fc = ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/hackathon_dists').filter(ee.Filter.eq('district_n', district_name))

    # Filter the FeatureCollection for the specific village
    village_fc = district_fc.filter(ee.Filter.eq('village_na', village_name))

    # Get the geometry for the specific village
    village_geometry = village_fc.geometry()
     # Define the ImageCollection for Karauli LandUseLandCover
    image_collection = ee.ImageCollection('users/jaltolwelllabs/LULC/hackathon').filterBounds(village_geometry)

    # Define the labels for the classes (only include the specified two classes)
    class_labels = {
        '8': 'Single cropping cropland',
        '10': 'Double cropping cropland',
    }

    # Compute the area for each class over the years
    area_change_data = {}
    for year in range(2014, 2023):  # Assuming you have data from 2014 to 2022
        # Filter the ImageCollection for the specific year
        start_date = ee.Date.fromYMD(year, 6, 1)
        end_date = start_date.advance(1, 'year')
        year_image = image_collection.filterDate(start_date, end_date).mosaic()
        
        # Calculate the area for each of the two land cover classes
        for class_value, class_name in class_labels.items():
            area = calculate_class_area(year_image, int(class_value), village_geometry)
            if year not in area_change_data:
                area_change_data[year] = {}
            area_change_data[year][class_name] = area
            print(area)

    return JsonResponse(area_change_data)
    
    
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


precipitation_collection = ee.ImageCollection("users/jaltolwelllabs/IMD/rain")

# Function to compute the yearly sum of precipitation
def yearly_sum(year: int) -> ee.Image:
    ee.Initialize(credentials)
    # Your provided yearly_sum function here
    precipitation_collection = ee.ImageCollection("users/jaltolwelllabs/IMD/rain")
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

# View function to fetch rainfall data
def fetch_rainfall_data(request, district_name ,village_name):
    ee.Initialize(credentials)
    try:

        district_fc = ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/hackathon_dists').filter(ee.Filter.eq('district_n', district_name))
        village_fc = district_fc.filter(ee.Filter.eq('village_na', village_name))
        village_geometry = village_fc.geometry()
        print(village_geometry)

        # Define the years you're interested in analyzing
        year_list = [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]  # Example years

        # Process rainfall data for each year
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


def get_district_carbon(request, district_name):
    ee.Initialize(credentials)
    
    try:
        
        # Access the ImageCollection for Karauli
        district_fc = ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/hackathon_dists').filter(ee.Filter.eq('district_n', district_name))
        
        image_collection = ee.Image('OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02').multiply(5).clipToCollection(district_fc)
        # Here you might want to select a specific image by date or other criteria.
        # For example, to get the first image:
        # image = ee.Image(image_collection.filterDate('2022-07-01', '2023-06-30').first())
        image = ee.Image(image_collection)
        
        
        vis_params = {
        'bands': ['b0'],
        'min': 0.0,
        'max': 60.0,
        'palette': ['F9EFDB','9DBC98','638889','green']
         }
        
        
        # Get the map ID and token
        map_id_dict = image.getMapId(vis_params)
        
        # Construct the tiles URL template
        tiles_url = map_id_dict['tile_fetcher'].url_format
        
        return JsonResponse({'tiles_url': tiles_url})
    except Exception as e:
        logger.error('Failed to get Carbon', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
    
def get_district_slope(request, district_name):
    ee.Initialize(credentials)
    
    try:
        
        # Access the ImageCollection for Karauli
        district_fc = ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/hackathon_dists').filter(ee.Filter.eq('district_n', district_name))
        
        image_collection = ee.Image('USGS/SRTMGL1_003')
        
    
        elevation = image_collection.select('elevation')
        slope = ee.Terrain.slope(elevation).clipToCollection(district_fc)
        vis_params = {min: 0, max :60}
        
        
        # Get the map ID and token
        map_id_dict = slope.getMapId(vis_params)
        
        # Construct the tiles URL template
        tiles_url = map_id_dict['tile_fetcher'].url_format
        
        return JsonResponse({'tiles_url': tiles_url})
    except Exception as e:
        logger.error('Failed to get Carbon', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)