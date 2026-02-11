
from django import forms
from .models import PointTransaction
from apps.customers.models import Customer

class PointAssignmentForm(forms.ModelForm):
    """Formulario para asignar/quitar puntos manualmente"""
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['customer'].queryset = Customer.objects.filter(organization=tenant)
            
    class Meta:
        model = PointTransaction
        fields = ['customer', 'transaction_type', 'points', 'description']
        widgets = {
            'customer': forms.HiddenInput(),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Bono por cumpleaños'}),
        }
