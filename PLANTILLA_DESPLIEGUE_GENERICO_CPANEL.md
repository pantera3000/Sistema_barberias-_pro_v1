# Guía Genérica: Despliegue Django en Hosting Compartido (cPanel)

Esta guía sirve como plantilla estándar para desplegar aplicaciones Django en entornos de hosting compartido con cPanel (como Namecheap, Bluehost, etc.).

## 📋 Prerrequisitos del Servidor

1.  **Acceso SSH** habilitado en cPanel.
2.  **Setup Python App** disponible en cPanel.
3.  **Base de Datos MySQL/PostgreSQL** creada.

## 📝 Variables de Configuración (Reemplazar)

Define estos valores antes de empezar:

- **[USUARIO_CPANEL]:** Tu usuario de cPanel (ej. `miusuario`).
- **[NOMBRE_APP]:** Nombre de la carpeta donde vivirá la app (ej. `mi_proyecto_web`).
- **[DOMINIO]:** El dominio o subdominio donde se alojará (ej. `app.midominio.com`).
- **[VERSION_PYTHON]:** La versión seleccionada en "Setup Python App" (ej. `3.9`, `3.11`, `3.13`).
- **[URL_REPO]:** URL HTTPS de tu repositorio Git.
- **[RAMA]:** Rama a desplegar (ej. `main`, `master`, `production`).
- **[NOMBRE_PROYECTO_DJANGO]:** El nombre de la carpeta interna que contiene `settings.py`.

---

## 🚀 Pasos de Despliegue

### 1. Conectar via SSH

```bash
ssh [USUARIO_CPANEL]@[DOMINIO]
# Ingresa tu contraseña de cPanel si se solicita
```

### 2. Clonar el Repositorio

Navega a la raíz y clona tu proyecto en la carpeta destino.

```bash
# Asegúrate de estar en el home o la carpeta raíz deseada
cd /home/[USUARIO_CPANEL]

# Clona el repositorio (incluyendo el punto al final para clonar EN la carpeta creada si ya existe, o crea la carpeta primero)
# Opción A: Si la carpeta NO existe (más común en primer despliegue manual):
git clone [URL_REPO] [NOMBRE_APP]

# Opción B: Si la carpeta YA fue creada por cPanel (asegúrate que esté vacía):
cd [NOMBRE_APP]
git clone [URL_REPO] .
```

Selecciona tu rama estable:

```bash
cd /home/[USUARIO_CPANEL]/[NOMBRE_APP]
git checkout [RAMA]
```

### 3. Identificar y Activar Virtualenv

El entorno virtual es creado automáticamente por cPanel cuando configuras la "Python App". La ruta suele seguir este patrón:

`/home/[USUARIO_CPANEL]/virtualenv/[NOMBRE_APP]/[VERSION_PYTHON]`

Actívalo e instala las dependencias:

```bash
source /home/[USUARIO_CPANEL]/virtualenv/[NOMBRE_APP]/[VERSION_PYTHON]/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install mysqlclient  # Si usas MySQL (a veces necesario instalar manualmente)
```

### 4. Configurar Variables de Entorno (.env)

Crea el archivo `.env` en la raíz de tu proyecto. **Importante:** Usa `cat` para evitar problemas de codificación (BOM) que a veces ocurren con editores de texto.

```bash
cd /home/[USUARIO_CPANEL]/[NOMBRE_APP]

cat > .env << 'EOF'
DEBUG=False
SECRET_KEY=genera-una-clave-segura-y-larga-aqui
ALLOWED_HOSTS=[DOMINIO],www.[DOMINIO]
# Configuración de Base de Datos (Ejemplo MySQL)
DB_NAME=[NOMBRE_BASE_DATOS]
DB_USER=[USUARIO_BASE_DATOS]
DB_PASSWORD=[PASSWORD_BASE_DATOS]
DB_HOST=localhost
DB_PORT=3306
EOF
```

### 5. Configurar Base de Datos y Archivos Estáticos

Ejecuta las migraciones y recolecta los archivos estáticos.

```bash
# Migraciones
python manage.py migrate

# Estáticos (CSS, JS, Imágenes del sistema)
python manage.py collectstatic --noinput

# Crear superusuario (solo la primera vez)
python manage.py createsuperuser
```

### 6. Configurar Carpetas de Medios y Temporales

Asegúrate de que las carpetas para archivos subidos por usuarios y archivos temporales existan.

```bash
mkdir -p public/static  # Si tu STATIC_ROOT apunta aquí
mkdir -p public/media   # Si tu MEDIA_ROOT apunta aquí
mkdir -p tmp            # Para el archivo de reinicio
chmod -R 755 public
```

### 7. Configuración de `passenger_wsgi.py`

Este archivo es el punto de entrada para cPanel (Passenger). Asegúrate de que apunte a tu `wsgi.py`.

Edita `/home/[USUARIO_CPANEL]/[NOMBRE_APP]/passenger_wsgi.py`:

```python
import os
import sys

# Ruta a tu aplicación
sys.path.insert(0, os.path.dirname(__file__))

# Configura la variable de entorno para los settings
os.environ['DJANGO_SETTINGS_MODULE'] = '[NOMBRE_PROYECTO_DJANGO].settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 8. Reiniciar Aplicación

Para aplicar los cambios, debes tocar el archivo `restart.txt`.

```bash
touch tmp/restart.txt
```

*Alternativa:* Desde cPanel ve a **Setup Python App → [Tu App] → Restart**.

### 9. Verificar

Espera unos segundos y visita `https://[DOMINIO]`.

---

## 🔄 Flujo de Actualización (Update)

Para futuros despliegues o actualizaciones:

```bash
# 1. Ir a la carpeta
cd /home/[USUARIO_CPANEL]/[NOMBRE_APP]

# 2. Traer cambios
git pull origin [RAMA]

# 3. Activar entorno
source /home/[USUARIO_CPANEL]/virtualenv/[NOMBRE_APP]/[VERSION_PYTHON]/bin/activate

# 4. Actualizar dependencias y DB
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# 5. Reiniciar
touch tmp/restart.txt
```

## 🐛 Debugging en Producción

Si obtienes un "Internal Server Error" o la página no carga:

1.  **Ver logs de error estándar:**
    ```bash
    tail -n 50 /home/[USUARIO_CPANEL]/[NOMBRE_APP]/stderr.log
    ```
2.  **Ver logs específicos de Django (si los configuraste):**
    ```bash
    tail -f /home/[USUARIO_CPANEL]/[NOMBRE_APP]/django_errors.log
    ```
3.  **Verificar `.env`:** Asegúrate de que no tenga caracteres extraños y que las credenciales de la BD sean correctas.

## 🔒 Post-Despliegue: Seguridad

1.  **SSL:** Activa "Run AutoSSL" en cPanel → SSL/TLS Status.
2.  **Forzar HTTPS:** En tu `settings.py` (o `settings_production.py`), asegúrate de tener:
    ```python
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    ```
