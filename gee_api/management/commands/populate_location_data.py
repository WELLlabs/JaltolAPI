from django.core.management.base import BaseCommand
from gee_api.models import State, District, SubDistrict, Village
from typing import List, Dict


class Command(BaseCommand):
    help = 'Populate the RDS instance with location data for states, districts, sub-districts, and villages'

    def add_villages(self, subdistrict: SubDistrict, villages: List[str]) -> None:
        """
        Adds villages to a given subdistrict.

        Args:
            subdistrict (SubDistrict): The subdistrict to which the villages belong.
            villages (List[str]): A list of village names.
        """
        for village_name in villages:
            Village.objects.get_or_create(name=village_name, subdistrict=subdistrict)
        self.stdout.write(self.style.SUCCESS(f'Added villages to {subdistrict.name}'))

    def add_subdistricts(self, district: District, subdistricts_and_villages: Dict[str, List[str]]) -> None:
        """
        Adds subdistricts and their corresponding villages to a given district.

        Args:
            district (District): The district to which the subdistricts belong.
            subdistricts_and_villages (Dict[str, List[str]]): A dictionary where the keys are subdistrict names
                                                             and the values are lists of village names.
        """
        for subdistrict_name, villages in subdistricts_and_villages.items():
            subdistrict, created = SubDistrict.objects.get_or_create(name=subdistrict_name, district=district)
            self.add_villages(subdistrict, villages)
        self.stdout.write(self.style.SUCCESS(f'Added subdistricts to {district.name}'))

    def add_districts(self, state: State, districts_and_subdistricts: Dict[str, Dict[str, List[str]]]) -> None:
        """
        Adds districts and their corresponding subdistricts to a given state.

        Args:
            state (State): The state to which the districts belong.
            districts_and_subdistricts (Dict[str, Dict[str, List[str]]]): A dictionary where the keys are district names,
                                                                          the values are dictionaries that map subdistrict
                                                                          names to lists of village names.
        """
        for district_name, subdistricts in districts_and_subdistricts.items():
            district, created = District.objects.get_or_create(name=district_name, state=state)
            self.add_subdistricts(district, subdistricts)
        self.stdout.write(self.style.SUCCESS(f'Added districts to {state.name}'))

    def handle(self, *args, **kwargs) -> None:
        """
        Handles the command to populate location data.
        """
        # Example data for Rajasthan
       

        # Populate Rajasthan data
        rajasthan, created = State.objects.get_or_create(name='Rajasthan')
        self.add_districts(rajasthan, rajasthan_data)

        # Populate Andhra Pradesh data
        andhra_pradesh, created = State.objects.get_or_create(name='Andhra Pradesh')
        self.add_districts(andhra_pradesh, andhra_pradesh_data)

        # Populate Karnataka data
        karnataka, created = State.objects.get_or_create(name='Karnataka')
        self.add_districts(karnataka, karnataka_data)
        
        uttar_pradesh, created = State.objects.get_or_create(name='Uttar Pradesh')
        self.add_districts(uttar_pradesh, uttar_pradesh_data)
        
        maharashtra, created = State.objects.get_or_create(name='Maharashtra')
        self.add_districts(maharashtra, maharashtra_data)
        
        jharkhand, created = State.objects.get_or_create(name='Jharkhand')
        self.add_districts(jharkhand, jharkhand_data)
        

        self.stdout.write(self.style.SUCCESS('Successfully populated the RDS instance with location data.'))