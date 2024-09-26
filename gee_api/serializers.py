from rest_framework import serializers
from gee_api.models import State, District, SubDistrict, Village


class VillageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Village model.

    Converts Village instances into JSON format.
    """
    class Meta:
        model = Village
        fields = ['id', 'name']


class SubDistrictSerializer(serializers.ModelSerializer):
    """
    Serializer for the SubDistrict model.

    Converts SubDistrict instances into JSON format, including related villages.
    """
    villages: serializers.ListSerializer = VillageSerializer(many=True, read_only=True)

    class Meta:
        model = SubDistrict
        fields = ['id', 'name', 'villages']


class DistrictSerializer(serializers.ModelSerializer):
    """
    Serializer for the District model.

    Converts District instances into JSON format, including related subdistricts.
    """
    subdistricts: serializers.ListSerializer = SubDistrictSerializer(many=True, read_only=True)

    class Meta:
        model = District
        fields = ['id', 'name', 'subdistricts']


class StateSerializer(serializers.ModelSerializer):
    """
    Serializer for the State model.

    Converts State instances into JSON format, including related districts.
    """
    districts: serializers.ListSerializer = DistrictSerializer(many=True, read_only=True)

    class Meta:
        model = State
        fields = ['id', 'name', 'districts']
