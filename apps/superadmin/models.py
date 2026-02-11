from django.db import models

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
    
    # Funcionalidades Incluidas
    enable_whatsapp = models.BooleanField(default=False, verbose_name="WhatsApp Marketing")
    enable_reports = models.BooleanField(default=False, verbose_name="Reportes Avanzados")
    enable_audit = models.BooleanField(default=False, verbose_name="Auditoría y Logs")
    enable_stamps = models.BooleanField(default=True, verbose_name="Punch Cards (Sellos)")
    enable_points = models.BooleanField(default=True, verbose_name="Sistema de Puntos")
    enable_appointments = models.BooleanField(default=False, verbose_name="Sistema de Citas")
    
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Planes"
        ordering = ['price']

    def __str__(self):
        return f"{self.name} ({self.price} {settings.CURRENCY if hasattr(settings, 'CURRENCY') else 'PEN'})"
