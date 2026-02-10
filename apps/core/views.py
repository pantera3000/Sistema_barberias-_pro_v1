
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from datetime import timedelta
from apps.customers.models import Customer
from apps.loyalty.models import PointTransaction
from apps.stamps.models import StampCard, StampTransaction, StampPromotion

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
        return redirect('stamps:my_stamps')
        
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

@login_required
def dashboard_stats_api(request):
    """API que devuelve datos para los gráficos del dashboard"""
    tenant = getattr(request, 'tenant', None) or request.user.organization
    last_30_days = timezone.now().date() - timedelta(days=30)
    
    # 1. Crecimiento de Clientes (Línea)
    customer_growth = Customer.objects.filter(
        organization=tenant,
        created_at__date__gte=last_30_days
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # 2. Actividad de Sellos (Barras)
    stamp_activity = StampTransaction.objects.filter(
        organization=tenant,
        created_at__date__gte=last_30_days
    ).annotate(
        date=TruncDate('created_at')
    ).values('date', 'action').annotate(
        count=Sum('quantity')
    ).order_by('date')
    
    # 3. Popularidad de Promociones (Pastel)
    promo_stats = StampPromotion.objects.filter(
        organization=tenant
    ).annotate(
        card_count=Count('cards')
    ).values('name', 'card_count').order_by('-card_count')[:5]
    
    return JsonResponse({
        'customer_growth': list(customer_growth),
        'stamp_activity': list(stamp_activity),
        'promo_stats': list(promo_stats)
    })
from django.contrib import messages
from .forms import OrganizationSettingsForm

@login_required
def tenant_settings(request):
    """Configuración general del negocio (solo para dueños)"""
    tenant = getattr(request, 'tenant', None) or request.user.organization
    
    if not request.user.is_owner and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a la configuración.")
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = OrganizationSettingsForm(request.POST, request.FILES, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración actualizada correctamente.")
            return redirect('core:tenant_settings')
    else:
        form = OrganizationSettingsForm(instance=tenant)

    return render(request, 'core/settings.html', {
        'form': form,
        'title': 'Configuración del Negocio',
        'tenant': tenant
    })
