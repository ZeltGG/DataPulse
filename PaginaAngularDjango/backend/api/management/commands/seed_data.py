from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import IndicadorEconomico, Pais, Portafolio, Posicion, TipoCambio
from api.views import recalculate_all_risks


PAISES_SEED = [
    ('CO', 'Colombia', 'COP', 'Peso colombiano', 'ANDINA', 4.5709, -74.2973, 52321000),
    ('BR', 'Brasil', 'BRL', 'Real brasileño', 'CONO_SUR', -14.2350, -51.9253, 203062512),
    ('MX', 'Mexico', 'MXN', 'Peso mexicano', 'CENTROAMERICA', 23.6345, -102.5528, 130118356),
    ('AR', 'Argentina', 'ARS', 'Peso argentino', 'CONO_SUR', -38.4161, -63.6167, 46234830),
    ('CL', 'Chile', 'CLP', 'Peso chileno', 'CONO_SUR', -35.6751, -71.5430, 19116201),
    ('PE', 'Peru', 'PEN', 'Sol peruano', 'ANDINA', -9.1900, -75.0152, 34049588),
    ('EC', 'Ecuador', 'USD', 'Dolar estadounidense', 'ANDINA', -1.8312, -78.1834, 18255188),
    ('UY', 'Uruguay', 'UYU', 'Peso uruguayo', 'CONO_SUR', -32.5228, -55.7658, 3426260),
    ('PY', 'Paraguay', 'PYG', 'Guarani paraguayo', 'CONO_SUR', -23.4428, -58.4438, 6861524),
    ('PA', 'Panama', 'PAB', 'Balboa', 'CENTROAMERICA', 8.5380, -80.7821, 4468087),
]


class Command(BaseCommand):
    help = 'Carga seed minimo: paises, usuarios de prueba, indicadores/FX, portafolios de ejemplo.'

    def handle(self, *args, **options):
        for row in PAISES_SEED:
            Pais.objects.update_or_create(
                codigo_iso=row[0],
                defaults={
                    'nombre': row[1],
                    'moneda_codigo': row[2],
                    'moneda_nombre': row[3],
                    'region': row[4],
                    'latitud': row[5],
                    'longitud': row[6],
                    'poblacion': row[7],
                    'activo': True,
                },
            )

        years = [timezone.now().year - 2, timezone.now().year - 1, timezone.now().year]
        for pais in Pais.objects.filter(activo=True):
            for y in years:
                IndicadorEconomico.objects.update_or_create(
                    pais=pais,
                    tipo='PIB',
                    anio=y,
                    defaults={'valor': 50000000000 + (pais.id * 1000000) + (y * 1000), 'unidad': 'USD', 'fuente': 'MANUAL'},
                )
                IndicadorEconomico.objects.update_or_create(
                    pais=pais,
                    tipo='PIB_PERCAPITA',
                    anio=y,
                    defaults={'valor': 2500 + (pais.id * 350), 'unidad': 'USD', 'fuente': 'MANUAL'},
                )
                IndicadorEconomico.objects.update_or_create(
                    pais=pais,
                    tipo='INFLACION',
                    anio=y,
                    defaults={'valor': 3 + (pais.id % 12), 'unidad': 'PORCENTAJE', 'fuente': 'MANUAL'},
                )
                IndicadorEconomico.objects.update_or_create(
                    pais=pais,
                    tipo='DESEMPLEO',
                    anio=y,
                    defaults={'valor': 4 + (pais.id % 10), 'unidad': 'PORCENTAJE', 'fuente': 'MANUAL'},
                )
                IndicadorEconomico.objects.update_or_create(
                    pais=pais,
                    tipo='BALANZA_COMERCIAL',
                    anio=y,
                    defaults={'valor': -2 + (pais.id % 5), 'unidad': 'PORCENTAJE', 'fuente': 'MANUAL'},
                )
                IndicadorEconomico.objects.update_or_create(
                    pais=pais,
                    tipo='DEUDA_PIB',
                    anio=y,
                    defaults={'valor': 30 + (pais.id % 25), 'unidad': 'PORCENTAJE', 'fuente': 'MANUAL'},
                )

        for pais in Pais.objects.filter(activo=True):
            for d in range(30):
                fx_date = timezone.now().date() - timedelta(days=d)
                base_rate = 1.0 if pais.moneda_codigo == 'USD' else max(0.0001, 1 / (10 + pais.id + d * 0.05))
                TipoCambio.objects.update_or_create(
                    moneda_origen=pais.moneda_codigo,
                    moneda_destino='USD',
                    fecha=fx_date,
                    defaults={
                        'tasa': base_rate,
                        'variacion_porcentual': 0.0 if d == 0 else ((d % 7) - 3) * 0.35,
                        'fuente': 'SEED',
                    },
                )

        for name in ['ADMIN', 'ANALISTA', 'VIEWER']:
            Group.objects.get_or_create(name=name)

        users = [
            ('admin@datapulse.com', 'admin@datapulse.com', 'DataPulse2026!', 'ADMIN'),
            ('analista@datapulse.com', 'analista@datapulse.com', 'DataPulse2026!', 'ANALISTA'),
            ('viewer@datapulse.com', 'viewer@datapulse.com', 'DataPulse2026!', 'VIEWER'),
        ]
        for username, email, password, role in users:
            user, _ = User.objects.get_or_create(username=username, defaults={'email': email, 'is_staff': role == 'ADMIN'})
            user.email = email
            if role == 'ADMIN':
                user.is_staff = True
            user.set_password(password)
            user.save()
            grp = Group.objects.get(name=role)
            user.groups.add(grp)

        analista = User.objects.get(username='analista@datapulse.com')
        viewer = User.objects.get(username='viewer@datapulse.com')
        p1, _ = Portafolio.objects.get_or_create(owner=analista, nombre='Portafolio Growth', defaults={'descripcion': 'Ejemplo crecimiento', 'es_publico': True, 'activo': True})
        p2, _ = Portafolio.objects.get_or_create(owner=viewer, nombre='Portafolio Conservador', defaults={'descripcion': 'Ejemplo conservador', 'es_publico': False, 'activo': True})
        co = Pais.objects.get(codigo_iso='CO')
        br = Pais.objects.get(codigo_iso='BR')
        Posicion.objects.get_or_create(portafolio=p1, pais=co, activo='ETF COLCAP', ticker='ICOLCAP', defaults={'tipo_activo': 'RENTA_VARIABLE', 'moneda': 'COP', 'cantidad': 100, 'precio_unitario': 30, 'monto_inversion_usd': 3000})
        Posicion.objects.get_or_create(portafolio=p1, pais=br, activo='Bono BR', ticker='BRBOND', defaults={'tipo_activo': 'RENTA_FIJA', 'moneda': 'BRL', 'cantidad': 50, 'precio_unitario': 80, 'monto_inversion_usd': 4000})
        Posicion.objects.get_or_create(portafolio=p2, pais=co, activo='Caja USD', ticker='USD', defaults={'tipo_activo': 'MONEDA', 'moneda': 'USD', 'cantidad': 1, 'precio_unitario': 10000, 'monto_inversion_usd': 10000})

        risk_payload = recalculate_all_risks()
        self.stdout.write(self.style.SUCCESS('Seed completado'))
        self.stdout.write(self.style.SUCCESS(f'Paises: {Pais.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Indicadores: {IndicadorEconomico.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'TipoCambio: {TipoCambio.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Indices riesgo recalculados: {risk_payload["updated"]}'))
