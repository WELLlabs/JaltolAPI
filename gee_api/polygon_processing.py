import ee
from typing import Dict, List
from gee_api.constants import ee_assets
    
def get_lulc_for_region(
    year: int,
    state_name: str,
    district_name: str,
    geometry: ee.Geometry
) -> ee.Image:
    """
    Get appropriate LULC data for a region based on state/district.
    
    :param year: Year for LULC data.
    :param state_name: State name.
    :param district_name: District name.
    :param geometry: Geometry to filter by.
    :return: LULC image for the region.
    """
    start_date = f'{year}-07-01'
    end_date = f'{int(year) + 1}-06-30'
    
    # Select appropriate LULC collection based on state/district
    if state_name.lower() in ['maharashtra', 'uttar pradesh', 'jharkhand']:
        ic = ee.ImageCollection(ee_assets['bhuvan_lulc'])
        # For Bhuvan LULC, adjust dates to match its period
        start_date = f'{year}-06-01'
        end_date = f'{int(year) + 1}-05-31'
    elif district_name.lower() in ['vadodara']:
        ic = ee.ImageCollection(ee_assets['farmboundary'])
    else:
        ic = ee.ImageCollection(ee_assets['indiasat'])
    
    # Filter and process image
    filtered = ic.filterBounds(geometry).filterDate(start_date, end_date)
    
    if filtered.size().getInfo() == 0:
        raise ValueError(f"No LULC data available for {state_name}/{district_name} in {year}")
    
    return filtered.mosaic().clip(geometry)

def lulc_area_stats(
    image: ee.Image, 
    geometry: ee.Geometry, 
    class_values: Dict[str, List[int]]
) -> Dict[str, float]:
    """
    Calculate area statistics for specific LULC classes within a geometry.
    
    :param image: LULC image.
    :param geometry: Geometry to analyze.
    :param class_values: Dictionary mapping class names to their values.
    :return: Dictionary with area statistics in hectares.
    """
    result = {}
    
    for class_name, values in class_values.items():
        # Create a mask for the class values
        class_mask = None
        for value in values:
            if class_mask is None:
                class_mask = image.eq(value)
            else:
                class_mask = class_mask.Or(image.eq(value))
        
        # Calculate area
        area_image = class_mask.multiply(ee.Image.pixelArea())
        area = area_image.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=30,
            maxPixels=1e10
        ).get(class_mask.bandNames().get(0))
        
        # Convert to hectares
        result[class_name] = ee.Number(area).divide(10000).getInfo()
    
    return result
