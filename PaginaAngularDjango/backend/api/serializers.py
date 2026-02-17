from rest_framework import serializers
from .models import (
    Project, ContactMessage,
    Pais, IndicadorEconomico, TipoCambio,
    Portafolio, Posicion
)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = "__all__"


class IndicadorEconomicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicadorEconomico
        fields = "__all__"


class TipoCambioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCambio
        fields = "__all__"


class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = "__all__"


class PaisDetailSerializer(serializers.ModelSerializer):
    indicadores = IndicadorEconomicoSerializer(many=True, read_only=True)

    class Meta:
        model = Pais
        fields = "__all__"


class PosicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Posicion
        fields = "__all__"
        read_only_fields = ("portafolio", "created_at")


class PortafolioListSerializer(serializers.ModelSerializer):
    pais_nombre = serializers.CharField(source="pais.nombre", read_only=True)
    posiciones_count = serializers.IntegerField(source="posiciones.count", read_only=True)

    class Meta:
        model = Portafolio
        fields = ("id", "nombre", "descripcion", "pais", "pais_nombre", "activo", "created_at", "updated_at", "posiciones_count")


class PortafolioDetailSerializer(serializers.ModelSerializer):
    pais_detalle = PaisSerializer(source="pais", read_only=True)
    posiciones = PosicionSerializer(many=True, read_only=True)

    class Meta:
        model = Portafolio
        fields = "__all__"


class PortafolioCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portafolio
        fields = ("nombre", "descripcion", "pais", "activo")