
from django import forms
from apps.core.models import Organization, FeatureFlag, UsageLimit
from apps.users.models import User

class OrganizationForm(forms.ModelForm):
    """Formulario para crear/editar organizaciones"""
    owner_email = forms.EmailField(
        label="Email del Dueño", 
        help_text="Correo del usuario que será el dueño. Si no existe, se creará.",
        required=True
    )
    
    class Meta:
        model = Organization
        fields = ['name', 'slug', 'plan', 'timezone', 'currency', 'logo', 'is_active']
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dejar vacío para autogenerar'}),
            'timezone': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['owner_email'].initial = self.instance.owner.email

    def clean_owner_email(self):
        email = self.cleaned_data['owner_email']
        return email

class UsageLimitForm(forms.ModelForm):
    """Formulario para editar un límite específico"""
    class Meta:
        model = UsageLimit
        fields = ['limit_value', 'warning_threshold', 'enforce_limit']
        widgets = {
            'limit_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'warning_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'enforce_limit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
from .models import SystemAnnouncement, Plan

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        exclude = ['created_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_customers': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_staff': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_appointments_monthly': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_campaigns_monthly': forms.NumberInput(attrs={'class': 'form-control'}),
            'enable_whatsapp': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_reports': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_audit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_stamps': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_points': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_appointments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SystemAnnouncementForm(forms.ModelForm):
    class Meta:
        model = SystemAnnouncement
        fields = ['title', 'content', 'style', 'is_active', 'show_to_owners', 'show_to_staff', 'expires_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'style': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_to_owners': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_to_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
