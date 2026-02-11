
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
from .decorators import owner_or_superuser_required

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
        
    today = timezone.localtime().date()
    if tenant and hasattr(tenant, 'timezone') and tenant.timezone:
        import zoneinfo
        try:
            today = timezone.now().astimezone(zoneinfo.ZoneInfo(tenant.timezone)).date()
        except: pass
    
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
    last_30_days = timezone.localtime().date() - timedelta(days=30)
    
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

@owner_or_superuser_required
def tenant_settings(request):
    """Configuración general del negocio (solo para dueños)"""
    tenant = getattr(request, 'tenant', None) or request.user.organization
    
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
from apps.audit.models import AuditLog
from django.contrib.auth import get_user_model

User = get_user_model()

@owner_or_superuser_required
def owner_dashboard(request):
    """
    Panel de control avanzado para el dueño: Cuadre y Auditoría Visual.
    """
    tenant = getattr(request, 'tenant', None) or request.user.organization
    
    today = timezone.localtime().date()
    now_time = timezone.localtime().time()
    if tenant and hasattr(tenant, 'timezone') and tenant.timezone:
        import zoneinfo
        try:
            local_now = timezone.now().astimezone(zoneinfo.ZoneInfo(tenant.timezone))
            today = local_now.date()
            now_time = local_now.time()
        except: pass
    
    # 1. Ranking de Barberos (Hoy)
    # Contamos transacciones por usuario hoy
    barber_stats = User.objects.filter(
        organization=tenant,
        is_active=True
    ).filter(
        Q(is_owner=True) | Q(is_staff_member=True)
    ).annotate(
        total_stamps=Count('performed_audit_logs', filter=Q(performed_audit_logs__action='STAMP_ADD', performed_audit_logs__created_at__date=today)),
        total_points=Count('performed_audit_logs', filter=Q(performed_audit_logs__action='POINTS_ADD', performed_audit_logs__created_at__date=today)),
    ).order_by('-total_stamps')

    # 2. Semáforo de Alertas (Lógica de Auditoría)
    alerts = []
    
    # A. Alerta fuera de horario
    logs_off_hours = AuditLog.objects.filter(
        organization=tenant,
        created_at__date=today
    ).filter(
        Q(created_at__time__lt=tenant.opening_time) | 
        Q(created_at__time__gt=tenant.closing_time)
    ).select_related('user', 'customer')
    
    for log in logs_off_hours:
        alerts.append({
            'type': 'DANGER',
            'icon': 'fas fa-clock',
            'title': 'Actividad fuera de horario',
            'message': f"{log.user} registró {log.get_action_display()} a las {log.created_at.strftime('%H:%M')}",
            'log': log
        })
        
    # B. Alerta de registros rápidos (Sucesión sospechosa)
    # Buscamos si el mismo barbero puso 2+ sellos en menos de 10 min
    recent_logs = AuditLog.objects.filter(
        organization=tenant,
        created_at__date=today,
        action__in=['STAMP_ADD', 'POINTS_ADD']
    ).order_by('user', 'created_at')
    
    prev_log = None
    for log in recent_logs:
        if prev_log and prev_log.user == log.user:
            time_diff = (log.created_at - prev_log.created_at).total_seconds() / 60
            if time_diff < 10: # Menos de 10 minutos
                alerts.append({
                    'type': 'WARNING',
                    'icon': 'fas fa-bolt',
                    'title': 'Registros muy seguidos',
                    'message': f"{log.user} registró dos acciones en {int(time_diff)} min.",
                    'log': log
                })
        prev_log = log

    context = {
        'barber_stats': barber_stats,
        'alerts': alerts,
        'title': 'Panel de Control - Cuadre y Auditoría',
        'today': today,
        'tenant': tenant
    }
    return render(request, 'core/owner_dashboard.html', context)
