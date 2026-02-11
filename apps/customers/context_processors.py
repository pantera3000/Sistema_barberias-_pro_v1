from django.utils import timezone
from .models import Customer

def birthday_celebrants(request):
    """
    Context processor to find customers celebrating their birthday today.
    """
    if not request.user.is_authenticated:
        return {}
        
    # Get organization (tenant)
    organization = getattr(request, 'tenant', None)
    if not organization and hasattr(request.user, 'organization'):
        organization = request.user.organization
        
    if not organization:
        return {}
        
    today = timezone.localtime().date()
    
    # Si por alguna razón localtime no está funcionando, forzamos la zona del tenant
    if organization and hasattr(organization, 'timezone') and organization.timezone:
        import zoneinfo
        try:
            tz = zoneinfo.ZoneInfo(organization.timezone)
            today = timezone.now().astimezone(tz).date()
        except Exception:
            pass
    
    # Filter customers of this organization whose birthday is today (month & day)
    celebrants = Customer.objects.filter(
        organization=organization,
        birth_month=today.month,
        birth_day=today.day
    )
    
    return {
        'birthday_celebrants': celebrants,
        'has_birthday_today': celebrants.exists()
    }
