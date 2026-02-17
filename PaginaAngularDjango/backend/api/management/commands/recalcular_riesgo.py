from django.core.management.base import BaseCommand

from api.views import recalculate_all_risks


class Command(BaseCommand):
    help = 'Recalcula el indice de riesgo para todos los paises activos.'

    def handle(self, *args, **options):
        payload = recalculate_all_risks()
        self.stdout.write(self.style.SUCCESS(f'Indices recalculados: {payload[\"updated\"]}'))
        self.stdout.write(self.style.SUCCESS(f'Alertas warning: {payload[\"warnings\"]}'))
        self.stdout.write(self.style.SUCCESS(f'Alertas critical: {payload[\"critical\"]}'))
