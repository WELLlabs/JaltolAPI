from django.urls import path
from . import views
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import StateViewSet, DistrictViewSet, SubDistrictViewSet, VillageViewSet

router = DefaultRouter()
router.register(r'states', StateViewSet)
router.register(r'districts', DistrictViewSet)
router.register(r'subdistricts', SubDistrictViewSet)
router.register(r'villages', VillageViewSet)



urlpatterns = [
    path('get_boundary_data/', views.get_boundary_data, name='get_boundary_data'),
    path('get_lulc_raster/', views.get_lulc_raster, name='get_lulc_raster'),
    path('get_area_change/', views.get_area_change, name='get_area_change'),
    path('get_control_village/', views.get_control_village, name='get_control_village'),
    path('get_rainfall_data/', views.get_rainfall_data, name='get_rainfall_data'),
    path('health/', views.health_check, name='health_check'),
    path('', include(router.urls)),
]
    
