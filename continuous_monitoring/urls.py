from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CMProjectViewSet, PublicProjectView, RawDatasetViewSet

router = DefaultRouter()
router.register(r'projects', CMProjectViewSet, basename='cm-projects')
router.register(r'datasets', RawDatasetViewSet, basename='cm-datasets')
router.register(r'public', PublicProjectView, basename='cm-public')

urlpatterns = [
    path('', include(router.urls)),
]
