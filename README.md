# JaltolAPI

## Overview
This is a Django application designed to act as backend server for the Jaltol Web App. This guide will help you set up the project on your local machine.

## Prerequisites
- **Python 3.12.1**: Make sure you have Python 3.12.1 installed. You can download it from [python.org](https://www.python.org/downloads/).
- **pip 23.2.1**: Ensure you have `pip` version 23.2.1 installed. You can check your `pip` version by running:
  ```sh
  pip --version

## Installation
git clone https://github.com/WELLlabs/JaltolAPI.git
cd your-repo-name

## Create and Activate a Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

## Install the Required Dependencies
pip install -r requirements.txt

## Run the Development Server
python manage.py runserver

## Access the Application
Open a web browser and navigate to http://127.0.0.1:8000 to access the application.

## Project Structure

### `views.py`
The `views.py` file contains the main view functions for handling requests and returning responses. It includes functions to interact with Earth Engine, process geographic data, and generate responses based on specific endpoints.

Key Functions:
python
- district_boundary
- village_boundary
- srtm_slope
- compute_slope
- get_buffer
- compare_village
- IndiaSAT_lulc
- yearly_sum
- getStats
- IMD_precipitation
- health_check
- get_karauli_raster
- get_rainfall_data
- get_boundary_data
- get_lulc_raster
- get_area_change
- get_control_village

### constants.py
The constants.py file defines constants and helper functions used across the project. This includes Earth Engine asset paths, buffer sizes, and field names for SHRUG datasets.

Key Constants and Functions:

- ee_assets
- compare_village_buffer
- shrug_fields
- shrug_dataset

### ee_processing.py
The ee_processing.py file includes functions that perform specific data processing tasks using Google Earth Engine. These functions are imported and used in the views to handle complex data processing.

Key Functions:

- compare_village
- district_boundary
- IndiaSAT_lulc
- IMD_precipitation
- village_boundary
