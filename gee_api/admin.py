# Update your gee_api/admin.py file with this code:

from django.contrib import admin
from .models import Member, State, District, SubDistrict, Village, Project

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'is_google_user', 'created_at']
    list_filter = ['is_google_user', 'created_at']
    search_fields = ['user__username', 'user__email', 'organization']
    readonly_fields = ['member_id', 'created_at', 'updated_at']

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'state']
    list_filter = ['state']
    search_fields = ['name', 'state__name']

@admin.register(SubDistrict)
class SubDistrictAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'district']
    list_filter = ['district__state', 'district']
    search_fields = ['name', 'district__name']

@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'village_id', 'subdistrict']
    list_filter = ['subdistrict__district__state', 'subdistrict__district', 'subdistrict']
    search_fields = ['name', 'village_id', 'subdistrict__name']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'project_type', 'state', 'district', 'village', 'created_at']
    list_filter = ['project_type', 'state', 'district', 'created_at']
    search_fields = ['name', 'owner__username', 'village', 'district']
    readonly_fields = ['project_id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'project_type', 'owner')
        }),
        ('Intervention Details', {
            'fields': ('state', 'district', 'subdistrict', 'village', 'village_id')
        }),
        ('Control Village Details', {
            'fields': ('control_state', 'control_district', 'control_subdistrict', 'control_village', 'control_village_id')
        }),
        ('Time Period', {
            'fields': ('intervention_start_year', 'intervention_end_year')
        }),
        ('GeoJSON Data', {
            'fields': ('geojson_data',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('project_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )