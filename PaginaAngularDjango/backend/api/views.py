from rest_framework import viewsets, permissions
from .models import Project, ContactMessage, Pais
from .serializers import ProjectSerializer, ContactMessageSerializer, PaisSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.AllowAny]


class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class PaisViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/paises/?region=ANDINA
    /api/paises/CO/
    """
    queryset = Pais.objects.filter(activo=True)
    serializer_class = PaisSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "codigo_iso"

    def get_queryset(self):
        qs = super().get_queryset()
        region = self.request.query_params.get("region")
        if region:
            qs = qs.filter(region=region)
        return qs