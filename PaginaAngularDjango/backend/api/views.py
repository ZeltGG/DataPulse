import json
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Alerta,
    IndicadorEconomico,
    IndiceRiesgo,
    LogActividad,
    Pais,
    Portafolio,
    Posicion,
    TipoCambio,
)
from .permissions import IsAdminRole, IsAnalystOrAdmin, IsViewerOrAbove
from .serializers import (
    AlertaSerializer,
    IndicadorEconomicoSerializer,
    IndiceRiesgoSerializer,
    MeUpdateSerializer,
    PaisDetailSerializer,
    PaisSerializer,
    PortafolioDetailSerializer,
    PortafolioListSerializer,
    PortafolioWriteSerializer,
    PosicionSerializer,
    RegisterSerializer,
    TipoCambioSerializer,
)


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def log_activity(request, accion, entidad, entidad_id='', detalle=None):
    if request.path.startswith('/admin/'):
        return
    LogActividad.objects.create(
        usuario=request.user if request.user and request.user.is_authenticated else None,
        accion=accion,
        entidad_afectada=entidad,
        entidad_id=str(entidad_id),
        detalle=detalle or {},
        ip_address=_client_ip(request),
    )


def classify_risk(score):
    if score < 25:
        return IndiceRiesgo.NivelRiesgo.CRITICO
    if score < 50:
        return IndiceRiesgo.NivelRiesgo.ALTO
    if score < 75:
        return IndiceRiesgo.NivelRiesgo.MODERADO
    return IndiceRiesgo.NivelRiesgo.BAJO


def calculate_country_risk(pais):
    indicadores = {i.tipo: i for i in IndicadorEconomico.objects.filter(pais=pais)}
    inflacion = indicadores.get('INFLACION').valor if indicadores.get('INFLACION') else 0
    desempleo = indicadores.get('DESEMPLEO').valor if indicadores.get('DESEMPLEO') else 0
    deuda = indicadores.get('DEUDA_PIB').valor if indicadores.get('DEUDA_PIB') else 0
    fx = (
        TipoCambio.objects.filter(moneda_origen=pais.moneda_codigo, moneda_destino='USD')
        .order_by('-fecha')
        .first()
    )
    variacion_fx = abs(fx.variacion_porcentual) if fx and fx.variacion_porcentual is not None else 0

    score_economico = max(0, min(100, 100 - (inflacion * 1.5 + desempleo + deuda * 0.3)))
    score_cambiario = max(0, min(100, 100 - variacion_fx * 8))
    score_estabilidad = max(0, min(100, 80 - inflacion * 0.8 + 20))
    compuesto = round(score_economico * 0.45 + score_cambiario * 0.25 + score_estabilidad * 0.30, 2)

    return {
        'score_economico': round(score_economico, 2),
        'score_cambiario': round(score_cambiario, 2),
        'score_estabilidad': round(score_estabilidad, 2),
        'indice_compuesto': compuesto,
        'nivel_riesgo': classify_risk(compuesto),
        'detalle_calculo': {
            'inflacion': inflacion,
            'desempleo': desempleo,
            'deuda_pib': deuda,
            'variacion_fx': variacion_fx,
        },
    }


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'id': user.id, 'username': user.username, 'email': user.email}, status=status.HTTP_201_CREATED)


class PaisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pais.objects.filter(activo=True)
    serializer_class = PaisSerializer
    permission_classes = [IsViewerOrAbove]
    lookup_field = 'codigo_iso'

    def get_queryset(self):
        qs = super().get_queryset()
        region = self.request.query_params.get('region')
        if region:
            qs = qs.filter(region=region)
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaisDetailSerializer
        return PaisSerializer

    @action(detail=True, methods=['get'], url_path='indicadores')
    def indicadores(self, request, codigo_iso=None):
        pais = self.get_object()
        qs = IndicadorEconomico.objects.filter(pais=pais).order_by('-anio')
        serializer = IndicadorEconomicoSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='tipo-cambio')
    def tipo_cambio(self, request, codigo_iso=None):
        pais = self.get_object()
        qs = TipoCambio.objects.filter(moneda_origen=pais.moneda_codigo, moneda_destino='USD').order_by('-fecha')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        if start:
            qs = qs.filter(fecha__gte=start)
        if end:
            qs = qs.filter(fecha__lte=end)
        serializer = TipoCambioSerializer(qs, many=True)
        return Response(serializer.data)


class SyncPaisesView(APIView):
    permission_classes = [IsAdminRole]

    ISO_CODES = ['CO', 'BR', 'MX', 'AR', 'CL', 'PE', 'EC', 'BO', 'PY', 'UY']
    ANDINA = {'CO', 'PE', 'EC', 'BO'}
    CONO_SUR = {'AR', 'CL', 'PY', 'UY', 'BR'}
    CENTROAMERICA = {'MX'}
    CARIBE = set()

    def _map_region(self, iso: str) -> str:
        iso = iso.upper()
        if iso in self.ANDINA:
            return 'ANDINA'
        if iso in self.CONO_SUR:
            return 'CONO_SUR'
        if iso in self.CENTROAMERICA:
            return 'CENTROAMERICA'
        if iso in self.CARIBE:
            return 'CARIBE'
        return 'ANDINA'

    def post(self, request):
        codes = ','.join([c.lower() for c in self.ISO_CODES])
        url = f'https://restcountries.com/v3.1/alpha?codes={codes}'

        try:
            req = Request(url, headers={'User-Agent': 'DataPulseDev/1.0'})
            with urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except HTTPError as e:
            return Response({'detail': f'RestCountries HTTPError: {e.code}'}, status=status.HTTP_502_BAD_GATEWAY)
        except URLError as e:
            return Response({'detail': f'RestCountries URLError: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({'detail': f'Error inesperado: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        created = 0
        updated = 0
        errors = []

        for item in data:
            try:
                iso = (item.get('cca2') or '').upper()
                if not iso:
                    continue
                nombre = (item.get('name') or {}).get('common', iso)
                currencies = item.get('currencies') or {}
                moneda_codigo = ''
                moneda_nombre = ''
                if currencies:
                    moneda_codigo = list(currencies.keys())[0]
                    moneda_nombre = currencies[moneda_codigo].get('name', moneda_codigo)

                latlng = item.get('latlng') or [0.0, 0.0]
                latitud = float(latlng[0]) if len(latlng) > 0 else 0.0
                longitud = float(latlng[1]) if len(latlng) > 1 else 0.0
                poblacion = int(item.get('population') or 0)
                region = self._map_region(iso)

                _, was_created = Pais.objects.update_or_create(
                    codigo_iso=iso,
                    defaults={
                        'nombre': nombre,
                        'moneda_codigo': moneda_codigo,
                        'moneda_nombre': moneda_nombre,
                        'region': region,
                        'latitud': latitud,
                        'longitud': longitud,
                        'poblacion': poblacion,
                        'activo': True,
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({'iso': item.get('cca2'), 'error': str(e)})

        Alerta.objects.create(
            usuario=None,
            pais=None,
            tipo_alerta=Alerta.TipoAlerta.INDICADOR,
            severidad=Alerta.Severidad.INFO,
            titulo='Sincronizacion completada',
            mensaje=f'Se sincronizaron paises: creados={created}, actualizados={updated}',
        )
        log_activity(request, LogActividad.Accion.CREAR, 'SyncPaises', detalle={'created': created, 'updated': updated, 'errors': len(errors)})

        return Response({'detail': 'Sync completado', 'created': created, 'updated': updated, 'errors': errors}, status=status.HTTP_200_OK)


class SyncIndicadoresView(SyncPaisesView):
    pass


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        groups = list(user.groups.values_list('name', flat=True))
        return Response(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'groups': groups,
            }
        )

    def put(self, request):
        serializer = MeUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PortafolioViewSet(viewsets.ModelViewSet):
    queryset = Portafolio.objects.all().prefetch_related('posiciones')

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'resumen', 'export_pdf']:
            return [IsViewerOrAbove()]
        return [IsAnalystOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        qs = Portafolio.objects.filter(activo=True)
        if not user.is_authenticated:
            return qs.none()
        if user.is_superuser or user.groups.filter(name='ADMIN').exists():
            return qs
        return qs.filter(Q(owner=user) | Q(es_publico=True)).distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return PortafolioListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return PortafolioWriteSerializer
        return PortafolioDetailSerializer

    def perform_create(self, serializer):
        portafolio = serializer.save(owner=self.request.user)
        log_activity(self.request, LogActividad.Accion.CREAR, 'Portafolio', portafolio.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.activo = False
        instance.save(update_fields=['activo', 'updated_at'])
        log_activity(request, LogActividad.Accion.ELIMINAR, 'Portafolio', instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='posiciones')
    def create_posicion(self, request, pk=None):
        portafolio = self.get_object()
        serializer = PosicionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        posicion = serializer.save(portafolio=portafolio)
        log_activity(request, LogActividad.Accion.CREAR, 'Posicion', posicion.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put'], url_path=r'posiciones/(?P<posicion_id>[^/.]+)')
    def update_posicion(self, request, pk=None, posicion_id=None):
        portafolio = self.get_object()
        try:
            posicion = portafolio.posiciones.get(pk=posicion_id)
        except Posicion.DoesNotExist:
            return Response({'detail': 'Posicion no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PosicionSerializer(posicion, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_activity(request, LogActividad.Accion.EDITAR, 'Posicion', posicion.id)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path=r'posiciones/(?P<posicion_id>[^/.]+)')
    def delete_posicion(self, request, pk=None, posicion_id=None):
        portafolio = self.get_object()
        try:
            posicion = portafolio.posiciones.get(pk=posicion_id)
        except Posicion.DoesNotExist:
            return Response({'detail': 'Posicion no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        posicion.fecha_salida = date.today()
        posicion.save(update_fields=['fecha_salida'])
        log_activity(request, LogActividad.Accion.ELIMINAR, 'Posicion', posicion.id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='resumen')
    def resumen(self, request, pk=None):
        portafolio = self.get_object()
        activas = portafolio.posiciones.filter(fecha_salida__isnull=True)
        total = activas.aggregate(total=Sum('monto_inversion_usd'))['total'] or 0

        por_pais = list(
            activas.values('pais__nombre').annotate(total=Sum('monto_inversion_usd')).order_by('-total')
        )
        por_tipo = list(
            activas.values('tipo_activo').annotate(total=Sum('monto_inversion_usd')).order_by('-total')
        )

        riesgo_promedio = (
            IndiceRiesgo.objects.filter(pais__in=activas.values('pais')).aggregate(avg=Avg('indice_compuesto'))['avg'] or 0
        )

        return Response(
            {
                'portafolio_id': portafolio.id,
                'monto_total': total,
                'riesgo_promedio': round(riesgo_promedio, 2),
                'distribucion_pais': por_pais,
                'distribucion_tipo_activo': por_tipo,
            }
        )

    @action(detail=True, methods=['get'], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        portafolio = self.get_object()
        # PDF minimo valido para descarga simple
        body = f'%PDF-1.1\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<<>>>>endobj\n4 0 obj<</Length 78>>stream\nBT /F1 18 Tf 50 740 Td (Portafolio: {portafolio.nombre}) Tj ET\nendstream\nendobj\ntrailer<</Root 1 0 R>>\n%%EOF'
        response = HttpResponse(body.encode('latin-1', errors='ignore'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=portafolio_{portafolio.id}.pdf'
        log_activity(request, LogActividad.Accion.EXPORT, 'Portafolio', portafolio.id)
        return response


class RiesgoRankingView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        items = IndiceRiesgo.objects.select_related('pais').order_by('indice_compuesto')
        serializer = IndiceRiesgoSerializer(items, many=True)
        return Response(serializer.data)


class RiesgoDetailView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request, codigo_iso):
        item = (
            IndiceRiesgo.objects.select_related('pais')
            .filter(pais__codigo_iso=codigo_iso.upper())
            .order_by('-fecha_calculo')
            .first()
        )
        if not item:
            return Response({'detail': 'No hay riesgo calculado para este pais.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(IndiceRiesgoSerializer(item).data)


class RiesgoHistoricoView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request, codigo_iso):
        qs = IndiceRiesgo.objects.filter(pais__codigo_iso=codigo_iso.upper()).order_by('-fecha_calculo')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        if start:
            qs = qs.filter(fecha_calculo__gte=start)
        if end:
            qs = qs.filter(fecha_calculo__lte=end)
        return Response(IndiceRiesgoSerializer(qs, many=True).data)


class RiesgoCalcularView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        created = 0
        for pais in Pais.objects.filter(activo=True):
            payload = calculate_country_risk(pais)
            obj, _ = IndiceRiesgo.objects.update_or_create(
                pais=pais,
                fecha_calculo=date.today(),
                defaults=payload,
            )
            created += 1

            if obj.indice_compuesto < 25:
                Alerta.objects.create(
                    usuario=None,
                    pais=pais,
                    tipo_alerta=Alerta.TipoAlerta.RIESGO,
                    severidad=Alerta.Severidad.CRITICAL,
                    titulo=f'Riesgo critico en {pais.nombre}',
                    mensaje=f'IRPC en {obj.indice_compuesto}',
                )

        log_activity(request, LogActividad.Accion.CREAR, 'IndiceRiesgo', detalle={'updated': created})
        return Response({'detail': 'Calculo de riesgo completado', 'paises_actualizados': created})


class AlertaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AlertaSerializer
    permission_classes = [IsViewerOrAbove]

    def get_queryset(self):
        user = self.request.user
        qs = Alerta.objects.filter(Q(usuario=user) | Q(usuario__isnull=True))
        tipo = self.request.query_params.get('tipo')
        severidad = self.request.query_params.get('severidad')
        leida = self.request.query_params.get('leida')
        if tipo:
            qs = qs.filter(tipo_alerta=tipo)
        if severidad:
            qs = qs.filter(severidad=severidad)
        if leida in ['true', 'false']:
            qs = qs.filter(leida=(leida == 'true'))
        return qs

    @action(detail=True, methods=['put'], url_path='leer', permission_classes=[IsViewerOrAbove])
    def marcar_leida(self, request, pk=None):
        alerta = self.get_object()
        alerta.leida = True
        alerta.save(update_fields=['leida'])
        return Response({'detail': 'Alerta marcada como leida.'})

    @action(detail=False, methods=['put'], url_path='leer-todas', permission_classes=[IsViewerOrAbove])
    def leer_todas(self, request):
        count = self.get_queryset().filter(leida=False).update(leida=True)
        return Response({'detail': 'Alertas actualizadas', 'count': count})

    @action(detail=False, methods=['get'], url_path='resumen', permission_classes=[IsViewerOrAbove])
    def resumen(self, request):
        qs = self.get_queryset()
        return Response(
            {
                'total': qs.count(),
                'no_leidas': qs.filter(leida=False).count(),
                'por_tipo': list(qs.values('tipo_alerta').annotate(count=Count('id')).order_by('tipo_alerta')),
                'por_severidad': list(qs.values('severidad').annotate(count=Count('id')).order_by('severidad')),
            }
        )


class DashboardResumenView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        total_paises = Pais.objects.filter(activo=True).count()
        alertas_activas = Alerta.objects.filter(leida=False).count()
        portafolios_usuario = Portafolio.objects.filter(owner=request.user, activo=True).count()
        promedio_irpc = IndiceRiesgo.objects.aggregate(avg=Avg('indice_compuesto'))['avg'] or 0

        ranking = list(
            IndiceRiesgo.objects.select_related('pais')
            .order_by('indice_compuesto')
            .values('pais__codigo_iso', 'pais__nombre', 'indice_compuesto', 'nivel_riesgo')[:10]
        )

        return Response(
            {
                'kpis': {
                    'total_paises': total_paises,
                    'alertas_activas': alertas_activas,
                    'portafolios_usuario': portafolios_usuario,
                    'promedio_irpc': round(promedio_irpc, 2),
                },
                'ranking': ranking,
            }
        )
