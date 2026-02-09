
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
        fields = ['name', 'slug', 'timezone', 'currency', 'logo', 'is_active']
        widgets = {
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
