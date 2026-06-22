from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Q


# Importación de tus modelos manuales
from .models import Usuario, Rol, Cita, Servicio
from negocio.models import Barbero, Agenda

# =========================================================================
# 1. VISTA: INICIAR SESIÓN
# =========================================================================
def iniciar_sesion(request):
    if request.method == 'POST':
        usuario_input = request.POST.get('identificador')  
        contrasena_input = request.POST.get('contrasena')
        rol_formulario = request.POST.get('rol')  
        
        # 1. Aseguramos que el rol del HTML venga limpio y en minúsculas
        if rol_formulario:
            rol_formulario = str(rol_formulario).lower().strip()
        
        # Mapeo manual super estricto
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
                
                # Intentamos obtener el ID del rol de dos maneras por seguridad
                try:
                    rol_actual_id = usuario_manual.idrolfk.idrol
                except Exception:
                    rol_actual_id = usuario_manual.idrolfk_id 

                print(f"Usuario encontrado en MySQL: {usuario_manual.nombre}")
                print(f"Rol ID real en la Base de Datos: {rol_actual_id}")
                
                # 2. Control de seguridad
                if rol_actual_id != rol_esperado_id:
                    print(f"BLOQUEO: Roles no coinciden (DB: {rol_actual_id} vs Form: {rol_esperado_id})")
                    messages.error(request, "El usuario no corresponde al rol seleccionado.")
                    return redirect('iniciar_sesion')

                # 3. Loguear al usuario en Django
                auth_login(request, user)
                
                # Variables de sesión para el navbar
                request.session['sesion_iniciada'] = True
                request.session['usuario_nombre'] = user.first_name if user.first_name else user.username
                request.session['usuario_rol_id'] = int(rol_actual_id)
                
                # 4. REDIRECCIÓN FORZADA DE SEGURIDAD (Convertimos a int para asegurar)
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
# ======================================================o===================
def cerrar_sesion(request):
    # 1. Desloguear de Django nativo
    auth_logout(request)
    
    # 2. Eliminamos los datos manuales de sesión de la memoria
    if 'sesion_iniciada' in request.session:
        del request.session['sesion_iniciada']
    if 'usuario_nombre' in request.session:
        del request.session['usuario_nombre']
        
    # Limpieza total y destrucción de la cookie de sesión por seguridad
    request.session.flush() 
    
    # 3. Mensaje de éxito para el usuario
    messages.success(request, "Has cerrado sesión exitosamente. ¡Vuelve pronto!")
    
    # 4. Redirigir al formulario de login limpio
    return redirect('iniciar_sesion')

# =========================================================================
# 3. VISTA: REGISTRARSE
# =========================================================================
def registrarse(request):
    if request.method == 'POST':
        try:
            # 1. Capturar datos del formulario HTML
            nombre = request.POST.get('nombre')
            apellido = request.POST.get('apellido')
            cedula = request.POST.get('cedula')
            correo = request.POST.get('correo')
            password = request.POST.get('password')
            telefono = request.POST.get('telefono')
            fecha = request.POST.get('fecha')
            
            # 2. Buscar el Rol en tu tabla manual (ID 3 = Cliente)
            rol_cliente = Rol.objects.get(idrol=3)

            # 3. GUARDAR EN TU TABLA MANUAL ('usuario') en minúsculas
            nuevo_usuario_manual = Usuario.objects.create(
                cedula=cedula,
                nombre=f"{nombre} {apellido}",
                correo=correo,
                contrasena=make_password(password),  
                numcelular=telefono,
                fechanacimiento=fecha,
                idrolfk=rol_cliente
            )

            # 4. GUARDAR EN LA TABLA NATIVA DE DJANGO ('auth_user')
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
        # 1. Buscamos el usuario por su correo
        usuario_manual = Usuario.objects.get(correo=request.user.email)
        
        # 2. Verificamos que tenga Rol de Barbero (ID 2)
        if usuario_manual.idrolfk_id != 2:
            print(f"DEBUG PANEL: Acceso denegado para {usuario_manual.nombre}. Rol actual: {usuario_manual.idrolfk_id}")
            return redirect('home')
        
        # 3. Buscamos su perfil operativo en la tabla barbero
        barbero_perfil = Barbero.objects.get(idusuariofk=usuario_manual)
        
    except (Usuario.DoesNotExist, Barbero.DoesNotExist):
        print("DEBUG PANEL: El usuario o perfil de barbero no existe.")
        return redirect('home')

    # 4. Obtener la fecha del día de hoy del servidor
    hoy = timezone.now().date()

    # 5. Filtrar las citas de HOY asignadas a este barbero
    # Filtramos usando la relación inversa o directa según tus modelos cruzados
    citas_hoy = Cita.objects.filter(
        idbarberofk=barbero_perfil, 
        idagendafk__fecha=hoy
    ).order_by('idagendafk__horainicio')

    # ========================================================
    # VARIABLES ESTADÍSTICAS CORREGIDAS PARA EL TEMPLATE
    # ========================================================
    total_citas = citas_hoy.count()
    
    # Contamos cuántas tienen la palabra "Completado" en observaciones
    completadas = citas_hoy.filter(observaciones__icontains='Completado').count()

    # Producido Total (Suma del campo mapeado de precio)
    producido_dict = citas_hoy.aggregate(total=Sum('idserviciofk__precioservicio'))
    producido_total = producido_dict['total'] if producido_dict['total'] is not None else 0.0

    # Comisión Estimada (50% de lo producido hoy)
    comision_estimada = float(producido_total) * 0.50

    # 6. Sincronización exacta con las variables de tu barbero.html
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
    # En tu base de datos el ID de la cita se llama 'idcita'
    cita = get_object_or_404(Cita, idcita=cita_id)
    
    # Marcamos el servicio como realizado
    cita.observaciones = "Completado - Servicio realizado"
    cita.save()
    
    return redirect('panel_barbero')