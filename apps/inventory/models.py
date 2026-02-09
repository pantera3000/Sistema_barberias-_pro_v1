
from django.db import models
from apps.core.models import TenantAwareModel
from django.core.validators import MinValueValidator

class Supplier(TenantAwareModel):
    """Proveedores de productos"""
    name = models.CharField(max_length=200, verbose_name="Nombre")
    contact_name = models.CharField(max_length=200, blank=True, verbose_name="Contacto")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.name

class Product(TenantAwareModel):
    """Productos para venta o consumo interno"""
    PRODUCT_TYPE_CHOICES = [
        ('RETAIL', 'Venta al Cliente'),
        ('INTERNAL', 'Consumo Interno'),
    ]

    name = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    sku = models.CharField(max_length=50, blank=True, verbose_name="SKU/Código")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES, default='RETAIL')
    
    # Precios
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio de Costo")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio de Venta")
    
    # Inventario
    current_stock = models.IntegerField(default=0, verbose_name="Stock Actual")
    min_stock_alert = models.IntegerField(default=5, verbose_name="Stock Mínimo (Alerta)")
    
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Proveedor")
    
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.current_stock <= self.min_stock_alert

class StockMovement(TenantAwareModel):
    """Movimientos de inventario (Entradas/Salidas)"""
    MOVEMENT_TYPE_CHOICES = [
        ('IN', 'Entrada (Compra/Ajuste)'),
        ('OUT', 'Salida (Venta/Consumo/Pérdida)'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    reason = models.CharField(max_length=255, blank=True, verbose_name="Razón/Nota")
    
    performed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, verbose_name="Realizado por")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Actualizar stock del producto al guardar movimiento
        product = self.product
        if self.movement_type == 'IN':
            product.current_stock += self.quantity
        else:
            product.current_stock -= self.quantity
        product.save()
        super().save(*args, **kwargs)
