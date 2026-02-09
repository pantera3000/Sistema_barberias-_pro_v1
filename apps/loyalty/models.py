
from django.db import models
from apps.core.models import TenantAwareModel
from apps.customers.models import Customer
from django.contrib.auth import get_user_model

User = get_user_model()

class PointTransaction(TenantAwareModel):
    """
    Registro de todas las transacciones de puntos (ganancia o canje).
    """
    TRANSACTION_TYPES = [
        ('EARN', 'Ganancia'),
        ('REDEEM', 'Canje'),
        ('ADJUST', 'Ajuste Manual'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='point_transactions', verbose_name="Cliente")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='EARN', verbose_name="Tipo")
    points = models.IntegerField(verbose_name="Puntos")
    description = models.CharField(max_length=255, verbose_name="Descripción")
    
    # Auditoría
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Realizado por")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Transacción de Puntos"
        verbose_name_plural = "Transacciones de Puntos"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.points} pts ({self.customer})"
