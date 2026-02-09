
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from apps.customers.models import Customer
from apps.loyalty.models import PointTransaction
from apps.stamps.models import StampCard

@login_required
def dashboard_dispatch(request):
    """
    Redirige al usuario a su dashboard correspondiente según su rol.
    """
    user = request.user
    
    if user.is_superuser:
        return redirect('superadmin:dashboard')
    
    if user.is_owner or user.is_staff_member:
        return redirect('core:dashboard')
        
    if user.is_customer:
        # TODO: Redirigir al perfil del cliente
        return render(request, 'core/customer_dashboard_placeholder.html')
        
    return redirect('users:login')

@login_required
def tenant_dashboard(request):
    """
    Dashboard principal del negocio (Tenant) con estadísticas.
    """
    # Validar que el usuario tenga organización (o tenant detectado por middleware)
    tenant = getattr(request, 'tenant', None) or request.user.organization
    
    if not tenant:
        return render(request, 'core/no_organization.html')
        
    today = timezone.now().date()
    
    # --- Estadísticas Clave ---
    
    # 1. Clientes
    total_customers = Customer.objects.filter(organization=tenant).count()
    new_customers_today = Customer.objects.filter(organization=tenant, created_at__date=today).count()
    
    # 2. Puntos Emitidos Hoy
    points_today = PointTransaction.objects.filter(
        organization=tenant, 
        created_at__date=today, 
        transaction_type='EARN'
    ).aggregate(total=Sum('points'))['total'] or 0
    
    # 3. Tarjetas de Sellos Activas
    active_stamp_cards = StampCard.objects.filter(
        organization=tenant, 
        is_redeemed=False,
        is_completed=False
    ).count()
    
    # 4. Actividad Reciente (Últimas 5 transacciones de puntos)
    recent_activity = PointTransaction.objects.filter(organization=tenant).select_related('customer', 'performed_by').order_by('-created_at')[:5]

    context = {
        'total_customers': total_customers,
        'new_customers_today': new_customers_today,
        'points_today': points_today,
        'active_stamp_cards': active_stamp_cards,
        'recent_activity': recent_activity,
        'title': f"Dashboard - {tenant.name}"
    }
    return render(request, 'core/dashboard.html', context)
