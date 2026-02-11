from .models import StampPromotion

def stamp_assets(request):
    """
    Provee datos necesarios para el modal global de sellos (base.html).
    """
    if not request.user.is_authenticated or not hasattr(request, 'tenant'):
        return {}

    # Obtenemos las promociones activas para el tenant actual
    active_promotions = StampPromotion.objects.filter(
        organization=request.tenant,
        is_active=True
    ).only('id', 'name')

    return {
        'global_active_promotions': active_promotions
    }
