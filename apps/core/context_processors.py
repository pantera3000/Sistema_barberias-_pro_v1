from django.db import models
from django.utils import timezone
from apps.superadmin.models import SystemAnnouncement

def global_announcements(request):
    """
    Agrega comunicados activos al contexto de todas las páginas.
    """
    if not request.user.is_authenticated:
        return {}

    # Filtrar comunicados por rol y estado
    now = timezone.now()
    announcements = SystemAnnouncement.objects.filter(
        is_active=True
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
    )

    if request.user.is_superuser:
        # El superadmin ve todos
        pass
    else:
        if request.user.is_owner:
            announcements = announcements.filter(show_to_owners=True)
        elif request.user.is_staff_member:
            announcements = announcements.filter(show_to_staff=True)
        else:
            # Usuarios sin rol específico no ven comunicados (o ajustar según necesidad)
            announcements = announcements.none()

    return {
        'system_announcements': announcements
    }

def tenant_usage(request):
    """
    Agrega información del plan y uso de la organización al contexto global.
    Para el sidebar y dashboard dinámico.
    """
    if not request.user.is_authenticated or request.user.is_superuser:
        return {}
    
    org = request.user.organization
    if not org:
        return {}
    
    # Obtener el límite de clientes
    from apps.core.models import UsageLimit
    customer_limit = org.usage_limits.filter(limit_type='customers').first()
    
    # Solo mostrar el límite de clientes si el módulo CRM, Puntos o Sellos está activo
    if customer_limit:
        if not (request.user.has_feature_customers or 
                request.user.has_feature_points or 
                request.user.has_feature_stamps):
            customer_limit = None

    return {
        'tenant_org': org,
        'customer_limit': customer_limit,
    }
