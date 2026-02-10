import requests
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def send_whatsapp_message(config, phone, message):
    """
    Envía un mensaje usando la API local configurada (estilo UltraMsg).
    """
    if not config.whatsapp_api_url or not config.whatsapp_token:
        logger.warning(f"Configuración de WhatsApp incompleta para {config.organization.name}")
        return False

    # Limpiar el teléfono (debería ser internacional sin +)
    clean_phone = ''.join(filter(str.isdigit, str(phone)))
    
    payload = {
        'token': config.whatsapp_token,
        'to': clean_phone,
        'body': message
    }

    try:
        # UltraMsg usa POST a la URL con token en el body o param
        response = requests.post(config.whatsapp_api_url, data=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Error enviando WhatsApp a {clean_phone}: {str(e)}")
        return False

def send_email_notification(config, email, subject, message):
    """
    Envía un correo electrónico si la organización lo tiene habilitado.
    """
    if not config.email_enabled or not email:
        return False
        
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Error enviando Email a {email}: {str(e)}")
        return False

def format_message(template, customer, promotion=None, reward_name=None):
    """
    Reemplaza variables en la plantilla.
    """
    data = {
        '{nombre}': customer.full_name,
        '{negocio}': customer.organization.name,
        '{premio}': reward_name or (promotion.reward.name if promotion and promotion.reward else (promotion.reward_description if promotion else "Premio")),
    }
    
    formatted = template
    for key, val in data.items():
        if val:
            formatted = formatted.replace(key, str(val))
    
    return formatted
