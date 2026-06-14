from django.shortcuts import render,redirect
from servicios.models import Servicio
from usuarios.models import Usuario
from .models import Cita

# Create your views here.

def crear_reserva(request):
    if request.method == 'POST':
        fecha_reserva = request.POST.get('fecha')
        hora_reserva = request.POST.get('hora')
        servicio_id = request.POST.get('servicio')
        barbero_id = request.POST.get('barbero')
        
        user_sistema = request.user
        cliente_instancia = Usuario.objects.get(correo=user_sistema.email)
        
        nueva_cita = Cita(
            fecha = fecha_reserva,
            horainicio = hora_reserva,
            idserviciofk_id = servicio_id,
            idbarberofk_id=barbero_id,
            idclientefk=cliente_instancia,
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
