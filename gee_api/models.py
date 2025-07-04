# gee_api/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class Member(models.Model):
    """
    Extended profile for User model to store additional user information.
    One-to-one relationship with the Django User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    member_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.CharField(max_length=255, blank=True, null=True)  # URL to profile image
    is_google_user = models.BooleanField(default=False)
    google_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to create/update Member profile when User is created/updated
@receiver(post_save, sender=User)
def create_or_update_member_profile(sender, instance, created, **kwargs):
    """
    Signal handler to create or update Member profile when User is saved.
    """
    if created:
        Member.objects.create(user=instance)
    else:
        instance.member_profile.save()

# # Example Project model for future use
# class Project(models.Model):
#     """
#     Model for user-specific projects.
#     """
#     project_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
#     title = models.CharField(max_length=255)
#     description = models.TextField(blank=True, null=True)
#     owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     def __str__(self):
#         return self.title

class State(models.Model):
    """
    Model representing a State.
    """
    name: str = models.CharField(max_length=100)
    state_id: int = models.IntegerField(null=True, blank=True, unique=True)  # pc11_s_id from CSV

    def __str__(self) -> str:
        return self.name


class District(models.Model):
    """
    Model representing a District belonging to a specific State.
    """
    name: str = models.CharField(max_length=100)
    state: State = models.ForeignKey(State, related_name='districts', on_delete=models.CASCADE)
    district_id: int = models.IntegerField(null=True, blank=True)  # pc11_d_id from CSV

    def __str__(self) -> str:
        return self.name


class SubDistrict(models.Model):
    """
    Model representing a SubDistrict belonging to a specific District.
    """
    name: str = models.CharField(max_length=100)
    district: District = models.ForeignKey(District, related_name='subdistricts', on_delete=models.CASCADE)
    subdistrict_id: str = models.CharField(max_length=20, null=True, blank=True)  # pc11_sd_id from CSV

    def __str__(self) -> str:
        return self.name


class Village(models.Model):
    """
    Model representing a Village belonging to a specific SubDistrict.
    """
    name: str = models.CharField(max_length=100)
    subdistrict: SubDistrict = models.ForeignKey(SubDistrict, related_name='villages', on_delete=models.CASCADE)
    village_id: int = models.IntegerField(null=True, blank=True)  # pc11_tv_id from CSV
    # Additional fields from CSV
    total_population: int = models.IntegerField(null=True, blank=True)  # tot_p
    sc_population: int = models.IntegerField(null=True, blank=True)  # p_sc
    st_population: int = models.IntegerField(null=True, blank=True)  # p_st

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    """
    Model for user-specific projects representing intervention areas.
    """
    PROJECT_TYPE_CHOICES = [
        ('village', 'Village-based'),
        ('geojson', 'GeoJSON Upload'),
        ('drawn', 'Drawn Polygons'),
    ]
    
    project_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, default='village')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    
    # Project image - base64 encoded image data
    project_image = models.TextField(blank=True, null=True, help_text="Base64 encoded satellite image")
    
    # Intervention details
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    subdistrict = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=100, blank=True, null=True)
    village_id = models.IntegerField(blank=True, null=True)  # pc11_tv_id
    
    # Control village details
    control_state = models.CharField(max_length=100, blank=True, null=True)
    control_district = models.CharField(max_length=100, blank=True, null=True)
    control_subdistrict = models.CharField(max_length=100, blank=True, null=True)
    control_village = models.CharField(max_length=100, blank=True, null=True)
    control_village_id = models.IntegerField(blank=True, null=True)
    
    # Intervention period
    intervention_start_year = models.IntegerField(blank=True, null=True)
    intervention_end_year = models.IntegerField(blank=True, null=True)
    
    # For GeoJSON projects
    geojson_data = models.JSONField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.owner.username}"

    @property
    def intervention_villages(self):
        """Return formatted intervention village details"""
        if self.project_type == 'village':
            return f"{self.village}, {self.subdistrict}"
        return "Custom Polygons"
    
    @property
    def control_villages(self):
        """Return formatted control village details"""
        if self.control_village:
            return f"{self.control_village}, {self.control_subdistrict}"
        return "Auto-selected"
    
    @property
    def intervention_period_display(self):
        """Return formatted intervention period"""
        if self.intervention_start_year and self.intervention_end_year:
            return f"{self.intervention_start_year} - {self.intervention_end_year}"
        return "Not specified"