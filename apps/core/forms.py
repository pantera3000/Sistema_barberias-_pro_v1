from django import forms
from .models import Organization

class OrganizationSettingsForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'primary_color', 'timezone', 'currency', 'stamp_lock_hours']
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
        }
