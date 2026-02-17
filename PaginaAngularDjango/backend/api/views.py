import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .permissions import IsAdminRole, IsViewerOrAbove, IsAnalystOrAdmin
from .models import (
    Project,
    ContactMessage,
    Pais,
    IndicadorEconomico,
    TipoCambio,
    Portafolio,
    Posicion,
)
from .serializers import (
    ProjectSerializer,
    ContactMessageSerializer,
    PaisSerializer,
    PaisDetailSerializer,
    IndicadorEconomicoSerializer,
    TipoCambioSerializer,
    PortafolioListSerializer,
    PortafolioDetailSerializer,
    PortafolioCreateSerializer,
    PosicionSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.AllowAny]


class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def get_permissions(self):
        # El formulario (Angular) debe poder crear sin login
        if self.action == "create":
            return [permissions.AllowAny()]
        # El resto (listar/ver/borrar/editar) solo ADMIN (por rol)
        return [IsAdminRole()]


class PaisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pais.objects.filter(activo=True)
    serializer_class = PaisSerializer
    permission_classes = [IsViewerOrAbove]
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
        fx = (
            TipoCambio.objects.filter(
                moneda_origen=pais.moneda_codigo,
                moneda_destino="USD",
            )
            .order_by("-fecha")
            .first()
        )
        if not fx:
            return Response({"detail": "No hay tipo de cambio registrado."}, status=404)
        serializer = TipoCambioSerializer(fx)
        return Response(serializer.data)


class SyncPaisesView(APIView):
    """
    Admin-only (por grupo ADMIN): sincroniza países desde RestCountries.
    POST /api/sync/paises/
    """
    permission_classes = [IsAdminRole]

    ISO_CODES = ["CO", "BR", "MX", "AR", "CL", "PE", "EC", "BO", "PY", "UY"]

    ANDINA = {"CO", "PE", "EC", "BO"}
    CONO_SUR = {"AR", "CL", "PY", "UY", "BR"}
    CENTROAMERICA = {"MX"}
    CARIBE = set()

    def _map_region(self, iso: str) -> str:
        iso = iso.upper()
        if iso in self.ANDINA:
            return "ANDINA"
        if iso in self.CONO_SUR:
            return "CONO_SUR"
        if iso in self.CENTROAMERICA:
            return "CENTROAMERICA"
        if iso in self.CARIBE:
            return "CARIBE"
        return "ANDINA"

    def post(self, request):
        codes = ",".join([c.lower() for c in self.ISO_CODES])
        url = f"https://restcountries.com/v3.1/alpha?codes={codes}"

        try:
            req = Request(url, headers={"User-Agent": "DataPulseDev/1.0"})
            with urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            return Response(
                {"detail": f"RestCountries HTTPError: {e.code}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except URLError as e:
            return Response(
                {"detail": f"RestCountries URLError: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            return Response(
                {"detail": f"Error inesperado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        created = 0
        updated = 0
        errors = []

        for item in data:
            try:
                iso = (item.get("cca2") or "").upper()
                if not iso:
                    continue

                nombre = (item.get("name") or {}).get("common", iso)

                currencies = item.get("currencies") or {}
                moneda_codigo = ""
                moneda_nombre = ""
                if currencies:
                    moneda_codigo = list(currencies.keys())[0]
                    moneda_nombre = currencies[moneda_codigo].get("name", moneda_codigo)

                latlng = item.get("latlng") or [0.0, 0.0]
                latitud = float(latlng[0]) if len(latlng) > 0 else 0.0
                longitud = float(latlng[1]) if len(latlng) > 1 else 0.0

                poblacion = int(item.get("population") or 0)

                region = self._map_region(iso)

                _, was_created = Pais.objects.update_or_create(
                    codigo_iso=iso,
                    defaults={
                        "nombre": nombre,
                        "moneda_codigo": moneda_codigo,
                        "moneda_nombre": moneda_nombre,
                        "region": region,
                        "latitud": latitud,
                        "longitud": longitud,
                        "poblacion": poblacion,
                        "activo": True,
                    },
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                errors.append({"iso": item.get("cca2"), "error": str(e)})

        return Response(
            {
                "detail": "Sync completado",
                "created": created,
                "updated": updated,
                "errors": errors,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        groups = list(user.groups.values_list("name", flat=True))
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "groups": groups,
            }
        )


class PortafolioViewSet(viewsets.ModelViewSet):
    queryset = Portafolio.objects.all()

    def get_permissions(self):
        # Leer: VIEWER o superior
        if self.action in ["list", "retrieve"]:
            return [IsViewerOrAbove()]
        # Escribir: ANALISTA o superior
        return [IsAnalystOrAdmin()]

    def get_serializer_class(self):
        # List: liviano
        if self.action == "list":
            return PortafolioListSerializer

        # Create/Update: acepta posiciones anidadas
        if self.action in ["create", "update", "partial_update"]:
            return PortafolioCreateSerializer

        # Retrieve: detalle con posiciones
        return PortafolioDetailSerializer