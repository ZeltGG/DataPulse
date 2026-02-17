from datetime import date

from django.core.management.base import BaseCommand

from api.models import IndiceRiesgo, Pais
from api.views import calculate_country_risk


class Command(BaseCommand):
    help = 'Recalcula el indice de riesgo para todos los paises activos.'

    def handle(self, *args, **options):
        total = 0
        for pais in Pais.objects.filter(activo=True):
            payload = calculate_country_risk(pais)
            IndiceRiesgo.objects.update_or_create(
                pais=pais,
                fecha_calculo=date.today(),
                defaults=payload,
            )
            total += 1
        self.stdout.write(self.style.SUCCESS(f'Indices recalculados: {total}'))
