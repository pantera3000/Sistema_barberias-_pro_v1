from django.db import models
from apps.core.models import TenantAwareModel
from django.conf import settings

class AuditLog(TenantAwareModel):
    """
    Registro de actividad para auditoría interna del negocio.
    """
    ACTION_CHOICES = [
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
        ('LOGIN', 'Inicio de Sesión'),
        ('STAMP_ADD', 'Sello Agregado'),
        ('STAMP_REDEEM', 'Sello Canjeado'),
        ('POINTS_ADD', 'Puntos Agregados'),
        ('POINTS_REDEEM', 'Puntos Canjeados'),
        ('WA_SENT', 'WhatsApp Enviado'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='performed_audit_logs',
        verbose_name="Usuario"
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name="Cliente"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Acción")
    resource = models.CharField(max_length=100, verbose_name="Recurso (Ej: Cliente, Sello)")
    description = models.TextField(verbose_name="Descripción del cambio")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")

    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization.name} - {self.action} - {self.resource} ({self.created_at})"
