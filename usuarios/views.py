# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
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
from datetime import timedelta

# Importación de tus modelos manuales
from .models import Usuario, Rol, Cita, Servicio, Cliente, Notificacion
from negocio.models import Barbero, Agenda

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

            nuevo_usuario_manual = Usuario.objects.create(
                cedula=cedula,
                nombre=f"{nombre} {apellido}",
                correo=correo,
                contrasena=make_password(password),  
                numcelular=telefono,
                fechanacimiento=fecha,
                idrolfk=rol_cliente
            )

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
    return render(request, 'index.html')

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

    # MODIFICADO: __gte=hoy hace que muestre las citas de HOY en adelante (mañana, pasado mañana, etc.)
    citas_proximas = Cita.objects.filter(
        idbarberofk=barbero_perfil.idbarbero, 
        idagendafk__fecha__gte=hoy
    ).order_by('idagendafk__fecha', 'idagendafk__horainicio')

    total_citas = citas_proximas.count()
    
    # Las estadísticas de completadas y ganancias las seguimos midiendo sobre las que ya marcó como Completadas
    citas_efectivas = Cita.objects.filter(
        idbarberofk=barbero_perfil.idbarbero,
        observaciones__icontains='Completado'
    )
    completadas = citas_efectivas.count()

    producido_dict = citas_efectivas.aggregate(total=Sum('idserviciofk__precioservicio'))
    producido_total = producido_dict['total'] if producido_dict['total'] is not None else 0.0
    comision_estimada = float(producido_total) * 0.50
    
    context = {
        'citas': citas_proximas,  # Enviamos las citas de hoy y del futuro
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

    # =====================================================================
    # NUEVO: Notificar a TODOS los administradores que el barbero confirmó
    # =====================================================================
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
        # Recuperamos al usuario de tu tabla manual
        usuario_manual = Usuario.objects.get(correo=request.user.email)
    except Usuario.DoesNotExist:
        messages.error(request, "No se encontraron datos registrados.")
        return redirect('home')
        
    # Pasamos el objeto al template
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
                
                # 1. Actualizar en la base de datos
                usuario_manual.nombre = nombre
                usuario_manual.numcelular = telefono
                
                # ========================================================
                # 2. ¡AQUÍ ESTÁ EL TRUCO! Actualizamos la sesión del navegador
                # ========================================================
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
    
    # PROCESAR GUARDAR CAMBIOS (SE MANTEIENE)
    if request.method == 'POST' and 'guardar_cambios' in request.POST:
        usuarios_ids = request.POST.getlist('usuario_id')
        
        for u_id in usuarios_ids:
            usuario = get_object_or_404(Usuario, pk=u_id)
            
            nuevo_correo = request.POST.get(f'correo_{u_id}')
            nuevo_celular = request.POST.get(f'celular_{u_id}')
            nuevo_rol_id = request.POST.get(f'rol_{u_id}')
            
            if nuevo_correo: 
                antiguo_correo = usuario.correo
                usuario.correo = nuevo_correo
            if nuevo_celular: 
                usuario.numcelular = nuevo_celular
            
            if nuevo_correo and antiguo_correo != nuevo_correo:
                User.objects.filter(username=antiguo_correo).update(username=nuevo_correo, email=nuevo_correo)
            
            if nuevo_rol_id:
                rol_final_id = int(nuevo_rol_id)
                
                if usuario.idrolfk_id == ID_ROL_CLIENTE and rol_final_id == ID_ROL_BARBERO:
                    usuario.idrolfk = rol_barbero
                    Barbero.objects.get_or_create(idusuariofk=usuario)
                    Cliente.objects.filter(idusuariofk=usuario).delete()
                
                elif usuario.idrolfk_id == ID_ROL_BARBERO and rol_final_id == ID_ROL_CLIENTE:
                    usuario.idrolfk = rol_cliente
                    Cliente.objects.get_or_create(idusuariofk=usuario)
                    Barbero.objects.filter(idusuariofk=usuario).delete()
            
            usuario.save()
            
        messages.success(request, "¡Los perfiles se actualizaron correctamente!")
        return redirect('editar_perfiles')

    # EL BLOQUE DE 'agregar_barbero' HA SIDO REMOVIDO DE AQUÍ

    # OBTENER DATOS PARA EL TEMPLATE
    usuarios = Usuario.objects.filter(idrolfk_id__in=[ID_ROL_BARBERO, ID_ROL_CLIENTE]).order_by('nombre')
    roles_disponibles = Rol.objects.filter(idrol__in=[ID_ROL_BARBERO, ID_ROL_CLIENTE])

    return render(request, 'editar_perfiles.html', {
        'usuarios': usuarios,
        'roles_disponibles': roles_disponibles
    })


def eliminar_perfil(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    nombre_eliminado = usuario.nombre
    correo_eliminado = usuario.correo

    cliente_perfil = Cliente.objects.filter(idusuariofk=usuario).first()
    barberos_perfil = list(Barbero.objects.filter(idusuariofk=usuario))  # puede haber más de uno

    # --- 1. Citas pendientes como CLIENTE ---
    if cliente_perfil:
        citas_pendientes_cliente = Cita.objects.filter(
            idclientefk=cliente_perfil
        ).exclude(observaciones__icontains='Completado')

        if citas_pendientes_cliente.exists():
            num_citas = citas_pendientes_cliente.count()
            messages.error(
                request,
                f"No se puede eliminar a '{nombre_eliminado}' porque tiene {num_citas} cita(s) agendada(s) "
                f"como cliente. Completa o cancela esas citas antes de eliminar su cuenta."
            )
            return redirect('editar_perfiles')

    # --- 2. Citas pendientes como BARBERO (revisando TODAS sus filas de barbero) ---
    if barberos_perfil:
        citas_pendientes_barbero = Cita.objects.filter(
            idbarberofk__in=barberos_perfil
        ).exclude(observaciones__icontains='Completado')

        if citas_pendientes_barbero.exists():
            num_citas = citas_pendientes_barbero.count()
            messages.error(
                request,
                f"No se puede eliminar a '{nombre_eliminado}' porque tiene {num_citas} cita(s) agendada(s) "
                f"como barbero. Completa o cancela esas citas antes de eliminar su cuenta."
            )
            return redirect('editar_perfiles')

    try:
        with transaction.atomic():
            if cliente_perfil:
                Cita.objects.filter(idclientefk=cliente_perfil).delete()

            if barberos_perfil:
                Cita.objects.filter(idbarberofk__in=barberos_perfil).delete()
                Agenda.objects.filter(idbarberofk__in=barberos_perfil).delete()

            Cliente.objects.filter(idusuariofk=usuario).delete()
            Barbero.objects.filter(idusuariofk=usuario).delete()

            usuario.delete()

            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM auth_user WHERE username = %s", [correo_eliminado])

    except Exception as e:
        messages.error(
            request,
            f"No se pudo eliminar a '{nombre_eliminado}'. Es posible que aún tenga información "
            f"relacionada en el sistema. Detalle técnico: {e}"
        )
        return redirect('editar_perfiles')

    messages.success(request, f"Se ha eliminado a {nombre_eliminado} de forma permanente.")
    return redirect('editar_perfiles')

@login_required
def gestionar_foto_perfil(request):
    if request.method == 'POST':
        usuario = Usuario.objects.get(correo=request.user.email)
        accion = request.POST.get('accion')

        if accion == 'cambiar' and 'nueva_foto' in request.FILES:
            archivo = request.FILES['nueva_foto']
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            
            # Nombre del archivo
            nombre_archivo = f"perfiles/usuario_{usuario.idusuario}_{archivo.name}"
            
            # Guardado físico
            if fs.exists(nombre_archivo):
                fs.delete(nombre_archivo)
            fs.save(nombre_archivo, archivo)
            
            # AQUÍ ES DONDE ESTABA EL ERROR: 
            # Ahora que el campo existe en el modelo, lo asignamos así:
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
    # Verificación estricta de seguridad 
    usuario_rol = request.session.get('usuario_rol_id')
    if usuario_rol != 1:  # ID 1 asignado para Administrador
        messages.error(request, "Acceso denegado. No tienes permisos de administrador.")
        return redirect('home')

    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)

    # --- KPI 1: CITAS PARA HOY ---
    total_citas_hoy = Cita.objects.filter(idagendafk__fecha=hoy).count()

    # --- KPI 2: CLIENTES ACTIVOS ---
    total_clientes = Cliente.objects.count()

    # --- KPI 3: INGRESOS DEL MES (Servicios completados en el mes actual) ---
    ingresos_mes_dict = Cita.objects.filter(
        idagendafk__fecha__gte=inicio_mes,
        idagendafk__fecha__lte=hoy,
        observaciones__icontains='Completado'
    ).aggregate(total=Sum('idserviciofk__precioservicio'))
    
    ingresos_mes = ingresos_mes_dict['total'] if ingresos_mes_dict['total'] is not None else 0.0

    # --- KPI 4: BARBEROS EN TURNO HOY ---
    # Contamos cuántos barberos únicos tienen franjas horarias registradas para el día de hoy
    barberos_hoy = Agenda.objects.filter(fecha=hoy).values('idbarberofk').distinct().count()
    total_barberos = Barbero.objects.count()
    barberos_turno_string = f"{barberos_hoy} / {total_barberos}"

    # --- TABLA: PRÓXIMAS CITAS DEL DÍA ---
    # Traemos las citas de hoy ordenadas por su hora de inicio (filtrando las no completadas primero si se desea)
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
    # Verificación de seguridad estricta para el Administrador
    usuario_rol = request.session.get('usuario_rol_id')
    if usuario_rol != 1:
        messages.error(request, "Acceso denegado. No tienes permisos de administrador.")
        return redirect('home')

    # Traemos absolutamente todas las citas del sistema ordenadas por fecha y hora descendente
    # (las más recientes arriba) utilizando select_related para evitar lentitud de base de datos
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
    """
    Devuelve en JSON las notificaciones del usuario logueado (máx. 20 más recientes)
    y el conteo de no leídas. Cada usuario SOLO ve las suyas.
    """
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
    """Marca como leídas todas las notificaciones del usuario logueado."""
    if request.method == 'POST':
        try:
            usuario = Usuario.objects.get(correo=request.user.email)
            Notificacion.objects.filter(idusuariofk=usuario, leida=False).update(leida=True)
        except Usuario.DoesNotExist:
            pass
    return JsonResponse({'ok': True})