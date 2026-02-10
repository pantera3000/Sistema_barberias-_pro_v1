
from django import forms

from .models import MarketingCampaign, NotificationConfig

class CampaignForm(forms.ModelForm):
    # ... (existing code below)
    class Meta:
        model = MarketingCampaign
        fields = ['name', 'channel', 'subject', 'content', 'target_segment', 'scheduled_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'channel': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Solo para Email'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'target_segment': forms.Select(choices=[('ALL', 'Todos los Clientes Activos')], attrs={'class': 'form-select'}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    template = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Cargar desde Plantilla",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            from .models import CampaignTemplate
            self.fields['template'].queryset = CampaignTemplate.objects.filter(organization=organization)

class NotificationConfigForm(forms.ModelForm):
    class Meta:
        model = NotificationConfig
        fields = [
            'whatsapp_api_url', 'whatsapp_token', 'email_enabled',
            'template_one_left', 'template_completed', 'template_expiring',
            'birthday_enabled', 'birthday_template'
        ]
        widgets = {
            'whatsapp_api_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://api.ultramsg.com/...'}),
            'whatsapp_token': forms.TextInput(attrs={'class': 'form-control'}),
            'email_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'template_one_left': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'template_completed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'template_expiring': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'birthday_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'birthday_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Variables: {nombre}, {negocio}'}),
        }
