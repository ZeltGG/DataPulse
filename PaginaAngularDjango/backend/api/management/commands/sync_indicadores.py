from datetime import datetime

from django.core.management.base import BaseCommand

from api.models import IndicadorEconomico, Pais


class Command(BaseCommand):
    help = 'Sincroniza (mock) indicadores economicos para paises activos.'

    def handle(self, *args, **options):
        year = datetime.utcnow().year
        total = 0
        for pais in Pais.objects.filter(activo=True):
            payloads = [
                ('PIB', 100 + pais.id * 3, 'USD_MILES_MILLONES'),
                ('INFLACION', 2 + (pais.id % 7), 'PORCENTAJE'),
                ('DESEMPLEO', 4 + (pais.id % 6), 'PORCENTAJE'),
                ('DEUDA_PIB', 25 + (pais.id % 10) * 3, 'PORCENTAJE'),
            ]
            for tipo, valor, unidad in payloads:
                IndicadorEconomico.objects.update_or_create(
                    pais=pais,
                    tipo=tipo,
                    anio=year,
                    defaults={'valor': valor, 'unidad': unidad, 'fuente': 'MANUAL'},
                )
                total += 1
        self.stdout.write(self.style.SUCCESS(f'Indicadores sincronizados: {total}'))
