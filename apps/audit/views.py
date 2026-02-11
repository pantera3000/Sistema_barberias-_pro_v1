from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from apps.users.models import User
from .models import AuditLog
from apps.core.decorators import owner_or_superuser_required

@owner_or_superuser_required
def log_list(request):
    """
    Listado de logs de auditoría para el dueño del negocio.
    """
    # Verificar feature flag y rol
    if not request.user.has_feature('audit'):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "El módulo de Auditoría no está activo en tu plan.")
        return redirect('core:dashboard')

    logs = AuditLog.objects.filter(organization=request.tenant).order_by('-created_at')
    
    # Filtros por usuario y acción si se solicitan
    user_id = request.GET.get('user')
    action = request.GET.get('action')
    
    if user_id:
        logs = logs.filter(user_id=user_id)
    if action:
        logs = logs.filter(action=action)

    paginator = Paginator(logs, 50)  # 50 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Usuarios para el filtro
    staff_users = User.objects.filter(organization=request.tenant)

    context = {
        'page_obj': page_obj,
        'title': 'Auditoría y Logs del Sistema',
        'staff_users': staff_users,
        'action_choices': AuditLog.ACTION_CHOICES,
    }
    return render(request, 'audit/log_list.html', context)
