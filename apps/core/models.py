
from django.db import models
from django.utils.text import slugify
from django.conf import settings
from threading import local

# Thread-local storage for current tenant
_thread_locals = local()

def get_current_tenant():
    """Retorna el tenant actual del thread-local storage"""
    return getattr(_thread_locals, 'tenant', None)

def set_current_tenant(tenant):
    """Establece el tenant actual en el thread-local storage"""
    _thread_locals.tenant = tenant

class Organization(models.Model):
    """
    Representa una barbería (Tenant).
    """
    name = models.CharField(max_length=255, verbose_name="Nombre del Negocio")
    slug = models.SlugField(max_length=255, unique=True, verbose_name="Slug URL")
    
    # Referencia a User usando string para evitar import circular
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='owned_organizations', 
        verbose_name="Dueño"
    )
    
    # Configuración básica
    logo = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo")
    primary_color = models.CharField(max_length=7, default='#3B82F6', verbose_name="Color Primario")
    timezone = models.CharField(max_length=50, default='America/Lima', verbose_name="Zona Horaria")
    currency = models.CharField(max_length=3, default='PEN', verbose_name="Moneda")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = "Organización"
        verbose_name_plural = "Organizaciones"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Domain(models.Model):
    """
    Dominios asociados a una organización (ej: mi-barberia.sistema.com)
    """
    domain = models.CharField(max_length=253, unique=True, verbose_name="Dominio")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='domains')
    is_primary = models.BooleanField(default=True, verbose_name="Es Principal")

    class Meta:
        verbose_name = "Dominio"
        verbose_name_plural = "Dominios"

    def __str__(self):
        return self.domain

class FeatureFlag(models.Model):
    """Control granular de funcionalidades por tenant"""
    
    FEATURE_CHOICES = [
        # Módulos principales
        ('customers', 'Gestión de Clientes'),
        ('services', 'Catálogo de Servicios'),
        ('points', 'Sistema de Puntos'),
        ('stamps', 'Sistema de Sellos (Punch Cards)'),
        ('rewards', 'Recompensas'),
        ('appointments', 'Sistema de Citas'),
        ('campaigns', 'Campañas de Marketing'),
        ('reports', 'Reportes Avanzados'),
        ('subscriptions', 'Suscripciones'),
        ('integrations', 'Integraciones (Pabbly/Webhooks)'),
        ('gamification', 'Gamificación'),
        ('audit', 'Auditoría y Logs'),
        
        # Funcionalidades específicas
        ('customers.import_csv', 'Importar Clientes CSV'),
        ('customers.export_data', 'Exportar Datos Clientes'),
        ('reports.export_pdf', 'Exportar Reportes PDF'),
        ('campaigns.whatsapp_manual', 'Campañas WhatsApp (Manual)'),
        ('campaigns.pabbly', 'Webhook Pabbly Connect'),
        ('appointments.online_booking', 'Reservas Online'),
        ('gamification.referrals', 'Programa de Referidos'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='feature_flags')
    feature_key = models.CharField(max_length=100, choices=FEATURE_CHOICES)
    is_enabled = models.BooleanField(default=False)
    
    # Metadata
    # enabled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL) # Opcional, puede causar ciclo si no usamos string
    enabled_at = models.DateTimeField(auto_now_add=True, null=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('organization', 'feature_key')
        verbose_name = "Feature Flag"
        verbose_name_plural = "Feature Flags"

    def __str__(self):
        return f"{self.organization.name} - {self.get_feature_key_display()}: {self.is_enabled}"

class UsageLimit(models.Model):
    """Límites configurables por tenant"""
    
    LIMIT_TYPES = [
        ('customers', 'Número de Clientes (Máximo)'),
        ('staff', 'Número de Trabajadores (Máximo)'),
        ('appointments_monthly', 'Citas por Mes'),
        ('campaigns_monthly', 'Campañas por Mes'),
        ('sms_monthly', 'SMS/WhatsApp por Mes'),
        ('storage_mb', 'Almacenamiento (MB)'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='usage_limits')
    limit_type = models.CharField(max_length=50, choices=LIMIT_TYPES)
    limit_value = models.IntegerField(help_text="Usar -1 para ilimitado")  # Valor configurable
    current_usage = models.IntegerField(default=0)
    
    # Control
    enforce_limit = models.BooleanField(default=True, verbose_name="Forzar Límite")
    warning_threshold = models.IntegerField(default=80, help_text="Porcentaje para alerta (0-100)")
    
    class Meta:
        unique_together = ('organization', 'limit_type')
        verbose_name = "Límite de Uso"
        verbose_name_plural = "Límites de Uso"
    
    def __str__(self):
        return f"{self.organization.name} - {self.get_limit_type_display()}"

    @property
    def is_exceeded(self):
        if self.limit_value == -1:
            return False
        return self.current_usage >= self.limit_value
    
    @property
    def usage_percentage(self):
        if self.limit_value <= 0:
            return 0
        return (self.current_usage / self.limit_value) * 100

class TenantAwareModel(models.Model):
    """
    Clase abstracta para modelos que pertenecen a un tenant específico.
    Automáticamente asigna el tenant al guardar y filtra por tenant al consultar.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Organización")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Si no tiene organización asignada, intentar asignar la del contexto actual
        if not self.organization_id:
            current_tenant = get_current_tenant()
            if current_tenant:
                self.organization = current_tenant
        super().save(*args, **kwargs)

class TenantManager(models.Manager):
    """
    Manager que filtra automáticamente por el tenant actual.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        current_tenant = get_current_tenant()
        if current_tenant:
            return queryset.filter(organization=current_tenant)
        return queryset
