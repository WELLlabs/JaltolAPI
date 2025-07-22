# gee_api/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class Plan(models.Model):
    """
    Model representing subscription plans
    """
    PLAN_TYPES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=50, choices=PLAN_TYPES, unique=True)
    display_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # null for enterprise/contact plans
    currency = models.CharField(max_length=3, default='INR')
    duration_days = models.IntegerField(null=True, blank=True)  # null for lifetime/enterprise plans
    description = models.TextField()
    features = models.JSONField(default=list)  # List of features
    limitations = models.JSONField(default=list)  # List of limitations
    
    # Usage limits
    max_api_calls_per_day = models.IntegerField(null=True, blank=True)  # null = unlimited
    max_village_views_per_month = models.IntegerField(null=True, blank=True)  # null = unlimited
    max_projects = models.IntegerField(null=True, blank=True)  # null = unlimited
    
    # Plan status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)  # Default plan for new users
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.display_name} - {self.currency} {self.price if self.price else 'Contact'}"
    
    class Meta:
        ordering = ['name']

class UserPlan(models.Model):
    """
    Model representing user's current subscription plan
    """
    PLAN_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_plan')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=PLAN_STATUS_CHOICES, default='active')
    
    # Subscription dates
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)  # null for lifetime/enterprise plans
    
    # Usage tracking
    api_calls_today = models.IntegerField(default=0)
    village_views_this_month = models.IntegerField(default=0)
    last_api_call_date = models.DateField(null=True, blank=True)
    last_village_view_date = models.DateField(null=True, blank=True)
    
    # Payment info (for future use)
    payment_id = models.CharField(max_length=255, null=True, blank=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.display_name}"
    
    @property
    def is_active(self):
        from django.utils import timezone
        if self.status != 'active':
            return False
        if self.end_date and timezone.now() > self.end_date:
            return False
        return True
    
    @property
    def can_make_api_call(self):
        if not self.plan.max_api_calls_per_day:
            return True  # Unlimited
        
        from django.utils import timezone
        today = timezone.now().date()
        
        # Reset counter if it's a new day
        if self.last_api_call_date != today:
            self.api_calls_today = 0
            self.last_api_call_date = today
            self.save()
        
        return self.api_calls_today < self.plan.max_api_calls_per_day
    
    @property
    def can_view_village(self):
        if not self.plan.max_village_views_per_month:
            return True  # Unlimited
        
        from django.utils import timezone
        today = timezone.now().date()
        
        # Reset counter if it's a new month
        if (not self.last_village_view_date or 
            self.last_village_view_date.month != today.month or 
            self.last_village_view_date.year != today.year):
            self.village_views_this_month = 0
            self.last_village_view_date = today
            self.save()
        
        return self.village_views_this_month < self.plan.max_village_views_per_month
    
    def increment_api_calls(self):
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.last_api_call_date != today:
            self.api_calls_today = 1
        else:
            self.api_calls_today += 1
        
        self.last_api_call_date = today
        self.save()
    
    def increment_village_views(self):
        from django.utils import timezone
        today = timezone.now().date()
        
        if (not self.last_village_view_date or 
            self.last_village_view_date.month != today.month or 
            self.last_village_view_date.year != today.year):
            self.village_views_this_month = 1
        else:
            self.village_views_this_month += 1
        
        self.last_village_view_date = today
        self.save()

class Member(models.Model):
    """
    Extended profile for User model to store additional user information.
    One-to-one relationship with the Django User model.
    """
    USER_ROLES = [
        ('user', 'Regular User'),
        ('admin', 'Network Admin'),
        ('superadmin', 'Super Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    member_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.CharField(max_length=255, blank=True, null=True)  # URL to profile image
    is_google_user = models.BooleanField(default=False)
    google_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Role and plan information
    role = models.CharField(max_length=20, choices=USER_ROLES, default='user')
    has_selected_plan = models.BooleanField(default=False)  # Track if user has made initial plan selection
    
    # Additional profile fields
    phone = models.CharField(max_length=20, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def current_plan(self):
        """Get user's current active plan"""
        try:
            return self.user.user_plan.plan if self.user.user_plan.is_active else None
        except UserPlan.DoesNotExist:
            return None
    
    @property
    def is_admin(self):
        return self.role in ['admin', 'superadmin']

# Signal to create/update Member profile when User is created/updated
@receiver(post_save, sender=User)
def create_or_update_member_profile(sender, instance, created, **kwargs):
    """
    Signal handler to create or update Member profile when User is saved.
    """
    if created:
        Member.objects.create(user=instance)
        # Assign default plan to new users
        try:
            default_plan = Plan.objects.get(is_default=True)
            UserPlan.objects.create(user=instance, plan=default_plan)
        except Plan.DoesNotExist:
            # If no default plan exists, we'll handle this in the frontend
            pass
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
    village_id: str = models.CharField(max_length=20, null=True, blank=True)  # pc11_tv_id from CSV - changed to CharField to preserve leading zeros
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
    village_id = models.CharField(max_length=20, blank=True, null=True)  # pc11_tv_id - changed to CharField
    
    # Control village details
    control_state = models.CharField(max_length=100, blank=True, null=True)
    control_district = models.CharField(max_length=100, blank=True, null=True)
    control_subdistrict = models.CharField(max_length=100, blank=True, null=True)
    control_village = models.CharField(max_length=100, blank=True, null=True)
    control_village_id = models.CharField(max_length=20, blank=True, null=True)  # Changed to CharField to match village_id
    
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