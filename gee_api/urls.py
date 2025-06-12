from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    get_boundary_data, get_lulc_raster, get_area_change,
    get_control_village, get_rainfall_data, health_check,
    custom_polygon_comparison, api_root
)

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from .authentication_views import (
    register_user,
    login_user,
    logout_user,
    user_profile,
    update_profile,
    change_password,
    CustomTokenObtainPairView,
)

from .google_auth import google_login



# # Initialize the default router and register the viewsets
# router = DefaultRouter()
# router.register(r'states', StateViewSet)
# router.register(r'districts', DistrictViewSet)
# router.register(r'subdistricts', SubDistrictViewSet)
# router.register(r'villages', VillageViewSet)

# Define the urlpatterns with included router and custom views
urlpatterns = [
    
     path('', api_root, name='api_root'),
    # Authentication endpoints
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_user, name='login'),
    path('auth/logout/', logout_user, name='logout'),
    path('auth/profile/', user_profile, name='user_profile'),
    path('auth/profile/update/', update_profile, name='update_profile'),
    path('auth/change-password/', change_password, name='change_password'),
    
    # Google authentication
    path('auth/google/', google_login, name='google_login'),
    
    # JWT token endpoints
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Alternative class-based authentication endpoints (optional)
    # path('auth/register-class/', RegisterView.as_view(), name='register_class'),
    # path('auth/profile-class/', UserProfileView.as_view(), name='profile_class'),
    path(
        'get_boundary_data/',
        get_boundary_data,
        name='get_boundary_data'),
    path(
        'get_lulc_raster/',
        get_lulc_raster,
        name='get_lulc_raster'),
    path(
        'get_area_change/',
        get_area_change,
        name='get_area_change'),
    path(
        'get_control_village/',
        get_control_village,
        name='get_control_village'),
    path(
        'get_rainfall_data/',
        get_rainfall_data,
        name='get_rainfall_data'),
    path(
        'health/',
        health_check,
        name='health_check'),
     path(
        'custom_polygon_comparison/',
        custom_polygon_comparison,
        name='custom_polygon_comparison'),
    
    path('districts/<int:state_id>/', views.district_list, name='district_list'),
    path('subdistricts/<int:district_id>/', views.subdistrict_list, name='subdistrict_list'),
    path('villages/<int:subdistrict_id>/', views.village_list, name='village_list'),
    
    
]
