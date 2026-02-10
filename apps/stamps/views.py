
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models, transaction
from .models import StampPromotion, StampCard, StampTransaction
from .forms import StampPromotionForm, StampAssignmentForm
from apps.customers.models import Customer

@login_required
def promotion_list(request):
    """Listar promociones activas"""
    if not hasattr(request, 'tenant'):
        return redirect('users:login')
        
    promotions = StampPromotion.objects.filter(organization=request.tenant)
    if request.method == 'POST':
        form = StampPromotionForm(request.POST)
        if form.is_valid():
            promo = form.save(commit=False)
            promo.organization = request.tenant
            promo.save()
            messages.success(request, "Promoción creada.")
            return redirect('stamps:promotion_list')
    else:
        form = StampPromotionForm()
        
    return render(request, 'stamps/promotion_list.html', {'promotions': promotions, 'form': form, 'title': 'Promociones de Sellos'})

@login_required
def promotion_edit(request, pk):
    promo = get_object_or_404(StampPromotion, pk=pk, organization=request.tenant)
    if request.method == 'POST':
        form = StampPromotionForm(request.POST, instance=promo)
        if form.is_valid():
            form.save()
            messages.success(request, "Promoción actualizada.")
            return redirect('stamps:promotion_list')
    else:
        form = StampPromotionForm(instance=promo)
    return render(request, 'stamps/promotion_form.html', {'form': form, 'title': f'Editar {promo.name}'})

@login_required
def assign_stamps(request):
    """Agregar sellos a un cliente - Soporta acumulación"""
    if request.method == 'POST':
        form = StampAssignmentForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            customer = form.cleaned_data['customer']
            quantity = form.cleaned_data['quantity']
            
            active_promo = StampPromotion.objects.filter(organization=request.tenant, is_active=True).first()
            if not active_promo:
                messages.error(request, "No hay ninguna promoción activa.")
                return redirect('stamps:promotion_list')
            
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
    
    # Agrupar tarjetas por cliente
    customer_groups = {}
    for card in cards:
        customer_id = card.customer.id
        if customer_id not in customer_groups:
            customer_groups[customer_id] = {
                'customer': card.customer,
                'active_card': None,
                'completed_cards': [],
                'requested_count': 0,
                'last_activity': card.last_stamp_at
            }
        
        if card.is_completed:
            customer_groups[customer_id]['completed_cards'].append(card)
            if card.redemption_requested:
                customer_groups[customer_id]['requested_count'] += 1
        else:
            # Asumimos que solo hay una activa por promoción (o tomamos la más reciente)
            if not customer_groups[customer_id]['active_card'] or card.last_stamp_at > customer_groups[customer_id]['active_card'].last_stamp_at:
                customer_groups[customer_id]['active_card'] = card
        
        if card.last_stamp_at > customer_groups[customer_id]['last_activity']:
            customer_groups[customer_id]['last_activity'] = card.last_stamp_at

    # Convertir a lista y ordenar: Primero los que tienen solicitudes, luego por actividad
    grouped_list = sorted(
        customer_groups.values(), 
        key=lambda x: (x['requested_count'] > 0, x['last_activity']), 
        reverse=True
    )

    stats = {
        'total_active': cards.filter(is_completed=False).count(),
        'completed': cards.filter(is_completed=True, redemption_requested=False).count(),
        'requested': cards.filter(redemption_requested=True).count(),
        'stamps_today': StampTransaction.objects.filter(organization=request.tenant, created_at__date=today, action='ADD').count()
    }

    return render(request, 'stamps/card_list.html', {
        'grouped_customers': grouped_list, 
        'title': 'Tarjetas de Clientes',
        'query': query,
        'stats': stats
    })

    return redirect('stamps:card_list')

@login_required
def add_stamp_customer(request, customer_id):
    """Agrega un sello a un cliente buscando su tarjeta activa o creando una"""
    if request.method == 'POST':
        customer = get_object_or_404(Customer, id=customer_id, organization=request.tenant)
        active_promo = StampPromotion.objects.filter(organization=request.tenant, is_active=True).first()
        
        if not active_promo:
            messages.error(request, "No hay promoción activa.")
            return redirect('stamps:card_list')

        with transaction.atomic():
            card, created = StampCard.objects.get_or_create(
                customer=customer,
                promotion=active_promo,
                is_completed=False,
                is_redeemed=False,
                defaults={'current_stamps': 0}
            )
            
            card.current_stamps += 1
            if card.current_stamps >= active_promo.total_stamps_needed:
                card.is_completed = True
                messages.success(request, f"¡Tarjeta completada para {customer.full_name}!")
            
            card.save()
            StampTransaction.objects.create(
                organization=request.tenant,
                card=card,
                action='ADD',
                quantity=1,
                performed_by=request.user
            )
            messages.success(request, "Sello añadido correctamente.")
            
    return redirect('stamps:card_list')

# --- CLIENT VIEWS ---

@login_required
def my_stamps(request):
    """Vista para que el cliente vea sus propias tarjetas"""
    # Intentar obtener el registro de cliente asociado por email
    customer = Customer.objects.filter(email=request.user.email, organization=request.user.organization).first()
    
    if not customer:
        return render(request, 'stamps/no_customer_profile.html')
        
    cards = StampCard.objects.filter(customer=customer, is_redeemed=False).select_related('promotion').order_by('-current_stamps')
    
    return render(request, 'stamps/my_stamps.html', {
        'cards': cards,
        'customer': customer,
        'title': 'Mis Sellos'
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
