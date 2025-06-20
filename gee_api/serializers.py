from rest_framework import serializers
from gee_api.models import State, District, SubDistrict, Village, Project


class VillageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Village model.

    Converts Village instances into JSON format.
    """
    subdistrict = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Village
        fields = ['id', 'name', 'village_id', 'subdistrict', 'display_name']

    def get_subdistrict(self, obj):
        return obj.subdistrict.name

    def get_display_name(self, obj):
        return f"{obj.name} - {obj.village_id}"


class SubDistrictSerializer(serializers.ModelSerializer):
    """
    Serializer for the SubDistrict model.

    Converts SubDistrict instances into JSON format, including related villages.
    """
    district = serializers.SerializerMethodField()
    villages: serializers.ListSerializer = VillageSerializer(many=True, read_only=True)

    class Meta:
        model = SubDistrict
        fields = ['id', 'name', 'district', 'villages']

    def get_district(self, obj):
        return obj.district.name


class DistrictSerializer(serializers.ModelSerializer):
    """
    Serializer for the District model.

    Converts District instances into JSON format, including related subdistricts.
    """
    state = serializers.SerializerMethodField()
    subdistricts: serializers.ListSerializer = SubDistrictSerializer(many=True, read_only=True)

    class Meta:
        model = District
        fields = ['id', 'name', 'state', 'subdistricts']

    def get_state(self, obj):
        return obj.state.name


class StateSerializer(serializers.ModelSerializer):
    """
    Serializer for the State model.

    Converts State instances into JSON format, including related districts.
    """
    districts: serializers.ListSerializer = DistrictSerializer(many=True, read_only=True)

    class Meta:
        model = State
        fields = ['id', 'name', 'districts']


class ProjectSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    intervention_villages = serializers.CharField(read_only=True)
    control_villages = serializers.CharField(read_only=True)
    intervention_period_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'project_id', 'name', 'description', 'project_type', 'owner', 'owner_username',
            'project_image',
            'state', 'district', 'subdistrict', 'village', 'village_id',
            'control_state', 'control_district', 'control_subdistrict', 'control_village', 'control_village_id',
            'intervention_start_year', 'intervention_end_year', 'intervention_period_display',
            'geojson_data', 'created_at', 'updated_at',
            'intervention_villages', 'control_villages'
        ]
        read_only_fields = ['project_id', 'owner', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for project creation"""
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'project_type',
            'project_image',
            'state', 'district', 'subdistrict', 'village', 'village_id',
            'control_state', 'control_district', 'control_subdistrict', 'control_village', 'control_village_id',
            'intervention_start_year', 'intervention_end_year', 'geojson_data'
        ]
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return Project.objects.create(**validated_data)
