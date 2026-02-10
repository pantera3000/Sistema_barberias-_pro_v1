
from django.apps import AppConfig

class StampsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.stamps'

    def ready(self):
        import apps.stamps.signals
