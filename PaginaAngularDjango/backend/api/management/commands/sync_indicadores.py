from django.core.management.base import BaseCommand

from api.models import Pais
from api.views import recalculate_all_risks, sync_exchange_rates, sync_world_bank_indicators


class Command(BaseCommand):
    help = 'Sincroniza indicadores economicos reales + tipo de cambio y recalcula IRPC.'

    def handle(self, *args, **options):
        iso_codes = list(Pais.objects.filter(activo=True).values_list('codigo_iso', flat=True))
        wb = sync_world_bank_indicators(iso_codes)
        fx = sync_exchange_rates()
        risk = recalculate_all_risks()
        self.stdout.write(self.style.SUCCESS(f'WorldBank created={wb[\"created\"]} updated={wb[\"updated\"]}'))
        self.stdout.write(self.style.SUCCESS(f'FX updated={fx[\"updated\"]} alerts={fx[\"alerts\"]}'))
        self.stdout.write(self.style.SUCCESS(f'Riesgo updated={risk[\"updated\"]}'))
        if wb['errors'] or fx['errors']:
            self.stdout.write(self.style.WARNING(f'Errores WB={len(wb[\"errors\"])} FX={len(fx[\"errors\"])}'))
