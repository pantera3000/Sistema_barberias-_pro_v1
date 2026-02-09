
from django.db import models
from apps.core.models import TenantAwareModel

class ServiceCategory(TenantAwareModel):
    """Categorías de servicios (ej: Cortes, Barba, Tintes)"""
    name = models.CharField(max_length=100, verbose_name="Nombre de la Categoría")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    class Meta:
        verbose_name = "Categoría de Servicio"
        verbose_name_plural = "Categorías de Servicios"

    def __str__(self):
        return self.name

class Service(TenantAwareModel):
    """
    Servicios ofrecidos por la barbería.
    """
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoría")
    name = models.CharField(max_length=150, verbose_name="Nombre del Servicio")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    # Precios y Tiempos
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    duration_minutes = models.PositiveIntegerField(default=30, verbose_name="Duración (minutos)")
    
    # Fidelización
    points_reward = models.PositiveIntegerField(default=0, verbose_name="Puntos a Otorgar", help_text="Puntos que gana el cliente al adquirir este servicio")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return f"{self.name} ({self.organization.currency} {self.price})"
