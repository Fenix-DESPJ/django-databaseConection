from django.shortcuts import render,redirect
from django.utils import timezone
import random

from servicios.models import Servicio, Pago
from usuarios.models import Usuario
from .models import Cita

# Create your views here.

def crear_reserva(request):
    if request.method == 'POST':
        fecha_reserva = request.POST.get('fecha')
        hora_reserva = request.POST.get('hora')
        servicio_id = request.POST.get('servicio')
        barbero_id = request.POST.get('barbero')
        metodo_pago = request.POST.get('metodo_pago')
        
        user_sistema = request.user
        cliente_instancia = Usuario.objects.get(correo=user_sistema.email)
        servicio = Servicio.objects.get(idservicio=servicio_id)
        
        if metodo_pago == "Efectivo":
            estado_pago = "PENDIENTE"
        else:
            estado_pago = "PAGADO"
            
        codigo_factura = f"FAC{random.randint(10000, 99999)}"
        
        nuevo_pago = Pago(
            metodopago=metodo_pago,
            montototal=servicio.precio,
            fechapago=timezone.now(),
            estadopago=estado_pago,
            codigofactura=codigo_factura
        )

        nuevo_pago.save()
        
        nueva_cita = Cita(
            fecha = fecha_reserva,
            horainicio = hora_reserva,
            idserviciofk_id = servicio_id,
            idbarberofk_id=barbero_id,
            idclientefk=cliente_instancia,
            idpagofk=nuevo_pago,
            observaciones="Reserva realizada desde la web"
        )
        
        nueva_cita.save()
        
        return redirect('crear_reserva')
    
    todos_los_servicios = Servicio.objects.all()
    todos_los_barberos = Usuario.objects.filter(idrolfk=2)
    
    contexto = {
        'servicios': todos_los_servicios,
        'barberos': todos_los_barberos
    }
    
    return render(request, 'reservas.html', contexto)
