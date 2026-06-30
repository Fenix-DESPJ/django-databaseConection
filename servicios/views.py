from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps
from .models import Servicio, Cita
import pandas as pd
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.db.models import Sum, Count
from usuarios.models import Usuario
from django.apps import apps
import json
from django.db.models import F
from django.http import FileResponse
from fpdf import FPDF
import os

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Usamos tu función es_admin existente
        if not es_admin(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

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
@admin_required
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
@admin_required
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
@admin_required
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

#reportes servicios
@login_required
def reportes_admin(request):
    # 1. Ingresos totales
    ingresos_totales = Cita.objects.aggregate(total=Sum('idserviciofk__precio'))['total'] or 0
    
    # 2. Total de reservas
    total_reservas = Cita.objects.count()
    
    # 3. Servicio más vendido
    servicio_top_obj = Cita.objects.values('idserviciofk__nombreservicio') \
                                   .annotate(total=Count('idcita')) \
                                   .order_by('-total').first()
    servicio_top = servicio_top_obj['idserviciofk__nombreservicio'] if servicio_top_obj else "N/A"
    
    # 4. Top 5 Servicios para la lista lateral
    top_servicios = Cita.objects.values('idserviciofk__nombreservicio') \
                                .annotate(total=Count('idcita')) \
                                .order_by('-total')[:5]

    # 5. NUEVO: Agrupación para la gráfica de barras por Barbero
    datos_barberos = Cita.objects.values('idbarberofk__idusuariofk__nombre') \
                             .annotate(total_ingreso=Sum('idserviciofk__precio')) \
                             .order_by('-total_ingreso')

    # Ahora, el diccionario SÍ tendrá la llave 'nombre_barbero'
    nombres_barberos = [item['idbarberofk__idusuariofk__nombre'] or "Sin Nombre" for item in datos_barberos]
    totales_barberos = [float(item['total_ingreso'] or 0) for item in datos_barberos]

    Barbero = apps.get_model('servicios', 'Barbero') # Ajusta 'servicios' si tu app se llama diferente

    context = {
        'ingresos_totales': ingresos_totales,
        'total_reservas': total_reservas,
        'servicio_top': servicio_top,
        'top_servicios': top_servicios,
        # Convertimos a JSON para que el template no sufra con los tipos de datos
        'nombres_barberos': json.dumps(nombres_barberos),
        'totales_barberos': json.dumps(totales_barberos),
    }
    return render(request, 'reportes.html', context)

@login_required
def descargar_reporte_excel(request):
    datos = Cita.objects.all().values(
        'idcita', 'fecha', 'horainicio', 
        'idserviciofk__nombreservicio', 'idserviciofk__precio'
    )
    df = pd.DataFrame(list(datos))
    
    # --- CORRECCIÓN AQUÍ ---
    # Convertimos la columna fecha a string para que no dé error en Excel
    if 'fecha' in df.columns:
        df['fecha'] = df['fecha'].astype(str)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="reporte_citas.xlsx"'
    df.to_excel(response, index=False)
    return response

@login_required
def descargar_reporte_pdf(request):
    # 1. Obtener datos
    datos = Cita.objects.all().values(
        'idcita', 'fecha', 'idserviciofk__nombreservicio', 'idserviciofk__precio'
    )
    
    # 2. Crear PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Reporte de Citas - BarberShop", ln=True, align='C')
    pdf.ln(10)
    
    # Encabezados
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(20, 10, "ID", 1)
    pdf.cell(40, 10, "Fecha", 1)
    pdf.cell(80, 10, "Servicio", 1)
    pdf.cell(30, 10, "Precio", 1)
    pdf.ln()
    
    # Datos
    pdf.set_font("Arial", '', 12)
    for cita in datos:
        pdf.cell(20, 10, str(cita.get('idcita', '')), 1)
        pdf.cell(40, 10, str(cita.get('fecha', '')), 1)
        pdf.cell(80, 10, str(cita.get('idserviciofk__nombreservicio', '')), 1)
        pdf.cell(30, 10, str(cita.get('idserviciofk__precio', '')), 1)
        pdf.ln()

    # 3. Guardar en archivo temporal (evita problemas de buffer)
    ruta_temp = "temp_reporte.pdf"
    pdf.output(ruta_temp)
    
    # 4. Enviar archivo al usuario
    response = FileResponse(open(ruta_temp, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_citas.pdf"'
    
    # Nota: Aquí no borramos el archivo inmediatamente para asegurar la descarga
    return response