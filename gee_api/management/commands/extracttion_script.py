import csv
import json
from collections import defaultdict

def extract_village_data(csv_file, target_subdistrict):
    """
    Extract village data from CSV for a specific subdistrict and format it for use
    in populate_location_data.py
    
    Args:
        csv_file (str): Path to the CSV file
        target_subdistrict (str): Name of the subdistrict to extract villages for
    
    Returns:
        dict: Dictionary mapping village names to their IDs for the specified subdistrict
    """
    village_data = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subdistrict = row.get('subdistric', '').strip().lower()
            if subdistrict == target_subdistrict.lower():
                village_name = row.get('village_na', '').strip().lower()
                village_id = row.get('pc11_tv_id', '')
                village_data[village_name] = village_id
    
    return village_data

def format_for_populate_script(village_data):
    """
    Format the extracted village data for use in populate_location_data.py
    
    Args:
        village_data (dict): Dictionary mapping village names to their IDs
    
    Returns:
        str: Formatted string for inclusion in populate_location_data.py
    """
    formatted_entries = []
    
    for village_name, village_id in village_data.items():
        formatted_entries.append(f"('{village_name}', {village_id})")
    
    formatted_string = "[\n                    " + ",\n                    ".join(formatted_entries) + "\n                ]"
    return formatted_string

def main():
    csv_file = 'Saraikela kharsawan.csv'  # Update with your actual file path
    target_subdistrict = 'gobindpur rajnagar'
    
    village_data = extract_village_data(csv_file, target_subdistrict)
    
    if not village_data:
        print(f"No villages found for subdistrict: {target_subdistrict}")
        return
    
    formatted_output = format_for_populate_script(village_data)
    print("\nVillage data for inclusion in populate_location_data.py:")
    print(formatted_output)
    
    # Also save to a file
    with open('gobindpur_rajnagar_villages.py', 'w', encoding='utf-8') as f:
        f.write(f"# Village data for subdistrict: {target_subdistrict}\n")
        f.write("villages_with_ids = ")
        f.write(formatted_output)

if __name__ == "__main__":
    main()