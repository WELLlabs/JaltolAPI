import ee
import json

# Existing functions remain unchanged
def read_geojson(file_path):
    """
    Reads a GeoJSON file and returns its content as a Python dictionary.

    :param file_path: Path to the GeoJSON file.
    :return: Dictionary containing the GeoJSON data.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from the file '{file_path}'.")

def calculate_area(fc):
    """
    Calculates the area of a given geometry.

    :param fc: Feature or FeatureCollection.
    :return: Area in square meters.
    """
    return fc.geometry().area().getInfo()

def calculate_radius(polygon_area, n):
    """
    Calculates the radius of a circle with the same area as the polygon.

    :param polygon_area: Area of the polygon in square meters.
    :param n: Number of points.
    :return: Radius in meters.
    """
    return ((polygon_area / (n * 3.14159)) ** 0.5)

def gen_buffer(fc, radius):
    """
    Generates a buffer around the given feature or feature collection.

    :param fc: Feature or FeatureCollection.
    :param radius: Radius for the buffer in meters.
    :return: Buffered Geometry.
    """
    return fc.geometry().buffer(radius)

def crop_mask_image(ic, roi, target_classes):
    """
    Applies a mask to the image based on the target classes.

    :param ic: LULC Image Collection.
    :param roi: Region of interest.
    :param target_classes: List of target classes for masking.
    :return: Masked image.
    """
    image = ic.filterBounds(roi).mode() # mode of LULC image over the roi
    return image.updateMask(
        ee.ImageCollection(
            target_classes.map(lambda val: image.eq(ee.Number(val)))
        ).reduce(ee.Reducer.anyNonZero())
    ).gt(0)

def gen_points_crop(image, roi, n, band='b1', scale=10):
    """
    Generates stratified random points over image pixels within ROI.

    :param image: Image to sample from.
    :param roi: Region of interest.
    :param n: Number of points to generate.
    :param band: Band name to extract values from.
    :param scale: Scale for sampling in meters.
    :return: Points Feature Collection.
    """
    return image.stratifiedSample(
        numPoints=n,
        classBand=band,
        region=roi,
        scale=scale,
        geometries=True
    )

# Add this new function to make the existing functionality callable from views.py
def process_custom_polygon(
    geojson_data, 
    state_name, 
    district_name, 
    subdistrict_name, 
    control_village_name, 
    num_points=10
):
    """
    Process a custom polygon GeoJSON, calculate equivalent area circles in control village.
    
    :param geojson_data: GeoJSON data as a Python dictionary
    :param state_name: Name of the state (used to get correct SHRUG dataset)
    :param district_name: District name
    :param subdistrict_name: Subdistrict name 
    :param control_village_name: Name of the control village
    :param num_points: Number of points/circles to generate
    :return: Dictionary with processing results
    """
    # Clean up input parameters
    state_name = state_name.strip().lower()
    
    subdistrict_name = subdistrict_name.strip().lower()
    control_village_name = control_village_name.strip()
    
    # IMPORTANT: Format state name properly for SHRUG dataset by replacing spaces with underscores
    formatted_state_name = state_name.title().replace(" ", "_")
    
    print(f"Using parameters: State={state_name}, Formatted State={formatted_state_name}, District={district_name}, Subdistrict={subdistrict_name}, ControlVillage={control_village_name}")
    
    # Convert GeoJSON to Earth Engine feature collection
    custom_polygon = ee.FeatureCollection(geojson_data)
    polygon_area = calculate_area(custom_polygon)
    
    # Access state-specific SHRUG dataset with proper formatting
    shrug = ee.FeatureCollection(f'users/jaltolwelllabs/SHRUG/{formatted_state_name}')
    control_village = shrug.filter(ee.Filter.And(
        ee.Filter.eq('district_n', district_name),
        ee.Filter.eq('subdistric', subdistrict_name),
        ee.Filter.eq('village_na', control_village_name)
    ))
    control_area = calculate_area(control_village)
    print(f"Control area: {control_area}")

    if polygon_area > control_area:
        raise ValueError("The custom polygon is larger than the control village.")
    
    radius = calculate_radius(polygon_area, num_points)
    buffer = gen_buffer(control_village, (-1 * radius))
    
    ic = ee.ImageCollection('users/jaltolwelllabs/LULC/Bhuvan_LULC')
    target_classes = ee.List([2, 6, 13, 3, 4, 5])
    
    crop_mask = crop_mask_image(ic, buffer, target_classes)
    points = gen_points_crop(crop_mask, buffer, num_points, band='b1', scale=50)
    
    # Create proper feature collection for circles with properties
    # This ensures they're visible on the map and have the right properties for analysis
    circles = points.map(lambda f: ee.Feature(
        f.geometry().buffer(radius),
        {
            'radius': radius,
            'center_x': f.geometry().centroid().coordinates().get(0),
            'center_y': f.geometry().centroid().coordinates().get(1),
            'control_village': control_village_name,
            'circle_id': f.id()
        }
    ))

    print(f"Radius: {radius}")
    print(f"Number of circles: {circles.size().getInfo()}")
    print(f"Polygon area: {polygon_area}, Circles area: {circles.geometry().area().getInfo()}")
    
    return {
        'polygon_area': polygon_area,
        'control_area': control_area,
        'radius': radius,
        'points': points,
        'circles': circles
    }

# Keep the original script functionality
if __name__ == "__main__":
    # Initialize Earth Engine credentials
    email = "admin-133@ee-papnejaanmol.iam.gserviceaccount.com"
    key_file = "./ee-papnejaanmol-23b4363dc984.json"
    credentials = ee.ServiceAccountCredentials(email=email, key_file=key_file)
    ee.Initialize(credentials)
    
    # Test with the sample data
    filename = 'sample.geojson'
    geojson_data = read_geojson(filename)
    
    # Test the new function
    result = process_custom_polygon(
        geojson_data,
        'uttar_pradesh',
        'chitrakoot',
        'mau',
        'bariya'
    )