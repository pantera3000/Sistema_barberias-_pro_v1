
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from apps.core.models import Organization, FeatureFlag, UsageLimit
from apps.users.models import User
from .forms import OrganizationForm

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def dashboard(request):
    """
    Dashboard principal del superadministrador.
    """
    organizations = Organization.objects.annotate(
        user_count=Count('users')
    ).prefetch_related('feature_flags', 'usage_limits')
    
    total_organizations = organizations.count()
    active_organizations = organizations.filter(is_active=True).count()
    total_users = User.objects.count()
    
    context = {
        'organizations': organizations,
        'total_organizations': total_organizations,
        'active_organizations': active_organizations,
        'total_users': total_users,
    }
    return render(request, 'superadmin/dashboard.html', context)

@user_passes_test(is_superuser)
def organization_create(request):
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['owner_email']
            user, created = User.objects.get_or_create(
                email=email, 
                defaults={'username': email, 'is_owner': True}
            )
            if created:
                user.set_password('123456') # Default password, should change
                user.save()
                messages.info(request, f"Usuario creado: {email} (Pass: 123456)")
            
            org = form.save(commit=False)
            org.owner = user
            org.save()
            
            # Asociar usuario a la organización si no tenía una
            if not user.organization:
                user.organization = org
                user.is_owner = True
                user.save()
            
            messages.success(request, f"Organización '{org.name}' creada exitosamente.")
            return redirect('superadmin:dashboard')
    else:
        form = OrganizationForm()
    
    return render(request, 'superadmin/organization_form.html', {'form': form, 'title': 'Nueva Organización'})

@user_passes_test(is_superuser)
def organization_edit(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=org)
        if form.is_valid():
            email = form.cleaned_data['owner_email']
            user, created = User.objects.get_or_create(
                email=email, 
                defaults={'username': email, 'is_owner': True}
            )
            org = form.save(commit=False)
            org.owner = user
            org.save()
            messages.success(request, f"Organización '{org.name}' actualizada.")
            return redirect('superadmin:dashboard')
    else:
        form = OrganizationForm(instance=org)
    
    return render(request, 'superadmin/organization_form.html', {'form': form, 'title': f'Editar {org.name}'})

@user_passes_test(is_superuser)
def organization_features(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    
    # Asegurar que existan todos los flags
    all_features = dict(FeatureFlag.FEATURE_CHOICES)
    for key, label in all_features.items():
        FeatureFlag.objects.get_or_create(organization=org, feature_key=key)
        
    # Asegurar que existan todos los límites
    all_limits = dict(UsageLimit.LIMIT_TYPES)
    for key, label in all_limits.items():
        UsageLimit.objects.get_or_create(organization=org, limit_type=key, defaults={'limit_value': 0})

    if request.method == 'POST':
        # Guardar Features
        feature_flags = org.feature_flags.all()
        for flag in feature_flags:
            enabled_key = f"feature_{flag.id}"
            flag.is_enabled = request.POST.get(enabled_key) == 'on'
            flag.save()
            
        # Guardar Límites
        usage_limits = org.usage_limits.all()
        for limit in usage_limits:
            limit.limit_value = request.POST.get(f"limit_value_{limit.id}", 0)
            limit.warning_threshold = request.POST.get(f"limit_warning_{limit.id}", 80)
            limit.enforce_limit = request.POST.get(f"limit_enforce_{limit.id}") == 'on'
            limit.save()
            
        messages.success(request, "Configuración actualizada correctamente.")
        return redirect('superadmin:organization_features', pk=pk)
        
    # Agrupar features por módulo para el template
    features = org.feature_flags.all().order_by('feature_key')
    modules_list = [f for f in features if '.' not in f.feature_key]
    sub_features = [f for f in features if '.' in f.feature_key]
    
    # Añadir lista de sub-features a cada objeto módulo (en memoria)
    for m in modules_list:
        m.subs = [s for s in sub_features if s.feature_key.startswith(f"{m.feature_key}.")]
    
    limits = org.usage_limits.all()
    
    context = {
        'org': org,
        'modules': modules_list,
        'limits': limits,
        'title': f'Configurar: {org.name}'
    }
    return render(request, 'superadmin/organization_features.html', context)
