# 1 - FcFilter
# feature collection filter dataclass
# input is a dictionary of field_name and value
# eg. {'state': state_name, 'district': district_name, 'subdistrict': subD_name, 'village_na': vill_name}
# create the filter object as output

# 2 - ImageFilter
# image collection filter dataclass
# input is a dictionary of start_date, end_date, geometry (for now these)
# create the filter object as output

# 3 - EeCore
# create a class
# create a method to reduceRegions of images with featurecollection
# create a method to get a buffer for the given feature
# create a method to filter the features intersecting the given feature
