from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Usuario, Rol
from .models import Cita
from django.utils import timezone
from django.db.models import Sum

# Vista para la página principal (la que te daba el error 404)
def home(request):
    return render(request, 'index.html')  # Asegúrate de tener tu index.html

# Vista completa de registro
def registrarse(request):
    if request.method == 'POST':
        try:
            # 1. Capturar datos del POST
            nombre = request.POST.get('nombre')
            apellido = request.POST.get('apellido')
            cedula = request.POST.get('cedula')
            correo = request.POST.get('correo')
            password = request.POST.get('password')
            telefono = request.POST.get('telefono')
            fecha = request.POST.get('fecha')
            
            # 2. Buscar el Rol (ID 3 = Cliente)
            rol_cliente = Rol.objects.get(idrol=3)

            # 3. Crear el objeto Usuario
            # Usamos el nombre del campo tal cual lo definiste en models.py
            nuevo_usuario = Usuario.objects.create(
                cedula=cedula,
                nombre=f"{nombre} {apellido}",
                correo=correo,
                contrasena=password,  # Nota: En producción, recuerda usar make_password
                numcelular=telefono,
                fechanacimiento=fecha,
                idrolfk=rol_cliente
            )
            
            print("DEBUG: Usuario guardado exitosamente")
            return redirect('index') # Asegúrate de que esta URL exista en tus urls.py

        except Exception as e:
            # Esto imprimirá el error real en tu consola (terminal de VS Code)
            print(f"DEBUG: ERROR AL GUARDAR EN BD: {e}")
            return render(request, 'registrarse.html', {'error': f"Error al registrar: {e}"})
    
    # Si es GET, solo renderizamos el formulario
    return render(request, 'registrarse.html')

@login_required
def panel_barbero(request):
    # Verifica de forma segura si el usuario tiene perfil y si es barbero
    if not hasattr(request.user, 'perfil') or request.user.perfil.rol != 'barbero':
        return redirect('barbero.html')
    
    hoy = timezone.now().date()
    
    # Filtramos citas del día pertenecientes al barbero logueado
    citas_hoy = Cita.objects.filter(barbero=request.user, fecha=hoy).order_by('hora')

    total_citas = citas_hoy.count()
    completadas = citas_hoy.filter(estado='completado').count()
    
    # Cálculos monetarios integrales
    producido_total = citas_hoy.filter(estado='completado').aggregate(Sum('precio'))['precio__sum'] or 0
    comision_estimada = producido_total * 0.5 # 50% de ganancia

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