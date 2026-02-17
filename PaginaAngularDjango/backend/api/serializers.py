from rest_framework import serializers

from .models import (
    ContactMessage,
    IndicadorEconomico,
    Pais,
    Portafolio,
    Posicion,
    Project,
    TipoCambio,
)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'


class IndicadorEconomicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicadorEconomico
        fields = '__all__'


class TipoCambioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCambio
        fields = '__all__'


class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = '__all__'


class PaisDetailSerializer(serializers.ModelSerializer):
    indicadores = IndicadorEconomicoSerializer(many=True, read_only=True)

    class Meta:
        model = Pais
        fields = '__all__'


class PosicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Posicion
        fields = (
            'id',
            'portafolio',
            'pais',
            'activo',
            'ticker',
            'tipo_activo',
            'moneda',
            'cantidad',
            'precio_unitario',
            'peso_porcentual',
            'created_at',
        )
        read_only_fields = ('id', 'created_at', 'portafolio')


class PortafolioListSerializer(serializers.ModelSerializer):
    posiciones_count = serializers.IntegerField(source='posiciones.count', read_only=True)

    class Meta:
        model = Portafolio
        fields = ('id', 'nombre', 'descripcion', 'owner', 'created_at', 'posiciones_count')


class PortafolioDetailSerializer(serializers.ModelSerializer):
    posiciones = PosicionSerializer(many=True, read_only=True)

    class Meta:
        model = Portafolio
        fields = ('id', 'nombre', 'descripcion', 'owner', 'created_at', 'posiciones')


class PortafolioWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portafolio
        fields = ('id', 'nombre', 'descripcion', 'owner', 'created_at')
        read_only_fields = ('id', 'owner', 'created_at')
