from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Project, ContactMessage, Pais, IndicadorEconomico, TipoCambio
from .serializers import (
    ProjectSerializer,
    ContactMessageSerializer,
    PaisSerializer,
    PaisDetailSerializer,
    IndicadorEconomicoSerializer,
    TipoCambioSerializer,
)


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

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PaisDetailSerializer
        return PaisSerializer

    @action(detail=True, methods=["get"], url_path="indicadores")
    def indicadores(self, request, codigo_iso=None):
        pais = self.get_object()
        qs = IndicadorEconomico.objects.filter(pais=pais).order_by("-anio")
        serializer = IndicadorEconomicoSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="tipo-cambio")
    def tipo_cambio(self, request, codigo_iso=None):
        pais = self.get_object()
        # último tipo de cambio por moneda del país hacia USD
        fx = (
            TipoCambio.objects.filter(moneda_origen=pais.moneda_codigo, moneda_destino="USD")
            .order_by("-fecha")
            .first()
        )
        if not fx:
            return Response({"detail": "No hay tipo de cambio registrado."}, status=404)
        serializer = TipoCambioSerializer(fx)
        return Response(serializer.data)