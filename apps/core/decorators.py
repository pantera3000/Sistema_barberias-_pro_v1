
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def owner_or_superuser_required(view_func):
    """
    Decorador que permite el acceso solo a dueños o superusuarios.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.is_owner:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "No tienes permiso para acceder a esta sección.")
        return redirect('core:dashboard')
        
    return _wrapped_view
