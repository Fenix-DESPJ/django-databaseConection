# M&A Barber Shop — Guía de instalación

Instrucciones para dejar el proyecto funcionando desde cero en cualquier equipo nuevo (Windows).

## 1. Requisitos previos (antes de tocar Python)

- **Python 3.11** instalado (⚠️ no uses 3.12+ ni 3.13+ todavía — `mediapipe` con el legacy API `mp.solutions` no es estable ahí).
- **MariaDB 10.4** corriendo, con la base de datos del proyecto ya creada.
- Git (si vas a clonar el repo).

Verificá tu versión de Python antes de crear el entorno virtual:

```powershell
py -0
```

Si ves varias versiones instaladas, asegurate de usar la 3.11 al crear el venv (ver paso 2).

## 2. Crear y activar el entorno virtual

```powershell
cd ruta\a\tu\proyecto

# Crear el venv específicamente con Python 3.11
py -3.11 -m venv .venv

# Activar (PowerShell)
.venv\Scripts\Activate.ps1

# Si PowerShell bloquea la ejecución de scripts, corré esto una vez y volvé a intentar:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Vas a saber que está activo porque tu terminal muestra `(.venv)` al inicio de la línea.

## 3. Instalar todas las dependencias

Con el venv activo:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Esto instala **todo** lo que el proyecto necesita: Django, el conector de MySQL, MediaPipe/OpenCV para el análisis de rostro, y las librerías de generación de PDF/Excel.

### Verificación rápida (correr estos 3 comandos después de instalar)

```powershell
python -c "import django; print('Django:', django.get_version())"
python -c "import mediapipe as mp; print(mp.solutions.face_mesh); print('MediaPipe OK')"
python -c "import MySQLdb; print('mysqlclient OK')"
```

Deberías ver:
- `Django: 4.2.30`
- Una línea con `<module 'mediapipe.python.solutions.face_mesh' ...>` seguida de `MediaPipe OK`
- `mysqlclient OK`

Si alguno de estos 3 falla, no sigas — resolvé eso primero (ver sección de problemas comunes más abajo).

## 4. Configurar la base de datos

1. Copiá `barbershopmya/settings.py` y confirmá que `DATABASES` apunta a tu MariaDB local (usuario, contraseña, nombre de la base, host, puerto).
2. Corré las migraciones:

```powershell
python manage.py migrate
```

3. (Opcional) Creá un superusuario para entrar al admin de Django:

```powershell
python manage.py createsuperuser
```

## 5. Archivos estáticos y de medios

```powershell
python manage.py collectstatic --noinput
```

Confirmá que existan las carpetas `media/` (para fotos de perfil) y `staticfiles/` (o la que tengas configurada en `STATIC_ROOT`) en la raíz del proyecto. Si no existen, Django las crea solo, pero si algo falla, creálas a mano.

## 6. Levantar el servidor

```powershell
python manage.py runserver
```

Entrá a `http://127.0.0.1:8000/` y probá:
- Iniciar sesión / registrarse
- El análisis de forma de rostro (`/usuarios/analisis-rostro/`) — usá cámara, subida de imagen, y foto de perfil, para confirmar que MediaPipe está funcionando bien.

## 7. Actualizar `requirements.txt` a futuro

Si en algún momento instalás una librería nueva, actualizá el archivo así para no perder el registro:

```powershell
pip freeze > requirements.txt
```

⚠️ **Cuidado:** después de correr esto, abrí el archivo y confirmá que `Django==4.2.30` (o la versión que estés usando a propósito) sigue ahí — `pip freeze` vuelca lo que esté instalado en ese momento, así que si instalaste o actualizaste algo sin querer, se puede colar una versión que no querías (por ejemplo Django 5.x, que rompe con MariaDB 10.4).

## Problemas comunes

### `mediapipe` no tiene `solutions` (o tira `AttributeError`)
Las versiones de `mediapipe` a partir de la ~0.10.29 rompieron el legacy API `mp.solutions` (el que usa `face_mesh`) en varias plataformas. Solución:

```powershell
pip uninstall mediapipe -y
pip install mediapipe==0.10.14
```

### Error de MariaDB al correr `migrate` o `runserver` (`NotSupportedError`)
Django 5.x requiere MariaDB 10.5+. Si tu servidor sigue en 10.4 (como el de este proyecto), la versión de Django en `requirements.txt` **tiene que ser 4.2.x**, nunca 5.x. Si por accidente se instaló Django 5:

```powershell
pip uninstall django -y
pip install "django>=4.2,<5.0"
```

### `mysqlclient` no compila en Windows
Si `pip install mysqlclient` falla al compilar, normalmente es porque falta el header de MySQL/MariaDB. Alternativas:
- Instalar el "MariaDB Connector C" desde la web oficial de MariaDB antes de reinstalar.
- O usar el wheel precompilado que ya trae este proyecto (`mysqlclient==2.2.8` en `requirements.txt` debería bajar directo sin compilar en la mayoría de los casos con pip reciente).

### La cámara no pide permiso / no carga en el análisis de rostro
Los navegadores solo permiten acceso a cámara en `localhost` o HTTPS. Si estás probando desde otro dispositivo en la red local (no `127.0.0.1`), la cámara no va a funcionar sin certificado HTTPS.