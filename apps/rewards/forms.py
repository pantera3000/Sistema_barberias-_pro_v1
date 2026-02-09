
from django import forms
from .models import Reward, Redemption
from apps.customers.models import Customer

class RewardForm(forms.ModelForm):
    """Formulario para gestionar el catálogo de premios"""
    class Meta:
        model = Reward
        fields = ['name', 'description', 'points_cost', 'is_active', 'valid_until']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'points_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input mb-2'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class RedemptionForm(forms.Form):
    """Formulario para canjear un premio"""
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.none(), 
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Cliente"
    )
    reward = forms.ModelChoiceField(
        queryset=Reward.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Premio a Canjear"
    )

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['customer'].queryset = Customer.objects.filter(organization=tenant)
            self.fields['reward'].queryset = Reward.objects.filter(organization=tenant, is_active=True)
