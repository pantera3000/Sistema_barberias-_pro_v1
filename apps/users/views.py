
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .forms import WorkerForm

from apps.core.decorators import owner_or_superuser_required

User = get_user_model()

@owner_or_superuser_required
def worker_list(request):
    """Listar trabajadores de la organización actual"""
    if not request.user.organization:
        return redirect('users:login')
        
    workers = User.objects.filter(
        organization=request.user.organization, 
        is_staff_member=True
    ).exclude(pk=request.user.pk) # Excluirse a sí mismo si se desea
    
    return render(request, 'users/worker_list.html', {'workers': workers})

@owner_or_superuser_required
def worker_create(request):
    """Crear nuevo trabajador en la organización"""
        
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            worker = form.save(commit=False)
            worker.organization = request.user.organization
            worker.username = worker.email # Usar email como username
            worker.is_staff_member = True
            worker.save()
            messages.success(request, f"Trabajador {worker.first_name} creado.")
            return redirect('users:worker_list')
    else:
        form = WorkerForm()
        
    return render(request, 'users/worker_form.html', {'form': form, 'title': 'Nuevo Trabajador'})

@owner_or_superuser_required
def worker_edit(request, pk):
    """Editar trabajador existente"""
        
    worker = get_object_or_404(User, pk=pk, organization=request.user.organization)
    
    if request.method == 'POST':
        form = WorkerForm(request.POST, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, f"Trabajador actualizado.")
            return redirect('users:worker_list')
    else:
        form = WorkerForm(instance=worker)
        
    return render(request, 'users/worker_form.html', {'form': form, 'title': f'Editar {worker.first_name}'})
