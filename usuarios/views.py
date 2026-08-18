# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
import requests as http_requests  # nombrado así para no chocar con la librería 'requests' del propio Django/WSGI
from django.core.mail import send_mail



from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.db import connection
from django.conf import settings
from django.http import JsonResponse
from django.db import transaction, connection  # agrega estos imports si no están
import os
import uuid
import tempfile
from datetime import timedelta, date
from allauth.socialaccount.models import SocialAccount, SocialToken
from allauth.account.models import EmailAddress
from django.contrib.admin.models import LogEntry
from django.templatetags.static import static
from django.contrib.auth import logout

# Importación de tus modelos manuales
from .models import Usuario, Rol, Cita, Servicio, Cliente, Notificacion, Calificacion, Pago, ContenidoIndex, BarberoDestacado, PerfilUsuario
from negocio.models import Barbero, Agenda
# NOTA: el import de `.utils` (analizar_forma_rostro, RostroNoDetectadoError,
# RECOMENDACIONES_POR_FORMA) se ELIMINÓ de aquí a propósito. Esa lógica y sus
# dependencias (cv2, mediapipe) ahora viven aisladas en la app analisis_facial/,
# así un fallo de esas librerías (o borrar esa carpeta por testing) ya NO puede
# tumbar el import de este archivo completo (login, perfiles, reservas, etc.).
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from .auth_utils import generar_password_provisional

# =========================================================================
# REGLAS DE NEGOCIO QUE ANTES ERAN TRIGGERS DE MYSQL
# =========================================================================
# Reemplazan:
#   - FormatearNombreUsuario          (BEFORE INSERT)
#   - DespuesInsertarUsuarioClasificarRol (AFTER INSERT)
#   - DespuesActualizarUsuarioCambioRol   (AFTER UPDATE)
#   - AntesEliminarUsuario            (BEFORE DELETE)
# Ahora todo ocurre explícitamente desde las views, en orden y dentro
# de transacciones cuando corresponde.
# =========================================================================

ID_ROL_ADMIN = 1
ID_ROL_BARBERO = 2
ID_ROL_CLIENTE = 3


def formatear_nombre(nombre):
    """Antes: trigger FormatearNombreUsuario (BEFORE INSERT)."""
    return (nombre or '').strip().upper()

@login_required
def eliminar_mi_cuenta(request):
    if request.method == 'POST':
        # 1. Obtener la cuenta de auth_user y el perfil de la tabla personalizada 'usuario'
        user_django = request.user
        correo_actual = user_django.email or user_django.username
        
        usuario = Usuario.objects.filter(correo=correo_actual).first()

        # Si por alguna razón no existe el perfil de usuario personalizado
        if not usuario:
            messages.error(request, "No se encontró un perfil de usuario asociado a esta cuenta.")
            return redirect('perfil')

        # 2. Validar que no tenga bloqueos (ej. citas pendientes o restricciones de negocio)
        error_bloqueo = validar_eliminacion_usuario(usuario)
        if error_bloqueo:
            messages.error(request, error_bloqueo)
            return redirect('perfil')

        nombre_eliminado = usuario.nombre

        try:
            with transaction.atomic():
                # 3. Limpieza en cascada de citas, agendas y datos de Cliente/Barbero
                for cliente in Cliente.objects.filter(idusuariofk=usuario):
                    _cascada_borrar_cliente(cliente)
                for barbero in Barbero.objects.filter(idusuariofk=usuario):
                    _cascada_borrar_barbero(barbero)

                # 4. Eliminar el registro de la tabla personalizada 'usuario'
                usuario.delete()

                # 5. Limpieza previa de relaciones de allauth y logs
                SocialToken.objects.filter(account__user=user_django).delete()
                SocialAccount.objects.filter(user=user_django).delete()
                EmailAddress.objects.filter(user=user_django).delete()
                PerfilUsuario.objects.filter(user=user_django).delete()
                user_django.groups.clear()
                user_django.user_permissions.clear()
                LogEntry.objects.filter(user=user_django).delete()

                # 6. IMPORTANTE: Cerrar sesión en el navegador ANTES de borrar el usuario de la BD
                logout(request)

                # 7. Borrado directo en auth_user para evitar el Collector de Django
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_django.pk])

        except Exception as e:
            messages.error(
                request,
                f"No se pudo eliminar tu cuenta. Detalle técnico: {e}"
            )
            return redirect('perfil')

        messages.success(
            request,
            f"Hola {nombre_eliminado}, tu cuenta y tus datos asociados han sido eliminados permanentemente."
        )
        return redirect('home')

    return redirect('perfil')

def clasificar_rol_nuevo_usuario(usuario):
    """
    Antes: trigger DespuesInsertarUsuarioClasificarRol (AFTER INSERT).
    Se llama justo después de crear un Usuario nuevo.
    """
    if usuario.idrolfk_id == ID_ROL_BARBERO:
        Barbero.objects.get_or_create(
            idusuariofk=usuario,
            defaults={'especialidad': 'Por asignar'}
        )
    elif usuario.idrolfk_id == ID_ROL_CLIENTE:
        Cliente.objects.get_or_create(
            idusuariofk=usuario,
            defaults={
                'direccion': 'Registrado desde la Web',
                'fecharegistro': date.today(),
                'contactoemergencia': 'No asignado',
            }
        )


def sincronizar_cambio_rol(usuario, rol_anterior_id, rol_nuevo_id):
    """
    Antes: trigger DespuesActualizarUsuarioCambioRol (AFTER UPDATE).
    Se llama cuando el rol de un usuario cambió (rol_anterior_id != rol_nuevo_id).
    """
    if rol_anterior_id == rol_nuevo_id:
        return

    if rol_nuevo_id == ID_ROL_BARBERO:
        # Antes de borrar el perfil de Cliente, hay que vaciar sus citas/agendas
        for cliente in Cliente.objects.filter(idusuariofk=usuario):
            _cascada_borrar_cliente(cliente)
        Barbero.objects.get_or_create(
            idusuariofk=usuario,
            defaults={'especialidad': 'Por asignar'}
        )

    elif rol_nuevo_id == ID_ROL_CLIENTE:
        # Antes de borrar el perfil de Barbero, hay que vaciar sus citas/agendas
        for barbero in Barbero.objects.filter(idusuariofk=usuario):
            _cascada_borrar_barbero(barbero)
        Cliente.objects.get_or_create(
            idusuariofk=usuario,
            defaults={
                'direccion': 'Cambio de Rol desde Panel',
                'fecharegistro': date.today(),
                'contactoemergencia': 'No asignado',
            }
        )

    else:  # pasó a Admin u otro rol operativo
        for cliente in Cliente.objects.filter(idusuariofk=usuario):
            _cascada_borrar_cliente(cliente)
        for barbero in Barbero.objects.filter(idusuariofk=usuario):
            _cascada_borrar_barbero(barbero)

def validar_eliminacion_usuario(usuario):
    """
    Antes: trigger AntesEliminarUsuario (BEFORE DELETE).
    Devuelve None si se puede borrar, o un mensaje de error si no.
    """
    if usuario.idrolfk_id == ID_ROL_ADMIN:
        return "No se puede eliminar al Administrador principal."
    return None

def _cascada_borrar_cliente(cliente):
    """
    Borra las citas de un Cliente y las filas de Agenda que esas citas ocupaban,
    y finalmente borra al Cliente. Nunca toca 'Servicio' (solo se borra la Cita
    que lo referenciaba). Calificacion se borra sola por CASCADE al borrar Cita.
    """
    citas = Cita.objects.filter(idclientefk=cliente)
    agendas_ids = list(
        citas.exclude(idagendafk__isnull=True).values_list('idagendafk', flat=True)
    )
    citas.delete()
    Agenda.objects.filter(idagenda__in=agendas_ids).delete()
    cliente.delete()


def _cascada_borrar_barbero(barbero):
    """
    Borra las citas de un Barbero y las Agendas asociadas a ese barbero,
    y finalmente borra al Barbero.
    """
    Cita.objects.filter(idbarberofk=barbero).delete()
    Agenda.objects.filter(idbarberofk=barbero).delete()
    barbero.delete()

# =========================================================================
# 1. VISTA: INICIAR SESIÓN
# =========================================================================
def iniciar_sesion(request):
    if request.method == 'POST':
        usuario_input = (request.POST.get('identificador') or '').strip()
        contrasena_input = request.POST.get('contrasena')
        rol_formulario = request.POST.get('rol')  
        
        if rol_formulario:
            rol_formulario = str(rol_formulario).lower().strip()
        
        # Mapeo de roles
        rol_esperado_id = None
        if rol_formulario in ['admin', 'administrador']:
            rol_esperado_id = 1  
        elif rol_formulario == 'barbero':
            rol_esperado_id = 2  
        elif rol_formulario == 'cliente':
            rol_esperado_id = 3  

        # --- NUEVO: si el identificador NO parece un correo, buscamos por celular ---
        username_para_auth = usuario_input
        if usuario_input and '@' not in usuario_input:
            usuario_por_celular = Usuario.objects.filter(numcelular=usuario_input).first()
            if usuario_por_celular:
                username_para_auth = usuario_por_celular.correo
            # si no existe ningún usuario con ese celular, se deja tal cual
            # y authenticate() fallará más abajo con el mensaje genérico de siempre

        # Autenticación con Django Auth
        user = authenticate(request, username=username_para_auth, password=contrasena_input)
        
        if user is not None:
            try:
                # Buscamos al usuario en la tabla MySQL
                usuario_manual = Usuario.objects.get(correo=user.email)
                
                # Obtención segura del ID del rol
                try:
                    rol_actual_id = usuario_manual.idrolfk.idrol
                except Exception:
                    rol_actual_id = usuario_manual.idrolfk_id 
                
                # Validación de rol
                if rol_actual_id != rol_esperado_id:
                    messages.error(request, "El usuario no corresponde al rol seleccionado.")
                    return redirect('iniciar_sesion')

                # Login exitoso
                auth_login(request, user)
                
                # Guardado en sesión
                request.session['sesion_iniciada'] = True
                request.session['usuario_nombre'] = user.first_name if user.first_name else user.username
                request.session['usuario_rol_id'] = int(rol_actual_id)
                
                if usuario_manual.foto_perfil:
                    request.session['usuario_foto'] = usuario_manual.foto_perfil.url
                else:
                    request.session['usuario_foto'] = None
                
                # Redirección basada en rol
                rol_final = int(rol_actual_id)
                if rol_final == 1:
                    return redirect('dashboard_admin')
                elif rol_final == 2:
                    return redirect('panel_barbero')
                else:
                    return redirect('home')

            except Usuario.DoesNotExist:
                messages.error(request, "Tu cuenta no está vinculada correctamente a la barbería.")
                return redirect('iniciar_sesion')
        else:
            messages.error(request, "El correo, celular o la contraseña son incorrectos.")
            return redirect('iniciar_sesion')
            
    return render(request, 'iniciarsesion.html')

# =========================================================================
# 1.B VISTA: INICIAR SESIÓN / AUTOREGISTRO CON GOOGLE
# =========================================================================
# --- Reemplaza la vista antigua @require_POST def google_login(request): por esta ---

def seleccionar_rol_google(request, rol):
    """
    Guarda en sesión el rol elegido (admin/barbero/cliente) ANTES de mandar
    al usuario al flujo de redirección de Google (allauth). El adapter
    (usuarios/adapters.py) lee este valor cuando Google redirige de vuelta.
    """
    rol = (rol or 'cliente').lower().strip()
    mapa_roles = {'admin': 1, 'administrador': 1, 'barbero': 2, 'cliente': 3}
    request.session['rol_google_seleccionado'] = mapa_roles.get(rol, 3)
    return redirect('/accounts/google/login/?process=login')

# =========================================================================
# 2. VISTA: CERRAR SESIÓN
# =========================================================================
def cerrar_sesion(request):
    # --- Revoca el token de Google ANTES de cerrar la sesión de Django ---
    # Esto NO cierra Gmail (eso el navegador lo controla en accounts.google.com,
    # fuera del alcance de cualquier sitio de terceros), pero sí revoca el
    # permiso que Google le dio a esta app. La próxima vez que el usuario
    # use "Continuar con Google", tendrá que volver a elegir cuenta y
    # autorizar en vez de entrar en automático por la cookie de Google.
    if request.user.is_authenticated:
        social_token = SocialToken.objects.filter(
            account__user=request.user,
            account__provider='google'
        ).first()

        if social_token:
            try:
                http_requests.post(
                    'https://oauth2.googleapis.com/revoke',
                    params={'token': social_token.token},
                    headers={'content-type': 'application/x-www-form-urlencoded'},
                    timeout=5,
                )
            except http_requests.RequestException:
                # Si Google no responde, no bloqueamos el logout del usuario
                # por eso — su sesión en tu app se cierra igual.
                pass

    auth_logout(request)
    if 'sesion_iniciada' in request.session:
        del request.session['sesion_iniciada']
    if 'usuario_nombre' in request.session:
        del request.session['usuario_nombre']

    request.session.flush()
    messages.success(request, "Has cerrado sesión exitosamente. ¡Vuelve pronto!")
    return redirect('iniciar_sesion')

# =========================================================================
# 3. VISTA: REGISTRARSE
# =========================================================================
def registrarse(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            apellido = request.POST.get('apellido')
            cedula = request.POST.get('cedula')
            correo = request.POST.get('correo')
            password = request.POST.get('password')
            telefono = request.POST.get('telefono')
            fecha = request.POST.get('fecha')
            
            # --- Validación: el correo no debe estar ya registrado ---
            if Usuario.objects.filter(correo__iexact=correo).exists() or \
                User.objects.filter(email__iexact=correo).exists():
                messages.error(request, "Ese correo ya está registrado. Intenta iniciar sesión o usa otro correo.")
                return render(request, 'registrarse.html', {'error': "Ese correo ya está registrado."})
            
            rol_cliente = Rol.objects.get(idrol=3)

            # Antes: trigger FormatearNombreUsuario (BEFORE INSERT)
            nombre_completo = formatear_nombre(f"{nombre} {apellido}")

            nuevo_usuario_manual = Usuario.objects.create(
                cedula=cedula,
                nombre=nombre_completo,
                correo=correo,
                contrasena=make_password(password),  
                numcelular=telefono,
                fechanacimiento=fecha,
                idrolfk=rol_cliente
            )

            # Antes: trigger DespuesInsertarUsuarioClasificarRol (AFTER INSERT)
            # Crea la fila en Cliente (antes dependía 100% del trigger)
            clasificar_rol_nuevo_usuario(nuevo_usuario_manual)

            nuevo_usuario_django = User.objects.create_user(
                username=correo,
                email=correo,
                password=password,
                first_name=nombre,
                last_name=apellido
            )
            
            print("DEBUG: Guardado con éxito en ambas tablas")
            messages.success(request, "Registro completado con éxito. Ahora puedes iniciar sesión.")
            return redirect('iniciar_sesion')

        except Exception as e:
            print(f"DEBUG: ERROR AL REGISTRAR: {e}")
            return render(request, 'registrarse.html', {'error': f"Error al registrar: {e}"})
            
    return render(request, 'registrarse.html')

# =========================================================================
# 4. VISTA: HOME / INDEX
# =========================================================================
def home(request):
    mejores_calificaciones = Calificacion.objects.filter(
        calificacion__gte=4
    ).select_related('idclientefk__idusuariofk').order_by('-fechacreacion')[:12]

    contenido = ContenidoIndex.cargar()

    barberos_qs = Barbero.objects.select_related('idusuariofk').filter(
        idusuariofk__idrolfk_id=ID_ROL_BARBERO
    ).order_by('idusuariofk__nombre', 'idbarbero')

    equipo = {}
    for b in barberos_qs:
        usuario = b.idusuariofk
        entrada = equipo.setdefault(usuario.idusuario, {
            'nombre': usuario.nombre,
            'foto': usuario.foto_perfil,
            'especialidades_agenda': [],       # fallback: viene de negocio.Barbero
            'especialidades_perfil': usuario.especialidades,  # editado en /perfil
        })
        if b.especialidad:
            entrada['especialidades_agenda'].append(b.especialidad)

    barberos = [
        {
            'nombre': datos['nombre'],
            'foto': datos['foto'],
            'especialidad': (
                datos['especialidades_perfil']
                or ' · '.join(datos['especialidades_agenda'])
                or 'Barbero'
            ),
        }
        for datos in equipo.values()
    ]

    return render(request, 'index.html', {
        'calificaciones': mejores_calificaciones,
        'contenido': contenido,
        'barberos': barberos,
    })


@login_required
def editar_contenido_index(request):
    """
    Permite al administrador editar el contenido del index (hero, marca,
    horarios, contacto y CTA) desde un formulario. Al guardar, redirige
    de vuelta al home para ver los cambios reflejados.
    """
    usuario_rol = request.session.get('usuario_rol_id')
    if usuario_rol != 1:
        messages.error(request, "Acceso denegado. No tienes permisos de administrador.")
        return redirect('home')

    contenido = ContenidoIndex.cargar()  # crea con defaults si no existe aún

    if request.method == 'POST':
        contenido.hero_etiqueta = request.POST.get('hero_etiqueta', '').strip()
        contenido.hero_titulo = request.POST.get('hero_titulo', '').strip()
        contenido.hero_descripcion = request.POST.get('hero_descripcion', '').strip()
        contenido.hero_tarjeta_titulo = request.POST.get('hero_tarjeta_titulo', '').strip()
        contenido.hero_tarjeta_texto = request.POST.get('hero_tarjeta_texto', '').strip()

        contenido.marca_titulo = request.POST.get('marca_titulo', '').strip()
        contenido.marca_descripcion = request.POST.get('marca_descripcion', '').strip()

        contenido.horario_semana = request.POST.get('horario_semana', '').strip()
        contenido.horario_sabado = request.POST.get('horario_sabado', '').strip()
        contenido.telefono_fijo = request.POST.get('telefono_fijo', '').strip()
        contenido.whatsapp = request.POST.get('whatsapp', '').strip()
        contenido.direccion = request.POST.get('direccion', '').strip()
        contenido.mapa_embed_url = request.POST.get('mapa_embed_url', '').strip()

        contenido.cta_titulo = request.POST.get('cta_titulo', '').strip()
        contenido.cta_texto = request.POST.get('cta_texto', '').strip()

        # Las imágenes solo se reemplazan si el admin sube un archivo nuevo;
        # si no se sube nada, se conserva la imagen que ya estaba guardada.
        for campo in ('hero_imagen_1', 'hero_imagen_2', 'hero_imagen_3', 'marca_imagen'):
            archivo_nuevo = request.FILES.get(campo)
            if archivo_nuevo:
                setattr(contenido, campo, archivo_nuevo)

        contenido.save()
        messages.success(request, "El contenido del inicio se actualizó correctamente.")
        return redirect('home')

    return render(request, 'editar_contenido_index.html', {'contenido': contenido})

# =========================================================================
# 5. VISTAS: PANEL DE BARBERO Y CITAS
# =========================================================================
@login_required
def panel_barbero(request):
    try:
        usuario_manual = Usuario.objects.get(correo=request.user.email)
        if usuario_manual.idrolfk_id != 2:
            return redirect('home')
        
        barbero_perfil = Barbero.objects.get(idusuariofk=usuario_manual)
        
    except (Usuario.DoesNotExist, Barbero.DoesNotExist):
        messages.error(request, "Tu perfil de barbero no está configurado.")
        return redirect('home')

    hoy = timezone.now().date()

    citas_proximas = Cita.objects.select_related(
        'idpagofk', 'idclientefk__idusuariofk', 'idserviciofk', 'idagendafk'
    ).filter(
        idbarberofk=barbero_perfil.idbarbero,
        idagendafk__fecha__gte=hoy
    ).order_by('idagendafk__fecha', 'idagendafk__horainicio')

    total_citas = citas_proximas.count()
    
    citas_efectivas = Cita.objects.filter(
        idbarberofk=barbero_perfil.idbarbero,
        observaciones__icontains='Completado'
    )
    completadas = citas_efectivas.count()

    producido_dict = citas_efectivas.aggregate(total=Sum('idserviciofk__precioservicio'))
    producido_total = producido_dict['total'] if producido_dict['total'] is not None else 0.0
    comision_estimada = float(producido_total) * 0.50
    
    context = {
        'citas': citas_proximas,
        'total_citas': total_citas,
        'completadas': completadas,
        'producido_total': producido_total,
        'comision_estimada': comision_estimada,
    }
    return render(request, 'barbero.html', context)


@login_required
def completar_cita(request, cita_id):
    cita = get_object_or_404(Cita, idcita=cita_id)

    # Idempotencia: si ya estaba completada, no volvemos a disparar notificaciones.
    if cita.esta_completada:
        return redirect('panel_barbero')

    cita.observaciones = "Completado - Servicio realizado"
    cita.save()

    # Al completarse la cita, el pago queda cerrado/confirmado (ya no editable).
    if cita.idpagofk and cita.idpagofk.estadopago != Pago.ESTADO_CANCELADO:
        cita.idpagofk.estadopago = Pago.ESTADO_PAGADO
        cita.idpagofk.save()

    try:
        barbero_usuario = cita.idbarberofk.idusuariofk
        cliente_usuario = cita.idclientefk.idusuariofk

        mensaje = (
            f"El barbero {barbero_usuario.nombre} confirmó exitosamente la cita de "
            f"{cliente_usuario.nombre} ({cita.idserviciofk.nombreservicio if cita.idserviciofk else 'servicio'})."
        )

        admins = Usuario.objects.filter(idrolfk_id=1)
        for admin in admins:
            Notificacion.objects.create(
                idusuariofk=admin,
                tipo='cita_confirmada',
                mensaje=mensaje
            )
    except Exception as e:
        print(f"DEBUG: No se pudo crear la notificación de confirmación: {e}")

    return redirect('panel_barbero')

@login_required
def marcar_incompleta(request, cita_id):
    cita = get_object_or_404(Cita, idcita=cita_id)
    
    if cita.esta_incompleta or cita.esta_completada:
        return redirect('panel_barbero')
    
    cita.observaciones = "Incompleta - Cliente no asistió"
    cita.save()
    
    if cita.idpagofk:
        cita.idpagofk.estadopago = "CANCELADO"
        cita.idpagofk.save()
        
    try:
        cliente_usuario = cita.idclientefk.idusuariofk if (cita.idclientefk and cita.idclientefk.idusuariofk) else None 
        if cliente_usuario:
            Notificacion.objects.create(
                idusuariofk=cliente_usuario,
                tipo='cita_incompleta',
                mensaje=(
                    f"Tu cita para el servicio de {cita.idserviciofk.nombreservicio if cita.idserviciofk else 'servicio'} "
                    f" ha sido marcada como Incompleta debido a la inasistencia."
                )
            )
    except Exception as e:
        print(f"DEBUG: No se pudo crear la notificacion de inasistencia: {e}")
        
    messages.warning(request, f"La cita #{cita.idcita} se ha marcado como Incompleta.")
    return redirect('panel_barbero')
        
        
# =========================================================================
# 5b. RESERVA SIMPLIFICADA (sin pasarela de pago) Y EDICIÓN DE MÉTODO DE PAGO
# =========================================================================
@login_required
@require_POST
def crear_reserva(request):
    """
    Crea la Cita + el registro de Pago asociado a partir del formulario de
    reservas.html. NO se integra con ninguna pasarela real: el método de
    pago elegido (Efectivo / PSE / Tarjeta) se guarda tal cual, junto con
    el monto del servicio, y la cita queda agendada de inmediato.

    Nota: si ya tienes una vista existente (p. ej. en negocio/views.py) que
    valida disponibilidad de agenda y crea la Cita, reemplaza ahí la parte
    de creación del Pago/Cita por la lógica de abajo; lo importante es que
    el guardado del método de pago no dependa de ningún formulario de
    tarjeta/banco.
    """
    try:
        usuario_manual = Usuario.objects.get(correo=request.user.email)
        cliente = Cliente.objects.get(idusuariofk=usuario_manual)
    except (Usuario.DoesNotExist, Cliente.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'Tu perfil de cliente no está configurado.'}, status=400)

    servicio_id = request.POST.get('servicio')
    barbero_id = request.POST.get('barbero')
    fecha = request.POST.get('fecha')
    hora = request.POST.get('hora')
    metodo_pago = (request.POST.get('metodo_pago') or '').strip()
    observaciones = (request.POST.get('observaciones') or '').strip()

    metodos_validos = dict(Pago.METODO_PAGO_CHOICES)
    if metodo_pago not in metodos_validos:
        return JsonResponse({'ok': False, 'error': 'Selecciona un método de pago válido.'}, status=400)

    if not all([servicio_id, barbero_id, fecha, hora]):
        return JsonResponse({'ok': False, 'error': 'Completa servicio, barbero, fecha y hora.'}, status=400)

    try:
        servicio = Servicio.objects.get(idservicio=servicio_id)
        barbero = Barbero.objects.get(idbarbero=barbero_id)
    except (Servicio.DoesNotExist, Barbero.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'Servicio o barbero no válido.'}, status=400)

    try:
        with transaction.atomic():
            # Aquí reutiliza tu lógica actual de búsqueda/creación de Agenda
            # para (barbero, fecha, hora). Se deja como placeholder explícito
            # porque esa parte no formaba parte de este archivo.
            agenda, _ = Agenda.objects.get_or_create(
                idbarberofk=barbero,
                fecha=fecha,
                horainicio=hora,
            )

            # El pago se cierra directamente: sin pasarela, sin validación bancaria.
            # Efectivo se cobra en el local -> queda PENDIENTE; los demás métodos
            # se registran como PAGADO porque el usuario ya "confirmó" el pago
            # en el flujo simplificado.
            estado_inicial = (
                Pago.ESTADO_PENDIENTE if metodo_pago == Pago.METODO_EFECTIVO
                else Pago.ESTADO_PAGADO
            )

            pago = Pago.objects.create(
                metodopago=metodo_pago,
                montototal=servicio.precioservicio,
                fechapago=timezone.now(),
                estadopago=estado_inicial,
            )

            cita = Cita.objects.create(
                idclientefk=cliente,
                idbarberofk=barbero,
                idserviciofk=servicio,
                idagendafk=agenda,
                idpagofk=pago,
                observaciones=observaciones,
            )
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'No se pudo agendar la cita: {e}'}, status=400)

    return JsonResponse({'ok': True, 'redirect': reverse('home')})


@login_required
@require_POST
def editar_metodo_pago(request, cita_id):
    """
    Permite al barbero (o admin) asignado a la cita cambiar el método de
    pago registrado, siempre que la cita NO esté completada. Se usa desde
    el botón "Editar" del dashboard del barbero, vía AJAX.
    """
    cita = get_object_or_404(Cita, idcita=cita_id)

    try:
        usuario_manual = Usuario.objects.get(correo=request.user.email)
    except Usuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Usuario no válido.'}, status=403)

    es_barbero_asignado = (
        usuario_manual.idrolfk_id == ID_ROL_BARBERO and
        cita.idbarberofk.idusuariofk_id == usuario_manual.idusuario
    )
    es_admin = usuario_manual.idrolfk_id == ID_ROL_ADMIN

    if not (es_barbero_asignado or es_admin):
        return JsonResponse({'ok': False, 'error': 'No tienes permiso para editar esta cita.'}, status=403)

    # --- Bloqueo backend: cita completada = inmutable ---
    if cita.esta_completada:
        return JsonResponse(
            {'ok': False, 'error': 'La cita ya fue completada; el método de pago no se puede modificar.'},
            status=400
        )

    nuevo_metodo = (request.POST.get('metodo_pago') or '').strip()
    metodos_validos = dict(Pago.METODO_PAGO_CHOICES)
    if nuevo_metodo not in metodos_validos:
        return JsonResponse({'ok': False, 'error': 'Método de pago no válido.'}, status=400)

    if cita.idpagofk:
        pago = cita.idpagofk
        pago.metodopago = nuevo_metodo
        pago.save()
    else:
        pago = Pago.objects.create(
            metodopago=nuevo_metodo,
            montototal=cita.idserviciofk.precioservicio if cita.idserviciofk else None,
            fechapago=timezone.now(),
            estadopago=Pago.ESTADO_PENDIENTE,
        )
        cita.idpagofk = pago
        cita.save()

    return JsonResponse({
        'ok': True,
        'metodo_pago': nuevo_metodo,
        'metodo_pago_display': metodos_validos[nuevo_metodo],
    })


def olvide_contrasena(request):
    if request.method == 'POST':
        correo = (request.POST.get('identificador') or request.POST.get('correo') or '').strip()

        usuario = Usuario.objects.filter(correo__iexact=correo).first()

        if usuario:
            signer = TimestampSigner()
            token = signer.sign(usuario.idusuario)
            link = request.build_absolute_uri(reverse('cambiar_contrasena', args=[token]))

            asunto = 'Recuperación de Contraseña - M&A Barbería'
            mensaje = (
                f"Hola {usuario.nombre},\n\n"
                f"Has solicitado restablecer tu contraseña para ingresar a M&A Barbería.\n"
                f"Haz clic en el siguiente enlace para crear una nueva contraseña:\n\n"
                f"{link}\n\n"
                f"Este enlace es válido únicamente durante 1 hora.\n"
                f"Si no solicitaste este cambio, puedes ignorar este mensaje."
            )
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.correo],
                fail_silently=False,
            )

            return render(request, 'mensaje_enviado.html')
        else:
            messages.error(request, "No encontramos ninguna cuenta con ese correo electrónico.")
            return render(request, 'olvide_contrasena.html')

    return render(request, 'olvide_contrasena.html')

def cambiar_contrasena(request, token):
    signer = TimestampSigner()
    
    try:
        # max_age=3600 valida que el token no tenga más de 1 hora (3600 segundos)
        id_usuario = signer.unsign(token, max_age=3600)
        usuario = Usuario.objects.get(pk=id_usuario)
    except SignatureExpired:
        messages.error(request, "El enlace ha expirado. Por favor, solicita uno nuevo.")
        return redirect('olvide_contrasena')
    except (BadSignature, Usuario.DoesNotExist):
        messages.error(request, "El enlace de recuperación no es válido o está corrupto.")
        return redirect('iniciar_sesion')

    if request.method == 'POST':
        nueva_pass = request.POST.get('contrasena')
        confirmar = request.POST.get('confirmar')
        
        if nueva_pass == confirmar:
            # Actualiza la contraseña en tu modelo personalizado
            usuario.contrasena = make_password(nueva_pass)
            usuario.save()
            
            # Sincroniza con el modelo nativo de Django (si aplica en tu sistema)
            try:
                user_auth = User.objects.get(username=usuario.correo) 
                user_auth.set_password(nueva_pass)
                user_auth.save()
            except User.DoesNotExist:
                pass

            messages.success(request, "¡Tu contraseña se ha actualizado correctamente! Ya puedes iniciar sesión.")
            return redirect('iniciar_sesion')
        else:
            messages.error(request, "Las contraseñas no coinciden. Inténtalo de nuevo.")

    return render(request, 'cambiar_contrasena.html')

@login_required
def perfil_usuario(request):
    try:
        usuario_manual = Usuario.objects.get(correo=request.user.email)
    except Usuario.DoesNotExist:
        messages.error(request, "No se encontraron datos registrados.")
        return redirect('home')
        
    return render(request, 'perfil.html', {'usuario': usuario_manual})

@login_required
def guardar_perfil(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre_profesional') or request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        especialidades = request.POST.get('especialidades')
        password_actual = request.POST.get('password_actual')
        password_nueva = request.POST.get('password_nueva')
        
        user_django = authenticate(username=request.user.username, password=password_actual)
        
        if user_django is not None:
            try:
                usuario_manual = Usuario.objects.get(correo=request.user.email)
                
                usuario_manual.nombre = nombre
                usuario_manual.numcelular = telefono

                # Especialidades y bio solo llegan desde el formulario del
                # barbero (perfil.html los muestra solo si idrolfk_id == 2),
                # pero se guardan igual si vienen en el POST.
                if especialidades is not None:
                    usuario_manual.especialidades = especialidades.strip()
                
                
                request.session['usuario_nombre'] = nombre
                
                if password_nueva and password_nueva.strip() != "":
                    usuario_manual.contrasena = make_password(password_nueva)
                    user_django.set_password(password_nueva)
                    user_django.save()
                    auth_login(request, user_django)
                
                usuario_manual.save()
                messages.success(request, "¡Perfil actualizado con éxito!")
                
            except Exception as e:
                messages.error(request, f"Ocurrió un error al guardar los datos: {e}")
        else:
            messages.error(request, "La contraseña actual es incorrecta. No se realizaron cambios.")
            
    return redirect('perfil_usuario')

# =========================================================================
# 6. VISTAS: ADMINISTRACIÓN - EDICIÓN DE PERFILES
# =========================================================================

def editar_perfiles_admin(request):
    ID_ROL_BARBERO = 2
    ID_ROL_CLIENTE = 3

    rol_barbero = get_object_or_404(Rol, pk=ID_ROL_BARBERO)
    rol_cliente = get_object_or_404(Rol, pk=ID_ROL_CLIENTE)

    if request.method == 'POST' and 'guardar_cambios' in request.POST:
        usuarios_ids = request.POST.getlist('usuario_id')
        errores = []

        for u_id in usuarios_ids:
            usuario = get_object_or_404(Usuario, pk=u_id)

            nuevo_correo = request.POST.get(f'correo_{u_id}')
            nuevo_celular = request.POST.get(f'celular_{u_id}')
            nuevo_rol_id = request.POST.get(f'rol_{u_id}')

            rol_anterior_id = usuario.idrolfk_id

            try:
                with transaction.atomic():
                    if nuevo_correo:
                        antiguo_correo = usuario.correo
                        usuario.correo = nuevo_correo
                    if nuevo_celular:
                        usuario.numcelular = nuevo_celular

                    if nuevo_correo and antiguo_correo != nuevo_correo:
                        User.objects.filter(username=antiguo_correo).update(
                            username=nuevo_correo, email=nuevo_correo
                        )

                    if nuevo_rol_id:
                        usuario.idrolfk_id = int(nuevo_rol_id)

                    usuario.save()

                    # Antes: trigger DespuesActualizarUsuarioCambioRol (AFTER UPDATE)
                    if nuevo_rol_id:
                        sincronizar_cambio_rol(usuario, rol_anterior_id, int(nuevo_rol_id))

            except Exception as e:
                errores.append(f"{usuario.nombre}: {e}")

        if errores:
            messages.error(
                request,
                "Algunos perfiles no se pudieron actualizar: " + " | ".join(errores)
            )
        else:
            messages.success(request, "¡Los perfiles se actualizaron correctamente!")

        return redirect('editar_perfiles')

    usuarios = Usuario.objects.filter(idrolfk_id__in=[ID_ROL_BARBERO, ID_ROL_CLIENTE]).order_by('nombre')
    roles_disponibles = Rol.objects.filter(idrol__in=[ID_ROL_BARBERO, ID_ROL_CLIENTE])

    return render(request, 'editar_perfiles.html', {
        'usuarios': usuarios,
        'roles_disponibles': roles_disponibles
    })

def eliminar_perfil(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)

    error_bloqueo = validar_eliminacion_usuario(usuario)
    if error_bloqueo:
        messages.error(request, error_bloqueo)
        return redirect('editar_perfiles')

    nombre_eliminado = usuario.nombre
    correo_eliminado = usuario.correo

    try:
        with transaction.atomic():
            for cliente in Cliente.objects.filter(idusuariofk=usuario):
                _cascada_borrar_cliente(cliente)
            for barbero in Barbero.objects.filter(idusuariofk=usuario):
                _cascada_borrar_barbero(barbero)

            usuario.delete()  # Notificacion se borra sola (on_delete=CASCADE)

            # --- Limpieza de todo lo que allauth pudo crear ---
            user_django = User.objects.filter(username=correo_eliminado).first()
            if user_django:
                SocialToken.objects.filter(account__user=user_django).delete()
                SocialAccount.objects.filter(user=user_django).delete()
                EmailAddress.objects.filter(user=user_django).delete()
                PerfilUsuario.objects.filter(user=user_django).delete()
                user_django.groups.clear()
                user_django.user_permissions.clear()
                LogEntry.objects.filter(user=user_django).delete()

                # --- IMPORTANTE: NO usar user_django.delete() ---
                # El collector de Django recorre TODAS las relaciones hacia
                # auth_user declaradas en tus modelos, incluida una que
                # parece existir en Usuario (campo "user") pero sin columna
                # real en la BD ("usuario.user_id"). Por eso truena con 1054.
                # Borramos la fila directo con SQL para saltarnos ese recorrido.
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_django.pk])

    except Exception as e:
        messages.error(
            request,
            f"No se pudo eliminar a '{nombre_eliminado}'. Detalle técnico: {e}"
        )
        return redirect('editar_perfiles')

    messages.success(
        request,
        f"Se ha eliminado a {nombre_eliminado} de forma permanente, junto con sus citas, agendas, calificaciones y su cuenta de acceso (incluida la de Google si aplicaba)."
    )
    return redirect('editar_perfiles')

@login_required
def gestionar_foto_perfil(request):
    if request.method == 'POST':
        usuario = Usuario.objects.get(correo=request.user.email)
        accion = request.POST.get('accion')

        if accion == 'cambiar' and 'nueva_foto' in request.FILES:
            archivo = request.FILES['nueva_foto']
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            
            nombre_archivo = f"perfiles/usuario_{usuario.idusuario}_{archivo.name}"
            
            if fs.exists(nombre_archivo):
                fs.delete(nombre_archivo)
            fs.save(nombre_archivo, archivo)
            
            usuario.foto_perfil = nombre_archivo
            usuario.save()
            request.session['usuario_foto'] = usuario.foto_perfil.url
            
            messages.success(request, "Foto actualizada.")

        elif accion == 'borrar':
            if usuario.foto_perfil:
                ruta_fisica = os.path.join(settings.MEDIA_ROOT, str(usuario.foto_perfil))
                if os.path.exists(ruta_fisica):
                    os.remove(ruta_fisica)
            
            usuario.foto_perfil = None
            usuario.save()
            messages.success(request, "Foto eliminada.")
            
    return redirect('perfil_usuario')

@login_required
def dashboard_admin(request):
    usuario_rol = request.session.get('usuario_rol_id')
    if usuario_rol != 1:
        messages.error(request, "Acceso denegado. No tienes permisos de administrador.")
        return redirect('home')

    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)

    total_citas_hoy = Cita.objects.filter(idagendafk__fecha=hoy).count()

    total_clientes = Cliente.objects.count()

    ingresos_mes_dict = Cita.objects.filter(
        idagendafk__fecha__gte=inicio_mes,
        idagendafk__fecha__lte=hoy,
        observaciones__icontains='Completado'
    ).aggregate(total=Sum('idserviciofk__precioservicio'))
    
    ingresos_mes = ingresos_mes_dict['total'] if ingresos_mes_dict['total'] is not None else 0.0

    barberos_hoy = Agenda.objects.filter(fecha=hoy).values('idbarberofk').distinct().count()
    total_barberos = Barbero.objects.count()
    barberos_turno_string = f"{barberos_hoy} / {total_barberos}"

    proximas_citas = Cita.objects.filter(
        idagendafk__fecha=hoy
    ).select_related('idclientefk__idusuariofk', 'idbarberofk__idusuariofk', 'idserviciofk', 'idagendafk').order_by('idagendafk__horainicio')[:10]

    context = {
        'total_citas_hoy': total_citas_hoy,
        'total_clientes': total_clientes,
        'ingresos_mes': ingresos_mes,
        'barberos_turno': barberos_turno_string,
        'proximas_citas': proximas_citas,
    }

    return render(request, 'dashboard_admin.html', context)

@login_required
def ver_todas_citas_admin(request):
    usuario_rol = request.session.get('usuario_rol_id')
    if usuario_rol != 1:
        messages.error(request, "Acceso denegado. No tienes permisos de administrador.")
        return redirect('home')

    todas_citas = Cita.objects.select_related(
        'idclientefk__idusuariofk', 
        'idbarberofk__idusuariofk', 
        'idserviciofk', 
        'idagendafk'
    ).order_by('-idagendafk__fecha', '-idagendafk__horainicio')

    return render(request, 'citas_admin.html', {'citas': todas_citas})


# =========================================================================
# 7. VISTAS: SISTEMA DE NOTIFICACIONES (Campanita)
# =========================================================================

@login_required
def listar_notificaciones(request):
    try:
        usuario = Usuario.objects.get(correo=request.user.email)
    except Usuario.DoesNotExist:
        return JsonResponse({'notificaciones': [], 'no_leidas': 0})

    notifs = Notificacion.objects.filter(idusuariofk=usuario)[:20]

    data = [{
        'id': n.idnotificacion,
        'tipo': n.tipo,
        'mensaje': n.mensaje,
        'leida': n.leida,
        'fecha': n.fechacreacion.strftime('%d/%m/%Y %H:%M'),
    } for n in notifs]

    no_leidas = Notificacion.objects.filter(idusuariofk=usuario, leida=False).count()

    return JsonResponse({'notificaciones': data, 'no_leidas': no_leidas})


@login_required
def marcar_notificaciones_leidas(request):
    if request.method == 'POST':
        try:
            usuario = Usuario.objects.get(correo=request.user.email)
            Notificacion.objects.filter(idusuariofk=usuario, leida=False).update(leida=True)
        except Usuario.DoesNotExist:
            pass
    return JsonResponse({'ok': True})

# =========================================================================
# 8. VISTA: ANALIZAR FORMA DE ROSTRO
# =========================================================================
# ELIMINADA de aquí a propósito. analisis_rostro_view y analizar_rostro_ajax
# ahora viven, intactas (mismo código, mismo comportamiento), en
# analisis_facial/views.py. Las urls con name='analisis_rostro' y
# name='analizar_rostro_ajax' se sirven desde ahí (ver barbershopmya/urls.py
# y usuarios/urls.py — este último ya NO debe tener esas dos rutas).
# No hace falta tocar ningún template: usan los mismos `name=` de siempre.

# =========================================================================
# 9. VISTAS: SISTEMA DE CALIFICACIONES Y RESEÑAS
# =========================================================================

@login_required
def verificar_calificacion_pendiente(request):
    try:
        usuario = Usuario.objects.get(correo=request.user.email)
        cliente = Cliente.objects.get(idusuariofk=usuario)
    except (Usuario.DoesNotExist, Cliente.DoesNotExist):
        return JsonResponse({'pendiente': False})

    # Citas que el usuario omitió "por ahora" durante ESTA sesión.
    # Se reinicia al cerrar sesión (request.session.flush() en cerrar_sesion).
    citas_omitidas_sesion = request.session.get('citas_omitidas_calificacion', [])

    cita_pendiente = Cita.objects.filter(
        idclientefk=cliente,
        observaciones__icontains='Completado',
        calificacion__isnull=True,
    ).exclude(
        idcita__in=citas_omitidas_sesion
    ).select_related(
        'idserviciofk', 'idbarberofk__idusuariofk'
    ).order_by('-idagendafk__fecha').first()

    if not cita_pendiente:
        return JsonResponse({'pendiente': False})

    return JsonResponse({
        'pendiente': True,
        'cita_id': cita_pendiente.idcita,
        'servicio': cita_pendiente.idserviciofk.nombreservicio if cita_pendiente.idserviciofk else 'tu servicio',
        'barbero': cita_pendiente.idbarberofk.idusuariofk.nombre if cita_pendiente.idbarberofk else '',
    })

@login_required
@require_POST
def guardar_calificacion(request):
    try:
        usuario = Usuario.objects.get(correo=request.user.email)
        cliente = Cliente.objects.get(idusuariofk=usuario)
    except (Usuario.DoesNotExist, Cliente.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'No se encontró tu perfil de cliente.'}, status=404)

    cita_id = request.POST.get('cita_id')
    estrellas = request.POST.get('calificacion')
    comentario = (request.POST.get('comentario') or '').strip()

    if not cita_id or not estrellas:
        return JsonResponse({'ok': False, 'error': 'Falta la cita o la calificación en estrellas.'}, status=400)

    try:
        estrellas = int(estrellas)
        if estrellas < 1 or estrellas > 5:
            raise ValueError
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'La calificación debe ser un número entre 1 y 5.'}, status=400)

    cita = get_object_or_404(Cita, idcita=cita_id, idclientefk=cliente)

    if 'Completado' not in (cita.observaciones or ''):
        return JsonResponse({'ok': False, 'error': 'Esta cita todavía no ha sido finalizada.'}, status=400)

    if Calificacion.objects.filter(idcitafk=cita).exists():
        return JsonResponse({'ok': False, 'error': 'Ya calificaste esta cita.'}, status=400)

    Calificacion.objects.create(
        idcitafk=cita,
        idclientefk=cliente,
        calificacion=estrellas,
        comentario=comentario if comentario else None
    )

    return JsonResponse({'ok': True, 'mensaje': '¡Gracias por tu calificación!'})

@login_required
@require_POST
def omitir_calificacion(request):
    """
    Oculta el aviso de calificación para esta cita SOLO durante la sesión
    actual (hasta que el usuario cierre sesión). Si vuelve a iniciar sesión
    y la cita sigue sin calificar, el aviso vuelve a aparecer.
    """
    try:
        usuario = Usuario.objects.get(correo=request.user.email)
        cliente = Cliente.objects.get(idusuariofk=usuario)
    except (Usuario.DoesNotExist, Cliente.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'No se encontró tu perfil de cliente.'}, status=404)

    cita_id = request.POST.get('cita_id')
    if not cita_id:
        return JsonResponse({'ok': False, 'error': 'Falta el identificador de la cita.'}, status=400)

    cita = get_object_or_404(Cita, idcita=cita_id, idclientefk=cliente)

    # Si ya la calificó, no hace falta guardar nada.
    if not Calificacion.objects.filter(idcitafk=cita).exists():
        citas_omitidas = request.session.get('citas_omitidas_calificacion', [])
        cita_id_int = int(cita_id)
        if cita_id_int not in citas_omitidas:
            citas_omitidas.append(cita_id_int)
        request.session['citas_omitidas_calificacion'] = citas_omitidas

    return JsonResponse({'ok': True})