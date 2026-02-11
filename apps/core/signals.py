
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.customers.models import Customer
from apps.users.models import User
from .models import UsageLimit

def update_usage_counter(organization, limit_type):
    """Actualiza el contador de uso para un tipo de límite específico"""
    if not organization:
        return
        
    limit = UsageLimit.objects.filter(organization=organization, limit_type=limit_type).first()
    if not limit:
        return

    if limit_type == 'customers':
        count = Customer.objects.filter(organization=organization).count()
    elif limit_type == 'staff':
        count = User.objects.filter(organization=organization, is_staff_member=True).count()
    else:
        return

    limit.current_usage = count
    limit.save()

# --- Señales para Clientes ---
@receiver(post_save, sender=Customer)
def customer_usage_update_on_save(sender, instance, created, **kwargs):
    if created:
        update_usage_counter(instance.organization, 'customers')

@receiver(post_delete, sender=Customer)
def customer_usage_update_on_delete(sender, instance, **kwargs):
    update_usage_counter(instance.organization, 'customers')

# --- Señales para Staff ---
@receiver(post_save, sender=User)
def staff_usage_update_on_save(sender, instance, created, **kwargs):
    if instance.is_staff_member:
        update_usage_counter(instance.organization, 'staff')

@receiver(post_delete, sender=User)
def staff_usage_update_on_delete(sender, instance, **kwargs):
    if instance.is_staff_member:
        update_usage_counter(instance.organization, 'staff')
