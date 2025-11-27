from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import CMProject, RawDataset
from .serializers import CMProjectSerializer, RawDatasetSerializer

class CMProjectViewSet(viewsets.ModelViewSet):
    """
    CRUD for Continuous Monitoring Projects.
    """
    serializer_class = CMProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only show projects owned by the user
        return CMProject.objects.filter(owner=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_dataset(self, request, pk=None):
        """
        Upload a raw CSV dataset to the project.
        """
        project = self.get_object()
        file_obj = request.data.get('file')
        
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Create RawDataset entry
        dataset = RawDataset.objects.create(
            project=project,
            file=file_obj,
            original_filename=file_obj.name,
            status='PENDING'
        )
        
        serializer = RawDatasetSerializer(dataset)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class PublicProjectView(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only view for projects via slug.
    """
    serializer_class = CMProjectSerializer
    permission_classes = [AllowAny]
    lookup_field = 'public_slug'

    def get_queryset(self):
        return CMProject.objects.filter(is_public=True)
