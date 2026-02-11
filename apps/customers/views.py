from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.db.models import Q
from django.db import transaction
from .models import Customer, Tag
from .forms import CustomerForm
# Importaciones para auto-asignación y estadísticas
from apps.stamps.models import StampPromotion, StampCard, StampTransaction, StampRequest
from apps.loyalty.models import PointTransaction
from apps.audit.utils import log_action
from django.utils import timezone
from collections import Counter

from apps.core.models import Organization

@login_required
def customer_list(request):
    """Listar clientes de la organización actual con soporte para búsqueda AJAX"""
    if not hasattr(request, 'tenant') or not request.tenant:
         return redirect('users:login')
         
    query = request.GET.get('q', '')
    from django.db.models import Case, When, Value, IntegerField
    today = timezone.localtime().date()
    if request.tenant and hasattr(request.tenant, 'timezone') and request.tenant.timezone:
        import zoneinfo
        try:
            today = timezone.now().astimezone(zoneinfo.ZoneInfo(request.tenant.timezone)).date()
        except: pass
    
    customers = Customer.objects.filter(organization=request.tenant).annotate(
        is_birthday_today=Case(
            When(birth_day=today.day, birth_month=today.month, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    )
    
    if query:
        customers = customers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )
    
    customers = customers.order_by('-is_birthday_today', '-created_at')
    
    # Si es una petición AJAX, devolvemos solo el parcial de las filas
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'customers/partials/customer_table_rows.html', {'customers': customers})
        
    context = {
        'customers': customers,
        'title': 'Gestión de Clientes',
        'query': query,
        'form': CustomerForm()
    }
    return render(request, 'customers/customer_list.html', context)

@login_required
def customer_detail(request, pk):
    """Perfil detallado del cliente"""
    customer = get_object_or_404(Customer, pk=pk, organization=request.tenant)
    
    # --- Módulo de Sellos ---
    # Obtener tarjetas de sellos (activas e historial)
    stamp_cards = StampCard.objects.filter(customer=customer).order_by('-created_at')
    
    # Premios listos para canjear (completadas pero no canjeadas)
    rewards_ready = stamp_cards.filter(is_completed=True, is_redeemed=False).count()
    
    # NUEVO: Tarjetas que han SOLICITADO el premio específicamente
    requested_cards = stamp_cards.filter(redemption_requested=True, is_redeemed=False)

    # Obtener historial de puntos (si aplica)
    point_transactions = []
    if hasattr(customer, 'point_transactions'):
         point_transactions = customer.point_transactions.all().order_by('-created_at')

    # --- Lógica de ADN del Cliente ---
    # 1. Recopilar todas las visitas (transacciones de acumulación)
    stamp_txns = StampTransaction.objects.filter(card__customer=customer, action='ADD').order_by('created_at')
    point_txns = PointTransaction.objects.filter(customer=customer, transaction_type='EARN').order_by('created_at')
    
    visit_dates = sorted([tx.created_at for tx in stamp_txns] + [tx.created_at for tx in point_txns])
    
    adn = {
        'frecuencia': 'Primera visita',
        'servicio_favorito': 'Corte Regular',  # Default
        'dias_ultima_visita': 0,
        'status_ultima_visita': 'text-muted'
    }
    
    if visit_dates:
        # Última visita
        last_visit = visit_dates[-1]
        delta_last = (timezone.now() - last_visit).days
        adn['dias_ultima_visita'] = delta_last
        if delta_last > 30:
            adn['status_ultima_visita'] = 'text-danger fw-bold'
        elif delta_last < 7:
            adn['status_ultima_visita'] = 'text-success'
        else:
            adn['status_ultima_visita'] = 'text-primary'
            
        # Frecuencia media
        if len(visit_dates) > 1:
            diffs = [(visit_dates[i] - visit_dates[i-1]).days for i in range(1, len(visit_dates))]
            if diffs:
                avg_days = sum(diffs) / len(diffs)
                adn['frecuencia'] = f"Viene cada {int(avg_days)} días"
            
        # Servicio favorito (basado en descripciones o promos)
        services = [tx.card.promotion.name for tx in stamp_txns] + [tx.description for tx in point_txns]
        if services:
            most_common = Counter(services).most_common(1)
            adn['servicio_favorito'] = most_common[0][0]

    # --- Lógica de Cumpleaños ---
    birthday_info = {
        'days_to': None,
        'is_today': False,
        'message': 'No registrado'
    }
    if customer.birth_day and customer.birth_month:
        try:
            today = timezone.localtime().date()
            if request.tenant and hasattr(request.tenant, 'timezone') and request.tenant.timezone:
                import zoneinfo
                try:
                    today = timezone.now().astimezone(zoneinfo.ZoneInfo(request.tenant.timezone)).date()
                except: pass
            # Crear fecha de cumple para este año
            this_year_bday = today.replace(month=customer.birth_month, day=customer.birth_day)
            
            # Si ya pasó este año, mirar el siguiente
            if this_year_bday < today:
                next_bday = this_year_bday.replace(year=today.year + 1)
            else:
                next_bday = this_year_bday
                
            delta = (next_bday - today).days
            birthday_info['days_to'] = delta
            birthday_info['is_today'] = (delta == 0)
            
            if delta == 0:
                birthday_info['message'] = "¡Hoy es su cumpleaños! 🎉"
            elif delta <= 7:
                birthday_info['message'] = f"¡Faltan solo {delta} días! 🎂"
            else:
                birthday_info['message'] = f"Faltan {delta} días"
        except ValueError:
            pass # Fechas inválidas como 29 de febrero en años no bisiestos

    # --- Línea de Vida (Audit Logs) ---
    # Dueño ve todo, trabajador ve filtrado
    activity_logs = customer.audit_logs.all().select_related('user')
    if not request.user.is_owner:
        # Filtrar solo acciones operativas para trabajadores
        activity_logs = activity_logs.filter(action__in=['STAMP_ADD', 'STAMP_REDEEM', 'POINTS_ADD', 'POINTS_REDEEM', 'WA_SENT'])

    # --- Solicitudes QR Pendientes ---
    pending_requests = StampRequest.objects.filter(customer=customer, status='PENDING').select_related('promotion')

    context = {
        'customer': customer,
        'stamp_cards': stamp_cards,
        'rewards_ready': rewards_ready,
        'requested_cards': requested_cards,
        'point_transactions': point_transactions,
        'adn': adn,
        'birthday_info': birthday_info,
        'activity_logs': activity_logs[:20],  # Últimos 20 movimientos
        'pending_requests': pending_requests,
        'title': f'Perfil: {customer.full_name}'
    }
    return render(request, 'customers/customer_detail.html', context)

@login_required
def customer_create(request):
    """Crear nuevo cliente"""
    # Verificación de límites (Suscripción)
    from apps.core.models import UsageLimit
    cust_limit = UsageLimit.objects.filter(organization=request.tenant, limit_type='customers').first()
    if cust_limit and cust_limit.enforce_limit and cust_limit.is_exceeded:
        messages.warning(request, "⚠️ Has alcanzado el límite de clientes de tu plan. Mejora tu suscripción para seguir registrando clienes.")
        return redirect('customers:customer_list')

    if request.method == 'POST':
        form = CustomerForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            with transaction.atomic():
                customer = form.save(commit=False)
                customer.organization = request.tenant
                customer.save()
                form.save_m2m() # Importante para guardar las etiquetas!
                
                log_action(request, 'CREATE', 'Cliente', f"Creado cliente: {customer.full_name}", customer=customer)

                # Lógica de auto-asignación de sellos
                if form.cleaned_data.get('auto_assign_stamps'):
                    active_promo = StampPromotion.objects.filter(organization=request.tenant, is_active=True).first()
                    if active_promo:
                        StampCard.objects.create(
                            organization=request.tenant,
                            customer=customer,
                            promotion=active_promo,
                            current_stamps=0
                        )
                        messages.info(request, f"Se ha asignado automáticamente la tarjeta: {active_promo.name}")
                
            messages.success(request, f"Cliente {customer.full_name} creado.")
            return redirect('customers:customer_list')
    else:
        form = CustomerForm(tenant=request.tenant)
        
    return render(request, 'customers/customer_form.html', {'form': form, 'title': 'Nuevo Cliente'})

@login_required
def customer_edit(request, pk):
    """Editar cliente existente"""
    # Filtrar por tenant para seguridad!
    customer = get_object_or_404(Customer, pk=pk, organization=request.tenant)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer, tenant=request.tenant)
        if form.is_valid():
            form.save()
            log_action(request, 'UPDATE', 'Cliente', f"Actualizado cliente: {customer.full_name}", customer=customer)
            messages.success(request, "Cliente actualizado.")
            return redirect('customers:customer_list')
    else:
        form = CustomerForm(instance=customer, tenant=request.tenant)
        
    return render(request, 'customers/customer_form.html', {'form': form, 'title': f'Editar {customer.full_name}'})

@login_required
def customer_delete(request, pk):
    """Eliminar (desactivar) cliente"""
    customer = get_object_or_404(Customer, pk=pk, organization=request.tenant)
    name = customer.full_name
    log_action(request, 'DELETE', 'Cliente', f"Eliminado cliente: {name}", customer=customer)
    customer.delete()
    messages.success(request, f"Cliente {name} eliminado.")
    return redirect('customers:customer_list')

@login_required
def customer_search_api(request):
    """API para búsqueda rápida de clientes (AJAX)"""
    query = request.GET.get('q', '')
    if len(query) < 1:
        return JsonResponse({'results': []})
        
    customers = Customer.objects.filter(
        organization=request.tenant
    ).filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(phone__icontains=query) |
        Q(email__icontains=query)
    )[:10]
    
    results = [
        {
            'id': c.id,
            'full_name': c.full_name,
            'phone': c.phone or 'Sin teléfono',
            'email': c.email or ''
        } for c in customers
    ]
    
    return JsonResponse({'results': results})

@login_required
def log_whatsapp_message(request, pk):
    """API para registrar el envío de un WhatsApp"""
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=pk, organization=request.tenant)
        message_type = request.POST.get('template_name', 'Personalizado')
        
        log_action(
            request, 
            'WA_SENT', 
            'WhatsApp', 
            f"Enviado mensaje: {message_type}", 
            customer=customer
        )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

def customer_login(request, slug):
    """Acceso para clientes usando Celular + DNI"""
    organization = get_object_or_404(Organization, slug=slug, is_active=True)
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        dni = request.POST.get('dni', '').strip()
        
        if phone and dni:
            customer = Customer.objects.filter(
                organization=organization,
                phone=phone,
                dni=dni
            ).first()
            
            if customer:
                request.session['customer_id'] = customer.id
                request.session['customer_org_id'] = organization.id
                messages.success(request, f"¡Bienvenido de nuevo, {customer.first_name}!")
                return redirect('stamps:my_stamps')
            else:
                messages.error(request, "Los datos no coinciden. Prueba de nuevo o solicita ayuda en la barbería.")
        else:
            messages.error(request, "Por favor ingresa tu número y DNI.")
            
    return render(request, 'customers/customer_login.html', {
        'organization': organization,
        'title': 'Acceso Clientes'
    })

def customer_logout(request):
    """Cerrar sesión de cliente (limpiar sesión)"""
    request.session.flush()
    messages.info(request, "Has cerrado tu sesión correctamente.")
    return redirect('core:home')
