
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Usuario personalizado que puede pertenecer a una organización.
    """
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    
    # Roles
    is_owner = models.BooleanField(default=False, verbose_name="Es Dueño")
    is_staff_member = models.BooleanField(default=False, verbose_name="Es Trabajador")
    is_customer = models.BooleanField(default=False, verbose_name="Es Cliente")
    
    # Relación opcional con organización (Superadmin no tiene orga)
    organization = models.ForeignKey(
        'core.Organization', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='users',
        verbose_name="Organización"
    )

    # Campos adicionales
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Avatar")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.email
