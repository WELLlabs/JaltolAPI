from rest_framework import serializers
from .models import CMProject, RawDataset

class CMProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CMProject
        fields = ['id', 'name', 'description', 'is_public', 'public_slug', 'created_at']
        read_only_fields = ['id', 'created_at', 'owner']

    def create(self, validated_data):
        # Assign the current user as owner
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

class RawDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawDataset
        fields = ['id', 'project', 'file', 'original_filename', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at', 'original_filename']

    def create(self, validated_data):
        # Capture original filename
        file_obj = validated_data['file']
        validated_data['original_filename'] = file_obj.name
        return super().create(validated_data)
