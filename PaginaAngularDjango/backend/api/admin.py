from django.contrib import admin

from .models import Alerta, IndicadorEconomico, IndiceRiesgo, LogActividad, Pais, Portafolio, Posicion, TipoCambio


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ('codigo_iso', 'nombre', 'moneda_codigo', 'region', 'activo')
    search_fields = ('codigo_iso', 'nombre', 'moneda_codigo')
    list_filter = ('region', 'activo')


@admin.register(IndicadorEconomico)
class IndicadorEconomicoAdmin(admin.ModelAdmin):
    list_display = ('pais', 'tipo', 'anio', 'valor', 'unidad', 'fuente')
    search_fields = ('pais__codigo_iso', 'pais__nombre')
    list_filter = ('tipo', 'fuente', 'anio')
    ordering = ('-anio',)


@admin.register(TipoCambio)
class TipoCambioAdmin(admin.ModelAdmin):
    list_display = ('moneda_origen', 'moneda_destino', 'fecha', 'tasa', 'variacion_porcentual')
    search_fields = ('moneda_origen', 'moneda_destino')
    list_filter = ('moneda_origen', 'moneda_destino')
    ordering = ('-fecha',)


@admin.register(Portafolio)
class PortafolioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'owner', 'activo', 'es_publico', 'created_at')
    search_fields = ('nombre', 'owner__username')
    list_filter = ('activo', 'es_publico')


@admin.register(Posicion)
class PosicionAdmin(admin.ModelAdmin):
    list_display = ('id', 'portafolio', 'pais', 'tipo_activo', 'monto_inversion_usd', 'fecha_entrada', 'fecha_salida')
    search_fields = ('portafolio__nombre', 'pais__nombre', 'activo', 'ticker')
    list_filter = ('tipo_activo',)


@admin.register(IndiceRiesgo)
class IndiceRiesgoAdmin(admin.ModelAdmin):
    list_display = ('pais', 'fecha_calculo', 'indice_compuesto', 'nivel_riesgo')
    list_filter = ('nivel_riesgo',)
    ordering = ('-fecha_calculo',)


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo_alerta', 'severidad', 'leida', 'fecha_creacion')
    list_filter = ('tipo_alerta', 'severidad', 'leida')


@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = ('accion', 'entidad_afectada', 'entidad_id', 'usuario', 'fecha')
    list_filter = ('accion',)
    ordering = ('-fecha',)
