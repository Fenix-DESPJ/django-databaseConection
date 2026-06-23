from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from django.db import connection 
import random
from datetime import datetime
from servicios.models import Servicio, Pago
from usuarios.models import Usuario
from .models import Cita
from django.db import transaction, connection # Importa transaction

def crear_reserva(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para realizar una reserva.")
        return redirect('login') 

    if request.method == 'POST':
        fecha_reserva = request.POST.get('fecha')
        hora_reserva = request.POST.get('hora')
        servicio_id = request.POST.get('servicio')
        barbero_id = request.POST.get('barbero')
        metodo_pago = request.POST.get('metodo_pago')
        
        if not all([fecha_reserva, hora_reserva, servicio_id, barbero_id, metodo_pago]):
            messages.error(request, "Por favor completa todos los campos.")
            return redirect('crear_reserva')
            
        try:
            with transaction.atomic():
                # 1. Obtener datos básicos
                user_sistema = request.user
                usuario_actual = Usuario.objects.get(correo=user_sistema.email)
                hora_objeto = datetime.strptime(hora_reserva, '%H:%M').time()
                servicio = Servicio.objects.get(idservicio=servicio_id)
                
                with connection.cursor() as cursor:
                    # 2. Consultar IDs de Cliente y Barbero
                    cursor.execute("SELECT idcliente FROM cliente WHERE idusuariofk = %s", [usuario_actual.idusuario])
                    fila_cliente = cursor.fetchone()
                    
                    cursor.execute("SELECT idbarbero FROM barbero WHERE idusuariofk = %s", [barbero_id])
                    fila_barbero = cursor.fetchone()

                if not fila_cliente or not fila_barbero:
                    raise Exception("Error en la asociación de Cliente o Barbero.")

                # 3. Guardar Pago (ORM es seguro aquí)
                nuevo_pago = Pago.objects.create(
                    metodopago=metodo_pago,
                    montototal=servicio.precio,
                    fechapago=timezone.now(),
                    estadopago="PENDIENTE" if metodo_pago == "Efectivo" else "PAGADO",
                    codigofactura=f"FAC{random.randint(10000, 99999)}"
                )
                
                # 4. Insertar Agenda y Cita usando SQL puro para garantizar el ID
                with connection.cursor() as cursor:
                    # Insertar Agenda
                    cursor.execute(
                        "INSERT INTO agenda (idBarberoFk, fecha, horaInicio) VALUES (%s, %s, %s)",
                        [fila_barbero[0], fecha_reserva, hora_objeto]
                    )
                    # Capturar el ID generado
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    id_agenda_creada = cursor.fetchone()[0]

                    # Insertar Cita vinculando el ID de la agenda
                    cursor.execute(
                        """INSERT INTO cita (fecha, horaInicio, idServicioFk, idPagoFk, 
                           idClienteFk, idBarberoFk, idAgendaFk, observaciones) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        [fecha_reserva, hora_objeto, servicio_id, nuevo_pago.idpago, 
                         fila_cliente[0], fila_barbero[0], id_agenda_creada, "Reserva realizada desde la web"]
                    )
                
            messages.success(request, "¡Cita reservada y guardada exitosamente!")
            return redirect('crear_reserva')
            
        except Exception as e:
            messages.error(request, f"Hubo un problema al guardar la reserva: {e}")
            return redirect('crear_reserva')

    # Método GET
    return render(request, 'reservas.html', {
        'servicios': Servicio.objects.all(), 
        'barberos': Usuario.objects.filter(idrolfk=2)
    })