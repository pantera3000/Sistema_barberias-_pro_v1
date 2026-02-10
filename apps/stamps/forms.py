
from django import forms
from .models import StampPromotion, StampCard, StampTransaction
from apps.customers.models import Customer

class StampPromotionForm(forms.ModelForm):
    """Formulario para definir la promoción de sellos"""
    class Meta:
        model = StampPromotion
        fields = ['name', 'primary_color', 'description', 'total_stamps_needed', 'reward', 'reward_description', 'is_active', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'total_stamps_needed': forms.NumberInput(attrs={'class': 'form-control'}),
            'reward': forms.Select(attrs={'class': 'form-select'}),
            'reward_description': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input mb-2'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.rewards.models import Reward
            self.fields['reward'].queryset = Reward.objects.filter(organization=tenant, is_active=True)

class StampAssignmentForm(forms.Form):
    """Formulario para agregar sellos a un cliente manualmente"""
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.none(), 
        widget=forms.HiddenInput(), # Cambiado a Hidden para el modal
        label="Cliente"
    )
    promotion = forms.ModelChoiceField(
        queryset=StampPromotion.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Promoción / Tarjeta"
    )
    quantity = forms.IntegerField(
        initial=1, 
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Cantidad de Sellos"
    )

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['customer'].queryset = Customer.objects.filter(organization=tenant)
            self.fields['promotion'].queryset = StampPromotion.objects.filter(organization=tenant, is_active=True)
            if self.fields['promotion'].queryset.exists():
                self.fields['promotion'].initial = self.fields['promotion'].queryset.first()
