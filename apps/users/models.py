
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
    
    @property
    def role_display(self):
        if self.is_superuser: return "Administrador"
        if self.is_owner: return "Dueño"
        if self.is_staff_member: return "Trabajador"
        if self.is_customer: return "Cliente"
        return "Usuario"
    
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

    def has_feature(self, feature_key):
        """Verifica si la organización del usuario tiene habilitada una feature específica"""
        # El Superadmin siempre ve todo (Maestro)
        if self.is_superuser:
            return True
            
        if not self.organization:
            return False
            
        return self.organization.feature_flags.filter(feature_key=feature_key, is_enabled=True).exists()
    @property
    def has_feature_notifications(self):
        return self.has_feature('campaigns.auto_notifications')

    @property
    def has_feature_stamps(self):
        return self.has_feature('stamps')

    @property
    def has_feature_points(self):
        return self.has_feature('points')

    @property
    def has_feature_rewards(self):
        return self.has_feature('rewards')

    @property
    def has_feature_audit(self):
        return self.has_feature('audit')

    @property
    def has_feature_reports(self):
        return self.has_feature('reports')

    @property
    def has_feature_campaigns(self):
        return self.has_feature('campaigns')

    @property
    def has_feature_services(self):
        return self.has_feature('services')

    @property
    def has_feature_appointments(self):
        return self.has_feature('appointments')

    @property
    def has_feature_customers(self):
        return self.has_feature('customers')

    @property
    def has_feature_import_csv(self):
        return self.has_feature('customers.import_csv')

    @property
    def has_feature_export_data(self):
        return self.has_feature('customers.export_data')

    @property
    def has_feature_export_pdf(self):
        return self.has_feature('reports.export_pdf')
