"""
Script to update subdistrict 66 with village IDs and remove subdistrict 68.
Save as update_66_remove_68.py and run with: python manage.py shell < update_66_remove_68.py
"""

from gee_api.models import Village, SubDistrict
import sys

# Get both subdistricts
try:
    subdistrict_66 = SubDistrict.objects.get(id=66)
    subdistrict_68 = SubDistrict.objects.get(id=68)
    
    print(f"Subdistrict 66 (to keep): {subdistrict_66.name} in {subdistrict_66.district.name}")
    print(f"Subdistrict 68 (to remove): {subdistrict_68.name} in {subdistrict_68.district.name}")
except SubDistrict.DoesNotExist:
    print("One of the subdistricts doesn't exist.")
    sys.exit(1)

# Get all villages from both subdistricts
villages_66 = Village.objects.filter(subdistrict=subdistrict_66)
villages_68 = Village.objects.filter(subdistrict=subdistrict_68)

print(f"\nSubdistrict 66 has {villages_66.count()} villages")
print(f"Subdistrict 68 has {villages_68.count()} villages")

# Create a mapping of village names in subdistrict 68 to their village_id values
village_id_map = {}
for village in villages_68:
    if village.village_id:
        village_id_map[village.name.lower()] = village.village_id

print(f"Found {len(village_id_map)} villages with IDs in subdistrict 68")

# Update village IDs in subdistrict 66
updated_count = 0
missing_count = 0

for village in villages_66:
    village_name_lower = village.name.lower()
    if village_name_lower in village_id_map:
        village.village_id = village_id_map[village_name_lower]
        village.save()
        updated_count += 1
        print(f"Updated {village.name} with ID {village.village_id}")
    else:
        missing_count += 1

print(f"\nUpdated {updated_count} villages in subdistrict 66 with IDs from subdistrict 68")
print(f"{missing_count} villages in subdistrict 66 did not have matching IDs in subdistrict 68")

# Confirm with user before deleting subdistrict 68
print("\nWARNING: About to delete subdistrict 68 and all its villages.")
print("Make sure you have a database backup before proceeding.")
confirm = input("Type 'yes' to continue, anything else to cancel: ")

if confirm.lower() != 'yes':
    print("Operation cancelled. Subdistrict 68 was not deleted.")
    sys.exit(0)

# Delete all villages in subdistrict 68
villages_68.delete()
print(f"Deleted all villages in subdistrict 68")

# Delete subdistrict 68
subdistrict_68.delete()
print("Deleted subdistrict 68")

# Verify the update
villages_with_ids = Village.objects.filter(
    subdistrict=subdistrict_66, 
    village_id__isnull=False
).count()
print(f"\nVillages with IDs in subdistrict 66 after update: {villages_with_ids}")

print("\nDONE! Your application should continue to work with subdistrict 66.")