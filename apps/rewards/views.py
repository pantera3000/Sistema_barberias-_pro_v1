
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from .models import Reward, Redemption
from .forms import RewardForm, RedemptionForm
from apps.loyalty.models import PointTransaction

@login_required
def reward_list(request):
    """Listar catálogo de premios"""
    rewards = Reward.objects.filter(organization=request.tenant)
    
    if request.method == 'POST':
        form = RewardForm(request.POST)
        if form.is_valid():
            reward = form.save(commit=False)
            reward.organization = request.tenant
            reward.save()
            messages.success(request, "Premio agregado al catálogo.")
            return redirect('rewards:reward_list')
    else:
        form = RewardForm()

    return render(request, 'rewards/reward_list.html', {'rewards': rewards, 'form': form, 'title': 'Catálogo de Recompensas'})

@login_required
def reward_edit(request, pk):
    reward = get_object_or_404(Reward, pk=pk, organization=request.tenant)
    if request.method == 'POST':
        form = RewardForm(request.POST, instance=reward)
        if form.is_valid():
            form.save()
            messages.success(request, "Premio actualizado.")
            return redirect('rewards:reward_list')
    else:
        form = RewardForm(instance=reward)
    return render(request, 'rewards/reward_form.html', {'form': form, 'title': f'Editar {reward.name}'})

@login_required
def redeem_reward(request):
    """Procesar canje de premio"""
    if request.method == 'POST':
        form = RedemptionForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            customer = form.cleaned_data['customer']
            reward = form.cleaned_data['reward']
            
            # Verificar saldo de puntos
            # TODO: Mover lógica de saldo a un método en Customer o Service
            total_points = PointTransaction.objects.filter(customer=customer).aggregate(
                total=Sum('points', default=0)
            )['total'] or 0
            
            redeemed_points = PointTransaction.objects.filter(
                customer=customer, 
                transaction_type='REDEEM'
            ).aggregate(total=Sum('points', default=0))['total'] or 0
            
            # Nota: En mi modelo actual, PointTransaction guarda el valor absoluto en 'points'.
            # Pero en la vista de lista mostré '+' o '-'.
            # Debo asegurarme cómo guardo los canjes.
            # Opción A: Guardar canjes como negativo en la DB.
            # Opción B: Guardar positivo y restar al calcular.
            # Revisando loyalty/models.py: defined 'points' as IntegerField.
            # Revisando loyalty/views.py: No implemented calculation logic yet aside from basic subtraction in template.
            
            # Vamos a asumir que EARN suma y REDEEM resta.
            # Calcularemos el saldo real:
            earned = PointTransaction.objects.filter(customer=customer, transaction_type__in=['EARN', 'ADJUST']).aggregate(s=Sum('points'))['s'] or 0
            redeemed = PointTransaction.objects.filter(customer=customer, transaction_type='REDEEM').aggregate(s=Sum('points'))['s'] or 0
            
            current_balance = earned - redeemed
            
            if current_balance < reward.points_cost:
                messages.error(request, f"Saldo insuficiente. El cliente tiene {current_balance} pts, necesita {reward.points_cost} pts.")
                return redirect('rewards:redeem_reward')
            
            # Proceder con canje atómico
            with transaction.atomic():
                # 1. Crear transacción de puntos (resta)
                point_txn = PointTransaction.objects.create(
                    organization=request.tenant,
                    customer=customer,
                    transaction_type='REDEEM',
                    points=reward.points_cost,
                    description=f"Canje de recompensa: {reward.name}",
                    performed_by=request.user
                )
                
                # 2. Registrar el canje
                Redemption.objects.create(
                    organization=request.tenant,
                    customer=customer,
                    reward=reward,
                    points_spent=reward.points_cost,
                    point_transaction=point_txn,
                    processed_by=request.user
                )
                
                messages.success(request, f"¡Canje exitoso! Se descontaron {reward.points_cost} pts a {customer.full_name}.")
                return redirect('rewards:redemption_history')

    else:
        form = RedemptionForm(tenant=request.tenant)
        
    return render(request, 'rewards/redeem_form.html', {'form': form, 'title': 'Canjear Puntos'})

@login_required
def redemption_history(request):
    """Historial de canjes realizados"""
    redemptions = Redemption.objects.filter(organization=request.tenant).select_related('customer', 'reward', 'processed_by').order_by('-redeemed_at')
    return render(request, 'rewards/redemption_history.html', {'redemptions': redemptions, 'title': 'Historial de Canjes'})
