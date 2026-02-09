
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
    """Agregar sellos a un cliente"""
    if request.method == 'POST':
        form = StampAssignmentForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            customer = form.cleaned_data['customer']
            quantity = form.cleaned_data['quantity']
            
            # Buscar promoción activa (Tomamos la primera activa por defecto para simplificar UX)
            active_promo = StampPromotion.objects.filter(organization=request.tenant, is_active=True).first()
            
            if not active_promo:
                messages.error(request, "No hay ninguna promoción de sellos activa. Configura una primero.")
                return redirect('stamps:promotion_list')
            
            # Buscar tarjeta activa del cliente
            with transaction.atomic():
                card, created = StampCard.objects.get_or_create(
                    customer=customer, 
                    promotion=active_promo, 
                    is_redeemed=False,
                    is_completed=False,
                    defaults={'current_stamps': 0}
                )
                
                # Sumar sellos
                card.current_stamps += quantity
                
                # Verificar si completó
                if card.current_stamps >= active_promo.total_stamps_needed:
                    card.is_completed = True
                    messages.success(request, f"¡Felicidades! {customer.full_name} completó su tarjeta. Ganó: {active_promo.reward_description}")
                
                card.save()
                
                # Registrar transacción
                StampTransaction.objects.create(
                    organization=request.tenant,
                    card=card,
                    action='ADD',
                    quantity=quantity,
                    performed_by=request.user
                )
                
                messages.success(request, f"Se agregaron {quantity} sellos a {customer.full_name}.")
                return redirect('stamps:card_list')
    else:
        form = StampAssignmentForm(tenant=request.tenant)
        
    return render(request, 'stamps/assign_stamps.html', {'form': form, 'title': 'Agregar Sellos'})

@login_required
def card_list(request):
    """Ver estado de tarjetas de los clientes con buscador"""
    query = request.GET.get('q', '')
    cards = StampCard.objects.filter(organization=request.tenant, is_redeemed=False).select_related('customer', 'promotion')
    
    if query:
        cards = cards.filter(
            models.Q(customer__first_name__icontains=query) | 
            models.Q(customer__last_name__icontains=query) |
            models.Q(customer__phone__icontains=query) |
            models.Q(customer__email__icontains=query)
        )

    # Estadísticas para el ribbon
    from django.utils import timezone
    today = timezone.now().date()
    stats = {
        'total_active': cards.count(),
        'completed': cards.filter(is_completed=True).count(),
        'stamps_today': StampTransaction.objects.filter(
            organization=request.tenant, 
            created_at__date=today, 
            action='ADD'
        ).count()
    }

    return render(request, 'stamps/card_list.html', {
        'cards': cards, 
        'title': 'Tarjetas de Clientes',
        'query': query,
        'stats': stats
    })

@login_required
def add_stamp_direct(request, pk):
    """Agregar un sello directamente desde la tarjeta"""
    if request.method == 'POST':
        card = get_object_or_404(StampCard, pk=pk, organization=request.tenant, is_redeemed=False)
        
        if card.is_completed:
            messages.warning(request, "Esta tarjeta ya está completada.")
            return redirect('stamps:card_list')
            
        with transaction.atomic():
            card.current_stamps += 1
            if card.current_stamps >= card.promotion.total_stamps_needed:
                card.is_completed = True
                messages.success(request, f"¡Tarjeta completada! {card.customer.full_name} ganó su premio.")
            
            card.save()
            
            # Registrar transacción
            StampTransaction.objects.create(
                organization=request.tenant,
                card=card,
                action='ADD',
                quantity=1,
                performed_by=request.user
            )
            
            messages.success(request, f"Sello añadido a {card.customer.full_name}.")
            
    return redirect('stamps:card_list')

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
