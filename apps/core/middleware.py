from .models import Domain, set_current_tenant
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib import messages

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

class FeatureRestrictionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated or request.user.is_superuser:
            return None

        # Mapa de rutas a llaves de feature
        feature_map = {
            '/app/loyalty/': 'points',
            '/app/stamps/': 'stamps',
            '/app/rewards/': 'rewards',
            '/app/reports/': 'reports',
            '/app/campaigns/': 'campaigns',
            '/app/services/': 'services',
            '/app/appointments/': 'appointments',
            '/app/audit/': 'audit',
        }

        path = request.path
        for prefix, feature_key in feature_map.items():
            if path.startswith(prefix):
                # Usar el método que creamos en el modelo User
                if not request.user.has_feature(feature_key):
                    messages.error(request, f"El módulo '{feature_key.capitalize()}' no está incluido en tu plan actual.")
                    return redirect('core:dashboard')

        return None
