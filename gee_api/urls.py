from django.urls import path
from . import views

urlpatterns = [
    path('get_boundary_data/', views.get_boundary_data, name='get_boundary_data'),
    path('get_lulc_raster/', views.get_lulc_raster, name='get_lulc_raster'),
    path('get_area_change/', views.get_area_change, name='get_area_change'),
    path('get_control_village/', views.get_control_village, name='get_control_village'),
    path('get_rainfall_data/', views.get_rainfall_data, name='get_rainfall_data'),
]
    
