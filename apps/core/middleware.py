
from .models import Domain, set_current_tenant
from django.utils.deprecation import MiddlewareMixin

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host().split(':')[0].lower()
        domain_obj = Domain.objects.filter(domain=host).select_related('organization').first()
        
        tenant = None
        if domain_obj:
            tenant = domain_obj.organization
        
        # Fallback: Si no hay dominio, usar la organización del usuario autenticado (útil para dev local)
        if not tenant and request.user.is_authenticated and hasattr(request.user, 'organization'):
            tenant = request.user.organization

        request.tenant = tenant
        set_current_tenant(tenant)
