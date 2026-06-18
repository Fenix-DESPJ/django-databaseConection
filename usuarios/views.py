from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Usuario, Rol
from .models import Cita
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from .models import PerfilUsuario  # Asegúrate de importarlo
from django.contrib.auth.hashers import make_password

# Vista para la página principal (la que te daba el error 404)
def home(request):
    return render(request, 'index.html')  # Asegúrate de tener tu index.html

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

            # 3. GUARDAR EN TU TABLA MANUAL ('usuario')
            # Encriptamos la contraseña con make_password por seguridad
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
            # Usamos el correo como username para que inicien sesión con su correo
            nuevo_usuario_django = User.objects.create_user(
                username=correo,
                email=correo,
                password=password,
                first_name=nombre,
                last_name=apellido
            )
            
            print("DEBUG: Guardado con éxito en ambas tablas")
            return redirect('login') # Te manda a la pantalla de login

        except Exception as e:
            print(f"DEBUG: ERROR AL REGISTRAR: {e}")
            return render(request, 'registrarse.html', {'error': f"Error al registrar: {e}"})
            
    return render(request, 'registrarse.html')

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

    # --- El resto de tu código de las citas se queda exactamente igual ---
    hoy = timezone.now().date()
    citas_hoy = Cita.objects.filter(barbero=request.user, fecha=hoy).order_by('hora')

    total_citas = citas_hoy.count()
    completadas = citas_hoy.filter(estado='completado').count()
    
    producido_total = citas_hoy.filter(estado='completado').aggregate(Sum('precio'))['precio__sum'] or 0
    comision_estimada = produced_total * 0.5 

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
    cita = get_object_or_404(Cita, id=cita_id, barbero=request.user)
    cita.estado = 'completado'
    cita.save()
    return redirect('panel_barbero')

def iniciar_sesion(request):
    if request.method == 'POST':
        usuario_input = request.POST.get('username')
        contrasena_input = request.POST.get('password')
        
        print(f"DEBUG LOGIN: Intentando entrar con Usuario: {usuario_input} y Contraseña: {contrasena_input}")
        
        user = authenticate(request, username=usuario_input, password=contrasena_input)
        
        if user is not None:
            print(f"DEBUG LOGIN: Autenticación Exitosa para el usuario de Django: {user.username}")
            auth_login(request, user)
            
            try:
                usuario_manual = Usuario.objects.get(correo=user.email)
                print(f"DEBUG LOGIN: Se encontró el usuario manual. Su ID de rol es: {usuario_manual.idrolfk.idrol}")
                
                if usuario_manual.idrolfk.idrol == 2:
                    print("DEBUG LOGIN: Es barbero. Redirigiendo a panel_barbero...")
                    return redirect('panel_barbero')
            except Usuario.DoesNotExist:
                print("DEBUG LOGIN: ADVERTENCIA: El usuario existe en auth_user pero NO en la tabla manual 'usuario'")
                
            print("DEBUG LOGIN: No es barbero o no tiene perfil manual. Redirigiendo a home...")
            return redirect('home') 
        else:
            print("DEBUG LOGIN: FALLÓ LA AUTENTICACIÓN. Django devolvió None (Usuario o contraseña incorrectos)")
            return render(request, 'iniciarsesion.html', {'error': 'Credenciales incorrectas'})
            
    return render(request, 'iniciarsesion.html')