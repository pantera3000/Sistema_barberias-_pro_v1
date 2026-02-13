import os
import sys

# Monkey-patch para usar PyMySQL en lugar de mysqlclient (evita errores de compilación en cPanel)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# Ruta a tu aplicación
sys.path.insert(0, os.path.dirname(__file__))

# Configura la variable de entorno para los settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
