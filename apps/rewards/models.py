
from django.db import models
from apps.core.models import TenantAwareModel
from apps.customers.models import Customer
from apps.loyalty.models import PointTransaction
from django.contrib.auth import get_user_model

User = get_user_model()

class Reward(TenantAwareModel):
    """
    Catálogo de premios disponibles para canje con puntos.
    """
    name = models.CharField(max_length=150, verbose_name="Nombre del Premio")
    description = models.TextField(blank=True, verbose_name="Descripción")
    points_cost = models.PositiveIntegerField(verbose_name="Costo en Puntos")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Opcional: Imagen del premio, stock limitado, vigencia
    valid_until = models.DateField(null=True, blank=True, verbose_name="Válido hasta")

    class Meta:
        verbose_name = "Recompensa"
        verbose_name_plural = "Recompensas"
        ordering = ['points_cost']

    def __str__(self):
        return f"{self.name} ({self.points_cost} pts)"

class Redemption(TenantAwareModel):
    """
    Registro de canje de un premio por un cliente.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='redemptions', verbose_name="Cliente")
    reward = models.ForeignKey(Reward, on_delete=models.PROTECT, verbose_name="Premio")
    points_spent = models.PositiveIntegerField(verbose_name="Puntos Gastados") # Guardamos el costo en el momento del canje
    
    # Enlace a la transacción de puntos (la que resta el saldo)
    point_transaction = models.OneToOneField(PointTransaction, on_delete=models.CASCADE, related_name='redemption_detail', verbose_name="Transacción de Puntos")
    
    redeemed_at = models.DateTimeField(auto_now_add=True, verbose_name="Canjeado el")
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Procesado por")

    class Meta:
        verbose_name = "Canje de Recompensa"
        verbose_name_plural = "Canjes de Recompensas"

    def __str__(self):
        return f"{self.customer} canjeó {self.reward}"
