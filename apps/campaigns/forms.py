
from django import forms
from .models import MarketingCampaign

class CampaignForm(forms.ModelForm):
    """Formulario para crear campañas de marketing"""
    
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
