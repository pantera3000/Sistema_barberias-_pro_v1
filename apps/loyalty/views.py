
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import PointTransaction
from .forms import PointAssignmentForm
from apps.customers.models import Customer
from apps.audit.utils import log_action

@login_required
def transaction_list(request):
    """Historial de transacciones de puntos"""
    if not hasattr(request, 'tenant'):
        return redirect('users:login')
        
    transactions = PointTransaction.objects.filter(organization=request.tenant).select_related('customer', 'performed_by')
    
    # Calcular totales por cliente (básico)
    # En un sistema real, esto iría en el modelo Customer o una vista materializada
    
    context = {
        'transactions': transactions,
        'title': 'Historial de Puntos'
    }
    return render(request, 'loyalty/transaction_list.html', context)

@login_required
def assign_points(request):
    """Asignar puntos manualmente"""
    if request.method == 'POST':
        form = PointAssignmentForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.organization = request.tenant
            txn.performed_by = request.user
            txn.save()
            log_action(
                request, 
                'POINTS_ADD', 
                'Puntos', 
                f"Asignados {txn.points} puntos a {txn.customer.full_name}",
                customer=txn.customer
            )
            messages.success(request, f"Transacción registrada: {txn.points} pts a {txn.customer}")
            return redirect('loyalty:transaction_list')
    else:
        form = PointAssignmentForm(tenant=request.tenant)
        
    return render(request, 'loyalty/assign_points_form.html', {'form': form, 'title': 'Asignar Puntos Manualmente'})
