# usuarios/adapters.py
import uuid
from datetime import date
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.shortcuts import redirect as django_redirect

from .models import Usuario, Rol, PerfilUsuario
from .views import formatear_nombre, clasificar_rol_nuevo_usuario, ID_ROL_CLIENTE
from .auth_utils import generar_password_provisional


class MiSocialAccountAdapter(DefaultSocialAccountAdapter):

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        Se dispara cuando algo falla en el intercambio con Google ANTES de
        llegar a pre_social_login (token inválido, el usuario canceló en la
        pantalla de Google, error de red, etc.) o cuando pre_social_login
        lanza una excepción no controlada. Sin este método, allauth muestra
        su propia plantilla genérica (socialaccount/authentication_error.html).
        Con ImmediateHttpResponse, en cambio, mandamos al usuario de vuelta
        a NUESTRO iniciar_sesion con un mensaje.
        """
        import logging
        logging.getLogger(__name__).exception(
            "Fallo de autenticación social (provider=%s): %s", provider_id, exception
        )
        messages.error(
            request,
            "No se pudo completar el inicio de sesión con Google. Intenta de nuevo."
        )
        raise ImmediateHttpResponse(django_redirect('iniciar_sesion'))

    def pre_social_login(self, request, sociallogin):
        """
        Se ejecuta justo después de que Google confirma la identidad,
        ANTES de que allauth cree/loguee al User de Django. Aquí replicamos
        toda la lógica que antes tenía tu vista google_login manual.
        """
        correo_google = sociallogin.account.extra_data.get('email')
        nombre_google = sociallogin.account.extra_data.get('name') or (
            correo_google.split('@')[0] if correo_google else 'Usuario'
        )
        google_sub = sociallogin.account.extra_data.get('sub') or sociallogin.account.uid

        rol_esperado_id = request.session.get('rol_google_seleccionado', ID_ROL_CLIENTE)

        if not correo_google:
            messages.error(request, "Tu cuenta de Google no tiene un correo válido.")
            raise ImmediateHttpResponse(django_redirect('iniciar_sesion'))

        password_generada = None
        usuario_manual = Usuario.objects.filter(correo__iexact=correo_google).first()

        # --- CASO 1: usuario nuevo (nunca se había registrado, ni manual ni con Google) ---
        if usuario_manual is None:
            rol_cliente = Rol.objects.get(idrol=ID_ROL_CLIENTE)
            password_generada = generar_password_provisional()
            cedula_temporal = f"G-{uuid.uuid4().hex[:10].upper()}"

            usuario_manual = Usuario.objects.create(
                cedula=cedula_temporal,
                nombre=formatear_nombre(nombre_google),
                correo=correo_google,
                contrasena=make_password(password_generada),
                numcelular='',
                fechanacimiento=date(2000, 1, 1),
                idrolfk=rol_cliente,
            )
            clasificar_rol_nuevo_usuario(usuario_manual)

            user_django, _creado = User.objects.get_or_create(
                username=correo_google,
                defaults={'email': correo_google, 'first_name': nombre_google}
            )
            user_django.set_password(password_generada)
            user_django.save()

            # Nota: un usuario recién creado por Google siempre nace como
            # Cliente (ID_ROL_CLIENTE), así que aquí NO hace falta validar
            # rol_esperado_id vs rol_real_id — todavía no existía ningún rol
            # "real" que pudiera chocar. Si más adelante quieres bloquear el
            # auto-registro cuando alguien elige "Administrador"/"Barbero" en
            # el selector sin tener cuenta previa, dímelo y lo agregamos aquí.

        # --- CASO 2: usuario ya existía en tu tabla Usuario (manual o de una sesión anterior) ---
        else:
            try:
                rol_real_id = usuario_manual.idrolfk.idrol
            except Exception:
                rol_real_id = usuario_manual.idrolfk_id

            if rol_real_id != rol_esperado_id:
                messages.error(request, "Esa cuenta de Google no corresponde al rol seleccionado.")
                raise ImmediateHttpResponse(django_redirect('iniciar_sesion'))

            user_django, creado_django = User.objects.get_or_create(
                username=usuario_manual.correo,
                defaults={'email': usuario_manual.correo, 'first_name': usuario_manual.nombre}
            )
            if creado_django:
                password_generada = generar_password_provisional()
                user_django.set_password(password_generada)
                user_django.save()
                usuario_manual.contrasena = make_password(password_generada)
                usuario_manual.save(update_fields=['contrasena'])

        perfil, _creado_perfil = PerfilUsuario.objects.get_or_create(user=user_django)
        # Ajusta este bloque si tu PerfilUsuario no tiene 'google_id'/'password_provisional'
        if hasattr(perfil, 'google_id') and getattr(perfil, 'google_id', None) != google_sub:
            perfil.google_id = google_sub
            if password_generada and hasattr(perfil, 'password_provisional'):
                perfil.password_provisional = True
            perfil.save()

        # Conecta el sociallogin al User de Django ya existente/creado,
        # para que allauth loguee a ESE usuario en vez de crear uno nuevo.
        sociallogin.connect(request, user_django)

        # Guarda el rol real para usarlo en get_login_redirect_url
        try:
            request.session['usuario_rol_id'] = int(
                usuario_manual.idrolfk.idrol if hasattr(usuario_manual.idrolfk, 'idrol') else usuario_manual.idrolfk_id
            )
        except Exception:
            request.session['usuario_rol_id'] = ID_ROL_CLIENTE

        request.session['sesion_iniciada'] = True
        request.session['usuario_nombre'] = user_django.first_name or user_django.username
        request.session['usuario_foto'] = usuario_manual.foto_perfil.url if usuario_manual.foto_perfil else None

        if password_generada:
            messages.info(
                request,
                f"¡Bienvenido, {usuario_manual.nombre}! Creamos tu cuenta usando Google. "
                f"También dejamos lista una contraseña de acceso tradicional: {password_generada}. "
                f"Puedes cambiarla cuando quieras desde tu perfil.",
                extra_tags='password-provisional'
            )

    def get_connect_redirect_url(self, request, socialaccount):
        return self._redirect_por_rol(request)

    def get_login_redirect_url(self, request):
        return self._redirect_por_rol(request)

    def _redirect_por_rol(self, request):
        rol = request.session.get('usuario_rol_id', ID_ROL_CLIENTE)
        if rol == 1:
            return '/usuarios/admin-dashboard/'
        elif rol == 2:
            return '/usuarios/panel-barbero/'
        return '/'