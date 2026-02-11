
from django.db import models
from apps.core.models import TenantAwareModel

class Tag(TenantAwareModel):
    """
    Etiquetas personalizadas para clasificar clientes (Ej: VIP, Barba, Difícil).
    """
    name = models.CharField(max_length=50, verbose_name="Nombre de la Etiqueta")
    color = models.CharField(max_length=20, default="#6c757d", verbose_name="Color (Hex)")

    class Meta:
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"
        unique_together = ('organization', 'name')

    def __str__(self):
        return self.name

class Customer(TenantAwareModel):
    """
    Cliente de una barbería específica.
    """
    first_name = models.CharField(max_length=150, verbose_name="Nombres")
    last_name = models.CharField(max_length=150, verbose_name="Apellidos")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono / WhatsApp")
    dni = models.CharField(max_length=20, blank=True, null=True, verbose_name="DNI/ID", db_index=True)
    birth_day = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Día de Nacimiento")
    birth_month = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Mes de Nacimiento")
    birth_year = models.PositiveIntegerField(blank=True, null=True, verbose_name="Año de Nacimiento")
    
    # Datos internos
    notes = models.TextField(blank=True, verbose_name="Notas Internas")
    tags = models.ManyToManyField(Tag, blank=True, related_name='customers', verbose_name="Etiquetas")
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

    @property
    def birthday_display(self):
        if not self.birth_day or not self.birth_month:
            return "-"
        
        meses = [
            'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
        ]
        mes_nombre = meses[self.birth_month - 1]
        
        display = f"{self.birth_day} {mes_nombre}"
        if self.birth_year:
            display += f" {self.birth_year}"
        return display
