M&A Barber Shop — Guía de instalación
Instrucciones para dejar el proyecto funcionando desde cero en cualquier equipo nuevo (Windows).

1. Requisitos previos (antes de tocar Python)
Python 3.11 instalado (⚠️ no uses 3.12+ ni 3.13+ todavía — mediapipe con el legacy API mp.solutions no es estable ahí).
MariaDB 10.4 corriendo, con la base de datos del proyecto ya creada.
Git (si vas a clonar el repo).
Verificá tu versión de Python antes de crear el entorno virtual:

py -0
Si ves varias versiones instaladas, asegurate de usar la 3.11 al crear el venv (ver paso 2).

2. Crear y activar el entorno virtual
cd ruta\a\tu\proyecto

# Crear el venv específicamente con Python 3.11
py -3.11 -m venv .venv

# Activar (PowerShell)
.venv\Scripts\Activate.ps1

# Si PowerShell bloquea la ejecución de scripts, corré esto una vez y volvé a intentar:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
Vas a saber que está activo porque tu terminal muestra (.venv) al inicio de la línea.

3. Instalar todas las dependencias
Con el venv activo:

python -m pip install --upgrade pip
python -m pip install "django>=4.2,<5.0" pymysql mysqlclient django-widget-tweaks xhtml2pdf fpdf2 pandas openpyxl pillow opencv-python-headless mediapipe==0.10.14 google-auth

O directamente con el archivo de dependencias:

pip install -r requirements.txt

Esto instala todo lo que el proyecto necesita: Django, el conector de MySQL, MediaPipe/OpenCV para el análisis de rostro, las librerías de generación de PDF/Excel, y (desde agosto 2026) google-auth para el login con Google.

Verificación rápida (correr estos 4 comandos después de instalar)
python -c "import django; print('Django:', django.get_version())"
python -c "import mediapipe as mp; print(mp.solutions.face_mesh); print('MediaPipe OK')"
python -c "import MySQLdb; print('mysqlclient OK')"
python -c "import google.oauth2.id_token; print('Google-auth OK')"

Deberías ver:

Django: 4.2.30
Una línea con <module 'mediapipe.python.solutions.face_mesh' ...> seguida de MediaPipe OK
mysqlclient OK
Google-auth OK

Si alguno de estos 4 falla, no sigas — resolvé eso primero (ver sección de problemas comunes más abajo).

4. Configurar la base de datos
Copiá barbershopmya/settings.py y confirmá que DATABASES apunta a tu MariaDB local (usuario, contraseña, nombre de la base, host, puerto).
Corré las migraciones:
python manage.py migrate
(Opcional) Creá un superusuario para entrar al admin de Django:
python manage.py createsuperuser

5. Configurar el archivo .env
Creá un archivo .env en la raíz del proyecto (al mismo nivel que manage.py) con este contenido:

EMAIL_HOST_USER=tu_correo_de_envio@gmail.com
EMAIL_HOST_PASSWORD=tu_password_de_aplicacion_de_gmail

GOOGLE_CLIENT_ID=tu_client_id.apps.googleusercontent.com

Notas sobre estas variables:
- EMAIL_HOST_USER / EMAIL_HOST_PASSWORD: correo Gmail y su "contraseña de aplicación" (no la contraseña normal de la cuenta) para el envío de recuperación de contraseña por correo.
- GOOGLE_CLIENT_ID: necesario para el botón "Acceder con Google" en el login/registro. Se obtiene creando un ID de cliente OAuth tipo "Aplicación web" en Google Cloud Console (APIs y servicios → Credenciales), con http://localhost:8000 y http://127.0.0.1:8000 como Orígenes de JavaScript autorizados. ⚠️ Después de crear o modificar los orígenes autorizados, Google puede tardar entre 5 minutos y algunas horas en aplicar el cambio — si el botón de Google da error 400 "origin not allowed" recién configurado, esperá un rato antes de asumir que algo está mal.
- Recordá reiniciar el servidor (Ctrl+C y volver a correr runserver) cada vez que edites el .env — las variables de entorno solo se cargan al arrancar el proceso, no se recargan solas.

6. Archivos estáticos y de medios
python manage.py collectstatic --noinput
Confirmá que existan las carpetas media/ (para fotos de perfil) y staticfiles/ (o la que tengas configurada en STATIC_ROOT) en la raíz del proyecto. Si no existen, Django las crea solo, pero si algo falla, creálas a mano.

7. Levantar el servidor
python manage.py runserver
Entrá a http://127.0.0.1:8000/ y probá:

Iniciar sesión / registrarse (incluyendo el botón "Acceder con Google" y el login por número de celular). La recuperación de contraseña olvidada funciona únicamente por correo electrónico.
El análisis de forma de rostro (/usuarios/analisis-rostro/) — usá cámara, subida de imagen, y foto de perfil, para confirmar que MediaPipe está funcionando bien.

8. Actualizar requirements.txt a futuro
Si en algún momento instalás una librería nueva, actualizá el archivo así para no perder el registro:

pip freeze > requirements.txt
⚠️ Cuidado: después de correr esto, abrí el archivo y confirmá que Django==4.2.30 (o la versión que estés usando a propósito) sigue ahí — pip freeze vuelca lo que esté instalado en ese momento, así que si instalaste o actualizaste algo sin querer, se puede colar una versión que no querías (por ejemplo Django 5.x, que rompe con MariaDB 10.4).

Problemas comunes
mediapipe no tiene solutions (o tira AttributeError)
Las versiones de mediapipe a partir de la ~0.10.29 rompieron el legacy API mp.solutions (el que usa face_mesh) en varias plataformas. Solución:

pip uninstall mediapipe -y
pip install mediapipe==0.10.14

Error de MariaDB al correr migrate o runserver (NotSupportedError)
Django 5.x requiere MariaDB 10.5+. Si tu servidor sigue en 10.4 (como el de este proyecto), la versión de Django en requirements.txt tiene que ser 4.2.x, nunca 5.x. Si por accidente se instaló Django 5:

pip uninstall django -y
pip install "django>=4.2,<5.0"

mysqlclient no compila en Windows
Si pip install mysqlclient falla al compilar, normalmente es porque falta el header de MySQL/MariaDB. Alternativas:

Instalar el "MariaDB Connector C" desde la web oficial de MariaDB antes de reinstalar.
O usar el wheel precompilado que ya trae este proyecto (mysqlclient==2.2.8 en requirements.txt debería bajar directo sin compilar en la mayoría de los casos con pip reciente).

La cámara no pide permiso / no carga en el análisis de rostro
Los navegadores solo permiten acceso a cámara en localhost o HTTPS. Si estás probando desde otro dispositivo en la red local (no 127.0.0.1), la cámara no va a funcionar sin certificado HTTPS.

El botón "Acceder con Google" da error 400 "The given origin is not allowed for the given client ID"
Antes de asumir que algo está mal configurado:
1. Confirmá que GOOGLE_CLIENT_ID en el .env coincide EXACTO (carácter por carácter) con el ID de cliente de Google Cloud Console.
2. Confirmá que reiniciaste el servidor después de editar el .env (no basta con guardar el archivo).
3. Confirmá que http://localhost:8000 y http://127.0.0.1:8000 están guardados en "Orígenes de JavaScript autorizados" de ese cliente OAuth (sin barra final, con Guardar aplicado).
4. Esperá — Google avisa que la propagación de estos cambios puede tardar entre 5 minutos y algunas horas.
Si después de esperar y verificar todo eso sigue fallando, probá en una ventana de incógnito para descartar caché/extensiones del navegador.