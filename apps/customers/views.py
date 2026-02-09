from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from .models import Customer
from .forms import CustomerForm

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
            customer = form.save(commit=False)
            customer.organization = request.tenant # Asignación explícita aunque TenantAwareModel lo maneja
            customer.save()
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
