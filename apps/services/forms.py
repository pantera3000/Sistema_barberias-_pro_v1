
from django import forms
from .models import Service, ServiceCategory

class ServiceCategoryForm(forms.ModelForm):
    """Formulario para categorías de servicios"""
    class Meta:
        model = ServiceCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ServiceForm(forms.ModelForm):
    """Formulario para servicios"""
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None) # Recibir tenant para filtrar categorías
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = ServiceCategory.objects.filter(organization=tenant)
        
    class Meta:
        model = Service
        fields = ['category', 'name', 'description', 'price', 'duration_minutes', 'points_reward', 'is_active']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'points_reward': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input mb-2'}),
        }
