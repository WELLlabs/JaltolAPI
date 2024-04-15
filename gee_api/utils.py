# gee_api/utils.py

import ee
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def initialize_earth_engine():
    try:
        ee.Initialize()
    except ee.EEException as e:
        ee.Authenticate()
        raise ValueError(f"Failed to authenticate Google Earth Engine: {e}")
