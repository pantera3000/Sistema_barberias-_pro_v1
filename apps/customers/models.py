
from django.db import models
from apps.core.models import TenantAwareModel

class Customer(TenantAwareModel):
    """
    Cliente de una barbería específica.
    """
    first_name = models.CharField(max_length=150, verbose_name="Nombres")
    last_name = models.CharField(max_length=150, verbose_name="Apellidos")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono / WhatsApp")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Fecha de Nacimiento")
    
    # Datos internos
    notes = models.TextField(blank=True, verbose_name="Notas Internas")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
