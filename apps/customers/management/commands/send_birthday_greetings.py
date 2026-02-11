from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.customers.models import Customer
from apps.campaigns.models import NotificationConfig
from apps.campaigns.utils import send_whatsapp_message, send_email_notification, format_message
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Envía saludos de cumpleaños automáticos a los clientes.'

    def handle(self, *args, **options):
        today = timezone.localtime().date()
        
        # 1. Buscar clientes que celebran cumpleaños hoy
        # Filtramos por día y mes únicamente
        celebrants = Customer.objects.filter(
            birth_day=today.day,
            birth_month=today.month,
            is_active=True
        ).select_related('organization')
        
        counts = {'whatsapp': 0, 'email': 0, 'errors': 0}
        
        for customer in celebrants:
            # Intentar obtener config de notificaciones del negocio
            try:
                config = NotificationConfig.objects.get(organization=customer.organization)
            except NotificationConfig.DoesNotExist:
                continue

            # Saltar si no está habilitado
            if not config.birthday_enabled:
                continue
            
            message = format_message(config.birthday_template, customer)
            
            # --- Enviar por WhatsApp ---
            if customer.phone and config.whatsapp_api_url:
                if send_whatsapp_message(config, customer.phone, message):
                    counts['whatsapp'] += 1
                    logger.info(f"Cumpleaños WA enviado a {customer.full_name}")
                else:
                    counts['errors'] += 1

            # --- Enviar por Correo ---
            if customer.email and config.email_enabled:
                subject = f"¡Feliz Cumpleaños, {customer.first_name}! 🎂"
                if send_email_notification(config, customer.email, subject, message):
                    counts['email'] += 1
                    logger.info(f"Cumpleaños Email enviado a {customer.full_name}")
                else:
                    counts['errors'] += 1

        self.stdout.write(self.style.SUCCESS(
            f"Proceso de cumpleaños completado. WA: {counts['whatsapp']}, Email: {counts['email']}, Errores: {counts['errors']}"
        ))
