
from django.db import models
from apps.core.models import TenantAwareModel
from apps.customers.models import Customer
from django.contrib.auth import get_user_model

User = get_user_model()

class MarketingCampaign(TenantAwareModel):
    """
    Campaña de marketing masiva.
    """
    CHANNEL_CHOICES = [
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
        ('SMS', 'SMS'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('SCHEDULED', 'Programada'),
        ('SENT', 'Enviada'),
        ('CANCELLED', 'Cancelada'),
    ]

    name = models.CharField(max_length=150, verbose_name="Nombre de la Campaña")
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='WHATSAPP', verbose_name="Canal de Envío")
    subject = models.CharField(max_length=200, blank=True, verbose_name="Asunto (Email)")
    content = models.TextField(verbose_name="Contenido del Mensaje")
    
    # Segmentación básica (Filtros guardados)
    # Por ahora simple: "Todos", "Cumpleañeros", "Inactivos"
    target_segment = models.CharField(max_length=50, default='ALL', verbose_name="Segmento Objetivo")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Estado")
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name="Programar para")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviada el")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Creada por")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Campaña de Marketing"
        verbose_name_plural = "Campañas de Marketing"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

class CampaignLog(TenantAwareModel):
    """
    Registro de envío individual a cada cliente.
    """
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, related_name='logs', verbose_name="Campaña")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='campaign_logs', verbose_name="Cliente")
    status = models.CharField(max_length=20, default='PENDING') # PENDING, SENT, FAILED, DELIVERED
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Log de Envío"
        verbose_name_plural = "Logs de Envíos"
