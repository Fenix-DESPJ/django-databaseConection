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
import os

# Importación de tus modelos manuales
from .models import Usuario, Rol, Cita, Servicio, Cliente
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
        
        rol_esperado_id = None
        if rol_formulario in ['admin', 'administrador']:
            rol_esperado_id = 1  
        elif rol_formulario == 'barbero':
            rol_esperado_id = 2  
        elif rol_formulario == 'cliente':
            rol_esperado_id = 3  

        print(f"\n--- [DEBUG LOGIN] ---")
        print(f"Texto recibido del HTML: '{rol_formulario}' -> ID esperado: {rol_esperado_id}")

        user = authenticate(request, username=usuario_input, password=contrasena_input)
        
        if user is not None:
            try:
                usuario_manual = Usuario.objects.get(correo=user.email)
                
                try:
                    rol_actual_id = usuario_manual.idrolfk.idrol
                except Exception:
                    rol_actual_id = usuario_manual.idrolfk_id 

                print(f"Usuario encontrado en MySQL: {usuario_manual.nombre}")
                print(f"Rol ID real en la Base de Datos: {rol_actual_id}")
                
                if rol_actual_id != rol_esperado_id:
                    print(f"BLOQUEO: Roles no coinciden (DB: {rol_actual_id} vs Form: {rol_esperado_id})")
                    messages.error(request, "El usuario no corresponde al rol seleccionado.")
                    return redirect('iniciar_sesion')

                auth_login(request, user)
                
                request.session['sesion_iniciada'] = True
                request.session['usuario_nombre'] = user.first_name if user.first_name else user.username
                request.session['usuario_rol_id'] = int(rol_actual_id)
                
                rol_final = int(rol_actual_id)
                
                if rol_final == 1:
                    print("Redirigiendo a panel de Administrador...")
                    return redirect('home')
                elif rol_final == 2:
                    print("¡¡REDIRECCIÓN BARBERO DETECTADA!! Enviando a panel_barbero...")
                    return redirect('panel_barbero')
                else:
                    print("Redirigiendo a Home de Clientes...")
                    return redirect('home')

            except Usuario.DoesNotExist:
                print(f"ERROR: {user.email} está en auth_user pero no en la tabla Usuario de MySQL.")
                messages.error(request, "Tu cuenta no está vinculada correctamente a la barbería.")
                return redirect('iniciar_sesion')
        else:
            print("ERROR: Credenciales incorrectas en auth_user.")
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
            print(f"DEBUG PANEL: Acceso denegado para {usuario_manual.nombre}. Rol actual: {usuario_manual.idrolfk_id}")
            return redirect('home')
        
        barbero_perfil = Barbero.objects.get(idusuariofk=usuario_manual)
        
    except (Usuario.DoesNotExist, Barbero.DoesNotExist):
        print("DEBUG PANEL: El usuario o perfil de barbero no existe.")
        return redirect('home')

    hoy = timezone.now().date()
    citas_hoy = Cita.objects.filter(
        idbarberofk=barbero_perfil, 
        idagendafk__fecha=hoy
    ).order_by('idagendafk__horainicio')

    total_citas = citas_hoy.count()
    completadas = citas_hoy.filter(observaciones__icontains='Completado').count()
    citas_efectivas = citas_hoy.filter(observaciones__icontains='Completado')

    producido_dict = citas_efectivas.aggregate(total=Sum('idserviciofk__precioservicio'))
    producido_total = producido_dict['total'] if producido_dict['total'] is not None else 0.0
    comision_estimada = float(producido_total) * 0.50
    
    context = {
        'citas': citas_hoy,
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
    
    # 1. Verificar si tiene un perfil de cliente asociado
    cliente_perfil = Cliente.objects.filter(idusuariofk=usuario).first()
    
    if cliente_perfil:
        # 2. Buscar si el cliente tiene citas pendientes
        citas_pendientes = Cita.objects.filter(idclientefk=cliente_perfil).exclude(observaciones__icontains='Completado')
        
        if citas_pendientes.exists():
            num_citas = citas_pendientes.count()
            messages.error(
                request, 
                f"No se puede eliminar a '{nombre_eliminado}' porque tiene {num_citas} cita(s) pendiente(s). "
                f"Por favor, completa o cancela sus citas antes de remover su cuenta."
            )
            return redirect('editar_perfiles')
        
        # 3. Limpiar historial de citas del cliente
        Cita.objects.filter(idclientefk=cliente_perfil).delete()

    # 4. Si es un barbero, limpiamos sus citas
    barbero_perfil = Barbero.objects.filter(idusuariofk=usuario).first()
    if barbero_perfil:
        Cita.objects.filter(idbarberofk=barbero_perfil).delete()

    # 5. Borramos de Cliente y Barbero (estas tablas sí existen físicamente)
    Cliente.objects.filter(idusuariofk=usuario).delete()
    Barbero.objects.filter(idusuariofk=usuario).delete()
    
    # =========================================================================
    # SOLUCIÓN DEFINITIVA: SQL PURO TOTAL PARA PASAR DE LARGO DEL ORM
    # =========================================================================
    with connection.cursor() as cursor:
        # Borrado directo en tu tabla operativa 'usuario' de MySQL
        cursor.execute("DELETE FROM usuario WHERE idUsuario = %s", [usuario_id])
        
        # Borrado directo en la tabla de autenticación de Django 'auth_user'
        cursor.execute("DELETE FROM auth_user WHERE username = %s", [correo_eliminado])
    
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
            usuario.save() # Esto funcionará porque el campo ya existe en el modelo
            
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