import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import CMProject, RawDataset
from .serializers import CMProjectSerializer, RawDatasetSerializer

logger = logging.getLogger(__name__)

class CMProjectViewSet(viewsets.ModelViewSet):
    """
    CRUD for Continuous Monitoring Projects.
    """
    serializer_class = CMProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Guard against cases where self.request.user is not a fully
        resolved User instance (can happen during custom auth flows).
        """
        request_user = getattr(self.request, 'user', None)
        if not hasattr(request_user, 'id') or request_user.id is None:
            logger.warning("CMProjectViewSet.get_queryset called without auth user")
            return CMProject.objects.none()
        return CMProject.objects.filter(owner_id=request_user.id).order_by('-created_at')

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_dataset(self, request, pk=None):
        """
        Upload a raw CSV dataset to the project.
        """
        logger.info("upload_dataset request pk=%s user=%s", pk, request.user)
        project = self.get_object()
        file_obj = request.data.get('file')
        
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dataset = RawDataset.objects.create(
                project=project,
                file=file_obj,
                original_filename=file_obj.name,
                status='PENDING'
            )
        except Exception as exc:
            logger.exception("Failed to create RawDataset for project %s", project.id)
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = RawDatasetSerializer(dataset, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class RawDatasetViewSet(viewsets.ModelViewSet):
    """
    Manage uploaded datasets.
    """
    queryset = RawDataset.objects.all()
    serializer_class = RawDatasetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RawDataset.objects.filter(project__owner=self.request.user)

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """
        Extract column names from the uploaded CSV dataset.
        """
        try:
            dataset = self.get_object()
        except Exception as e:
            logger.exception("Failed to get dataset %s", pk)
            return Response({"error": f"Dataset not found: {str(e)}"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            from .services import DatasetIntrospectionService
            service = DatasetIntrospectionService()
            column_summary = service.analyze_dataset(dataset)
            return Response(column_summary, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Failed to analyze dataset %s", dataset.id)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm mapping and trigger ETL.
        Expects 'mapping' in request body.
        """
        dataset = self.get_object()
        mapping = request.data.get('mapping')
        
        if mapping:
            dataset.column_mapping = mapping
            dataset.save()
            
        try:
            from .services import ETLService
            service = ETLService()
            service.ingest_dataset(dataset)
            return Response({"status": "Ingested"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PublicProjectView(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only view for projects via slug.
    """
    serializer_class = CMProjectSerializer
    permission_classes = [AllowAny]
    lookup_field = 'public_slug'

    def get_queryset(self):
        return CMProject.objects.filter(is_public=True)
