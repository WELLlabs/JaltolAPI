from django.db import models
from django.contrib.auth.models import User
import uuid

class CMProject(models.Model):
    """
    Top-level container for a continuous monitoring project.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cm_projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    public_slug = models.SlugField(unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class RawDataset(models.Model):
    """
    Stores the original uploaded file and the AI-generated mapping configuration.
    This allows us to re-process data if mappings change.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Analysis'),
        ('ANALYZED', 'Analyzed (Waiting Confirmation)'),
        ('INGESTED', 'Ingested'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(CMProject, on_delete=models.CASCADE, related_name='datasets')
    file = models.FileField(upload_to='cm_uploads/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    
    # The mapping suggested by AI or confirmed by user
    # Structure: { "lat_col": "Latitude", "date_col": "Timestamp", "extra_cols": [...] }
    column_mapping = models.JSONField(default=dict, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_filename} ({self.project.name})"

class MetricCatalog(models.Model):
    """
    Standardized list of metrics (e.g., 'Groundwater Level', 'Salinity').
    Used to normalize data across different projects.
    """
    id = models.CharField(max_length=50, primary_key=True)  # e.g., 'gw_level'
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_core = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class UnifiedObject(models.Model):
    """
    A standardized Object entity (well, site, location, etc.).
    Core fields are strictly typed. All other site-specific fields go into 'extra_data'.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(CMProject, on_delete=models.CASCADE, related_name='unified_objects')
    
    # Core Fields (Normalized)
    external_id = models.CharField(max_length=100, help_text="ID from the source file")
    name = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # Flexible Fields (Context)
    # e.g., { "district": "Kolar", "depth_m": 150, "pump_type": "Submersible" }
    extra_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'external_id']

    def __str__(self):
        return f"{self.name or self.external_id} ({self.project.name})"

class UnifiedTimeSeries(models.Model):
    """
    Standardized Time Series data.
    """
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(CMProject, on_delete=models.CASCADE, related_name='time_series')
    object = models.ForeignKey(UnifiedObject, on_delete=models.CASCADE, related_name='readings')
    
    # Core Fields
    timestamp = models.DateTimeField()
    metric = models.ForeignKey(MetricCatalog, on_delete=models.PROTECT)
    value = models.FloatField()
    
    # Flexible Fields
    # e.g., { "sensor_id": "S-123", "quality_flag": "Good" }
    extra_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['project', 'object', 'timestamp']),
            models.Index(fields=['project', 'metric', 'timestamp']),
        ]
