from django.contrib.auth.models import Group, User
from rest_framework import serializers

from .models import (
    Alerta,
    ContactMessage,
    IndicadorEconomico,
    IndiceRiesgo,
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


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    rol = serializers.ChoiceField(choices=['ADMIN', 'ANALISTA', 'VIEWER'])

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('El username ya existe.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('El email ya existe.')
        return value

    def create(self, validated_data):
        rol = validated_data.pop('rol')
        user = User.objects.create_user(**validated_data)
        group, _ = Group.objects.get_or_create(name=rol)
        user.groups.add(group)
        if rol == 'ADMIN':
            user.is_staff = True
            user.save(update_fields=['is_staff'])
        return user


class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')


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
            'monto_inversion_usd',
            'fecha_entrada',
            'fecha_salida',
            'notas',
            'created_at',
        )
        read_only_fields = ('id', 'created_at', 'portafolio')


class PortafolioListSerializer(serializers.ModelSerializer):
    posiciones_count = serializers.IntegerField(source='posiciones.count', read_only=True)

    class Meta:
        model = Portafolio
        fields = (
            'id',
            'nombre',
            'descripcion',
            'owner',
            'es_publico',
            'activo',
            'created_at',
            'updated_at',
            'posiciones_count',
        )


class PortafolioDetailSerializer(serializers.ModelSerializer):
    posiciones = PosicionSerializer(many=True, read_only=True)

    class Meta:
        model = Portafolio
        fields = (
            'id',
            'nombre',
            'descripcion',
            'owner',
            'es_publico',
            'activo',
            'created_at',
            'updated_at',
            'posiciones',
        )


class PortafolioWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portafolio
        fields = ('id', 'nombre', 'descripcion', 'es_publico', 'owner', 'activo', 'created_at', 'updated_at')
        read_only_fields = ('id', 'owner', 'activo', 'created_at', 'updated_at')


class IndiceRiesgoSerializer(serializers.ModelSerializer):
    pais_codigo = serializers.CharField(source='pais.codigo_iso', read_only=True)
    pais_nombre = serializers.CharField(source='pais.nombre', read_only=True)

    class Meta:
        model = IndiceRiesgo
        fields = '__all__'


class AlertaSerializer(serializers.ModelSerializer):
    pais_codigo = serializers.CharField(source='pais.codigo_iso', read_only=True)

    class Meta:
        model = Alerta
        fields = '__all__'
