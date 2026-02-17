from django.core.management.base import BaseCommand

from api.views import sync_exchange_rates


class Command(BaseCommand):
    help = 'Actualiza tipos de cambio diarios y genera alertas por variacion > 3%.'

    def handle(self, *args, **options):
        payload = sync_exchange_rates()
        self.stdout.write(self.style.SUCCESS(f'Tipos de cambio actualizados: {payload["updated"]}'))
        self.stdout.write(self.style.SUCCESS(f'Alertas generadas: {payload["alerts"]}'))
        if payload['errors']:
            self.stdout.write(self.style.WARNING(f'Errores: {len(payload["errors"])}'))
