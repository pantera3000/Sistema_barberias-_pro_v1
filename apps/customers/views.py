from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.db.models import Q
from django.db import transaction
from .models import Customer
from .forms import CustomerForm
# Importaciones para auto-asignación
from apps.stamps.models import StampPromotion, StampCard

@login_required
def customer_list(request):
    """Listar clientes de la organización actual"""
    if not hasattr(request, 'tenant') or not request.tenant:
         # TODO: Manejar mejor este caso
         return redirect('users:login')
         
    customers = Customer.objects.filter(organization=request.tenant)
    context = {
        'customers': customers,
        'title': 'Gestión de Clientes'
    }
    return render(request, 'customers/customer_list.html', context)

@login_required
def customer_create(request):
    """Crear nuevo cliente"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                customer = form.save(commit=False)
                customer.organization = request.tenant
                customer.save()
                
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
        form = CustomerForm()
        
    return render(request, 'customers/customer_form.html', {'form': form, 'title': 'Nuevo Cliente'})

@login_required
def customer_edit(request, pk):
    """Editar cliente existente"""
    # Filtrar por tenant para seguridad!
    customer = get_object_or_404(Customer, pk=pk, organization=request.tenant)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente actualizado.")
            return redirect('customers:customer_list')
    else:
        form = CustomerForm(instance=customer)
        
    return render(request, 'customers/customer_form.html', {'form': form, 'title': f'Editar {customer.full_name}'})

@login_required
def customer_delete(request, pk):
    """Eliminar (desactivar) cliente"""
    customer = get_object_or_404(Customer, pk=pk, organization=request.tenant)
    customer.delete() # O lógica soft-delete si se prefiere
    messages.success(request, "Cliente eliminado.")
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
