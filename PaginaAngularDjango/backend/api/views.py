import json
import statistics
from datetime import date, datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
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
    DashboardMapaSerializer,
    DashboardTendenciaSerieSerializer,
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

WORLD_BANK_MAP = {
    'PIB': 'NY.GDP.MKTP.CD',
    'INFLACION': 'FP.CPI.TOTL.ZG',
    'DESEMPLEO': 'SL.UEM.TOTL.ZS',
    'BALANZA_COMERCIAL': 'NE.RSB.GNFS.ZS',
    'DEUDA_PIB': 'GC.DOD.TOTL.GD.ZS',
    'PIB_PERCAPITA': 'NY.GDP.PCAP.CD',
}

INDICATOR_UNIT = {
    'PIB': 'USD',
    'INFLACION': 'PORCENTAJE',
    'DESEMPLEO': 'PORCENTAJE',
    'BALANZA_COMERCIAL': 'PORCENTAJE',
    'DEUDA_PIB': 'PORCENTAJE',
    'PIB_PERCAPITA': 'USD',
}


def fetch_json(url: str, timeout: int = 20):
    req = Request(url, headers={'User-Agent': 'DataPulseDev/1.0'})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


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


def risk_color(level: str) -> str:
    if level == IndiceRiesgo.NivelRiesgo.CRITICO:
        return '#ef4444'
    if level == IndiceRiesgo.NivelRiesgo.ALTO:
        return '#f97316'
    if level == IndiceRiesgo.NivelRiesgo.MODERADO:
        return '#eab308'
    return '#22c55e'


def get_indicator_value(pais: Pais, tipo: str, anio=None):
    qs = IndicadorEconomico.objects.filter(pais=pais, tipo=tipo)
    if anio is not None:
        qs = qs.filter(anio=anio)
    item = qs.order_by('-anio', '-fecha_actualizacion').first()
    return item.valor if item else None


def obtener_variaciones_tipo_cambio(pais: Pais, dias=30):
    return list(
        TipoCambio.objects.filter(moneda_origen=pais.moneda_codigo, moneda_destino='USD')
        .order_by('-fecha')
        .values_list('variacion_porcentual', flat=True)[:dias]
    )


def calcular_score_economico(pais: Pais):
    score = 100
    missing = []

    pib_pc = get_indicator_value(pais, 'PIB_PERCAPITA')
    if pib_pc is None:
        missing.append('PIB_PERCAPITA')
    else:
        if pib_pc < 3000:
            score -= 30
        elif pib_pc < 6000:
            score -= 15
        elif pib_pc < 12000:
            score -= 5

    inflacion = get_indicator_value(pais, 'INFLACION')
    if inflacion is None:
        missing.append('INFLACION')
    else:
        if inflacion > 50:
            score -= 40
        elif inflacion > 10:
            score -= 25
        elif inflacion > 5:
            score -= 10

    desempleo = get_indicator_value(pais, 'DESEMPLEO')
    if desempleo is None:
        missing.append('DESEMPLEO')
    else:
        if desempleo > 15:
            score -= 25
        elif desempleo > 10:
            score -= 15
        elif desempleo > 7:
            score -= 5

    deuda = get_indicator_value(pais, 'DEUDA_PIB')
    if deuda is None:
        missing.append('DEUDA_PIB')
    else:
        if deuda > 80:
            score -= 20
        elif deuda > 50:
            score -= 10

    return max(0, score), missing


def calcular_score_cambiario(pais: Pais):
    score = 100
    variaciones = [v for v in obtener_variaciones_tipo_cambio(pais, dias=30) if v is not None]
    if not variaciones:
        return score, {'volatilidad': None, 'depreciacion': None, 'faltantes': ['TIPO_CAMBIO']}

    volatilidad = statistics.pstdev(variaciones) if len(variaciones) > 1 else 0
    if volatilidad > 3.0:
        score -= 40
    elif volatilidad > 1.5:
        score -= 25
    elif volatilidad > 0.5:
        score -= 10

    factor = 1.0
    for v in variaciones:
        factor *= (1 + (v / 100))
    depreciacion = max(0, -((factor - 1) * 100))
    if depreciacion > 10:
        score -= 30
    elif depreciacion > 5:
        score -= 15
    elif depreciacion > 2:
        score -= 5

    return max(0, score), {'volatilidad': round(volatilidad, 4), 'depreciacion': round(depreciacion, 4), 'faltantes': []}


def contar_indicadores_en_riesgo(pais: Pais, crecimiento_pib):
    cnt = 0
    inflacion = get_indicator_value(pais, 'INFLACION')
    desempleo = get_indicator_value(pais, 'DESEMPLEO')
    deuda = get_indicator_value(pais, 'DEUDA_PIB')
    balanza = get_indicator_value(pais, 'BALANZA_COMERCIAL')

    if inflacion is not None and inflacion > 10:
        cnt += 1
    if desempleo is not None and desempleo > 10:
        cnt += 1
    if deuda is not None and deuda > 60:
        cnt += 1
    if balanza is not None and balanza < 0:
        cnt += 1
    if crecimiento_pib is not None and crecimiento_pib < 1:
        cnt += 1
    return cnt


def calcular_score_estabilidad(pais: Pais):
    score = 100
    missing = []

    balanza = get_indicator_value(pais, 'BALANZA_COMERCIAL')
    if balanza is None:
        missing.append('BALANZA_COMERCIAL')
    else:
        if balanza < -10:
            score -= 25
        elif balanza < -5:
            score -= 15
        elif balanza < 0:
            score -= 5

    anio_actual = timezone.now().year
    pib_actual = get_indicator_value(pais, 'PIB', anio_actual)
    pib_anterior = get_indicator_value(pais, 'PIB', anio_actual - 1)
    crecimiento = None
    if pib_actual and pib_anterior:
        crecimiento = ((pib_actual - pib_anterior) / pib_anterior) * 100
        if crecimiento < -2:
            score -= 30
        elif crecimiento < 0:
            score -= 20
        elif crecimiento < 1:
            score -= 10
    else:
        missing.append('PIB_TENDENCIA')

    indicadores_negativos = contar_indicadores_en_riesgo(pais, crecimiento)
    score -= (indicadores_negativos * 5)

    return max(0, score), {
        'crecimiento_pib': None if crecimiento is None else round(crecimiento, 4),
        'indicadores_negativos': indicadores_negativos,
        'faltantes': missing,
    }


def calculate_country_risk(pais):
    score_economico, missing_e = calcular_score_economico(pais)
    score_cambiario, det_c = calcular_score_cambiario(pais)
    score_estabilidad, det_s = calcular_score_estabilidad(pais)

    compuesto = round((score_economico * 0.40) + (score_cambiario * 0.30) + (score_estabilidad * 0.30), 2)

    detalle = {
        'formula': 'IRPC=(E*0.40)+(C*0.30)+(S*0.30)',
        'faltantes': sorted(set(missing_e + det_c.get('faltantes', []) + det_s.get('faltantes', []))),
        'cambiario': det_c,
        'estabilidad': det_s,
    }

    return {
        'score_economico': round(score_economico, 2),
        'score_cambiario': round(score_cambiario, 2),
        'score_estabilidad': round(score_estabilidad, 2),
        'indice_compuesto': compuesto,
        'nivel_riesgo': classify_risk(compuesto),
        'detalle_calculo': detalle,
    }


def recalculate_all_risks():
    today = date.today()
    updated = 0
    warnings = 0
    critical = 0
    for pais in Pais.objects.filter(activo=True):
        prev = (
            IndiceRiesgo.objects.filter(pais=pais)
            .exclude(fecha_calculo=today)
            .order_by('-fecha_calculo')
            .first()
        )
        payload = calculate_country_risk(pais)
        current, _ = IndiceRiesgo.objects.update_or_create(
            pais=pais,
            fecha_calculo=today,
            defaults=payload,
        )
        updated += 1

        if current.indice_compuesto < 25:
            critical += 1
            Alerta.objects.create(
                usuario=None,
                pais=pais,
                tipo_alerta=Alerta.TipoAlerta.RIESGO,
                severidad=Alerta.Severidad.CRITICAL,
                titulo=f'IRPC critico en {pais.nombre}',
                mensaje=f'El indice de riesgo compuesto cayo a {current.indice_compuesto}.',
            )

        if prev and (prev.indice_compuesto - current.indice_compuesto) > 15:
            warnings += 1
            Alerta.objects.create(
                usuario=None,
                pais=pais,
                tipo_alerta=Alerta.TipoAlerta.RIESGO,
                severidad=Alerta.Severidad.WARNING,
                titulo=f'Caida fuerte de IRPC en {pais.nombre}',
                mensaje=f'El IRPC disminuyo {(prev.indice_compuesto - current.indice_compuesto):.2f} puntos.',
            )

        inflacion = get_indicator_value(pais, 'INFLACION')
        if inflacion is not None and inflacion > 50:
            Alerta.objects.create(
                usuario=None,
                pais=pais,
                tipo_alerta=Alerta.TipoAlerta.INDICADOR,
                severidad=Alerta.Severidad.CRITICAL,
                titulo=f'Inflacion critica en {pais.nombre}',
                mensaje=f'La inflacion reportada es {inflacion:.2f}%, superior a 50%.',
            )

    return {'updated': updated, 'warnings': warnings, 'critical': critical}


def sync_world_bank_indicators(iso_codes, years_back=5):
    end_year = timezone.now().year
    start_year = end_year - years_back + 1

    created = 0
    updated = 0
    errors = []

    for iso in iso_codes:
        pais = Pais.objects.filter(codigo_iso=iso).first()
        if not pais:
            errors.append({'iso': iso, 'error': 'Pais no encontrado en BD'})
            continue

        for tipo, wb_code in WORLD_BANK_MAP.items():
            url = (
                f'https://api.worldbank.org/v2/country/{iso}/indicator/{wb_code}'
                f'?date={start_year}:{end_year}&format=json&per_page=200'
            )
            try:
                payload = fetch_json(url, timeout=30)
                series = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
                for point in series:
                    value = point.get('value')
                    year = point.get('date')
                    if value is None or year is None:
                        continue
                    _, was_created = IndicadorEconomico.objects.update_or_create(
                        pais=pais,
                        tipo=tipo,
                        anio=int(year),
                        defaults={
                            'valor': float(value),
                            'unidad': INDICATOR_UNIT[tipo],
                            'fuente': IndicadorEconomico.Fuente.WORLD_BANK,
                        },
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1
            except (HTTPError, URLError) as e:
                errors.append({'iso': iso, 'tipo': tipo, 'error': str(e)})
            except Exception as e:
                errors.append({'iso': iso, 'tipo': tipo, 'error': f'Error inesperado: {str(e)}'})
    return {'created': created, 'updated': updated, 'errors': errors}


def sync_exchange_rates():
    today = date.today()
    errors = []
    updated = 0
    alerts = 0

    try:
        payload = fetch_json('https://api.exchangerate-api.com/v4/latest/USD', timeout=30)
        rates = payload.get('rates', {})
    except Exception as e:
        return {'updated': 0, 'alerts': 0, 'errors': [f'No se pudo consultar tipo de cambio: {str(e)}']}

    for pais in Pais.objects.filter(activo=True):
        code = pais.moneda_codigo.upper()
        if code == 'USD':
            rate_usd_to_local = 1.0
        else:
            rate_usd_to_local = rates.get(code)
        if not rate_usd_to_local:
            errors.append(f'Sin tasa para {code}')
            continue

        local_to_usd = 1 / float(rate_usd_to_local)
        prev = (
            TipoCambio.objects.filter(moneda_origen=code, moneda_destino='USD')
            .exclude(fecha=today)
            .order_by('-fecha')
            .first()
        )
        variacion = None
        if prev and prev.tasa:
            variacion = ((local_to_usd - prev.tasa) / prev.tasa) * 100

        TipoCambio.objects.update_or_create(
            moneda_origen=code,
            moneda_destino='USD',
            fecha=today,
            defaults={
                'tasa': local_to_usd,
                'variacion_porcentual': variacion,
                'fuente': 'EXCHANGERATE_API',
            },
        )
        updated += 1

        if variacion is not None and abs(variacion) > 3:
            alerts += 1
            Alerta.objects.create(
                usuario=None,
                pais=pais,
                tipo_alerta=Alerta.TipoAlerta.TIPO_CAMBIO,
                severidad=Alerta.Severidad.WARNING,
                titulo=f'Variacion de tipo de cambio en {pais.nombre}',
                mensaje=f'La variacion diaria fue de {variacion:.2f}%.',
            )

    return {'updated': updated, 'alerts': alerts, 'errors': errors}


def paginated_response(request, queryset, serializer_cls, context=None):
    paginator = PageNumberPagination()
    paginator.page_size = 20
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size = 100
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_cls(page, many=True, context=context or {'request': request})
    return paginator.get_paginated_response(serializer.data)


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
        search = self.request.query_params.get('search')
        ordering = self.request.query_params.get('ordering')
        if region:
            qs = qs.filter(region=region)
        if search:
            qs = qs.filter(
                Q(nombre__icontains=search)
                | Q(codigo_iso__icontains=search)
                | Q(moneda_codigo__icontains=search)
            )
        if ordering in ['nombre', '-nombre', 'poblacion', '-poblacion', 'codigo_iso', '-codigo_iso']:
            qs = qs.order_by(ordering)
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaisDetailSerializer
        return PaisSerializer

    @action(detail=True, methods=['get'], url_path='indicadores')
    def indicadores(self, request, codigo_iso=None):
        pais = self.get_object()
        qs = IndicadorEconomico.objects.filter(pais=pais)
        tipo = request.query_params.get('tipo')
        anio = request.query_params.get('anio')
        if tipo:
            qs = qs.filter(tipo=tipo)
        if anio:
            qs = qs.filter(anio=anio)
        ordering = request.query_params.get('ordering', '-anio')
        if ordering in ['anio', '-anio', 'tipo', '-tipo', 'valor', '-valor']:
            qs = qs.order_by(ordering)
        return paginated_response(request, qs, IndicadorEconomicoSerializer, {'request': request})

    @action(detail=True, methods=['get'], url_path='tipo-cambio')
    def tipo_cambio(self, request, codigo_iso=None):
        pais = self.get_object()
        qs = TipoCambio.objects.filter(moneda_origen=pais.moneda_codigo, moneda_destino='USD')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        if start:
            qs = qs.filter(fecha__gte=start)
        if end:
            qs = qs.filter(fecha__lte=end)
        ordering = request.query_params.get('ordering', '-fecha')
        if ordering in ['fecha', '-fecha', 'tasa', '-tasa']:
            qs = qs.order_by(ordering)
        return paginated_response(request, qs, TipoCambioSerializer, {'request': request})


class SyncPaisesView(APIView):
    permission_classes = [IsAdminRole]

    ISO_CODES = ['CO', 'BR', 'MX', 'AR', 'CL', 'PE', 'EC', 'UY', 'PY', 'PA']
    ANDINA = {'CO', 'PE', 'EC'}
    CONO_SUR = {'AR', 'CL', 'PY', 'UY', 'BR'}
    CENTROAMERICA = {'MX', 'PA'}
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
            data = fetch_json(url, timeout=20)
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
            titulo='Sincronizacion de paises completada',
            mensaje=f'Se sincronizaron paises: creados={created}, actualizados={updated}',
        )
        log_activity(request, LogActividad.Accion.CREAR, 'SyncPaises', detalle={'created': created, 'updated': updated, 'errors': len(errors)})

        return Response({'detail': 'Sync completado', 'created': created, 'updated': updated, 'errors': errors}, status=status.HTTP_200_OK)


class SyncIndicadoresView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        iso_codes = list(Pais.objects.filter(activo=True).values_list('codigo_iso', flat=True))
        wb = sync_world_bank_indicators(iso_codes)
        fx = sync_exchange_rates()
        risks = recalculate_all_risks()

        Alerta.objects.create(
            usuario=None,
            pais=None,
            tipo_alerta=Alerta.TipoAlerta.INDICADOR,
            severidad=Alerta.Severidad.INFO,
            titulo='Datos economicos sincronizados',
            mensaje='Se completaron sincronizacion de indicadores, tipo de cambio y recalculo de IRPC.',
        )
        log_activity(
            request,
            LogActividad.Accion.CREAR,
            'SyncIndicadores',
            detalle={'world_bank': wb, 'fx': fx, 'riesgo': risks},
        )
        return Response({'world_bank': wb, 'tipo_cambio': fx, 'riesgo': risks}, status=status.HTTP_200_OK)


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
        if self.action in ['list', 'retrieve', 'resumen', 'export_pdf', 'validate_nombre']:
            return [IsViewerOrAbove()]
        return [IsAnalystOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        qs = Portafolio.objects.filter(activo=True)
        if not user.is_authenticated:
            return qs.none()
        if user.is_superuser or user.groups.filter(name='ADMIN').exists():
            base = qs
        else:
            base = qs.filter(Q(owner=user) | Q(es_publico=True)).distinct()

        search = self.request.query_params.get('search')
        ordering = self.request.query_params.get('ordering')
        if search:
            base = base.filter(Q(nombre__icontains=search) | Q(descripcion__icontains=search))
        if ordering in ['nombre', '-nombre', 'created_at', '-created_at', 'updated_at', '-updated_at']:
            base = base.order_by(ordering)
        return base

    def get_serializer_class(self):
        if self.action == 'list':
            return PortafolioListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return PortafolioWriteSerializer
        return PortafolioDetailSerializer

    def perform_create(self, serializer):
        portafolio = serializer.save(owner=self.request.user)
        log_activity(self.request, LogActividad.Accion.CREAR, 'Portafolio', portafolio.id)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_activity(self.request, LogActividad.Accion.EDITAR, 'Portafolio', instance.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.activo = False
        instance.save(update_fields=['activo', 'updated_at'])
        log_activity(request, LogActividad.Accion.ELIMINAR, 'Portafolio', instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='validate-nombre')
    def validate_nombre(self, request):
        nombre = (request.query_params.get('nombre') or '').strip()
        if not nombre:
            return Response({'unique': False, 'detail': 'Debe enviar nombre.'}, status=status.HTTP_400_BAD_REQUEST)
        exists = Portafolio.objects.filter(owner=request.user, nombre__iexact=nombre, activo=True).exists()
        return Response({'unique': not exists})

    @action(detail=True, methods=['post'], url_path='posiciones')
    def create_posicion(self, request, pk=None):
        portafolio = self.get_object()
        serializer = PosicionSerializer(data=request.data, context={'request': request, 'portafolio': portafolio})
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

        serializer = PosicionSerializer(
            posicion,
            data=request.data,
            partial=True,
            context={'request': request, 'portafolio': portafolio},
        )
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

        if not posicion.fecha_salida:
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
        body = (
            f'%PDF-1.1\\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\\n'
            f'2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\\n'
            f'3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<<>>>>endobj\\n'
            f'4 0 obj<</Length 120>>stream\\n'
            f'BT /F1 16 Tf 50 760 Td (DataPulse - Portafolio {portafolio.id}) Tj ET\\n'
            f'BT /F1 12 Tf 50 730 Td (Nombre: {portafolio.nombre}) Tj ET\\n'
            f'BT /F1 12 Tf 50 710 Td (Fecha: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}) Tj ET\\n'
            f'endstream\\nendobj\\ntrailer<</Root 1 0 R>>\\n%%EOF'
        )
        response = HttpResponse(body.encode('latin-1', errors='ignore'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=portafolio_{portafolio.id}.pdf'
        log_activity(request, LogActividad.Accion.EXPORT, 'Portafolio', portafolio.id)
        return response


class RiesgoRankingView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        qs = IndiceRiesgo.objects.select_related('pais').order_by('indice_compuesto', 'pais__nombre')
        ordering = request.query_params.get('ordering')
        if ordering in ['indice_compuesto', '-indice_compuesto', 'fecha_calculo', '-fecha_calculo']:
            qs = qs.order_by(ordering)
        return paginated_response(request, qs, IndiceRiesgoSerializer, {'request': request})


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
        return paginated_response(request, qs, IndiceRiesgoSerializer, {'request': request})


class RiesgoCalcularView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        payload = recalculate_all_risks()
        log_activity(request, LogActividad.Accion.CREAR, 'IndiceRiesgo', detalle=payload)
        return Response({'detail': 'Calculo de riesgo completado', **payload})


class AlertaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AlertaSerializer
    permission_classes = [IsViewerOrAbove]

    def get_queryset(self):
        user = self.request.user
        qs = Alerta.objects.filter(Q(usuario=user) | Q(usuario__isnull=True))
        tipo = self.request.query_params.get('tipo')
        severidad = self.request.query_params.get('severidad')
        leida = self.request.query_params.get('leida')
        ordering = self.request.query_params.get('ordering')
        if tipo:
            qs = qs.filter(tipo_alerta=tipo)
        if severidad:
            qs = qs.filter(severidad=severidad)
        if leida in ['true', 'false']:
            qs = qs.filter(leida=(leida == 'true'))
        if ordering in ['fecha_creacion', '-fecha_creacion', 'severidad', '-severidad']:
            qs = qs.order_by(ordering)
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

        ranking_items = (
            IndiceRiesgo.objects.select_related('pais')
            .order_by('indice_compuesto')
            .values('pais_id', 'pais__codigo_iso', 'pais__nombre', 'indice_compuesto', 'nivel_riesgo')[:10]
        )
        ranking = []
        for row in ranking_items:
            prev = (
                IndiceRiesgo.objects.filter(pais_id=row['pais_id'])
                .exclude(fecha_calculo=date.today())
                .order_by('-fecha_calculo')
                .first()
            )
            variacion = 0 if not prev else round(row['indice_compuesto'] - prev.indice_compuesto, 2)
            tendencia = 'ESTABLE'
            if variacion > 0.25:
                tendencia = 'ALZA'
            elif variacion < -0.25:
                tendencia = 'BAJA'

            ranking.append(
                {
                    'pais__codigo_iso': row['pais__codigo_iso'],
                    'pais__nombre': row['pais__nombre'],
                    'indice_compuesto': row['indice_compuesto'],
                    'nivel_riesgo': row['nivel_riesgo'],
                    'variacion': variacion,
                    'tendencia': tendencia,
                }
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


class DashboardMapaView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        latest_by_country = {}
        for riesgo in IndiceRiesgo.objects.select_related('pais').order_by('pais__codigo_iso', '-fecha_calculo'):
            key = riesgo.pais.codigo_iso
            if key in latest_by_country:
                continue
            latest_by_country[key] = riesgo

        rows = []
        for pais in Pais.objects.filter(activo=True):
            riesgo = latest_by_country.get(pais.codigo_iso)
            if not riesgo:
                continue
            rows.append(
                {
                    'codigo_iso': pais.codigo_iso,
                    'nombre': pais.nombre,
                    'latitud': pais.latitud,
                    'longitud': pais.longitud,
                    'indice_compuesto': riesgo.indice_compuesto,
                    'nivel_riesgo': riesgo.nivel_riesgo,
                    'color': risk_color(riesgo.nivel_riesgo),
                }
            )
        serializer = DashboardMapaSerializer(rows, many=True)
        return Response(serializer.data)


class DashboardTendenciasView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        tipo = (request.query_params.get('tipo') or 'INFLACION').upper()
        if tipo not in WORLD_BANK_MAP.keys():
            return Response({'detail': 'Indicador no valido.'}, status=status.HTTP_400_BAD_REQUEST)

        requested = (request.query_params.get('paises') or '').upper().replace(' ', '')
        selected = [x for x in requested.split(',') if x] if requested else []
        if not selected:
            selected = list(Pais.objects.filter(activo=True).order_by('nombre').values_list('codigo_iso', flat=True)[:3])
        selected = selected[:3]

        current_year = timezone.now().year
        years = list(range(current_year - 4, current_year + 1))
        series = []
        for iso in selected:
            pais = Pais.objects.filter(codigo_iso=iso).first()
            if not pais:
                continue
            values = []
            for y in years:
                val = get_indicator_value(pais, tipo, y)
                values.append(None if val is None else round(float(val), 2))
            series.append({'pais_codigo': pais.codigo_iso, 'pais_nombre': pais.nombre, 'valores': values})

        serializer = DashboardTendenciaSerieSerializer(series, many=True)
        return Response({'tipo': tipo, 'years': years, 'series': serializer.data})
