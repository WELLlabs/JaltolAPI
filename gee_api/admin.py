from django.contrib import admin
from gee_api.models import State, District, SubDistrict, Village

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'state')

@admin.register(SubDistrict)
class SubDistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'district')

@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'subdistrict')
