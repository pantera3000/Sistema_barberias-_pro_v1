import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.customers.models import Tag
from apps.core.models import Organization

def populate_tags():
    orgs = Organization.objects.all()
    default_tags = [
        ('VIP', '#ffd700'),
        ('Cliente Difícil', '#dc3545'),
        ('Barba', '#0d6efd'),
        ('Corte Largo', '#6610f2'),
        ('Frecuente', '#198754')
    ]
    
    for org in orgs:
        for name, color in default_tags:
            Tag.objects.get_or_create(organization=org, name=name, defaults={'color': color})
        print(f"Tags created for {org.name}")

if __name__ == "__main__":
    populate_tags()
