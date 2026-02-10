from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StampCard
from apps.campaigns.models import NotificationConfig
from apps.campaigns.utils import send_whatsapp_message, format_message
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=StampCard)
def handle_stamp_card_notifications(sender, instance, created, **kwargs):
    """
    Escucha cambios en las tarjetas de sellos para enviar notificaciones automáticas.
    """
    # Solo actuar si el negocio tiene la configuración de notificaciones
    try:
        config = NotificationConfig.objects.get(organization=instance.organization)
    except NotificationConfig.DoesNotExist:
        return

    customer = instance.customer
    if not customer.phone:
        return

    # 1. CASO: Tarjeta Completada
    if instance.is_completed and not instance.is_redeemed and not instance.completed_notified:
        message = format_message(config.template_completed, customer, promotion=instance.promotion)
        if send_whatsapp_message(config, customer.phone, message):
            # Usamos update para evitar disparar el signal de nuevo recursivamente
            StampCard.objects.filter(pk=instance.pk).update(completed_notified=True)
            logger.info(f"Notificación de completion enviada a {customer.full_name}")

    # 2. CASO: Falta 1 sello
    elif not instance.is_completed:
        needed = instance.promotion.total_stamps_needed
        if instance.current_stamps == (needed - 1) and not instance.one_stamp_reminder_sent:
            message = format_message(config.template_one_left, customer, promotion=instance.promotion)
            if send_whatsapp_message(config, customer.phone, message):
                StampCard.objects.filter(pk=instance.pk).update(one_stamp_reminder_sent=True)
                logger.info(f"Notificación de 'falta 1' enviada a {customer.full_name}")
        
        # Resetear el flag si por algún motivo bajó de sellos (ej: deshacer) para que pueda volver a enviarse si sube
        elif instance.current_stamps < (needed - 1) and instance.one_stamp_reminder_sent:
            StampCard.objects.filter(pk=instance.pk).update(one_stamp_reminder_sent=False)
