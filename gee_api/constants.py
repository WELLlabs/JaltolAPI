from django.http import HttpResponse, JsonResponse
import json
import ee

# Initialize Earth Engine credentials
import os
import google.auth

# def initialize_earth_engine():
#     try:
#         credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not credentials_path:
#             raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        
#         credentials = ee.ServiceAccountCredentials(None, credentials_path)
#         ee.Initialize(credentials)
#         return credentials
#     except Exception as e:
#         raise ValueError(f"Failed to initialize Earth Engine: {e}")

def initialize_earth_engine():
    creds, _ = google.auth.default(scopes=[
        'https://www.googleapis.com/auth/earthengine',
        'https://www.googleapis.com/auth/cloud-platform',
    ])
    ee.Initialize(credentials=creds, project=os.getenv('EE_PROJECT', 'gcp-welllabs'))
    return creds

# Initialize on module load
credentials = initialize_earth_engine()

# Earth Engine assets and configuration
ee_assets = {
    "shrug_folder": 'users/jaltolwelllabs/SHRUG',
    "srtm": 'USGS/SRTMGL1_003',
    "indiasat": 'users/jaltolwelllabs/LULC/IndiaSAT_V2_draft',
    "imd_rain": "users/jaltolwelllabs/IMD/rain",
    "farmboundary" : 'users/jaltolwelllabs/LULC/Farmboundary_NDVI_Tree',
    "bhuvan_lulc": 'users/jaltolwelllabs/LULC/Bhuvan_LULC',
}

# States that use Bhuvan LULC data
BHUVAN_LULC_STATES = [
    'andhra pradesh', 'bihar', 'chhattisgarh', 'gujarat',
    'haryana', 'himachal pradesh', 'jharkhand', 'karnataka', 
    'kerala', 'madhya pradesh', 'maharashtra', 'odisha',
    'punjab', 'rajasthan', 'tamil nadu', 'uttarakhand', 'uttar pradesh', 'west bengal'
]

compare_village_buffer: int = 5000

shrug_fields = {
    'state_field': 'state_name',
    'district_field': 'district_n',
    'subdistrict_field': 'subdistric',
    'village_field': 'village_na',
    'unique_field': 'unique_name',
}


def shrug_dataset() -> ee.FeatureCollection:
    """
    Retrieve the SHRUG dataset from the specified folder in Earth Engine.

    :return: Merged Earth Engine FeatureCollection containing the SHRUG dataset
    :raises: JsonResponse with status 500 if unable to access the Earth Engine asset
    """
    assets = ee.data.listAssets(ee_assets['shrug_folder'])
    feature_collections = []

    for asset in assets['assets']:
        if asset['type'] in {'FeatureCollection', 'TABLE'}:
            # Get the asset ID and add it to the list of feature collections
            asset_id = asset['id']
            feature_collection = ee.FeatureCollection(asset_id)
            feature_collections.append(feature_collection)
        else:
            return JsonResponse(
                {'error': 'Unable to access ee asset'}, status=500)

    # Merge all the FeatureCollections into a single variable
    return ee.FeatureCollection(feature_collections).flatten()
