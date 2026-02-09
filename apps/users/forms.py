
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class WorkerForm(forms.ModelForm):
    """Formulario para gestión de trabajadores por parte del dueño"""
    password = forms.CharField(widget=forms.PasswordInput(), required=False, help_text="Dejar vacío si no se desea cambiar")
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input mb-2'}),
        }
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff_member = True  # Forzar rol de trabajador
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
