
from django import forms
from .models import Customer, Tag

class CustomerForm(forms.ModelForm):
    """Formulario para gestión de clientes shadow-sm"""
    
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

    auto_assign_stamps = forms.BooleanField(
        label="Asignar tarjeta de sellos automáticamente",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    tags = forms.ModelMultipleChoiceField(
        label="Etiquetas",
        queryset=Tag.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['tags'].queryset = Tag.objects.filter(organization=tenant)

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone', 'birth_day', 'birth_month', 'birth_year', 'notes', 'tags', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1990 (Opcional)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input mb-2'}),
        }
