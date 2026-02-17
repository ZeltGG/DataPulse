from rest_framework import serializers
from .models import (
    Project,
    ContactMessage,
    Pais,
    IndicadorEconomico,
    TipoCambio,
    Portafolio,
    Posicion,
)


# ----------------- Base -----------------
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


# ----------------- Portafolios -----------------
class PosicionSerializer(serializers.ModelSerializer):
    # Para que el frontend muestre fácil:
    pais_codigo = serializers.CharField(source="pais.codigo_iso", read_only=True)
    pais_nombre = serializers.CharField(source="pais.nombre", read_only=True)

    class Meta:
        model = Posicion
        fields = "__all__"


class PortafolioListSerializer(serializers.ModelSerializer):
    posiciones_count = serializers.IntegerField(source="posiciones.count", read_only=True)

    class Meta:
        model = Portafolio
        fields = ["id", "nombre", "descripcion", "created_at", "posiciones_count"]


class PortafolioDetailSerializer(serializers.ModelSerializer):
    posiciones = PosicionSerializer(many=True)

    class Meta:
        model = Portafolio
        fields = ["id", "nombre", "descripcion", "created_at", "posiciones"]

    def validate_posiciones(self, posiciones):
        # Validación: suma de pesos <= 100
        total = 0.0
        for p in posiciones:
            total += float(p.get("peso_porcentual", 0.0))
        if total > 100.0 + 1e-6:
            raise serializers.ValidationError(
                f"La suma de peso_porcentual no puede ser > 100 (actual: {total})."
            )
        return posiciones

    def create(self, validated_data):
        posiciones_data = validated_data.pop("posiciones", [])
        request = self.context.get("request")

        portafolio = Portafolio.objects.create(
            **validated_data,
            creado_por=getattr(request, "user", None) if request else None,
        )

        for pos in posiciones_data:
            Posicion.objects.create(portafolio=portafolio, **pos)

        return portafolio

    def update(self, instance, validated_data):
        # Update portafolio
        posiciones_data = validated_data.pop("posiciones", None)

        instance.nombre = validated_data.get("nombre", instance.nombre)
        instance.descripcion = validated_data.get("descripcion", instance.descripcion)
        instance.save()

        # Si envían posiciones, reemplazamos todas (simple y robusto)
        if posiciones_data is not None:
            instance.posiciones.all().delete()
            for pos in posiciones_data:
                Posicion.objects.create(portafolio=instance, **pos)

        return instance
    
class PosicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Posicion
        fields = "__all__"


class PortafolioSerializer(serializers.ModelSerializer):
    posiciones = PosicionSerializer(many=True, read_only=True)

    class Meta:
        model = Portafolio
        fields = "__all__"


class PortafolioCreateSerializer(serializers.ModelSerializer):
    """
    Permite crear portafolio + posiciones en un solo POST
    """
    posiciones = PosicionSerializer(many=True)

    class Meta:
        model = Portafolio
        fields = ["id", "nombre", "descripcion", "owner", "created_at", "posiciones"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        posiciones_data = validated_data.pop("posiciones", [])
        portafolio = Portafolio.objects.create(**validated_data)
        for p in posiciones_data:
            Posicion.objects.create(portafolio=portafolio, **p)
        return portafolio