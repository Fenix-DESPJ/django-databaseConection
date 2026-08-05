# M&A Barber Shop — Guía de instalación

Instrucciones para dejar el proyecto funcionando desde cero en cualquier equipo nuevo (Windows).

## 1. Requisitos previos (antes de tocar Python)

- Python 3.11 instalado (⚠️ no uses 3.12+ ni 3.13+ todavía — mediapipe con el legacy API `mp.solutions` no es estable ahí).
- MariaDB 10.4 corriendo, con la base de datos del proyecto ya creada.
- Git (si vas a clonar el repo).

Verificá tu versión de Python antes de crear el entorno virtual:

```bash
py -0
```

Si ves varias versiones instaladas, asegurate de usar la 3.11 al crear el venv (ver paso 2).

## 2. Crear y activar el entorno virtual

```bash
cd ruta\a\tu\proyecto

# Crear el venv específicamente con Python 3.11
py -3.11 -m venv .venv

# Activar (PowerShell)
venv\Scripts\activate

# Si PowerShell bloquea la ejecución de scripts, corré esto una vez y volvé a intentar:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Vas a saber que está activo porque tu terminal muestra `(.venv)` al inicio de la línea.

## 3. Instalar todas las dependencias

Con el venv activo:

```bash
python -m pip install --upgrade pip
python -m pip install "django>=4.2,<5.0" pymysql mysqlclient django-widget-tweaks xhtml2pdf fpdf2 pandas openpyxl pillow opencv-python-headless mediapipe==0.10.14 django-allauth PyJWT google-auth
```

O directamente con el archivo de dependencias:

```bash
pip install -r requirements.txt
```

Esto instala todo lo que el proyecto necesita: Django, el conector de MySQL, MediaPipe/OpenCV para el análisis de rostro, las librerías de generación de PDF/Excel, y (desde agosto 2026) **`django-allauth`** para el login con Google.

> ⚠️ **Cambio importante (agosto 2026):** el proyecto migró del flujo manual de Google Identity Services (`google.oauth2.id_token`, paquete `google-auth`) a **`django-allauth`** con el flujo de redirección clásico de OAuth2. Ya **no** se necesita el paquete `google-auth` — si lo tenías instalado de una versión anterior del proyecto, podés desinstalarlo (`pip uninstall google-auth`), aunque dejarlo tampoco rompe nada.

### Verificación rápida (correr estos 4 comandos después de instalar)

```bash
python -c "import django; print('Django:', django.get_version())"
python -c "import mediapipe as mp; print(mp.solutions.face_mesh); print('MediaPipe OK')"
python -c "import MySQLdb; print('mysqlclient OK')"
python -c "import allauth; print('django-allauth OK')"
python -c "import jwt; print('PyJWT OK')"
python -c "import google.auth; print('google-auth OK')"
```

Deberías ver:

```
Django: 4.2.30
Una línea con <module 'mediapipe.python.solutions.face_mesh' ...> seguida de MediaPipe OK
mysqlclient OK
django-allauth OK
PyJWT OK
google-auth OK
```

Si alguno de estos 4 falla, no sigas — resolvé eso primero (ver sección de problemas comunes más abajo).

## 4. Configuración de `settings.py` para django-allauth

Estas apps y ajustes deben estar presentes (si estás configurando el proyecto desde cero, agrégalos):

```python
INSTALLED_APPS = [
    # ... tus apps normales de Django ...
    'django.contrib.sites',                          # requerido por allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # ... tus apps del proyecto (usuarios, negocio, servicios, reservas) ...
]

MIDDLEWARE = [
    # ...
    'allauth.account.middleware.AccountMiddleware',   # agregar después de AuthenticationMiddleware
    # ...
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
    }
}

LOGIN_REDIRECT_URL = '/'
SOCIALACCOUNT_ADAPTER = 'usuarios.adapters.MiSocialAccountAdapter'

# Salta la pantalla intermedia de confirmación de allauth: el botón de
# "Continuar con Google" va directo al selector de cuenta de Google.
SOCIALACCOUNT_LOGIN_ON_GET = True
```

`usuarios/urls.py` debe incluir las rutas de allauth en el `urls.py` raíz del proyecto:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # ... el resto de tus rutas ...
]
```

## 5. Configurar la base de datos

- Copiá `barbershopmya/settings.py` y confirmá que `DATABASES` apunta a tu MariaDB local (usuario, contraseña, nombre de la base, host, puerto).
- Corré las migraciones:

```bash
python manage.py migrate
```

- (Opcional) Creá un superusuario para entrar al admin de Django:

```bash
python manage.py createsuperuser
```

- **Configurá el dominio del `Site` (id=1)**, necesario para que allauth arme las URLs de callback correctamente:

```bash
python manage.py shell
```
```python
from django.contrib.sites.models import Site
s = Site.objects.get(pk=1)
s.domain = "localhost:8000"
s.name = "localhost:8000"
s.save()
```
Salí con `Ctrl+Z` y Enter.

## 6. Configurar el archivo `.env`

Creá un archivo `.env` en la raíz del proyecto (al mismo nivel que `manage.py`) con este contenido:

```env
EMAIL_HOST_USER=tu_correo_de_envio@gmail.com
EMAIL_HOST_PASSWORD=tu_password_de_aplicacion_de_gmail

GOOGLE_CLIENT_ID=tu_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_client_secret_real
```

Notas sobre estas variables:

- **`EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD`**: correo Gmail y su "contraseña de aplicación" (no la contraseña normal de la cuenta) para el envío de recuperación de contraseña por correo.
- **`GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`**: ambos son necesarios para el login con Google (antes solo hacía falta el `CLIENT_ID`; con `django-allauth` y el flujo de redirección también se necesita el `CLIENT_SECRET` porque el intercambio del código por el token ocurre servidor-a-servidor). Se obtienen en Google Cloud Console (APIs y servicios → Credenciales → tu Cliente OAuth 2.0 de tipo "Aplicación web"). El secreto se puede ver o regenerar ("Restablecer secreto") desde esa misma pantalla.
- **Nunca subas el `.env` a git ni lo compartas** — si alguna vez se expone (por ejemplo, pegado en un chat o commit), regenerá el secreto de inmediato desde Google Cloud Console.
- Recordá reiniciar el servidor (`Ctrl+C` y volver a correr `runserver`) cada vez que edites el `.env` — las variables de entorno solo se cargan al arrancar el proceso, no se recargan solas.

### Configuración en Google Cloud Console

En tu Cliente OAuth 2.0 (APIs y servicios → Credenciales):

**Orígenes autorizados de JavaScript** (Google los sigue pidiendo aunque ya no usemos el botón embebido):
```
http://localhost:8000
http://127.0.0.1:8000
```

**URIs de redireccionamiento autorizados** (estos sí son los que realmente usa el flujo actual):
```
http://localhost:8000/accounts/google/login/callback/
http://127.0.0.1:8000/accounts/google/login/callback/
```

⚠️ Después de crear o modificar estos campos, Google puede tardar entre unos minutos y algunas horas en aplicar el cambio.

Y en **OAuth consent screen**: si tu app sigue en modo "Testing" (no publicada), solo las cuentas de Gmail agregadas como "Usuarios de prueba" van a poder loguearse — agregá ahí las cuentas con las que vas a probar.

## 7. Archivos estáticos y de medios

```bash
python manage.py collectstatic --noinput
```

Confirmá que existan las carpetas `media/` (para fotos de perfil) y `staticfiles/` (o la que tengas configurada en `STATIC_ROOT`) en la raíz del proyecto. Si no existen, Django las crea solo, pero si algo falla, creálas a mano.

## 8. Levantar el servidor

```bash
python manage.py runserver
```

Entrá a `http://127.0.0.1:8000/` y probá:

- Iniciar sesión / registrarse (incluyendo el botón "Continuar con Google" y el login por número de celular). La recuperación de contraseña olvidada funciona únicamente por correo electrónico.
- El botón de Google en `http://localhost:8000/usuarios/iniciar-sesion/` debería llevarte directo al selector de cuenta de Google (sin pantallas intermedias), y volver a redirigirte según el rol elegido (Admin/Barbero/Cliente).
- El análisis de forma de rostro (`/usuarios/analisis-rostro/`) — usá cámara, subida de imagen, y foto de perfil, para confirmar que MediaPipe está funcionando bien.

## 9. Actualizar `requirements.txt` a futuro

Si en algún momento instalás una librería nueva, actualizá el archivo así para no perder el registro:

```bash
pip freeze > requirements.txt
```

⚠️ Cuidado: después de correr esto, abrí el archivo y confirmá que `Django==4.2.30` (o la versión que estés usando a propósito) sigue ahí — `pip freeze` vuelca lo que esté instalado en ese momento, así que si instalaste o actualizaste algo sin querer, se puede colar una versión que no querías (por ejemplo Django 5.x, que rompe con MariaDB 10.4).

---

## Problemas comunes

### `mediapipe` no tiene `solutions` (o tira `AttributeError`)
Las versiones de mediapipe a partir de la ~0.10.29 rompieron el legacy API `mp.solutions` (el que usa `face_mesh`) en varias plataformas. Solución:
```bash
pip uninstall mediapipe -y
pip install mediapipe==0.10.14
```

### Error de MariaDB al correr `migrate` o `runserver` (`NotSupportedError`)
Django 5.x requiere MariaDB 10.5+. Si tu servidor sigue en 10.4 (como el de este proyecto), la versión de Django en `requirements.txt` tiene que ser 4.2.x, nunca 5.x. Si por accidente se instaló Django 5:
```bash
pip uninstall django -y
pip install "django>=4.2,<5.0"
```

### `mysqlclient` no compila en Windows
Si `pip install mysqlclient` falla al compilar, normalmente es porque falta el header de MySQL/MariaDB. Alternativas:
- Instalar el "MariaDB Connector C" desde la web oficial de MariaDB antes de reinstalar.
- O usar el wheel precompilado que ya trae este proyecto (`mysqlclient==2.2.8` en `requirements.txt` debería bajar directo sin compilar en la mayoría de los casos con pip reciente).

### La cámara no pide permiso / no carga en el análisis de rostro
Los navegadores solo permiten acceso a cámara en `localhost` o HTTPS. Si estás probando desde otro dispositivo en la red local (no `127.0.0.1`), la cámara no va a funcionar sin certificado HTTPS.

### El login con Google devuelve `401 Unauthorized` en `/accounts/google/login/callback/`
Esto significa que Google aceptó el login (te dio el código de autorización) pero el intercambio de ese código por un token, que hace tu servidor directamente contra Google, falló. Casi siempre es porque **`GOOGLE_CLIENT_SECRET` en tu `.env` no es el valor real** (quedó un placeholder o está vacío). Verificalo así:
```bash
python manage.py shell
```
```python
import os
print(os.getenv('GOOGLE_CLIENT_SECRET', 'NO ENCONTRADO')[:10])
```
Si no es el secreto real, andá a Google Cloud Console → Credenciales → tu Cliente OAuth 2.0, copiá o regenerá el secreto ("Restablecer secreto"), actualizá el `.env` y **reiniciá el servidor**.

### Google te muestra "Falló la autenticación de terceros" (plantilla genérica, no la del proyecto)
Revisá la terminal donde corre `runserver` — ahí queda logueado el error real (`adapters.py` tiene un `authentication_error` que loguea la excepción y redirige a tu propio `iniciar_sesion` en vez de mostrar la plantilla de allauth).

### `migrate` falla con `Table 'usuarios_xxx' already exists`
Pasa si una migración se aplicó parcialmente a la base de datos pero el registro interno de Django (`django_migrations`) no quedó sincronizado. Si confirmás que la tabla ya tiene la estructura correcta (compará con `DESCRIBE nombre_tabla;` desde el shell de Django usando `connection.cursor()`), marcá la migración como aplicada sin ejecutarla:
```bash
python manage.py migrate usuarios <numero_migracion> --fake
```

### El botón "Continuar con Google" da error 400 "The given origin is not allowed for the given client ID"
Esto era un error del flujo viejo (Google Identity Services embebido) que ya no debería aparecer con el flujo de redirección actual. Si lo ves, probablemente estás mirando una versión vieja de las plantillas `iniciarsesion.html` / `registrarse.html` — confirmá que usan el link a `/usuarios/google-iniciar/<rol>/` y no `google.accounts.id.initialize(...)`.