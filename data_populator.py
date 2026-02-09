
import os
import django

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import Organization
from apps.users.models import User
from apps.customers.models import Customer
from apps.services.models import Service, ServiceCategory
from apps.loyalty.models import PointTransaction
from apps.stamps.models import StampPromotion, StampCard
from apps.rewards.models import Reward
from django.utils import timezone
from decimal import Decimal
from django.db import transaction

def populate():
    # 1. Nullify organization link in users to allow user deletion
    User.objects.all().update(organization=None)
    # 2. Delete data in correct order to avoid ProtectedError
    print("Deleting dependent data...")
    StampCard.objects.all().delete()
    StampPromotion.objects.all().delete()
    PointTransaction.objects.all().delete()
    Reward.objects.all().delete()
    Customer.objects.all().delete()
    
    # Now delete organizations
    Organization.objects.filter(name__in=['Premium Barbershop', 'Barbería Demo']).delete()
    # 3. Delete the specific users
    User.objects.filter(email__in=['dueno@demo.com', 'barbero1@demo.com', 'cliente_app@demo.com']).delete()
    print("Cleanup complete.")
    # 2. Superadmin
    if not User.objects.filter(username='admin').exists() and not User.objects.filter(email='admin@example.com').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Superadmin created: admin / admin123")
    else:
        print("Superadmin already exists.")

    # 3. Owner (Create user first, then org)
    user_owner, created = User.objects.get_or_create(
        email='dueno@demo.com',
        defaults={'username': 'dueno@demo.com', 'first_name': 'Juan', 'last_name': 'Dueño', 'is_owner': True}
    )
    if created:
        user_owner.set_password('demo123')
        user_owner.save()
    
    # Now create Org with owner
    org, _ = Organization.objects.get_or_create(
        name='Premium Barbershop',
        defaults={'slug': 'premium-barber', 'is_active': True, 'currency': 'PEN', 'owner': user_owner}
    )
    
    # Update owner with org link
    user_owner.organization = org
    user_owner.save()
    
    print(f"Org: {org.name} linked to {user_owner.email}")

    # 4. Staff / Worker
    staff, created = User.objects.get_or_create(
        email='barbero1@demo.com',
        defaults={'username': 'barbero1@demo.com', 'first_name': 'Carlos', 'last_name': 'Barbero', 'is_staff_member': True, 'organization': org}
    )
    if created:
        staff.set_password('demo123')
        staff.save()
    print("Staff created: barbero1@demo.com / demo123")

    # 5. Customer User (App Access)
    cust_user, created = User.objects.get_or_create(
        email='cliente_app@demo.com',
        defaults={'username': 'cliente_app@demo.com', 'first_name': 'Pedro', 'last_name': 'Cliente', 'is_customer': True, 'organization': org}
    )
    if created:
        cust_user.set_password('demo123')
        cust_user.save()
    print("Customer User created: cliente_app@demo.com / demo123")

    # 6. Customer Records
    customers = [
        ('Juan', 'Pérez', '999111222', 15, 8, 1985), # Full
        ('Andrés', 'García', '999333444', 22, 12, None), # Partial
        ('Luis', 'Sánchez', '999555666', 5, 5, 2000), # Full
    ]
    cust_objs = []
    for f, l, p, d, m, y in customers:
        c, _ = Customer.objects.get_or_create(
            first_name=f, last_name=l, organization=org,
            defaults={
                'phone': p, 
                'email': f'{f.lower()}@gmail.com',
                'birth_day': d,
                'birth_month': m,
                'birth_year': y
            }
        )
        cust_objs.append(c)
    print("Customers records created")

    # 7. Services
    cat_corte, _ = ServiceCategory.objects.get_or_create(name='Cortes', organization=org)
    cat_barba, _ = ServiceCategory.objects.get_or_create(name='Barba', organization=org)

    services_data = [
        (cat_corte, 'Corte Clásico', 25.00, 30, 10),
        (cat_corte, 'Corte Fade / Degradado', 35.00, 45, 15),
        (cat_barba, 'Afeitado Toalla Caliente', 20.00, 20, 5),
        (cat_barba, 'Perfilado de Barba', 15.00, 15, 5),
    ]
    for cat, name, price, dur, pts in services_data:
        Service.objects.get_or_create(
            name=name, organization=org,
            defaults={'category': cat, 'price': Decimal(price), 'duration_minutes': dur, 'points_reward': pts}
        )
    print("Services created")

    # 8. Stamp Promotion
    promo, _ = StampPromotion.objects.get_or_create(
        name='Tarjeta de Fidelidad 10+1',
        organization=org,
        defaults={
            'description': 'Cada 10 servicios un corte clásico gratis',
            'total_stamps_needed': 10,
            'reward_description': 'Corte Clásico Gratis',
            'is_active': True
        }
    )
    print("Stamp Promotion created")

    # 9. Initial data for Dashboard
    # Points for a client
    PointTransaction.objects.get_or_create(
        customer=cust_objs[0], organization=org, transaction_type='EARN', points=150,
        defaults={'description': 'Carga inicial demo', 'performed_by': user_owner}
    )
    
    # Stamp card for a client
    StampCard.objects.get_or_create(
        customer=cust_objs[1], promotion=promo, organization=org,
        defaults={'current_stamps': 3}
    )

    # 10. Rewards Catalog
    Reward.objects.get_or_create(
        name='Corte Clásico Gratis', organization=org,
        defaults={'points_cost': 200, 'description': 'Canjea tus puntos por un servicio gratis'}
    )
    Reward.objects.get_or_create(
        name='50% Descuento en Barba', organization=org,
        defaults={'points_cost': 80, 'description': 'Medio precio en tu próximo perfilado'}
    )

    print("--- POPULATION COMPLETE ---")

if __name__ == "__main__":
    populate()
