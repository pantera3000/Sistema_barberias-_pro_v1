
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Service, ServiceCategory
from .forms import ServiceForm, ServiceCategoryForm
from apps.core.decorators import owner_or_superuser_required

@owner_or_superuser_required
def service_list(request):
    """Listar servicios y categorías"""
    if not hasattr(request, 'tenant') or not request.tenant:
        return redirect('users:login')
        
    services = Service.objects.filter(organization=request.tenant).select_related('category')
    categories = ServiceCategory.objects.filter(organization=request.tenant)
    
    context = {
        'services': services,
        'categories': categories,
        'title': 'Catálogo de Servicios'
    }
    return render(request, 'services/service_list.html', context)

@owner_or_superuser_required
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            service = form.save(commit=False)
            service.organization = request.tenant
            service.save()
            messages.success(request, f"Servicio '{service.name}' creado.")
            return redirect('services:service_list')
    else:
        form = ServiceForm(tenant=request.tenant)
        
    return render(request, 'services/service_form.html', {'form': form, 'title': 'Nuevo Servicio'})

@owner_or_superuser_required
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk, organization=request.tenant)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service, tenant=request.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Servicio actualizado.")
            return redirect('services:service_list')
    else:
        form = ServiceForm(instance=service, tenant=request.tenant)
        
    return render(request, 'services/service_form.html', {'form': form, 'title': f'Editar {service.name}'})

@owner_or_superuser_required
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk, organization=request.tenant)
    service.delete()
    messages.success(request, "Servicio eliminado.")
    return redirect('services:service_list')

# --- Categories ---

@owner_or_superuser_required
def category_list(request):
    categories = ServiceCategory.objects.filter(organization=request.tenant)
    if request.method == 'POST':
        form = ServiceCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.organization = request.tenant
            cat.save()
            messages.success(request, "Categoría creada.")
            return redirect('services:category_list')
    else:
        form = ServiceCategoryForm()
        
    return render(request, 'services/category_list.html', {'categories': categories, 'form': form, 'title': 'Categorías'})

@owner_or_superuser_required
def category_delete(request, pk):
    cat = get_object_or_404(ServiceCategory, pk=pk, organization=request.tenant)
    cat.delete()
    messages.success(request, "Categoría eliminada.")
    return redirect('services:category_list')
