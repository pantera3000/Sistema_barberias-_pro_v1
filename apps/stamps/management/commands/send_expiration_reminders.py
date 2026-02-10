from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from apps.stamps.models import StampCard
from apps.campaigns.models import NotificationConfig
from apps.campaigns.utils import send_whatsapp_message, format_message
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Envía recordatorios de WhatsApp para tarjetas que vencen en 7 días.'

    def handle(self, *args, **options):
        # 1. Obtener tarjetas NO completadas y NO redimidas que NO hayan sido notificadas de expiración
        # Pero primero necesitamos saber la vigencia por negocio.
        # Como es variable, iteramos por los negocios que tienen notificaciones activas.
        
        configs = NotificationConfig.objects.all()
        count = 0

        for config in configs:
            org = config.organization
            months = org.stamps_expiration_months
            
            if months <= 0:
                continue # Sin vencimiento
            
            # Fecha exacta en la que se cumplen (Meses - 7 días)
            target_date_start = timezone.now().date() + relativedelta(days=7)
            
            # Buscamos tarjetas creadas hace (Meses - 7 días)
            # created_at + months - 7 days == today
            # created_at == today - months + 7 days
            creation_target_date = timezone.now() - relativedelta(months=months) + relativedelta(days=7)
            
            # Buscamos tarjetas creadas en esa fecha (aproximadamente hoy)
            cards = StampCard.objects.filter(
                organization=org,
                is_completed=False,
                is_redeemed=False,
                expiring_notified=False,
                created_at__date=creation_target_date.date()
            )

            for card in cards:
                if card.customer.phone:
                    message = format_message(config.template_expiring, card.customer, promotion=card.promotion)
                    if send_whatsapp_message(config, card.customer.phone, message):
                        card.expiring_notified = True
                        card.save(update_fields=['expiring_notified'])
                        count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Se enviaron {count} recordatorios de expiración.'))
