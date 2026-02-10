
from django.db import models
from apps.core.models import TenantAwareModel
from apps.customers.models import Customer
from django.contrib.auth import get_user_model

User = get_user_model()

class StampPromotion(TenantAwareModel):
    """
    Regla de la tarjeta de sellos (Ej: 10 cortes = 1 gratis).
    """
    name = models.CharField(max_length=150, verbose_name="Nombre de la Promoción")
    description = models.TextField(blank=True, verbose_name="Descripción")
    total_stamps_needed = models.PositiveIntegerField(default=10, verbose_name="Sellos necesarios")
    reward_description = models.CharField(max_length=200, verbose_name="Recompensa (Ej: Corte Gratis)")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    
    start_date = models.DateField(null=True, blank=True, verbose_name="Fecha Inicio")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fecha Fin")

    class Meta:
        verbose_name = "Promoción de Sellos"
        verbose_name_plural = "Promociones de Sellos"

    def __str__(self):
        return f"{self.name} ({self.total_stamps_needed} sellos)"

class StampCard(TenantAwareModel):
    """
    Tarjeta digital del cliente para una promoción específica.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='stamp_cards', verbose_name="Cliente")
    promotion = models.ForeignKey(StampPromotion, on_delete=models.PROTECT, related_name='cards', verbose_name="Promoción")
    current_stamps = models.PositiveIntegerField(default=0, verbose_name="Sellos actuales")
    is_completed = models.BooleanField(default=False, verbose_name="Completada")
    is_redeemed = models.BooleanField(default=False, verbose_name="Canjeada")
    
    last_stamp_at = models.DateTimeField(auto_now=True, verbose_name="Último sello")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Nuevos campos para el flujo A
    redemption_requested = models.BooleanField(default=False, verbose_name="Canje solicitado")
    requested_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de solicitud")

    class Meta:
        verbose_name = "Tarjeta de Sellos"
        verbose_name_plural = "Tarjetas de Sellos"
        # Quitamos unique_together para permitir acumulación de múltiples premios (tarjetas completadas no canjeadas)

    @property
    def is_expired(self):
        """Verifica si la tarjeta ha expirado según la configuración del tenant"""
        months = getattr(self.organization, 'stamps_expiration_months', 0)
        if months <= 0:
            return False
        
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        return timezone.now() > self.created_at + relativedelta(months=months)

    @property
    def expiration_date(self):
        """Retorna la fecha exacta de expiración"""
        months = getattr(self.organization, 'stamps_expiration_months', 0)
        if months <= 0:
            return None
        from dateutil.relativedelta import relativedelta
        return self.created_at + relativedelta(months=months)

    def __str__(self):
        return f"{self.customer} - {self.current_stamps}/{self.promotion.total_stamps_needed}"

class StampTransaction(TenantAwareModel):
    """
    Historial de movimientos de sellos.
    """
    ACTION_CHOICES = [
        ('ADD', 'Sello Agregado'),
        ('REDEEM', 'Recompensa Canjeada'),
        ('RESET', 'Reinicio / Manual'),
    ]
    
    card = models.ForeignKey(StampCard, on_delete=models.CASCADE, related_name='transactions', verbose_name="Tarjeta")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='ADD')
    quantity = models.IntegerField(default=1, verbose_name="Cantidad")
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Realizado por")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Transacción de Sello"
        verbose_name_plural = "Transacciones de Sellos"
