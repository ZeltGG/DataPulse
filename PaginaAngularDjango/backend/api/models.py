from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Project(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField()
    tech_stack = models.CharField(max_length=200, blank=True)
    repo_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.name} <{self.email}>'


class Pais(models.Model):
    class Region(models.TextChoices):
        ANDINA = 'ANDINA', 'ANDINA'
        CONO_SUR = 'CONO_SUR', 'CONO_SUR'
        CENTROAMERICA = 'CENTROAMERICA', 'CENTROAMERICA'
        CARIBE = 'CARIBE', 'CARIBE'

    codigo_iso = models.CharField(max_length=2, unique=True)
    nombre = models.CharField(max_length=100)
    moneda_codigo = models.CharField(max_length=3)
    moneda_nombre = models.CharField(max_length=50)
    region = models.CharField(max_length=20, choices=Region.choices)
    latitud = models.FloatField()
    longitud = models.FloatField()
    poblacion = models.BigIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self) -> str:
        return f'{self.nombre} ({self.codigo_iso})'


class IndicadorEconomico(models.Model):
    class Tipo(models.TextChoices):
        PIB = 'PIB', 'PIB'
        INFLACION = 'INFLACION', 'INFLACION'
        DESEMPLEO = 'DESEMPLEO', 'DESEMPLEO'
        BALANZA_COMERCIAL = 'BALANZA_COMERCIAL', 'BALANZA_COMERCIAL'
        DEUDA_PIB = 'DEUDA_PIB', 'DEUDA_PIB'
        PIB_PERCAPITA = 'PIB_PERCAPITA', 'PIB_PERCAPITA'

    class Unidad(models.TextChoices):
        PORCENTAJE = 'PORCENTAJE', 'PORCENTAJE'
        USD = 'USD', 'USD'
        USD_MILES_MILLONES = 'USD_MILES_MILLONES', 'USD_MILES_MILLONES'

    class Fuente(models.TextChoices):
        WORLD_BANK = 'WORLD_BANK', 'WORLD_BANK'
        MANUAL = 'MANUAL', 'MANUAL'

    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='indicadores')
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    valor = models.FloatField()
    unidad = models.CharField(max_length=30, choices=Unidad.choices)
    anio = models.PositiveIntegerField()
    fuente = models.CharField(max_length=20, choices=Fuente.choices, default=Fuente.MANUAL)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-anio']
        constraints = [
            models.UniqueConstraint(fields=['pais', 'tipo', 'anio'], name='uniq_indicador_pais_tipo_anio'),
        ]

    def __str__(self) -> str:
        return f'{self.pais.codigo_iso} {self.tipo} {self.anio}'


class TipoCambio(models.Model):
    moneda_origen = models.CharField(max_length=3)
    moneda_destino = models.CharField(max_length=3, default='USD')
    tasa = models.FloatField()
    fecha = models.DateField()
    variacion_porcentual = models.FloatField(null=True, blank=True)
    fuente = models.CharField(max_length=50, blank=True, default='MANUAL')

    class Meta:
        ordering = ['-fecha']
        constraints = [
            models.UniqueConstraint(fields=['moneda_origen', 'moneda_destino', 'fecha'], name='uniq_fx_pair_fecha'),
        ]

    def __str__(self) -> str:
        return f'{self.moneda_origen}/{self.moneda_destino} {self.fecha}'


class Portafolio(models.Model):
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='portafolios',
    )
    activo = models.BooleanField(default=True)
    es_publico = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['owner', 'nombre'], name='uniq_owner_portafolio_nombre_activo'),
        ]

    def __str__(self) -> str:
        return self.nombre


class Posicion(models.Model):
    class TipoActivo(models.TextChoices):
        RENTA_FIJA = 'RENTA_FIJA', 'RENTA_FIJA'
        RENTA_VARIABLE = 'RENTA_VARIABLE', 'RENTA_VARIABLE'
        COMMODITIES = 'COMMODITIES', 'COMMODITIES'
        MONEDA = 'MONEDA', 'MONEDA'
        ACCION = 'ACCION', 'ACCION'
        BONO = 'BONO', 'BONO'
        ETF = 'ETF', 'ETF'
        CRYPTO = 'CRYPTO', 'CRYPTO'
        OTRO = 'OTRO', 'OTRO'

    portafolio = models.ForeignKey(Portafolio, on_delete=models.CASCADE, related_name='posiciones')
    pais = models.ForeignKey(Pais, on_delete=models.PROTECT, related_name='posiciones')
    activo = models.CharField(max_length=120)
    ticker = models.CharField(max_length=20, blank=True)
    tipo_activo = models.CharField(max_length=20, choices=TipoActivo.choices, default=TipoActivo.ACCION)
    moneda = models.CharField(max_length=3, default='USD')
    cantidad = models.FloatField(default=0)
    precio_unitario = models.FloatField(default=0)
    peso_porcentual = models.FloatField(null=True, blank=True)
    monto_inversion_usd = models.FloatField(default=0, validators=[MinValueValidator(0)])
    fecha_entrada = models.DateField(default=timezone.now)
    fecha_salida = models.DateField(null=True, blank=True)
    notas = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_salida__isnull=True) | Q(fecha_salida__gt=F('fecha_entrada')),
                name='posicion_fecha_salida_gt_entrada',
            )
        ]

    def save(self, *args, **kwargs):
        if self.monto_inversion_usd <= 0 and self.cantidad > 0 and self.precio_unitario > 0:
            self.monto_inversion_usd = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.portafolio.nombre} - {self.activo}'


class IndiceRiesgo(models.Model):
    class NivelRiesgo(models.TextChoices):
        BAJO = 'BAJO', 'BAJO'
        MODERADO = 'MODERADO', 'MODERADO'
        ALTO = 'ALTO', 'ALTO'
        CRITICO = 'CRITICO', 'CRITICO'

    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='indices_riesgo')
    fecha_calculo = models.DateField(default=timezone.now)
    score_economico = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    score_cambiario = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    score_estabilidad = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    indice_compuesto = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    nivel_riesgo = models.CharField(max_length=12, choices=NivelRiesgo.choices)
    detalle_calculo = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_calculo', 'pais__nombre']
        constraints = [
            models.UniqueConstraint(fields=['pais', 'fecha_calculo'], name='uniq_riesgo_pais_fecha')
        ]


class Alerta(models.Model):
    class TipoAlerta(models.TextChoices):
        RIESGO = 'RIESGO', 'RIESGO'
        TIPO_CAMBIO = 'TIPO_CAMBIO', 'TIPO_CAMBIO'
        INDICADOR = 'INDICADOR', 'INDICADOR'

    class Severidad(models.TextChoices):
        INFO = 'INFO', 'INFO'
        WARNING = 'WARNING', 'WARNING'
        CRITICAL = 'CRITICAL', 'CRITICAL'

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='alertas')
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, null=True, blank=True, related_name='alertas')
    tipo_alerta = models.CharField(max_length=20, choices=TipoAlerta.choices)
    severidad = models.CharField(max_length=10, choices=Severidad.choices)
    titulo = models.CharField(max_length=160)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']


class LogActividad(models.Model):
    class Accion(models.TextChoices):
        CREAR = 'CREAR', 'CREAR'
        EDITAR = 'EDITAR', 'EDITAR'
        ELIMINAR = 'ELIMINAR', 'ELIMINAR'
        CONSULTAR = 'CONSULTAR', 'CONSULTAR'
        LOGIN = 'LOGIN', 'LOGIN'
        EXPORT = 'EXPORT', 'EXPORT'

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=Accion.choices)
    entidad_afectada = models.CharField(max_length=80)
    entidad_id = models.CharField(max_length=64, blank=True)
    detalle = models.JSONField(default=dict, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
