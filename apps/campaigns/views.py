
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import MarketingCampaign, CampaignLog
from .forms import CampaignForm
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
        form = CampaignForm(request.POST)
        if form.is_valid():
            camp = form.save(commit=False)
            camp.organization = request.tenant
            camp.created_by = request.user
            camp.status = 'DRAFT'
            camp.save()
            messages.success(request, "Campaña creada como borrador.")
            return redirect('campaigns:campaign_list')
    else:
        form = CampaignForm()
        
    return render(request, 'campaigns/campaign_form.html', {'form': form, 'title': 'Nueva Campaña'})

@login_required
def campaign_send(request, pk):
    """Simular envío masivo"""
    campaign = get_object_or_404(MarketingCampaign, pk=pk, organization=request.tenant)
    
    if campaign.status == 'SENT':
        messages.warning(request, "Esta campaña ya fue enviada.")
        return redirect('campaigns:campaign_list')
        
    # Filtrar destinatarios
    # TODO: Implementar lógica de segment real (ej: ultimos 30 días, cumpleaños)
    # Por ahora tomamos todos los activos
    customers = Customer.objects.filter(organization=request.tenant, is_active=True)
    
    if not customers.exists():
        messages.error(request, "No hay clientes destinatarios para enviar.")
        return redirect('campaigns:campaign_list')
        
    count = 0
    for customer in customers:
        # Aquí iría la integración con API de WhatsApp/Email (Twilio, SendGrid, etc.)
        # Por ahora solo logueamos
        CampaignLog.objects.create(
            organization=request.tenant,
            campaign=campaign,
            customer=customer,
            status='SENT',
            error_message='Simulación de envío'
        )
        count += 1
        
    campaign.status = 'SENT'
    campaign.sent_at = timezone.now()
    campaign.save()
    
    messages.success(request, f"Campaña enviada exitosamente a {count} clientes.")
    return redirect('campaigns:campaign_list')
