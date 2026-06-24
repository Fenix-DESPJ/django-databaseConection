from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Servicio

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
    # 1. Obtener todos los servicios de la base de datos
    servicios_list = Servicio.objects.all().order_by('nombreservicio')
    
    # 2. Configurar la paginación: 9 servicios por página
    paginator = Paginator(servicios_list, 9)
    
    # 3. Obtener el número de página de la URL (ej: ?page=2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'servicios-ind.html', {'servicios': page_obj})

def servicios_ind(request):
    # Cambia 'tipoServicio' por 'tiposervicio'
    servicios = Servicio.objects.filter(tiposervicio='Individual').order_by('nombreservicio')
    return render(request, 'servicios-ind.html', {'servicios': servicios})

def servicios_paq(request):
    # Cambia 'tipoServicio' por 'tiposervicio'
    paquetes = Servicio.objects.filter(tiposervicio='Paquete').order_by('nombreservicio')
    return render(request, 'servicios-paq-1.html', {'paquetes': paquetes})