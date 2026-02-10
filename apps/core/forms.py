from django import forms
from .models import Organization

class OrganizationSettingsForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'name', 'primary_color', 'timezone', 'currency', 
            'opening_time', 'closing_time',
            'stamp_lock_hours', 'stamps_expiration_months',
            'double_stamp_mon', 'double_stamp_tue', 'double_stamp_wed', 
            'double_stamp_thu', 'double_stamp_fri', 'double_stamp_sat', 'double_stamp_sun'
        ]
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'opening_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
