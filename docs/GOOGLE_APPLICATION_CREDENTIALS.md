# Google Application Credentials Setup Guide

This document explains how to set up and manage Google Application Credentials for the JaltolAPI project, which uses Google Earth Engine for geospatial analysis.

## Table of Contents
- [Overview](#overview)
- [Creating Service Account on Google Cloud](#creating-service-account-on-google-cloud)
- [Environment Variable Setup](#environment-variable-setup)
- [File Locations](#file-locations)
- [Usage in Code](#usage-in-code)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

Google Application Credentials are used to authenticate your application with Google Earth Engine API. The JaltolAPI project uses these credentials to:
- Access satellite imagery and geospatial datasets
- Process Land Use Land Cover (LULC) analysis
- Calculate rainfall data from IMD precipitation datasets
- Analyze village boundaries and district data
- Generate SRTM elevation data
- Process custom polygon analysis

## Creating Service Account on Google Cloud

### Step 1: Access Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Select your project or create a new one

### Step 2: Enable Earth Engine API
1. Navigate to **APIs & Services** > **Library**
2. Search for "Earth Engine API"
3. Click on it and press **Enable**

### Step 3: Create Service Account
1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Fill in the details:
   - **Service account name**: `jaltol-earth-engine-service`
   - **Service account ID**: `jaltol-earth-engine-service` (auto-generated)
   - **Description**: `Service account for JaltolAPI Earth Engine access`
4. Click **Create and Continue**

### Step 4: Assign Roles
1. In the **Grant this service account access to project** section:
   - Add role: **Earth Engine Resource Admin**
   - Add role: **Earth Engine Resource Viewer** (if needed)
2. Click **Continue**

### Step 5: Generate JSON Key
1. Click on the created service account
2. Go to the **Keys** tab
3. Click **Add Key** > **Create New Key**
4. Select **JSON** format
5. Click **Create**
6. The JSON file will be downloaded automatically

### Step 6: Rename and Secure the File
1. Rename the downloaded file to: `gcp-welllabs-6e4173f30e21.json`
2. Store it securely (never commit to version control)

## Environment Variable Setup

### Local Development (.env file)
Create or update your `.env` file in the project root:

```bash
# Google Earth Engine Service Account
GOOGLE_APPLICATION_CREDENTIALS=./creds/gcp-welllabs-6e4173f30e21.json
```

### Production (EC2 Server - env.prod file)
Update your `env.prod` file on the EC2 server:

```bash
# Google Earth Engine Service Account
GOOGLE_APPLICATION_CREDENTIALS=./creds/gcp-welllabs-6e4173f30e21.json
```

## File Locations

### Local Development
```
JaltolAPI/
├── .env                                    # Environment variables (local)
├── creds/
│   └── gcp-welllabs-6e4173f30e21.json    # Service account JSON file
└── ...
```

### Production (EC2 Server)
```
/home/ubuntu/JaltolAPI/
├── env.prod                               # Production environment variables
├── .env                                   # Copied from env.prod during deployment
├── creds/
│   └── gcp-welllabs-6e4173f30e21.json    # Service account JSON file
└── ...
```

### Important Notes
- The `creds/` directory should be created if it doesn't exist
- The JSON file must be placed in the `creds/` directory
- Never commit the JSON file to version control (it's in `.gitignore`)

## Usage in Code

The Google Application Credentials are used in the following files:

### 1. `my_gee_backend/settings.py`
```python
# Set the path to the credentials file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
```
- Sets the global environment variable for the Django application
- Reads the path from environment variables

### 2. `gee_api/views.py`
```python
def initialize_earth_engine():
    try:
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        
        credentials = ee.ServiceAccountCredentials(None, credentials_path)
        ee.Initialize(credentials)
        return credentials
    except Exception as e:
        raise ValueError(f"Failed to initialize Earth Engine: {e}")
```
- Initializes Earth Engine for API views
- Used in functions like `get_lulc_raster()`, `get_rainfall_data()`, `get_area_change()`

### 3. `gee_api/constants.py`
```python
def initialize_earth_engine():
    # Similar implementation as views.py
    # Used for accessing Earth Engine assets and datasets
```
- Initializes Earth Engine for accessing SHRUG datasets
- Used for village, district, and state boundary data

### 4. `gee_api/ee_processing.py`
```python
def initialize_earth_engine():
    # Similar implementation
    # Used for geospatial processing functions
```
- Initializes Earth Engine for processing functions
- Used in functions like `district_boundary()`, `village_boundary()`, `IMD_precipitation()`

### 5. `gee_api/custom_polygon.py`
```python
# In the main block
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if not credentials_path:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

credentials = ee.ServiceAccountCredentials(None, credentials_path)
ee.Initialize(credentials)
```
- Used for custom polygon analysis functionality

## Security Best Practices

### 1. Never Commit Credentials
- The JSON file is already in `.gitignore`
- Never add it to version control
- Use environment variables for paths

### 2. Rotate Credentials Regularly
- Generate new service account keys periodically
- Revoke old keys when no longer needed
- Update the JSON file in all environments

### 3. Restrict Permissions
- Only assign necessary roles to the service account
- Use principle of least privilege
- Regularly audit service account permissions

### 4. Secure File Storage
- Store JSON files in secure locations
- Use proper file permissions (600 or 644)
- Consider using Google Cloud Secret Manager for production

### 5. Environment Separation
- Use different service accounts for different environments
- Never use production credentials in development
- Keep local and production credentials separate

## Troubleshooting

### Common Issues

#### 1. "GOOGLE_APPLICATION_CREDENTIALS environment variable not set"
**Solution**: Ensure the environment variable is set in your `.env` file:
```bash
GOOGLE_APPLICATION_CREDENTIALS=./creds/gcp-welllabs-6e4173f30e21.json
```

#### 2. "Failed to initialize Earth Engine"
**Possible causes**:
- JSON file path is incorrect
- JSON file is corrupted
- Service account doesn't have proper permissions
- Earth Engine API is not enabled

**Solution**:
- Verify the file path in environment variable
- Check if the JSON file exists and is readable
- Ensure Earth Engine API is enabled in Google Cloud Console
- Verify service account has Earth Engine permissions

#### 3. "Permission denied" errors
**Solution**:
- Check if the service account has the correct roles
- Ensure Earth Engine API is enabled
- Verify the project ID in the JSON file matches your Google Cloud project

#### 4. File not found errors
**Solution**:
- Ensure the `creds/` directory exists
- Verify the JSON file is in the correct location
- Check file permissions

### Testing the Setup

To test if the credentials are working:

```bash
# In your project directory
python manage.py shell
```

```python
>>> import ee
>>> from gee_api.utils import initialize_earth_engine
>>> initialize_earth_engine()
>>> print("Earth Engine initialized successfully!")
```

### Deployment Checklist

Before deploying to production:

- [ ] Service account JSON file is in `creds/` directory on EC2
- [ ] `env.prod` file contains the correct `GOOGLE_APPLICATION_CREDENTIALS` path
- [ ] Environment variable is properly set during deployment
- [ ] Service account has necessary Earth Engine permissions
- [ ] Earth Engine API is enabled in the Google Cloud project
- [ ] JSON file has proper permissions (readable by the application)

## Additional Resources

- [Google Earth Engine Authentication](https://developers.google.com/earth-engine/guides/service_account)
- [Google Cloud Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Earth Engine API Documentation](https://developers.google.com/earth-engine/guides)
- [Django Environment Variables](https://docs.djangoproject.com/en/stable/topics/settings/#environment-variables)

---

**Last Updated**: December 2024  
**Version**: 1.0  
**Maintainer**: JaltolAPI Development Team

