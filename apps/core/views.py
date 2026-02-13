
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
    
    active_stamp_cards = StampCard.objects.filter(
        organization=tenant, 
        is_redeemed=False,
        is_completed=False
    ).count()

    # --- Worker Specific Stats (For My Activity) ---
    worker_stats = {}
    if not request.user.is_owner:
        worker_stats['my_points_today'] = PointTransaction.objects.filter(
            organization=tenant,
            created_at__date=today,
            performed_by=request.user,
            transaction_type='EARN'
        ).aggregate(total=Sum('points'))['total'] or 0

        worker_stats['my_stamps_today'] = StampTransaction.objects.filter(
            organization=tenant,
            created_at__date=today,
            performed_by=request.user,
            action='ADD'
        ).count()
        
        worker_stats['my_actions_today'] = worker_stats['my_stamps_today'] + (1 if worker_stats['my_points_today'] > 0 else 0) # Rough activity count
    
    # 4. Actividad Reciente (Unificada: Puntos y Sellos)
    point_recent = PointTransaction.objects.filter(organization=tenant).select_related('customer', 'performed_by').order_by('-created_at')[:5]
    stamp_recent = StampTransaction.objects.filter(organization=tenant).select_related('card__customer', 'performed_by').order_by('-created_at')[:5]
    
    recent_activity = []
    
    for pt in point_recent:
        recent_activity.append({
            'customer_name': pt.customer.full_name,
            'customer_initial': pt.customer.first_name[0] if pt.customer.first_name else 'C',
            'customer_id': pt.customer.id,
            'action_text': f"Ganó {pt.points} pts" if pt.transaction_type == 'EARN' else f"Canjeó {pt.points} pts",
            'details': pt.description or "Transacción de puntos",
            'is_earn': pt.transaction_type == 'EARN',
            'created_at': pt.created_at,
            'type': 'points',
            'staff_name': pt.performed_by.get_full_name() or pt.performed_by.username,
            'staff_initial': pt.performed_by.first_name[0] if pt.performed_by.first_name else pt.performed_by.username[0],
            'staff_role': pt.performed_by.role_display
        })
        
    for st in stamp_recent:
        action_desc = "Sello +" if st.action == 'ADD' else "Canje -"
        details_text = st.card.promotion.name if st.card.promotion else "Tarjeta de Sellos"
        
        recent_activity.append({
            'customer_name': st.card.customer.full_name,
            'customer_initial': st.card.customer.first_name[0] if st.card.customer.first_name else 'C',
            'customer_id': st.card.customer.id,
            'action_text': f"{action_desc} ({st.quantity})",
            'details': details_text,
            'is_earn': st.action == 'ADD',
            'created_at': st.created_at,
            'type': 'stamps',
            'staff_name': st.performed_by.get_full_name() or st.performed_by.username,
            'staff_initial': st.performed_by.first_name[0] if st.performed_by.first_name else st.performed_by.username[0],
            'staff_role': st.performed_by.role_display
        })
        
    # Ordenar por fecha y tomar los 10 más recientes
    recent_activity.sort(key=lambda x: x['created_at'], reverse=True)
    recent_activity = recent_activity[:8]

    # --- Métricas Avanzadas 2.0 ---
    
    # 5. Ranking de Staff (Hoy)
    from apps.audit.models import AuditLog
    staff_ranking = User.objects.filter(
        organization=tenant,
        is_active=True
    ).filter(
        Q(is_owner=True) | Q(is_staff_member=True)
    ).annotate(
        actions_today=Count('performed_audit_logs', filter=Q(performed_audit_logs__created_at__date=today))
    ).filter(actions_today__gt=0).order_by('-actions_today')[:5]

    # 6. Tasa de Retención (Clientes que han vuelto)
    # Definimos "retenido" como cliente con > 1 transacción total
    retained_count = Customer.objects.filter(organization=tenant).annotate(
        tx_count=Count('point_transactions')
    ).filter(tx_count__gt=1).count()
    
    retention_rate = 0
    if total_customers > 0:
        retention_rate = int((retained_count / total_customers) * 100)

    # 7. Caja Estimada (Hoy) - Basado en descripción de auditoría de sellos
    # (Asumimos que la descripción contiene el precio o podemos buscarlo)
    # Por ahora haremos una suma simple de puntos ganados como proxy o 0 si no hay precios
    estimated_revenue = PointTransaction.objects.filter(
        organization=tenant,
        created_at__date=today,
        transaction_type='EARN'
    ).count() * 10 # Multiplicamos por un ticket promedio base de 10 unidades de moneda
    
    # 8. Límites de Uso (Suscripción) - Filtrar solo los de módulos activos
    from apps.core.models import UsageLimit
    all_limits = UsageLimit.objects.filter(organization=tenant).order_by('limit_type')
    
    usage_limits = []
    for limit in all_limits:
        show_limit = True
        ltype = limit.limit_type
        
        if ltype == 'appointments_monthly' and not request.user.has_feature_appointments:
            show_limit = False
        elif ltype == 'campaigns_monthly' and not request.user.has_feature_campaigns:
            show_limit = False
        elif ltype == 'sms_monthly':
            show_limit = False  # Ocultar siempre por petición del usuario
        # El almacenamiento (storage_mb) es base y suele estar visible
        elif ltype == 'storage_mb' and limit.limit_value <= 0:
            show_limit = False
        elif ltype == 'customers' and not request.user.has_feature_customers:
            if not (request.user.has_feature_points or request.user.has_feature_stamps):
                show_limit = False
        
        if show_limit:
            usage_limits.append(limit)
    
    # 9. Canjes Hoy (Puntos + Sellos)
    point_redeems_today = PointTransaction.objects.filter(
        organization=tenant,
        created_at__date=today,
        transaction_type='REDEEM'
    ).count()
    
    stamp_redeems_today = StampTransaction.objects.filter(
        organization=tenant,
        created_at__date=today,
        action='REDEEM'
    ).count()
    
    redemptions_today = point_redeems_today + stamp_redeems_today
    
    context = {
        'total_customers': total_customers,
        'new_customers_today': new_customers_today,
        'points_today': points_today,
        'active_stamp_cards': active_stamp_cards,
        'recent_activity': recent_activity,
        'redemptions_today': redemptions_today,
        'retention_rate': retention_rate,
        'estimated_revenue': estimated_revenue,
        'staff_ranking': staff_ranking,
        'usage_limits': usage_limits,
        'worker_stats': worker_stats, # Added for worker dashboard
        'title': f"Dashboard - {tenant.name}"
    }
    return render(request, 'core/dashboard.html', context)

import csv
from django.http import HttpResponse

@login_required
def export_daily_report(request):
    """Exporta un resumen de la actividad de hoy en CSV"""
    tenant = getattr(request, 'tenant', None) or request.user.organization
    today = timezone.localtime().date()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Reporte_{today}.csv"'
    response.write(u'\ufeff'.encode('utf8')) # BOM para Excel
    
    writer = csv.writer(response)
    writer.writerow(['Cliente', 'Operación', 'Puntos/Sellos', 'Barbero', 'Hora'])
    
    # 1. Movimientos de Puntos
    point_txs = PointTransaction.objects.filter(organization=tenant, created_at__date=today).select_related('customer', 'performed_by')
    for tx in point_txs:
        writer.writerow([
            tx.customer.full_name,
            tx.get_transaction_type_display(),
            tx.points,
            tx.performed_by.get_full_name() if tx.performed_by else 'Sistema',
            tx.created_at.strftime('%H:%M')
        ])
    
    # 2. Movimientos de Sellos
    stamp_txs = StampTransaction.objects.filter(organization=tenant, created_at__date=today).select_related('card__customer', 'performed_by')
    for tx in stamp_txs:
        writer.writerow([
            tx.card.customer.full_name,
            f"Sello - {tx.get_action_display()}",
            tx.quantity,
            tx.performed_by.get_full_name() if tx.performed_by else 'Sistema',
            tx.created_at.strftime('%H:%M')
        ])
        
    return response

@login_required
def daily_activity_api(request):
    """Devuelve JSON con la actividad detallada de hoy"""
    tenant = getattr(request, 'tenant', None) or request.user.organization
    today = timezone.localtime().date()
    
    # 1. Puntos
    point_txs = PointTransaction.objects.filter(
        organization=tenant, 
        created_at__date=today
    ).select_related('customer', 'performed_by').order_by('-created_at')
    
    # 2. Sellos
    stamp_txs = StampTransaction.objects.filter(
        organization=tenant, 
        created_at__date=today
    ).select_related('card__customer', 'performed_by').order_by('-created_at')
    
    results = []
    for tx in point_txs:
        results.append({
            'time': tx.created_at.strftime('%H:%M'),
            'customer': tx.customer.full_name,
            'action': tx.get_transaction_type_display(),
            'value': f"{tx.points} pts",
            'staff': tx.performed_by.get_full_name() if tx.performed_by else 'Sistema',
            'type': 'points'
        })
        
    for tx in stamp_txs:
        results.append({
            'time': tx.created_at.strftime('%H:%M'),
            'customer': tx.card.customer.full_name,
            'action': f"Sello - {tx.get_action_display()}",
            'value': f"{tx.quantity} qty",
            'staff': tx.performed_by.get_full_name() if tx.performed_by else 'Sistema',
            'type': 'stamps'
        })
        
    # Ordenar por hora descendente
    results.sort(key=lambda x: x['time'], reverse=True)
    
    return JsonResponse({'activity': results})

@login_required
def dashboard_stats_api(request):
    """API que devuelve datos para los gráficos del dashboard"""
    tenant = getattr(request, 'tenant', None) or request.user.organization
    last_30_days = timezone.localtime().date() - timedelta(days=30)
    
    
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
