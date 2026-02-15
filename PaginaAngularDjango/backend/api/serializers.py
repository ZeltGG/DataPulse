from rest_framework import serializers
from .models import Project, ContactMessage, Pais, IndicadorEconomico, TipoCambio


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