from django.http import HttpResponse, JsonResponse
import json
import ee

# Initialize Earth Engine credentials
email = "admin-133@ee-papnejaanmol.iam.gserviceaccount.com"
key_file = "./creds/ee-papnejaanmol-23b4363dc984.json"
credentials = ee.ServiceAccountCredentials(email=email, key_file=key_file)
ee.Initialize(credentials)

# Earth Engine assets and configuration
ee_assets = {
    "shrug_folder": 'users/jaltolwelllabs/SHRUG',
    "srtm": 'USGS/SRTMGL1_003',
    "indiasat": 'users/jaltolwelllabs/LULC/IndiaSAT_V2_draft',
    "imd_rain": "users/jaltolwelllabs/IMD/rain",
    "farmboundary" : 'users/jaltolwelllabs/LULC/Farmboundary_NDVI',
}

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
