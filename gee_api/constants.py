import json
import ee
from django.http import JsonResponse

email = "admin-133@ee-papnejaanmol.iam.gserviceaccount.com"
key_file = "./creds/ee-papnejaanmol-23b4363dc984.json"
credentials = ee.ServiceAccountCredentials(email=email, key_file=key_file)

from django.http import HttpResponse
ee.Initialize(credentials)

ee_assets = {
    "shrug_folder" : 'users/jaltolwelllabs/SHRUG',
    "srtm" : 'USGS/SRTMGL1_003',
    "indiasat" : 'users/jaltolwelllabs/LULC/IndiaSAT_V2_draft',
    "imd_rain" : "users/jaltolwelllabs/IMD/rain",
}

compare_village_buffer = 5000

shrug_fields = {
    'state_field' : 'state_name',
    'district_field': 'district_n',
    'subdistrict_field' : 'subdistric',
    'village_field' : 'village_na',
    'unique_field' : 'unique_name',
}

def shrug_dataset():
        assets = ee.data.listAssets(ee_assets['shrug_folder'])
        feature_collections = []
        for asset in assets['assets']:
            if asset['type'] in {'FeatureCollection', 'TABLE'}:
            # Get the asset ID
               asset_id = asset['id']
               feature_collection = ee.FeatureCollection(asset_id)
               feature_collections.append(feature_collection)
            else:
               return JsonResponse({'error': 'Unable to access ee asset'}, status=500)
        
        # Merge all the FeatureCollections into a single variable
        return ee.FeatureCollection(feature_collections).flatten()
    
