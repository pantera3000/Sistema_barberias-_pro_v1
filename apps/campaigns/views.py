
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import MarketingCampaign, CampaignLog, NotificationConfig
from .forms import CampaignForm, NotificationConfigForm
from apps.core.models import FeatureFlag

@login_required
def notification_settings(request):
    """Configuración de notificaciones automáticas (Engagement)"""
    # Verificar si el negocio tiene activada esta feature (Flag de Superadmin)
    flag = FeatureFlag.objects.filter(
        organization=request.tenant, 
        feature_key='campaigns.auto_notifications', 
        is_enabled=True
    ).exists()
    
    if not flag:
        messages.error(request, "Esta funcionalidad no está incluida en tu plan actual. Contacta a soporte.")
        return redirect('core:dashboard')

    config, created = NotificationConfig.objects.get_or_create(organization=request.tenant)

    if request.method == 'POST':
        form = NotificationConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración de notificaciones actualizada.")
            return redirect('campaigns:notification_settings')
    else:
        form = NotificationConfigForm(instance=config)

    return render(request, 'campaigns/notification_settings.html', {
        'form': form,
        'title': 'Notificaciones Automáticas (Engagement)'
    })
from apps.customers.models import Customer

@login_required
def campaign_list(request):
    """Listar campañas"""
    if not hasattr(request, 'tenant'):
        return redirect('users:login')
        
    campaigns = MarketingCampaign.objects.filter(organization=request.tenant)
    return render(request, 'campaigns/campaign_list.html', {'campaigns': campaigns, 'title': 'Campañas de Marketing'})

@login_required
def campaign_create(request):
    """Crear nueva campaña"""
    if request.method == 'POST':
        form = CampaignForm(request.POST, organization=request.tenant)
        if form.is_valid():
            camp = form.save(commit=False)
            camp.organization = request.tenant
            camp.created_by = request.user
            camp.status = 'DRAFT'
            camp.save()
            messages.success(request, "Campaña creada como borrador.")
            return redirect('campaigns:campaign_list')
    else:
        form = CampaignForm(organization=request.tenant)
        
    return render(request, 'campaigns/campaign_form.html', {
        'form': form, 
        'title': 'Nueva Campaña',
        'is_edit': False
    })

@login_required
def campaign_edit(request, pk):
    """Editar una campaña existente (solo si es borrador)"""
    campaign = get_object_or_404(MarketingCampaign, pk=pk, organization=request.tenant)
    
    if campaign.status != 'DRAFT':
        messages.warning(request, "Solo se pueden editar campañas en estado Borrador.")
        return redirect('campaigns:campaign_list')
        
    if request.method == 'POST':
        form = CampaignForm(request.POST, instance=campaign, organization=request.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaña actualizada.")
            return redirect('campaigns:campaign_list')
    else:
        form = CampaignForm(instance=campaign, organization=request.tenant)
        
    return render(request, 'campaigns/campaign_form.html', {
        'form': form, 
        'title': f'Editar: {campaign.name}',
        'is_edit': True
    })

from .models import CampaignTemplate

@login_required
def get_template_content(request, pk):
    """Obtener el contenido de una plantilla vía AJAX"""
    template = get_object_or_404(CampaignTemplate, pk=pk, organization=request.tenant)
    return JsonResponse({'content': template.content})

@login_required
def campaign_send(request, pk):
    """Prepara la campaña para el envío manual"""
    campaign = get_object_or_404(MarketingCampaign, pk=pk, organization=request.tenant)
    
    if campaign.status == 'SENT':
        messages.warning(request, "Esta campaña ya fue enviada por completo.")
        return redirect('campaigns:campaign_list')
        
    # Filtrar destinatarios según el segmento
    # Por ahora solo soportamos ALL
    customers = Customer.objects.filter(organization=request.tenant, is_active=True)
    
    if not customers.exists():
        messages.error(request, "No hay clientes destinatarios para enviar.")
        return redirect('campaigns:campaign_list')
        
    # Crear logs pendientes si no existen
    existing_logs = CampaignLog.objects.filter(campaign=campaign).values_list('customer_id', flat=True)
    logs_to_create = []
    for customer in customers:
        if customer.id not in existing_logs:
            logs_to_create.append(CampaignLog(
                organization=request.tenant,
                campaign=campaign,
                customer=customer,
                status='PENDING'
            ))
    
    if logs_to_create:
        CampaignLog.objects.bulk_create(logs_to_create)
        
    campaign.status = 'SCHEDULED'
    campaign.save()
    
    return redirect('campaigns:campaign_detail', pk=campaign.id)

@login_required
def campaign_detail(request, pk):
    """Pantalla de ejecución manual de la campaña"""
    campaign = get_object_or_404(MarketingCampaign, pk=pk, organization=request.tenant)
    logs = campaign.logs.all().select_related('customer').order_by('status', 'customer__first_name')
    
    # Progreso
    total = logs.count()
    sent = logs.filter(status='SENT').count()
    progress_pct = (sent / total * 100) if total > 0 else 0

    return render(request, 'campaigns/campaign_detail.html', {
        'campaign': campaign,
        'logs': logs,
        'total': total,
        'sent': sent,
        'progress_pct': progress_pct,
        'title': f"Enviando: {campaign.name}"
    })

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def update_log_status(request, log_id):
    """Actualiza el estado de un envío individual vía AJAX"""
    log = get_object_or_404(CampaignLog, pk=log_id, organization=request.tenant)
    new_status = request.POST.get('status', 'SENT')
    
    log.status = new_status
    log.sent_at = timezone.now()
    log.save()
    
    # Si todos los logs están enviados, marcar campaña como enviada
    campaign = log.campaign
    if not campaign.logs.filter(status='PENDING').exists():
        campaign.status = 'SENT'
        campaign.sent_at = timezone.now()
        campaign.save()
    
    return JsonResponse({'status': 'ok', 'new_status': log.status})
