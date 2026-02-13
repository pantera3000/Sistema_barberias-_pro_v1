import os
import sys

# Ruta a tu aplicación
sys.path.insert(0, os.path.dirname(__file__))

# Configura la variable de entorno para los settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
