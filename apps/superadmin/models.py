from django.db import models
from django.conf import settings

class SystemAnnouncement(models.Model):
    """
    Comunicados globales enviados por el Superadmin a todos los usuarios.
    """
    STYLE_CHOICES = [
        ('primary', 'Información (Azul)'),
        ('warning', 'Aviso (Naranja)'),
        ('danger', 'Crítico (Rojo)'),
        ('success', 'Novedad (Verde)'),
        ('dark', 'Mantenimiento (Negro)'),
    ]

    title = models.CharField(max_length=200, verbose_name="Título")
    content = models.TextField(verbose_name="Contenido del Mensaje")
    style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='primary', verbose_name="Estilo")
    
    is_active = models.BooleanField(default=True, verbose_name="¿Publicado?")
    show_to_owners = models.BooleanField(default=True, verbose_name="Mostrar a Dueños")
    show_to_staff = models.BooleanField(default=True, verbose_name="Mostrar a Trabajadores")
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Expira el", help_text="Dejar vacío para permanente")

    class Meta:
        verbose_name = "Comunicado Global"
        verbose_name_plural = "Comunicados Globales"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Plan(models.Model):
    """
    Define los planes de suscripción disponibles.
    """
    name = models.CharField(max_length=100, verbose_name="Nombre del Plan")
    description = models.TextField(blank=True, verbose_name="Descripción")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Precio Mensual")
    
    # Límites
    max_customers = models.IntegerField(default=100, verbose_name="Máximo Clientes")
    max_staff = models.IntegerField(default=5, verbose_name="Máximo Staff")
    max_appointments_monthly = models.IntegerField(default=-1, verbose_name="Citas/Mes (-1 = ilimitado)")
    max_campaigns_monthly = models.IntegerField(default=2, verbose_name="Campañas/Mes")
    
    # Funcionalidades Incluidas (Módulos)
    enable_customers = models.BooleanField(default=True, verbose_name="Gestión de Clientes")
    enable_services = models.BooleanField(default=True, verbose_name="Catálogo de Servicios")
    enable_points = models.BooleanField(default=True, verbose_name="Sistema de Puntos")
    enable_stamps = models.BooleanField(default=True, verbose_name="Punch Cards (Sellos)")
    enable_rewards = models.BooleanField(default=True, verbose_name="Recompensas")
    enable_appointments = models.BooleanField(default=False, verbose_name="Sistema de Citas")
    enable_whatsapp = models.BooleanField(default=False, verbose_name="Campañas de Marketing")
    enable_reports = models.BooleanField(default=False, verbose_name="Reportes Avanzados")
    enable_subscriptions = models.BooleanField(default=False, verbose_name="Suscripciones")
    enable_integrations = models.BooleanField(default=False, verbose_name="Integraciones (Pabbly/Webhooks)")
    enable_gamification = models.BooleanField(default=False, verbose_name="Gamificación")
    enable_audit = models.BooleanField(default=False, verbose_name="Auditoría y Logs")
    
    # Funcionalidades Específicas (Sub-módulos)
    enable_customers_import_csv = models.BooleanField(default=False, verbose_name="Importar Clientes CSV")
    enable_customers_export_data = models.BooleanField(default=False, verbose_name="Exportar Datos Clientes")
    enable_reports_export_pdf = models.BooleanField(default=False, verbose_name="Exportar Reportes PDF")
    enable_campaigns_whatsapp_manual = models.BooleanField(default=False, verbose_name="Campañas WhatsApp (Manual)")
    enable_campaigns_auto_notifications = models.BooleanField(default=False, verbose_name="Notificaciones Automáticas (Engagement)")
    enable_campaigns_pabbly = models.BooleanField(default=False, verbose_name="Webhook Pabbly Connect")
    enable_appointments_online_booking = models.BooleanField(default=False, verbose_name="Reservas Online")
    enable_gamification_referrals = models.BooleanField(default=False, verbose_name="Programa de Referidos")
    
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_default = models.BooleanField(default=False, verbose_name="Plan por Defecto", help_text="Si se marca, se asignará a nuevos negocios sin plan.")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            # Asegurar que solo un plan sea el por defecto
            Plan.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
        
        # Sincronizar automáticamente todos los negocios suscritos a este plan
        # para que los cambios en límites o funcionalidades se apliquen de inmediato.
        try:
            from apps.core.models import Organization
            for org in self.organizations.all():
                org.sync_with_plan()
        except:
            # Evitar que fallos en la sincronización bloqueen el guardado del plan
            # (Útil durante migraciones o instalaciones iniciales)
            pass

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Planes"
        ordering = ['price']

    def __str__(self):
        return f"{self.name} ({self.price} {settings.CURRENCY if hasattr(settings, 'CURRENCY') else 'PEN'})"
