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

    def __str__(self) -> str:
        return self.name


class District(models.Model):
    """
    Model representing a District belonging to a specific State.
    """
    name: str = models.CharField(max_length=100)
    state: State = models.ForeignKey(State, related_name='districts', on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name


class SubDistrict(models.Model):
    """
    Model representing a SubDistrict belonging to a specific District.
    """
    name: str = models.CharField(max_length=100)
    district: District = models.ForeignKey(District, related_name='subdistricts', on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name


class Village(models.Model):
    """
    Model representing a Village belonging to a specific SubDistrict.
    """
    name: str = models.CharField(max_length=100)
    subdistrict: SubDistrict = models.ForeignKey(SubDistrict, related_name='villages', on_delete=models.CASCADE)
    village_id: int = models.IntegerField(null=True, blank=True)  # New field to store pc11_tv_id

    def __str__(self) -> str:
        return self.name