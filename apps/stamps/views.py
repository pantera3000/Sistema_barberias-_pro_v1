
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models, transaction
from .models import StampPromotion, StampCard, StampTransaction
from .forms import StampPromotionForm, StampAssignmentForm
from django.core.paginator import Paginator
from apps.customers.models import Customer

@login_required
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

@login_required
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
                
                messages.success(request, f"Se agregaron {quantity} sellos.")
                return redirect('stamps:card_list')
    else:
        form = StampAssignmentForm(tenant=request.tenant)
    return render(request, 'stamps/assign_stamps.html', {'form': form, 'title': 'Agregar Sellos'})

@login_required
def card_list(request):
    """Ver estado de tarjetas con buscador y solicitudes"""
    query = request.GET.get('q', '')
    cards = StampCard.objects.filter(organization=request.tenant, is_redeemed=False).select_related('customer', 'promotion').order_by('-redemption_requested', '-last_stamp_at')
    
    if query:
        cards = cards.filter(
            models.Q(customer__first_name__icontains=query) | 
            models.Q(customer__last_name__icontains=query) |
            models.Q(customer__phone__icontains=query) |
            models.Q(customer__email__icontains=query)
        )

    from django.utils import timezone
    today = timezone.now().date()
    
    # Filtrar tarjetas expiradas del listado general (en memoria ya que depends de una property)
    cards = [c for c in cards if not c.is_expired]

    # Agrupar tarjetas por cliente
    customer_groups = {}
    for card in cards:
        customer_id = card.customer.id
        if customer_id not in customer_groups:
            customer_groups[customer_id] = {
                'customer': card.customer,
                'active_cards': [],
                'completed_cards': [],
                'requested_count': 0,
                'last_activity': card.last_stamp_at
            }
        
        if card.is_completed:
            customer_groups[customer_id]['completed_cards'].append(card)
            if card.redemption_requested:
                customer_groups[customer_id]['requested_count'] += 1
        else:
            customer_groups[customer_id]['active_cards'].append(card)
        
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
            
            msg = f"Sello añadido correctamente."
            if quantity == 2:
                msg = f"⚡ ¡Sello DOBLE aplicado! ({quantity} sellos añadidos)."
            messages.success(request, msg)
            return redirect('stamps:card_list')

    # GET: Mostrar pantalla de confirmación (útil para escaneo QR)
    customer = get_object_or_404(Customer, id=customer_id, organization=request.tenant)
    promo_id = request.GET.get('promotion_id')
    
    if promo_id:
        active_promo = get_object_or_404(StampPromotion, id=promo_id, organization=request.tenant, is_active=True)
    else:
        active_promo = StampPromotion.objects.filter(organization=request.tenant, is_active=True).first()
    
    return render(request, 'stamps/confirm_add_stamp.html', {
        'customer': customer,
        'active_promo': active_promo
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

@login_required
def my_stamps(request):
    """Vista para que el cliente vea sus propias tarjetas"""
    # Intentar obtener el registro de cliente asociado por email
    customer = Customer.objects.filter(email=request.user.email, organization=request.user.organization).first()
    
    if not customer:
        return render(request, 'stamps/no_customer_profile.html')
        
    cards = StampCard.objects.filter(customer=customer, is_redeemed=False).select_related('promotion').order_by('-current_stamps')
    
    # Filtrar expiradas
    cards = [c for c in cards if not c.is_expired]
    
    return render(request, 'stamps/my_stamps.html', {
        'cards': cards,
        'customer': customer,
        'title': 'Mis Sellos'
    })

@login_required
def customer_kiosk(request):
    """Vista simplificada con QR para identificación rápida en el local"""
    customer = Customer.objects.filter(email=request.user.email, organization=request.user.organization).first()
    if not customer:
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

@login_required
def request_redemption(request, pk):
    """El cliente solicita canjear su premio"""
    if request.method == 'POST':
        card = get_object_or_404(StampCard, pk=pk, is_completed=True, is_redeemed=False)
        # Validar pertenencia
        if card.customer.email != request.user.email:
            messages.error(request, "No tienes permiso para esta acción.")
            return redirect('stamps:my_stamps')
            
        card.redemption_requested = True
        card.requested_at = timezone.now()
        card.save()
        messages.success(request, "¡Premio solicitado! Muéstrale esta pantalla al barbero.")
        
    return redirect('stamps:my_stamps')

@login_required
def redeem_card(request, pk):
    """Canjear una tarjeta completada"""
    card = get_object_or_404(StampCard, pk=pk, organization=request.tenant)
    if not card.is_completed:
        messages.error(request, "La tarjeta no está completa aún.")
        return redirect('stamps:card_list')
        
    card.is_redeemed = True
    card.save()

    # Log transacción canje
    StampTransaction.objects.create(
        organization=request.tenant,
        card=card,
        action='REDEEM',
        quantity=0,
        performed_by=request.user
    )
    
    messages.success(request, "Recompensa canjeada exitosamente. Se ha archivado la tarjeta.")
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
