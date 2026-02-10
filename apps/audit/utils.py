from .models import AuditLog

def log_action(request, action, resource, description, customer=None):
    """
    Registra una acción en el log de auditoría.
    """
    if not hasattr(request, 'tenant') or not request.tenant:
        return

    # Obtener IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        organization=request.tenant,
        user=request.user if request.user.is_authenticated else None,
        customer=customer,
        action=action,
        resource=resource,
        description=description,
        ip_address=ip
    )
