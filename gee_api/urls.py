from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    get_boundary_data, get_lulc_raster, get_area_change,
    get_control_village, get_rainfall_data, health_check,
    custom_polygon_comparison
)

from django.urls import path
from gee_api import views


# # Initialize the default router and register the viewsets
# router = DefaultRouter()
# router.register(r'states', StateViewSet)
# router.register(r'districts', DistrictViewSet)
# router.register(r'subdistricts', SubDistrictViewSet)
# router.register(r'villages', VillageViewSet)

# Define the urlpatterns with included router and custom views
urlpatterns = [
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
