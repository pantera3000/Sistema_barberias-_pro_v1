
from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    """Formulario para gestión de clientes"""
    
    DAYS = [(i, i) for i in range(1, 32)]
    MONTHS = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]

    birth_day = forms.ChoiceField(
        label="Día",
        choices=[('', '---')] + DAYS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    birth_month = forms.ChoiceField(
        label="Mes",
        choices=[('', '---')] + MONTHS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone', 'birth_day', 'birth_month', 'birth_year', 'notes', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1990 (Opcional)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input mb-2'}),
        }
