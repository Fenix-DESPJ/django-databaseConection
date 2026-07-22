# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
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

# Importación de tus modelos manuales
from .models import Usuario, Rol, Cita, Servicio, Cliente, Notificacion, Calificacion
from negocio.models import Barbero, Agenda
from .utils import analizar_forma_rostro, RostroNoDetectadoError, RECOMENDACIONES_POR_FORMA


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
        usuario_input = request.POST.get('identificador')  
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

        # Autenticación con Django Auth
        user = authenticate(request, username=usuario_input, password=contrasena_input)
        
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
                
                # --- INTEGRACIÓN DE FOTO DE PERFIL ---
                # Usamos .url para obtener la ruta completa (ej: /media/perfiles/foto.jpg)
                if usuario_manual.foto_perfil:
                    request.session['usuario_foto'] = usuario_manual.foto_perfil.url
                else:
                    request.session['usuario_foto'] = None
                # -------------------------------------
                
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
            messages.error(request, "El correo o la contraseña son incorrectos.")
            return redirect('iniciar_sesion')
            
    return render(request, 'iniciarsesion.html')

# =========================================================================
# 2. VISTA: CERRAR SESIÓN
# =========================================================================
def cerrar_sesion(request):
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

    return render(request, 'index.html', {'calificaciones': mejores_calificaciones})

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

    citas_proximas = Cita.objects.filter(
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
    cita.observaciones = "Completado - Servicio realizado"
    cita.save()

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


def olvide_contrasena(request):
    if request.method == 'POST':
        email = request.POST.get('correo')
        usuario = Usuario.objects.filter(correo=email).first()
        
        if usuario:
            signer = TimestampSigner()
            token = signer.sign(usuario.idusuario) 
            link = request.build_absolute_uri(reverse('cambiar_contrasena', args=[token]))
            
            send_mail(
                'Recuperación de contraseña',
                f'Hola {usuario.nombre}, haz clic aquí para cambiar tu contraseña: {link}',
                'tu-barberia@email.com',
                [usuario.correo],
                fail_silently=False,
            )
            return render(request, 'mensaje_enviado.html')
            
    return render(request, 'olvide_contrasena.html')


def cambiar_contrasena(request, token):
    signer = TimestampSigner()
    try:
        id_usuario = signer.unsign(token, max_age=3600)
        usuario = Usuario.objects.get(pk=id_usuario)
    except SignatureExpired:
        messages.error(request, "El enlace ha expirado. Solicita uno nuevo.")
        return redirect('olvide_contrasena')
    except (BadSignature, Usuario.DoesNotExist):
        messages.error(request, "El enlace no es válido.")
        return redirect('iniciar_sesion')

    if request.method == 'POST':
        nueva_pass = request.POST.get('contrasena')
        confirmar = request.POST.get('confirmar')
        
        if nueva_pass == confirmar:
            usuario.contrasena = make_password(nueva_pass)
            usuario.save()
            
            try:
                user_auth = User.objects.get(username=usuario.correo) 
                user_auth.set_password(nueva_pass)
                user_auth.save()
            except User.DoesNotExist:
                pass

            messages.success(request, "Contraseña actualizada correctamente. Ya puedes iniciar sesión.")
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
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        password_actual = request.POST.get('password_actual')
        password_nueva = request.POST.get('password_nueva')
        
        user_django = authenticate(username=request.user.username, password=password_actual)
        
        if user_django is not None:
            try:
                usuario_manual = Usuario.objects.get(correo=request.user.email)
                
                usuario_manual.nombre = nombre
                usuario_manual.numcelular = telefono
                
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

            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM auth_user WHERE username = %s", [correo_eliminado])

    except Exception as e:
        messages.error(
            request,
            f"No se pudo eliminar a '{nombre_eliminado}'. Detalle técnico: {e}"
        )
        return redirect('editar_perfiles')

    messages.success(request, f"Se ha eliminado a {nombre_eliminado} de forma permanente, junto con sus citas, agendas y calificaciones asociadas.")
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

def analisis_rostro_view(request):
    return render(request, 'analisis_rostro.html')


@login_required
@require_POST
def analizar_rostro_ajax(request):
    usar_perfil = request.POST.get('usar_perfil') == 'true'
    ruta_temporal = None
    es_archivo_temporal_propio = False

    try:
        if usar_perfil:
            try:
                usuario_actual = Usuario.objects.get(correo=request.user.email)
            except Usuario.DoesNotExist:
                return JsonResponse({
                    'ok': False,
                    'error': 'No encontramos tu perfil registrado. Intenta con la cámara en su lugar.'
                }, status=404)

            if not usuario_actual.foto_perfil:
                return JsonResponse({
                    'ok': False,
                    'error': 'Aún no tienes una foto de perfil registrada. Usa la cámara o sube una imagen para continuar.'
                }, status=400)

            ruta_fisica_perfil = os.path.join(settings.MEDIA_ROOT, str(usuario_actual.foto_perfil))
            if not os.path.exists(ruta_fisica_perfil):
                return JsonResponse({
                    'ok': False,
                    'error': 'Tu foto de perfil no se encuentra disponible en el servidor. Por favor usa la cámara o sube una nueva imagen.'
                }, status=404)

            ruta_temporal = ruta_fisica_perfil
            es_archivo_temporal_propio = False

        else:
            archivo = request.FILES.get('imagen')
            if not archivo:
                return JsonResponse({
                    'ok': False,
                    'error': 'No se recibió ninguna imagen. Captura una foto o selecciona un archivo.'
                }, status=400)

            extensiones_validas = ('.jpg', '.jpeg', '.png', '.webp')
            nombre_original = archivo.name.lower()
            if not nombre_original.endswith(extensiones_validas):
                return JsonResponse({
                    'ok': False,
                    'error': 'Formato de imagen no soportado. Usa JPG, PNG o WEBP.'
                }, status=400)

            if archivo.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'ok': False,
                    'error': 'La imagen es demasiado pesada (máximo 5MB).'
                }, status=400)

            carpeta_temporal = tempfile.gettempdir()
            extension = os.path.splitext(nombre_original)[1]
            nombre_temporal = f"analisis_rostro_{uuid.uuid4().hex}{extension}"
            ruta_temporal = os.path.join(carpeta_temporal, nombre_temporal)

            with open(ruta_temporal, 'wb+') as destino:
                for chunk in archivo.chunks():
                    destino.write(chunk)

            es_archivo_temporal_propio = True

        resultado = analizar_forma_rostro(ruta_temporal)
        forma_detectada = resultado['forma']

        return JsonResponse({
            'ok': True,
            'forma': forma_detectada,
            'metricas': resultado['metricas'],
            'recomendacion': RECOMENDACIONES_POR_FORMA.get(forma_detectada, ''),
        })

    except RostroNoDetectadoError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=422)

    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': f'Ocurrió un problema al procesar la imagen: {e}'
        }, status=500)

    finally:
        if ruta_temporal and es_archivo_temporal_propio and os.path.exists(ruta_temporal):
            try:
                os.remove(ruta_temporal)
            except OSError:
                pass
            
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

    cita_pendiente = Cita.objects.filter(
        idclientefk=cliente,
        observaciones__icontains='Completado',
        calificacion__isnull=True
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