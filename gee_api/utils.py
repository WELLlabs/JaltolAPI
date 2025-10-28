# gee_api/utils.py

import ee
from django.conf import settings
import logging
import os
import google.auth

logger = logging.getLogger(__name__)


def initialize_earth_engine():
    try:
        creds, _ = google.auth.default(scopes=[
            'https://www.googleapis.com/auth/earthengine',
            'https://www.googleapis.com/auth/cloud-platform',
        ])
        ee.Initialize(credentials=creds, project=os.getenv('EE_PROJECT', 'gcp-welllabs'))
        return creds
    except Exception as e:
        raise ValueError(f"Failed to initialize Google Earth Engine: {e}")
