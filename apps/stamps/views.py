
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models, transaction
from .models import StampPromotion, StampCard, StampTransaction
from .forms import StampPromotionForm, StampAssignmentForm
from django.core.paginator import Paginator
from apps.customers.models import Customer
from apps.audit.utils import log_action
from apps.core.models import Organization, set_current_tenant
from .models import StampPromotion, StampCard, StampTransaction, StampRequest
from django.utils import timezone
from apps.core.decorators import owner_or_superuser_required
from apps.campaigns.models import NotificationConfig
from apps.campaigns.utils import send_email_notification, format_message
from django.urls import reverse
import urllib.parse

def qr_request_stamp(request, slug):
    """Vista pública para solicitar un sello vía QR"""
    organization = get_object_or_404(Organization, slug=slug, is_active=True)
    set_current_tenant(organization)
    
    # Buscar una promoción activa (la más reciente)
    promotion = StampPromotion.objects.filter(organization=organization, is_active=True).last()
    
    if not promotion:
        return render(request, 'stamps/qr_request_error.html', {
            'organization': organization,
            'error': 'No hay promociones de sellos vigentes en este momento.'
        })

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        
        if not phone:
            messages.error(request, "El número de teléfono es obligatorio.")
        elif not first_name:
            messages.error(request, "El nombre es obligatorio.")
        else:
            # Buscar o crear cliente
            customer, created = Customer.objects.get_or_create(
                phone=phone,
                organization=organization,
                defaults={'first_name': first_name or 'Cliente QR'}
            )
            
            # NUEVO: Evitar duplicados según la configuración del negocio (Cooldown dinámico)
            cooldown_total_mins = (organization.stamp_lock_hours * 60) + organization.stamp_lock_minutes
            
            recent_request = StampRequest.objects.filter(
                customer=customer,
                promotion=promotion,
                status='PENDING',
                requested_at__gte=timezone.now() - timezone.timedelta(minutes=cooldown_total_mins)
            ).exists()
            
            already_exists = False
            if not recent_request:
                # Crear solicitud
                StampRequest.objects.create(
                    customer=customer,
                    promotion=promotion,
                    organization=organization
                )
            else:
                already_exists = True
            
            # Buscar solicitudes pendientes totales para esta promo (para mostrar en éxito)
            pending_count = StampRequest.objects.filter(
                customer=customer,
                promotion=promotion,
                status='PENDING'
            ).count()
            
            # Buscar tarjeta activa
            active_card = StampCard.objects.filter(
                customer=customer,
                promotion=promotion,
                is_completed=False,
                is_redeemed=False
            ).first()
            
            # Auto-login: Crear sesión de cliente automáticamente
            request.session['customer_id'] = customer.id
            request.session['customer_org_id'] = organization.id
            
            return render(request, 'stamps/qr_request_success.html', {
                'organization': organization,
                'customer': customer,
                'promotion': promotion,
                'active_card': active_card,
                'pending_count': pending_count,
                'already_exists': already_exists
            })
            
    return render(request, 'stamps/qr_request.html', {
        'organization': organization,
        'promotion': promotion
    })

def public_lookup(request, slug):
    """Vista pública para consultar sellos por teléfono (sin login)"""
    organization = get_object_or_404(Organization, slug=slug, is_active=True)
    set_current_tenant(organization)
    
    cards = []
    customer = None
    phone = request.GET.get('phone', '').strip()
    
    if phone:
        customer = Customer.objects.filter(phone=phone, organization=organization).first()
        if customer:
            cards = StampCard.objects.filter(customer=customer, is_redeemed=False).select_related('promotion').order_by('-current_stamps')
            # Filtrar expiradas
            cards = [c for c in cards if not c.is_expired]
        else:
            messages.info(request, "No encontramos ninguna tarjeta con ese número.")

    return render(request, 'stamps/public_lookup.html', {
        'organization': organization,
        'customer': customer,
        'cards': cards,
        'phone': phone,
        'days_range': range(1, 32),
        'title': 'Consultar mis Sellos'
    })

@login_required
def get_pending_requests(request):
    """API para obtener solicitudes de sellos pendientes"""
    if not hasattr(request, 'tenant'):
        return JsonResponse({'error': 'No tenant'}, status=400)
    
    query = request.GET.get('q', '')
    requests = StampRequest.objects.filter(
        organization=request.tenant, 
        status='PENDING'
    ).select_related('customer', 'promotion')
    
    if query:
        requests = requests.filter(
            models.Q(customer__first_name__icontains=query) |
            models.Q(customer__last_name__icontains=query) |
            models.Q(customer__phone__icontains=query)
        )
    
    data = []
    for r in requests:
        data.append({
            'id': r.id,
            'customer_id': r.customer.id,
            'customer_name': r.customer.full_name,
            'customer_phone': r.customer.phone,
            'promotion_name': r.promotion.name,
            'requested_at': timezone.localtime(r.requested_at).strftime('%H:%M'),
        })
    
    return JsonResponse({'requests': data})

@login_required
@transaction.atomic
def resolve_stamp_request(request, pk):
    """Aprobar o rechazar una solicitud de sello"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    stamp_request = get_object_or_404(StampRequest, pk=pk, organization=request.tenant)
    action = request.POST.get('action') # 'approve' or 'reject'
    
    if stamp_request.status != 'PENDING':
        return JsonResponse({'error': 'Solicitud ya procesada'}, status=400)
        
    if action == 'approve':
        # Obtener o crear tarjeta
        card, created = StampCard.objects.get_or_create(
            customer=stamp_request.customer,
            promotion=stamp_request.promotion,
            organization=request.tenant,
            is_completed=False,
            is_redeemed=False
        )
        
        # Añadir sello
        card.current_stamps += 1
        if card.current_stamps >= card.promotion.total_stamps_needed:
            card.is_completed = True
        card.save()
        
        # Registrar transacción
        StampTransaction.objects.create(
            card=card,
            action='ADD',
            quantity=1,
            performed_by=request.user,
            organization=request.tenant
        )
        
        # Registrar auditoría
        log_action(
            request,
            'STAMP_REQUEST_APPROVED',
            'Sello QR',
            f"Sello aprobado vía QR para {stamp_request.customer.full_name}",
            customer=stamp_request.customer
        )
        
        stamp_request.status = 'APPROVED'
        # NOTIFICACIÓN AUTOMÁTICA (Email)
        config = NotificationConfig.objects.filter(organization=request.tenant).first()
        if config and config.email_enabled and stamp_request.customer.email:
            msg = f"¡Hola {stamp_request.customer.first_name}! Has recibido un nuevo sello. Tienes {card.current_stamps}/{card.promotion.total_stamps_needed}."
            send_email_notification(config, stamp_request.customer.email, "Nuevo Sello Recibido 💈", msg)
    else:
        stamp_request.status = 'REJECTED'
        
    stamp_request.resolved_at = timezone.now()
    stamp_request.resolved_by = request.user
    stamp_request.save()
    
    if action == 'approve':
        return JsonResponse({
            'status': 'success', 
            'message': 'Solicitud aprobada',
            'redirect_url': reverse('stamps:assignment_success', kwargs={'card_id': card.pk}) + f"?qty=1"
        })
    return JsonResponse({'status': 'ok', 'new_status': stamp_request.status})

def api_customer_nudge(request):
    """API para que el cliente complete su perfil (soporta actualizaciones parciales)"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'Método no permitido'}, status=405)
    
    # Obtener ID del cliente (POST o Sesión)
    customer_id = request.POST.get('customer_id') or request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({'status': 'error', 'error': 'Sesión no encontrada'}, status=401)
    
    dni = request.POST.get('dni')
    first_name = request.POST.get('first_name')
    email = request.POST.get('email')
    birth_day = request.POST.get('birth_day')
    birth_month = request.POST.get('birth_month')
    
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Actualizar solo si se envían
    if first_name: customer.first_name = first_name
    if dni: customer.dni = dni
    if email: customer.email = email
    
    if birth_day and birth_month:
        try:
            customer.birth_day = int(birth_day)
            customer.birth_month = int(birth_month)
        except (ValueError, TypeError):
            pass
            
    customer.save()
    
    log_action(
        request,
        'CUSTOMER_NUDGE_UPDATE',
        'Cliente',
        f"Perfil actualizado (Cumple: {birth_day}/{birth_month})",
        customer=customer
    )
    
    return JsonResponse({'status': 'ok'})

@login_required
def pending_requests_list(request):
    """Vista para gestionar solicitudes de sellos QR pendientes"""
    if not hasattr(request, 'tenant'):
        return redirect('users:login')
        
    pending_count = StampRequest.objects.filter(
        organization=request.tenant, 
        status='PENDING'
    ).count()
    
    return render(request, 'stamps/pending_requests.html', {
        'pending_count': pending_count
    })

@owner_or_superuser_required
def promotion_list(request):
    """Listar promociones activas"""
    if not hasattr(request, 'tenant'):
        return redirect('users:login')
        
    promotions = StampPromotion.objects.filter(organization=request.tenant)
    if request.method == 'POST':
        form = StampPromotionForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            promo = form.save(commit=False)
            promo.organization = request.tenant
            promo.save()
            messages.success(request, "Promoción creada.")
            return redirect('stamps:promotion_list')
    else:
        form = StampPromotionForm(tenant=request.tenant)
        
    return render(request, 'stamps/promotion_list.html', {'promotions': promotions, 'form': form, 'title': 'Promociones de Sellos'})

@owner_or_superuser_required
def promotion_edit(request, pk):
    promo = get_object_or_404(StampPromotion, pk=pk, organization=request.tenant)
    if request.method == 'POST':
        form = StampPromotionForm(request.POST, instance=promo, tenant=request.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Promoción actualizada.")
            return redirect('stamps:promotion_list')
    else:
        form = StampPromotionForm(instance=promo, tenant=request.tenant)
    return render(request, 'stamps/promotion_form.html', {'form': form, 'title': f'Editar {promo.name}'})

@login_required
def assign_stamps(request):
    """Agregar sellos a un cliente - Soporta acumulación"""
    if request.method == 'POST':
        form = StampAssignmentForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            customer = form.cleaned_data['customer']
            quantity = form.cleaned_data['quantity']
            active_promo = form.cleaned_data['promotion']
            
            if not active_promo:
                messages.error(request, "Selecciona una promoción válida.")
                return redirect('stamps:card_list')
            
            with transaction.atomic():
                # Buscamos SOLO la tarjeta que aún no está llena
                card, created = StampCard.objects.get_or_create(
                    customer=customer, 
                    promotion=active_promo, 
                    is_completed=False, # <-- Clave para acumulación
                    is_redeemed=False,
                    defaults={'current_stamps': 0}
                )
                
                card.current_stamps += quantity
                if card.current_stamps >= active_promo.total_stamps_needed:
                    card.is_completed = True
                    messages.success(request, f"¡Tarjeta completada para {customer.full_name}!")
                
                card.save()
                StampTransaction.objects.create(
                    organization=request.tenant,
                    card=card,
                    action='ADD',
                    quantity=quantity,
                    performed_by=request.user
                )

                # NOTIFICACIÓN AUTOMÁTICA (Email)
                config = NotificationConfig.objects.filter(organization=request.tenant).first()
                if config and config.email_enabled and customer.email:
                    msg = f"¡Hola {customer.first_name}! Has recibido {quantity} nuevos sellos. Tienes {card.current_stamps}/{active_promo.total_stamps_needed}."
                    send_email_notification(config, customer.email, "Nuevos Sellos Recibidos 💈", msg)

            messages.success(request, f"Se agregaron {quantity} sellos.")
            
            # Preservar next
            next_url = request.POST.get('next')
            redirect_url = reverse('stamps:assignment_success', kwargs={'card_id': card.pk}) + f"?qty={quantity}"
            if next_url:
                redirect_url += f"&next={urllib.parse.quote(next_url)}"
                
            return redirect(redirect_url)
    else:
        form = StampAssignmentForm(tenant=request.tenant)
        
    return render(request, 'stamps/assign_stamps.html', {
        'form': form, 
        'title': 'Agregar Sellos',
        'next_url': request.GET.get('next')
    })

@login_required
def card_list(request):
    """Ver estado de tarjetas con buscador y solicitudes"""
    query = request.GET.get('q', '')
    cards = StampCard.objects.filter(organization=request.tenant, is_redeemed=False).select_related('customer', 'promotion').order_by('-redemption_requested', '-last_stamp_at')
    
    if query:
        search_filter = models.Q(customer__first_name__icontains=query) | \
                        models.Q(customer__last_name__icontains=query) | \
                        models.Q(customer__phone__icontains=query) | \
                        models.Q(customer__email__icontains=query)
        
        # NUEVO: Búsqueda por ID numérico (Código de Canje)
        clean_query = query.replace('#', '')
        if clean_query.isdigit():
            search_filter |= models.Q(pk=clean_query)
            
        cards = cards.filter(search_filter)

    from django.utils import timezone
    today = timezone.localtime().date()
    
    # Filtrar tarjetas expiradas del listado general (en memoria ya que depends de una property)
    cards = [c for c in cards if not c.is_expired]

    pending_reqs = StampRequest.objects.filter(
        organization=request.tenant,
        status='PENDING'
    ).order_by('requested_at')
    
    pending_map = {} # (cust_id, promo_id) -> {'count': X, 'id': Y}
    for pr in pending_reqs:
        key = (pr.customer_id, pr.promotion_id)
        if key not in pending_map:
            pending_map[key] = {'count': 0, 'id': pr.id}
        pending_map[key]['count'] += 1

    # Agrupar tarjetas por cliente
    customer_groups = {}
    for card in cards:
        customer_id = card.customer.id
        # Inyectar pendientes a la tarjeta
        pd_data = pending_map.get((customer_id, card.promotion.id), {'count': 0, 'id': None})
        card.pending_count = pd_data['count']
        card.first_pending_request_id = pd_data['id']
        
        if customer_id not in customer_groups:
            customer_groups[customer_id] = {
                'customer': card.customer,
                'active_cards': [],
                'completed_cards': [],
                'requested_count': 0,
                'total_pending_stamps': 0,
                'last_activity': card.last_stamp_at
            }
        
        if card.is_completed:
            customer_groups[customer_id]['completed_cards'].append(card)
            if card.redemption_requested:
                customer_groups[customer_id]['requested_count'] += 1
        else:
            customer_groups[customer_id]['active_cards'].append(card)
            customer_groups[customer_id]['total_pending_stamps'] += card.pending_count
        
        if card.last_stamp_at > customer_groups[customer_id]['last_activity']:
            customer_groups[customer_id]['last_activity'] = card.last_stamp_at

    # ... sorted algorithm stays the same ...
    grouped_list = sorted(
        customer_groups.values(), 
        key=lambda x: (x['requested_count'] > 0, x['last_activity']), 
        reverse=True
    )

    stats = {
        'total_active': sum(1 for c in cards if not c.is_completed),
        'completed': sum(1 for c in cards if c.is_completed and not c.redemption_requested),
        'requested': sum(1 for c in cards if c.redemption_requested),
        'stamps_today': StampTransaction.objects.filter(organization=request.tenant, created_at__date=today, action='ADD').count()
    }

    from .forms import StampAssignmentForm
    form = StampAssignmentForm(tenant=request.tenant)

    context = {
        'grouped_customers': grouped_list, 
        'title': 'Tarjetas de Clientes',
        'query': query,
        'stats': stats,
        'form': form
    }

    # Soporte para búsqueda AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'stamps/partials/card_grid.html', context)

    return render(request, 'stamps/card_list.html', context)

    return redirect('stamps:card_list')

@login_required
def add_stamp_customer(request, customer_id):
    """Agrega un sello a un cliente buscando su tarjeta activa o creando una"""
    if request.method == 'POST':
        customer = get_object_or_404(Customer, id=customer_id, organization=request.tenant)
        promo_id = request.POST.get('promotion_id')
        
        if promo_id:
            active_promo = get_object_or_404(StampPromotion, id=promo_id, organization=request.tenant, is_active=True)
        else:
            active_promo = StampPromotion.objects.filter(organization=request.tenant, is_active=True).first()
        
        if not active_promo:
            messages.error(request, "No hay promoción activa seleccionada.")
            return redirect('stamps:card_list')

        # --- Lógica Anti-Fraude (Time-Lock) ---
        from datetime import timedelta
        from django.utils import timezone
        
        # Obtenemos la configuración del tenant o usamos 2 por defecto
        lock_hours = getattr(request.tenant, 'stamp_lock_hours', 2)
        
        # BYPASS: El dueño y el superadmin NO están sujetos al bloqueo de tiempo
        is_privileged = request.user.is_owner or request.user.is_superuser
        
        if not is_privileged:
            last_add = StampTransaction.objects.filter(
                organization=request.tenant,
                card__customer=customer,
                action='ADD'
            ).order_by('-created_at').first()

            if last_add and (timezone.now() - last_add.created_at) < timedelta(hours=lock_hours):
                wait_time = last_add.created_at + timedelta(hours=lock_hours) - timezone.now()
                minutes_left = int(wait_time.total_seconds() / 60)
                messages.warning(request, f"🛡️ Anti-Fraude: Espera {minutes_left} min para dar otro sello a este cliente.")
                return redirect('stamps:card_list')

        # --- Lógica de Sello Doble ---
        quantity = 1
        weekday = timezone.now().weekday()
        double_days_map = {
            0: 'double_stamp_mon', 1: 'double_stamp_tue', 2: 'double_stamp_wed',
            3: 'double_stamp_thu', 4: 'double_stamp_fri', 5: 'double_stamp_sat',
            6: 'double_stamp_sun'
        }
        if getattr(request.tenant, double_days_map[weekday], False):
            quantity = 2

        with transaction.atomic():
            # Buscar tarjeta activa que NO esté completada ni canjeada
            card = StampCard.objects.filter(
                customer=customer,
                promotion=active_promo,
                is_completed=False,
                is_redeemed=False
            ).first()
            
            # Si existe pero está expirada, la "cerramos" implícitamente creando una nueva
            if card and card.is_expired:
                card = None
                
            if not card:
                card = StampCard.objects.create(
                    customer=customer,
                    promotion=active_promo,
                    organization=request.tenant,
                    current_stamps=0
                )
            
            card.current_stamps += quantity
            if card.current_stamps >= active_promo.total_stamps_needed:
                card.is_completed = True
                messages.success(request, f"¡Tarjeta completada para {customer.full_name}!")
            
            card.save()
            StampTransaction.objects.create(
                organization=request.tenant,
                card=card,
                action='ADD',
                quantity=quantity,
                performed_by=request.user
            )

            # Log de auditoría
            log_action(
                request, 
                'STAMP_ADD', 
                'Sello', 
                f"Sello(s) agregado(s): {quantity} - Promo: {card.promotion.name}",
                customer=customer
            )
            
            # NOTIFICACIÓN AUTOMÁTICA (Email)
            config = NotificationConfig.objects.filter(organization=request.tenant).first()
            if config and config.email_enabled and customer.email:
                msg = f"¡Hola {customer.first_name}! Has recibido {quantity} nuevo(s) sello(s). Tienes {card.current_stamps}/{card.promotion.total_stamps_needed}."
                send_email_notification(config, customer.email, "Nuevo Sello Recibido 💈", msg)

            msg = f"Sello añadido correctamente."
            if quantity == 2:
                msg = f"⚡ ¡Sello DOBLE aplicado! ({quantity} sellos añadidos)."
            messages.success(request, msg)
            
            # Preservar el parámetro 'next'
            next_url = request.POST.get('next')
            redirect_url = reverse('stamps:assignment_success', kwargs={'card_id': card.pk}) + f"?qty={quantity}"
            if next_url:
                redirect_url += f"&next={urllib.parse.quote(next_url)}"
                
            return redirect(redirect_url)

    # GET: Mostrar pantalla de confirmación (útil para escaneo QR)
    customer = get_object_or_404(Customer, id=customer_id, organization=request.tenant)
    promo_id = request.GET.get('promotion_id')
    next_url = request.GET.get('next')
    
    if promo_id:
        active_promo = get_object_or_404(StampPromotion, id=promo_id, organization=request.tenant, is_active=True)
    else:
        active_promo = StampPromotion.objects.filter(organization=request.tenant, is_active=True).first()
    
    return render(request, 'stamps/confirm_add_stamp.html', {
        'customer': customer,
        'active_promo': active_promo,
        'next_url': next_url
    })

@login_required
def customer_history(request, customer_id):
    """Retorna el historial de transacciones de un cliente (con paginación AJAX)"""
    customer = get_object_or_404(Customer, id=customer_id, organization=request.tenant)
    queryset = StampTransaction.objects.filter(
        organization=request.tenant,
        card__customer=customer
    ).select_related('card', 'card__promotion', 'performed_by').order_by('-created_at')

    paginator = Paginator(queryset, 15) # 15 transacciones por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'stamps/partials/customer_history.html', {
        'customer': customer,
        'page_obj': page_obj,
        'transactions': page_obj.object_list
    })

# --- CLIENT VIEWS ---

def my_stamps(request):
    """Vista para que el cliente vea sus propias tarjetas"""
    customer = None
    
    # Prioridad 1: Sesión de cliente (Login DNI/Celular)
    customer_id = request.session.get('customer_id')
    if customer_id:
        customer = Customer.objects.filter(id=customer_id).first()
    
    # Prioridad 2: Usuario logueado (Django User)
    if not customer and request.user.is_authenticated:
        customer = Customer.objects.filter(email=request.user.email, organization=request.user.organization).first()
    
    if not customer:
        # Si no hay cliente en sesión, redirigir a login si sabemos la organización
        if hasattr(request, 'tenant') and request.tenant:
            return redirect('customers:customer_login', slug=request.tenant.slug)
        return render(request, 'stamps/no_customer_profile.html')
        
    cards = StampCard.objects.filter(customer=customer, is_redeemed=False).select_related('promotion').order_by('-current_stamps')
    
    # Filtrar expiradas
    cards = [c for c in cards if not c.is_expired]
    
    # NUEVO: Buscar solicitudes pendientes
    pending_all = StampRequest.objects.filter(
        customer=customer, 
        status='PENDING'
    ).select_related('promotion')
    
    # Vincular solicitudes pendientes a tarjetas existentes para evitar duplicados visuales
    orphan_pending_map = {} # promotion_id -> StampRequest object with count
    for pr in pending_all:
        pr_promo_id = pr.promotion_id
        # Vincular solo si la tarjeta tiene espacio para UN sello más (considerando los ya vinculados en este loop)
        linked_card = next((
            c for c in cards 
            if c.promotion_id == pr_promo_id 
            and not c.is_completed 
            and (c.current_stamps + getattr(c, 'pending_count', 0)) < c.promotion.total_stamps_needed
        ), None)
        
        if linked_card:
            # Incrementar el contador de pendientes para esta tarjeta
            linked_card.pending_count = getattr(linked_card, 'pending_count', 0) + 1
        else:
            # Agrupar solicitudes huérfanas por promoción
            if pr_promo_id not in orphan_pending_map:
                pr.pending_count = 1
                orphan_pending_map[pr_promo_id] = pr
            else:
                orphan_pending_map[pr_promo_id].pending_count += 1
    
    orphan_pending = list(orphan_pending_map.values())
    
    return render(request, 'stamps/my_stamps.html', {
        'cards': cards,
        'pending_requests': orphan_pending, # Solo enviamos las huérfanas como Ghost Cards
        'customer': customer,
        'title': 'Mis Sellos'
    })

def customer_kiosk(request):
    """Vista simplificada con QR para identificación rápida en el local"""
    customer = None
    
    # Identificar cliente (Sesión o Django User)
    customer_id = request.session.get('customer_id')
    if customer_id:
        customer = Customer.objects.filter(id=customer_id).first()
    
    if not customer and request.user.is_authenticated:
        customer = Customer.objects.filter(email=request.user.email, organization=request.user.organization).first()

    if not customer:
        if hasattr(request, 'tenant') and request.tenant:
            return redirect('customers:customer_login', slug=request.tenant.slug)
        return render(request, 'stamps/no_customer_profile.html')
        
    # URL que el staff escaneará para dar un sello
    scheme = "https" if request.is_secure() else "http"
    domain = request.get_host()
    stamp_url = f"{scheme}://{domain}/app/stamps/customers/{customer.id}/add-stamp/"

    active_cards = StampCard.objects.filter(customer=customer, is_redeemed=False).count()
    completed_cards = StampCard.objects.filter(customer=customer, is_completed=True, is_redeemed=False).count()

    return render(request, 'stamps/customer_kiosk.html', {
        'customer': customer,
        'stamp_url': stamp_url,
        'active_cards': active_cards,
        'completed_cards': completed_cards,
        'title': 'Modo Kiosko'
    })

def request_redemption(request, pk):
    """El cliente solicita canjear su premio"""
    if request.method == 'POST':
        card = get_object_or_404(StampCard, pk=pk, is_completed=True, is_redeemed=False)
        
        # Validar pertenencia del cliente (Sesión o Email)
        customer_id = request.session.get('customer_id')
        is_owner = False
        
        if customer_id and card.customer.id == customer_id:
            is_owner = True
        elif request.user.is_authenticated and card.customer.email == request.user.email:
            is_owner = True
            
        if not is_owner:
            messages.error(request, "No tienes permiso para esta acción.")
            return redirect('stamps:my_stamps')
            
        card.redemption_requested = True
        card.requested_at = timezone.now()
        card.save()
        messages.success(request, "¡Premio solicitado! Muéstrale esta pantalla al barbero.")
        
    return redirect('stamps:my_stamps')

@login_required
def qr_scanner(request):
    """Vista con escáner de cámara para que el staff identifique clientes"""
    if not (request.user.is_owner or request.user.is_staff_member or request.user.is_superuser):
        messages.error(request, "No tienes permiso para acceder al escáner.")
        return redirect('core:dashboard')
        
    return render(request, 'stamps/qr_scanner.html', {
        'title': 'Escanear Cliente'
    })

@login_required
def redeem_card(request, pk):
    """Canjear una tarjeta completada"""
    card = get_object_or_404(StampCard, pk=pk, organization=request.tenant)
    if not card.is_completed:
        messages.error(request, "La tarjeta no está completa aún.")
        return redirect('stamps:card_list')
        
    card.is_redeemed = True
    card.save()

    # Log transacción canje (modelo stamps)
    StampTransaction.objects.create(
        organization=request.tenant,
        card=card,
        action='REDEEM',
        quantity=0,
        performed_by=request.user
    )

    # Log de auditoría general
    log_action(
        request, 
        'STAMP_REDEEM', 
        'Sello', 
        f"Canjeado premio para {card.customer.full_name} - Promo: {card.promotion.name}",
        customer=card.customer
    )
    
    messages.success(request, "Recompensa canjeada exitosamente. Se ha archivado la tarjeta.")
    
    # Redirección flexible
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('stamps:card_list')

@login_required
def undo_transaction(request, pk):
    """Deshacer una transacción reciente (solo staff/dueño)"""
    if request.method == 'POST':
        tx = get_object_or_404(StampTransaction, pk=pk, organization=request.tenant)
        
        # Seguridad: Solo transacciones de las últimas 24 horas
        from django.utils import timezone
        from datetime import timedelta
        if (timezone.now() - tx.created_at) > timedelta(hours=24):
            messages.error(request, "Esta transacción es muy antigua para ser deshecha.")
            return redirect('stamps:card_list')

        card = tx.card
        with transaction.atomic():
            if tx.action == 'ADD':
                if card.is_redeemed:
                    messages.error(request, "No se puede deshacer un sello de una tarjeta ya canjeada.")
                    return redirect('stamps:card_list')
                
                card.current_stamps = max(0, card.current_stamps - tx.quantity)
                card.is_completed = False
                card.save()
                
            elif tx.action == 'REDEEM':
                card.is_redeemed = False
                card.redemption_requested = False
                card.save()

            tx.delete() # Borramos el error del historial
            messages.success(request, "Acción deshecha correctamente.")
            
    return redirect('stamps:card_list')

@login_required
def assignment_success(request, card_id):
    """Página de éxito tras asignar sellos con opciones de compartir"""
    card = get_object_or_404(StampCard, pk=card_id, organization=request.tenant)
    added_quantity = request.GET.get('qty', 1)
    next_url = request.GET.get('next')
    
    # Preparar mensaje de WhatsApp
    clean_phone = ''.join(filter(str.isdigit, str(card.customer.phone)))
    kiosk_url = request.build_absolute_uri(reverse('stamps:public_lookup', kwargs={'slug': request.tenant.slug}))
    kiosk_url += f"?phone={card.customer.phone}"
    
    # Usar urllib.parse para asegurar que el mensaje esté bien codificado para la URL
    msg = f"¡Hola {card.customer.first_name}! 💈 Has ganado {added_quantity} sello(s) en {request.tenant.name}. "
    msg += f"Ya tienes {card.current_stamps} de {card.promotion.total_stamps_needed}. "
    
    if card.is_completed:
        msg += "¡FELICIDADES! Ya puedes reclamar tu premio. 🎁 "
    else:
        msg += f"¡Solo te faltan {card.promotion.total_stamps_needed - card.current_stamps} para tu premio! "
        
    msg += f"\nMira tu progreso aquí: {kiosk_url}"
    
    context = {
        'card': card,
        'customer': card.customer,
        'added_quantity': added_quantity,
        'clean_phone': clean_phone,
        'wa_message': msg,
        'title': '¡Sello Asignado!',
        'next_url': next_url
    }
    return render(request, 'stamps/assignment_success.html', context)
