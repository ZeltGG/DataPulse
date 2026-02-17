from django.contrib import admin
from .models import (
    Project,
    ContactMessage,
    Pais,
    IndicadorEconomico,
    TipoCambio,
    Portafolio,
    Posicion,
)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "tech_stack", "created_at")
    search_fields = ("title", "tech_stack")
    ordering = ("-created_at",)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email")
    ordering = ("-created_at",)

@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ("codigo_iso", "nombre", "moneda_codigo", "region", "activo")
    search_fields = ("codigo_iso", "nombre", "moneda_codigo")
    list_filter = ("region", "activo")

@admin.register(IndicadorEconomico)
class IndicadorEconomicoAdmin(admin.ModelAdmin):
    list_display = ("pais", "tipo", "anio", "valor", "unidad", "fuente")
    search_fields = ("pais__codigo_iso", "pais__nombre")
    list_filter = ("tipo", "fuente", "anio")
    ordering = ("-anio",)

@admin.register(TipoCambio)
class TipoCambioAdmin(admin.ModelAdmin):
    list_display = ("moneda_origen", "moneda_destino", "fecha", "tasa", "variacion_porcentual")
    search_fields = ("moneda_origen", "moneda_destino")
    list_filter = ("moneda_origen", "moneda_destino")
    ordering = ("-fecha",)

@admin.register(Portafolio)
class PortafolioAdmin(admin.ModelAdmin):
    list_display = ("id",)  # ajusta campos reales
    search_fields = ("id",)

@admin.register(Posicion)
class PosicionAdmin(admin.ModelAdmin):
    list_display = ("id",)  # ajusta campos reales
    search_fields = ("id",)