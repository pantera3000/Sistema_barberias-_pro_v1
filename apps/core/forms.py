from django import forms
from .models import Organization
import zoneinfo

# Lista de zonas comunes para facilitar al usuario (puedes ampliarla)
COMMON_TIMEZONES = [
    ('America/Lima', 'Perú (Lima)'),
    ('America/Bogota', 'Colombia (Bogotá)'),
    ('America/Mexico_City', 'México (CDMX)'),
    ('America/Santiago', 'Chile (Santiago)'),
    ('America/Argentina/Buenos_Aires', 'Argentina (Buenos Aires)'),
    ('America/Guayaquil', 'Ecuador (Guayaquil)'),
    ('America/Caracas', 'Venezuela (Caracas)'),
    ('America/La_Paz', 'Bolivia (La Paz)'),
    ('America/Asuncion', 'Paraguay (Asunción)'),
    ('America/Montevideo', 'Uruguay (Montevideo)'),
    ('America/Panama', 'Panamá'),
    ('America/Costa_Rica', 'Costa Rica'),
    ('America/Guatemala', 'Guatemala'),
    ('America/El_Salvador', 'El Salvador'),
    ('America/Tegucigalpa', 'Honduras'),
    ('America/Managua', 'Nicaragua'),
    ('America/Santo_Domingo', 'Rep. Dominicana'),
    ('America/Puerto_Rico', 'Puerto Rico'),
    ('America/New_York', 'USA (New York)'),
    ('America/Chicago', 'USA (Chicago)'),
    ('America/Los_Angeles', 'USA (Los Angeles)'),
    ('Europe/Madrid', 'España (Madrid)'),
    ('UTC', 'UTC / GMT'),
]

class OrganizationSettingsForm(forms.ModelForm):
    timezone = forms.ChoiceField(
        choices=COMMON_TIMEZONES, 
        label="Zona Horaria",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Organization
        fields = [
            'name', 'primary_color', 'timezone', 'currency', 
            'opening_time', 'closing_time',
            'stamp_lock_hours', 'stamp_lock_minutes', 'stamps_expiration_months',
            'double_stamp_mon', 'double_stamp_tue', 'double_stamp_wed', 
            'double_stamp_thu', 'double_stamp_fri', 'double_stamp_sat', 'double_stamp_sun'
        ]
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'opening_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
