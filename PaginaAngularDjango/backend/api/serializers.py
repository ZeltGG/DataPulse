from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q, Sum
from rest_framework import serializers

from .models import (
    Alerta,
    IndicadorEconomico,
    IndiceRiesgo,
    Pais,
    Portafolio,
    Posicion,
    TipoCambio,
)

User = get_user_model()


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
    monto_inversion_usd = serializers.FloatField(required=False)

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

    def validate_fecha_entrada(self, value):
        if value and value > date.today():
            raise serializers.ValidationError('La fecha de entrada no puede ser futura.')
        return value

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        portafolio = self.context.get('portafolio')
        pais = attrs.get('pais') or (instance.pais if instance else None)
        tipo_activo = attrs.get('tipo_activo') or (instance.tipo_activo if instance else None)
        moneda = attrs.get('moneda') or (instance.moneda if instance else 'USD')
        cantidad = attrs.get('cantidad')
        precio_unitario = attrs.get('precio_unitario')
        monto = attrs.get('monto_inversion_usd')
        fecha_salida = attrs.get('fecha_salida')
        fecha_entrada = attrs.get('fecha_entrada') or (instance.fecha_entrada if instance else None)

        if cantidad is None and instance:
            cantidad = instance.cantidad
        if precio_unitario is None and instance:
            precio_unitario = instance.precio_unitario

        if monto is None and cantidad is not None and precio_unitario is not None:
            monto = cantidad * precio_unitario
            attrs['monto_inversion_usd'] = monto

        if monto is not None and (monto < 1000 or monto > 10000000):
            raise serializers.ValidationError('El monto de inversion debe estar entre 1,000 y 10,000,000 USD.')

        if tipo_activo == Posicion.TipoActivo.MONEDA and pais and pais.moneda_codigo == 'USD':
            raise serializers.ValidationError('No se puede agregar posicion MONEDA para un pais cuya moneda es USD.')

        if fecha_salida and fecha_entrada and fecha_salida <= fecha_entrada:
            raise serializers.ValidationError('La fecha de salida debe ser mayor a la fecha de entrada.')

        if portafolio and monto is not None:
            qs = portafolio.posiciones.filter(fecha_salida__isnull=True)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            total_actual = qs.aggregate(total=Sum('monto_inversion_usd'))['total'] or 0
            if total_actual + monto > 50000000:
                raise serializers.ValidationError('El monto total del portafolio no puede superar 50,000,000 USD.')

        if portafolio and pais and tipo_activo:
            qs_tipo = portafolio.posiciones.filter(
                pais=pais,
                tipo_activo=tipo_activo,
                fecha_salida__isnull=True,
            )
            if instance:
                qs_tipo = qs_tipo.exclude(pk=instance.pk)
            if qs_tipo.count() >= 2:
                raise serializers.ValidationError('No se permiten mas de 2 posiciones activas del mismo tipo en el mismo pais.')

        if moneda and len(moneda) != 3:
            raise serializers.ValidationError('La moneda debe tener codigo ISO de 3 caracteres.')

        return attrs


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

    def validate_nombre(self, value):
        owner = self.context['request'].user
        instance = getattr(self, 'instance', None)
        qs = Portafolio.objects.filter(owner=owner, nombre__iexact=value.strip())
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe un portafolio con ese nombre para este usuario.')
        return value.strip()

    def validate_descripcion(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError('La descripcion no puede superar 500 caracteres.')
        return value


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


class DashboardMapaSerializer(serializers.Serializer):
    codigo_iso = serializers.CharField()
    nombre = serializers.CharField()
    latitud = serializers.FloatField()
    longitud = serializers.FloatField()
    indice_compuesto = serializers.FloatField()
    nivel_riesgo = serializers.CharField()
    color = serializers.CharField()


class DashboardTendenciaSerieSerializer(serializers.Serializer):
    pais_codigo = serializers.CharField()
    pais_nombre = serializers.CharField()
    valores = serializers.ListField(child=serializers.FloatField(allow_null=True))
