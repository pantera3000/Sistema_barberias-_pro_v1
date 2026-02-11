
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from apps.core.models import Organization, FeatureFlag, UsageLimit
from apps.users.models import User
from .models import SystemAnnouncement, Plan
from .forms import OrganizationForm, SystemAnnouncementForm, PlanForm

from apps.customers.models import Customer

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def master_search(request):
    """Buscador global en todas las tablas y organizaciones"""
    query = request.GET.get('q', '')
    results = {
        'customers': [],
        'users': [],
        'organizations': []
    }
    
    if len(query) >= 3:
        # Buscar Clientes
        results['customers'] = Customer.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(dni__icontains=query)
        ).select_related('organization')[:15]
        
        # Buscar Usuarios (Staff/Dueños)
        results['users'] = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).select_related('organization')[:15]
        
        # Buscar Organizaciones
        results['organizations'] = Organization.objects.filter(
            Q(name__icontains=query) |
            Q(slug__icontains=query)
        )[:15]

    return render(request, 'superadmin/master_search.html', {
        'results': results,
        'query': query,
        'title': 'Buscador Maestro Global'
    })

@user_passes_test(is_superuser)
def plan_list(request):
    """Listado de planes de suscripción"""
    planes = Plan.objects.all()
    return render(request, 'superadmin/plan_list.html', {
        'planes': planes,
        'title': 'Planes de Suscripción'
    })

@user_passes_test(is_superuser)
def plan_create(request):
    """Crear un nuevo plan"""
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan creado correctamente.")
            return redirect('superadmin:plan_list')
    else:
        form = PlanForm()
    return render(request, 'superadmin/plan_form.html', {'form': form, 'title': 'Nuevo Plan'})

@user_passes_test(is_superuser)
def plan_edit(request, pk):
    """Editar un plan existente"""
    plan = get_object_or_404(Plan, pk=pk)
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan actualizado.")
            return redirect('superadmin:plan_list')
    else:
        form = PlanForm(instance=plan)
    return render(request, 'superadmin/plan_form.html', {'form': form, 'title': 'Editar Plan'})


@user_passes_test(is_superuser)
def announcement_list(request):
    """Listado de comunicados globales"""
    announcements = SystemAnnouncement.objects.all()
    return render(request, 'superadmin/announcement_list.html', {
        'announcements': announcements,
        'title': 'Comunicados Globales'
    })

@user_passes_test(is_superuser)
def announcement_create(request):
    """Crear comunicado"""
    if request.method == 'POST':
        form = SystemAnnouncementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Comunicado creado correctamente.")
            return redirect('superadmin:announcement_list')
    else:
        form = SystemAnnouncementForm()
    
    return render(request, 'superadmin/announcement_form.html', {
        'form': form,
        'title': 'Nuevo Comunicado'
    })

@user_passes_test(is_superuser)
def announcement_edit(request, pk):
    """Editar comunicado"""
    announcement = get_object_or_404(SystemAnnouncement, pk=pk)
    if request.method == 'POST':
        form = SystemAnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Comunicado actualizado.")
            return redirect('superadmin:announcement_list')
    else:
        form = SystemAnnouncementForm(instance=announcement)
    
    return render(request, 'superadmin/announcement_form.html', {
        'form': form,
        'title': 'Editar Comunicado'
    })

from apps.audit.models import AuditLog

@user_passes_test(is_superuser)
def global_audit_list(request):
    """
    Listado global de auditoría para el superadmin (todas las organizaciones).
    """
    logs = AuditLog.objects.all().select_related('organization', 'user', 'customer').order_by('-created_at')
    
    # Filtros
    org_id = request.GET.get('organization')
    action = request.GET.get('action')
    
    if org_id:
        logs = logs.filter(organization_id=org_id)
    if action:
        logs = logs.filter(action=action)

    paginator = Paginator(logs, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    organizations = Organization.objects.all()

    return render(request, 'superadmin/global_audit.html', {
        'page_obj': page_obj,
        'organizations': organizations,
        'action_choices': AuditLog.ACTION_CHOICES,
        'title': 'Auditoría Global del Sistema'
    })
from django.core.paginator import Paginator

from django.db.models import Count, Q

@user_passes_test(is_superuser)
def usage_monitor(request):
    """Monitor de consumo de límites para todas las barberías"""
    organizations = Organization.objects.annotate(
        real_customers=Count('customer', distinct=True),
        real_staff=Count('users', filter=Q(users__is_staff_member=True), distinct=True),
        # Podríamos agregar citas reales aquí si el modelo existe
    ).prefetch_related('usage_limits', 'plan')
    
    # Procesar límites para mostrar barras de progreso
    for org in organizations:
        org.usage_stats = []
        limits = {l.limit_type: l for l in org.usage_limits.all()}
        
        # Mapeo de consumo real con límites definidos
        monitored_items = [
            ('customers', org.real_customers, 'Clientes'),
            ('staff', org.real_staff, 'Staff'),
        ]
        
        for limit_type, current, label in monitored_items:
            limit_obj = limits.get(limit_type)
            max_val = limit_obj.limit_value if limit_obj else -1
            
            percentage = 0
            if max_val > 0:
                percentage = min(100, (current / max_val) * 100)
            
            org.usage_stats.append({
                'label': label,
                'current': current,
                'max': max_val,
                'percentage': percentage,
                'status': 'danger' if percentage >= 90 else 'warning' if percentage >= 70 else 'success'
            })

    return render(request, 'superadmin/usage_monitor.html', {
        'organizations': organizations,
        'title': 'Monitor de Consumo y Límites'
    })

@user_passes_test(is_superuser)
def announcement_delete(request, pk):
    """Eliminar comunicado"""
    announcement = get_object_or_404(SystemAnnouncement, pk=pk)
    announcement.delete()
    messages.success(request, "Comunicado eliminado.")
    return redirect('superadmin:announcement_list')


@user_passes_test(is_superuser)
def dashboard(request):
    """
    Dashboard principal del superadministrador: Estadísticas globales.
    """
    total_organizations = Organization.objects.all().count()
    active_organizations = Organization.objects.filter(is_active=True).count()
    total_users = User.objects.count()
    
    # Organizaciones recientes
    recent_organizations = Organization.objects.order_by('-created_at')[:5]
    
    # Estadísticas de usuarios
    staff_users = User.objects.filter(is_staff_member=True).count()
    owner_users = User.objects.filter(is_owner=True).count()
    
    # Actividad reciente global
    recent_logs = AuditLog.objects.all().select_related('organization', 'user')[:8]
    
    context = {
        'total_organizations': total_organizations,
        'active_organizations': active_organizations,
        'total_users': total_users,
        'recent_organizations': recent_organizations,
        'recent_logs': recent_logs,
        'staff_users': staff_users,
        'owner_users': owner_users,
        'title': 'Panel de Control Superadmin'
    }
    return render(request, 'superadmin/dashboard.html', context)

@user_passes_test(is_superuser)
def organization_list(request):
    """
    Listado detallado de todas las organizaciones.
    """
    organizations = Organization.objects.annotate(
        user_count=Count('users')
    ).prefetch_related('feature_flags', 'usage_limits')
    
    context = {
        'organizations': organizations,
        'title': 'Listado de Barberías'
    }
    return render(request, 'superadmin/organization_list.html', context)

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
        
        # Guardar Estado General
        org.is_active = request.POST.get('org_is_active') == 'on'
        org.save()
            
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
