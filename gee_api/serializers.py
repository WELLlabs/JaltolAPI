# serializers.py

from rest_framework import serializers
from .models import State, District, SubDistrict, Village

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'

class SubDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubDistrict
        fields = '__all__'

class VillageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Village
        fields = '__all__'
