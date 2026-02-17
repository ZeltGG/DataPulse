from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class Project(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField()
    tech_stack = models.CharField(max_length=200, blank=True)
    repo_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"



# Core del PDF 


class Pais(models.Model):
    class Region(models.TextChoices):
        ANDINA = "ANDINA", "ANDINA"
        CONO_SUR = "CONO_SUR", "CONO_SUR"
        CENTROAMERICA = "CENTROAMERICA", "CENTROAMERICA"
        CARIBE = "CARIBE", "CARIBE"

    codigo_iso = models.CharField(max_length=2, unique=True)  # Ej: "CO"
    nombre = models.CharField(max_length=100)

    moneda_codigo = models.CharField(max_length=3)  # Ej: "COP"
    moneda_nombre = models.CharField(max_length=50)

    region = models.CharField(max_length=20, choices=Region.choices)

    latitud = models.FloatField()
    longitud = models.FloatField()
    poblacion = models.BigIntegerField()

    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.codigo_iso})"


class IndicadorEconomico(models.Model):
    class Tipo(models.TextChoices):
        PIB = "PIB", "PIB"
        INFLACION = "INFLACION", "INFLACION"
        DESEMPLEO = "DESEMPLEO", "DESEMPLEO"
        BALANZA_COMERCIAL = "BALANZA_COMERCIAL", "BALANZA_COMERCIAL"
        DEUDA_PIB = "DEUDA_PIB", "DEUDA_PIB"
        PIB_PERCAPITA = "PIB_PERCAPITA", "PIB_PERCAPITA"

    class Unidad(models.TextChoices):
        PORCENTAJE = "PORCENTAJE", "PORCENTAJE"
        USD = "USD", "USD"
        USD_MILES_MILLONES = "USD_MILES_MILLONES", "USD_MILES_MILLONES"

    class Fuente(models.TextChoices):
        WORLD_BANK = "WORLD_BANK", "WORLD_BANK"
        MANUAL = "MANUAL", "MANUAL"

    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name="indicadores")
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    valor = models.FloatField()
    unidad = models.CharField(max_length=30, choices=Unidad.choices)
    anio = models.PositiveIntegerField()
    fuente = models.CharField(max_length=20, choices=Fuente.choices, default=Fuente.MANUAL)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-anio"]
        constraints = [
            models.UniqueConstraint(
                fields=["pais", "tipo", "anio"],
                name="uniq_indicador_pais_tipo_anio",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.pais.codigo_iso} {self.tipo} {self.anio}"


class TipoCambio(models.Model):
    # Guardamos tasa de moneda local contra USD por defecto
    moneda_origen = models.CharField(max_length=3)  # Ej: "COP"
    moneda_destino = models.CharField(max_length=3, default="USD")
    tasa = models.FloatField()
    fecha = models.DateField()

    variacion_porcentual = models.FloatField(null=True, blank=True)
    fuente = models.CharField(max_length=50, blank=True, default="MANUAL")

    class Meta:
        ordering = ["-fecha"]
        constraints = [
            models.UniqueConstraint(
                fields=["moneda_origen", "moneda_destino", "fecha"],
                name="uniq_fx_pair_fecha",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.moneda_origen}/{self.moneda_destino} {self.fecha}"
    
   

class Portafolio(models.Model):
    
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="portafolios",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.nombre


class Posicion(models.Model):
   
    class TipoActivo(models.TextChoices):
        ACCION = "ACCION", "ACCION"
        BONO = "BONO", "BONO"
        ETF = "ETF", "ETF"
        CRYPTO = "CRYPTO", "CRYPTO"
        OTRO = "OTRO", "OTRO"

    portafolio = models.ForeignKey(Portafolio, on_delete=models.CASCADE, related_name="posiciones")
    pais = models.ForeignKey("Pais", on_delete=models.PROTECT, related_name="posiciones")

    activo = models.CharField(max_length=120)        # nombre del activo
    ticker = models.CharField(max_length=20, blank=True)
    tipo_activo = models.CharField(max_length=20, choices=TipoActivo.choices, default=TipoActivo.ACCION)

    moneda = models.CharField(max_length=3, default="USD")
    cantidad = models.FloatField(default=0)
    precio_unitario = models.FloatField(default=0)

    # % dentro del portafolio (si lo manejas manual)
    peso_porcentual = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.portafolio.nombre} - {self.activo}"
    
    