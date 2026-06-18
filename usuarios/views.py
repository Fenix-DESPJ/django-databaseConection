from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages

# Importación de tus modelos manuales
from .models import Usuario, Rol, Cita, PerfilUsuario  

# =========================================================================
# 1. VISTA: INICIAR SESIÓN
# =========================================================================
def iniciar_sesion(request):
    if request.method == 'POST':
        # Captura los datos usando los 'name' exactos de tu formulario HTML
        usuario_input = request.POST.get('identificador')
        contrasena_input = request.POST.get('contrasena')
        
        print(f"DEBUG LOGIN: Intentando entrar con Usuario: {usuario_input}")
        
        # Autentica en la tabla nativa 'auth_user' de Django
        user = authenticate(request, username=usuario_input, password=contrasena_input)
        
        if user is not None:
            print(f"DEBUG LOGIN: Autenticación Exitosa en Django: {user.username}")
            auth_login(request, user)
            
            # SETEAR VARIABLES DE SESIÓN (Para que base.html detecte el cambio en el NAV)
            request.session['sesion_iniciada'] = True
            request.session['usuario_nombre'] = user.first_name if user.first_name else user.username
            
            try:
                # Validar el rol en tu tabla manual 'usuario'
                usuario_manual = Usuario.objects.get(correo=user.email)
                print(f"DEBUG LOGIN: Se encontró usuario manual. Rol ID: {usuario_manual.idrolfk.idrol}")
                
                # Si el rol es Barbero (ID 2), mándalo directo a su panel de control
                if usuario_manual.idrolfk.idrol == 2:
                    print("DEBUG LOGIN: Es barbero. Redirigiendo a panel_barbero...")
                    return redirect('panel_barbero')
            except Usuario.DoesNotExist:
                print("DEBUG LOGIN: ADVERTENCIA: Existe en auth_user pero NO en la tabla manual 'usuario'")
                
            # Si es un cliente común o no tiene rol manual, mándalo a la página principal
            print("DEBUG LOGIN: Redirigiendo a home...")
            return redirect('home') 
        else:
            print("DEBUG LOGIN: FALLÓ LA AUTENTICACIÓN. Credenciales inválidas.")
            messages.error(request, "El correo o la contraseña son incorrectos.")
            return redirect('iniciar_sesion')
            
    return render(request, 'iniciarsesion.html')

# =========================================================================
# 2. VISTA: CERRAR SESIÓN
# =========================================================================
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
        # Buscamos el rol en tu tabla manual 'usuario' usando el correo del logueado
        usuario_manual = Usuario.objects.get(correo=request.user.email)
        
        # Si no es barbero (ID 2), lo sacamos de aquí
        if usuario_manual.idrolfk.idrol != 2:
            return redirect('home')
            
    except Usuario.DoesNotExist:
        return redirect('home')

    hoy = timezone.now().date()
    # Filtramos las citas asociadas al usuario barbero en la fecha actual
    citas_hoy = Cita.objects.filter(idbarberofk__idusuariofk=usuario_manual, fecha=hoy).order_by('horainicio')

    total_citas = citas_hoy.count()
    completadas = citas_hoy.filter(observaciones__icontains='completado').count() # O tu campo de estado respectivo
    
    # Cálculos estadísticos para el diseño del panel
    producido_total = citas_hoy.aggregate(Sum('idserviciofk__precio'))['idserviciofk__precio__sum'] or 0
    comision_estimada = producido_total * 0.5 

    context = {
        'citas': citas_hoy,
        'total_citas': total_citas,
        'completadas': completadas,
        'producido_total': producido_total,
        'comision_estimada': comision_estimada,
    }
    return render(request, 'secciones/barbero.html', context)

@login_required
def completar_cita(request, cita_id):
    # Corrección de campos en minúsculas conforme al estándar detectado de tu BD
    cita = get_object_or_404(Cita, id=cita_id)
    cita.observaciones = "Completado - Servicio realizado"
    cita.save()
    return redirect('panel_barbero')