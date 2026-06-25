from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Servicio
from usuarios.models import Usuario
import os

def index(request):
    return render(request, 'index.html')

def servicios(request):
    return render(request, 'servicios.html')

def servicios_ind(request):
    return render(request, 'servicios-ind.html')

def servicios_paq(request):
    return render(request, 'servicios-paq-1.html')

def servicios_paq_2(request):
    return render(request, 'servicios-paq-2.html')

def reservas(request):
    return render(request, 'reservas.html')

def agenda(request):
    return render(request, 'agenda.html')

def perfil(request):
    return render(request, 'perfil.html') # Aquí quitamos la coma y cerramos el paréntesis correctamente

def iniciar_sesion(request):
    return render(request, 'iniciarsesion.html')

def registrarse(request):
    return render(request, 'registrarse.html')

def agenda_view(request):
    return render(request, 'agenda.html')

def servicios_ind(request):
    # 1. Obtenemos servicios (paginados)
    servicios_list = Servicio.objects.filter(tiposervicio='Individual').order_by('nombreservicio')
    paginator = Paginator(servicios_list, 9)
    page_number = request.GET.get('page')
    servicios = paginator.get_page(page_number)
    
    # 2. Lógica Admin
    es_admin = False
    if request.user.is_authenticated:
        usuario_db = Usuario.objects.filter(correo=request.user.email).first()
        if usuario_db and usuario_db.idrolfk_id == 1:
            es_admin = True
            
    # 3. Retorno
    return render(request, 'servicios-ind.html', {
        'servicios': servicios,
        'es_admin': es_admin
    })

from django.core.paginator import Paginator

def servicios_paq(request):
    # 1. Obtenemos paquetes (filtrados por 'Paquete' y paginados)
    # Nota: Asegúrate de que el valor sea 'Paquete' tal como está en tu BD
    paquetes_list = Servicio.objects.filter(tiposervicio='Paquete').order_by('nombreservicio')
    paginator = Paginator(paquetes_list, 9)
    page_number = request.GET.get('page')
    paquetes = paginator.get_page(page_number)
    
    # 2. Lógica Admin (idéntica a servicios_ind)
    es_admin = False
    if request.user.is_authenticated:
        usuario_db = Usuario.objects.filter(correo=request.user.email).first()
        if usuario_db and usuario_db.idrolfk_id == 1:
            es_admin = True
            
    # 3. Retorno (usando la variable 'paquetes' que espera tu template)
    return render(request, 'servicios-paq-1.html', {
        'paquetes': paquetes,
        'es_admin': es_admin
    })

# Función para verificar si es admin
def es_admin(user):
    if not user.is_authenticated:
        return False
    
    # Buscamos en la tabla Usuario el registro que coincida con el email del usuario logueado
    # Como tu campo se llama 'correo', usaremos ese para la comparación
    perfil = Usuario.objects.filter(correo=user.email).first()
    
    # 1 es el ID del rol de administrador en tu tabla 'rol'
    return perfil is not None and perfil.idrolfk_id == 1

# 1. Crear Servicio
@login_required
def crear_servicio(request):
    # Validación de Admin
    usuario_db = Usuario.objects.filter(correo=request.user.email).first()
    if not (usuario_db and usuario_db.idrolfk_id == 1):
        raise PermissionDenied
    
    if request.method == 'POST':
        # 1. Capturamos datos
        nombre = request.POST.get('nombreservicio')
        precio = request.POST.get('precio')
        duracion = request.POST.get('duracion')
        tipo = request.POST.get('tiposervicio')
        
        # 2. Capturamos el archivo (IMPORTANTE: request.FILES)
        imagen = request.FILES.get('imagen')
        
        # 3. Guardado (Django gestiona la ruta si el campo es un ImageField)
        Servicio.objects.create(
            nombreservicio=nombre,
            precio=precio,
            duracion=duracion,
            tiposervicio=tipo,
            # Si 'imagen' es None, Django usará el valor 'default.jpg' definido en tu modelo
            imagen=imagen if imagen else 'default.jpg' 
        )
        
        return redirect('servicios_ind')
        
    return render(request, 'crear_servicio.html')

# 2. Editar Servicio
@login_required
def editar_servicio(request, pk):
    if not es_admin(request.user):
        raise PermissionDenied

    servicio = get_object_or_404(Servicio, pk=pk)

    if request.method == 'POST':
        servicio.nombreservicio = request.POST.get('nombreservicio')
        servicio.precio = request.POST.get('precio')
        servicio.duracion = request.POST.get('duracion')
        servicio.tiposervicio = request.POST.get('tiposervicio')

        if request.FILES.get('imagen'):
            # (Tu lógica de borrado de imagen vieja aquí)
            servicio.imagen = request.FILES['imagen']

        servicio.save()
        return redirect('servicios_ind') # <--- Esto es lo que necesitas

    # Si alguien entra por GET a la URL de editar, redirígelo a la lista
    return redirect('servicios_ind')
    
# 3. Eliminar Servicio
@login_required
def eliminar_servicio(request, pk):
    # Verificación de seguridad robusta
    if not es_admin(request.user):
        print("DEBUG: Acceso denegado en eliminar_servicio")
        raise PermissionDenied
        
    servicio = get_object_or_404(Servicio, pk=pk)
    servicio.delete()
    return redirect('servicios_ind')

def lista_servicios(request):
    servicios = Servicio.objects.all()
    return render(request, 'tu_plantilla.html', {
        'servicios': servicios,
        'es_admin': es_admin(request.user) # <--- Aquí calculas si es admin
    })