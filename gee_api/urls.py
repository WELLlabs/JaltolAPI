from django.urls import path
from . import views

urlpatterns = [
    path('village_analysis/<str:village_name>/', views.fetch_village_analysis, name='village_analysis'),
    path('karauli_villages_geojson/<str:district_name>/', views.karauli_villages_geojson, name='karauli_villages_geojson'), 
    path('get_karauli_raster/<str:district_name>/', views.get_karauli_raster, name='get_karauli_raster'),
    path('get_district_carbon/<str:district_name>/', views.get_district_carbon, name='get_district_carbon'),
    path('get_district_slope/<str:district_name>/', views.get_district_slope, name='get_district_slope'),
    path('area_change/<str:district_name>/<str:village_name>/', views.area_change_karauli, name='area_change_karauli'),
    path('rainfall_data/<str:district_name>/<str:village_name>/', views.fetch_rainfall_data, name='rainfall_data'),
    path('health/', views.health_check, name='health_check'),
    path('list_districts/', views.list_districts, name='list_districts'),
]
    
