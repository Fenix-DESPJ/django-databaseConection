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


def agenda_view(request):
    return render(request, 'agenda.html')

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


# ... (Tus imports actuales permanecen iguales)

def mis_citas_view(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para ver tus citas.")
        return redirect('login')

    user_sistema = request.user
    usuario_actual = Usuario.objects.get(correo=user_sistema.email)

    # Identificar si es Administrador (Suponiendo idrolfk == 1 para Administrador, ajusta si es necesario)
    # O también puedes usar request.user.is_staff
    es_admin = usuario_actual.idrolfk_id == 1 or user_sistema.is_staff

    if es_admin:
        # El administrador puede ver todas las citas del sistema
        citas = Cita.objects.all().order_by('-fecha', '-horainicio')
    else:
        # El cliente solo ve sus propias citas vinculadas a su ID de cliente
        with connection.cursor() as cursor:
            cursor.execute("SELECT idcliente FROM cliente WHERE idusuariofk = %s", [usuario_actual.idusuario])
            fila_cliente = cursor.fetchone()
        
        if fila_cliente:
            citas = Cita.objects.filter(idclientefk=fila_cliente[0]).order_by('-fecha', '-horainicio')
        else:
            citas = Cita.objects.none()

    return render(request, 'mis_citas.html', {
        'citas': citas,
        'es_admin': es_admin
    })


def cancelar_cita_cliente(request, id_cita):
    if not request.user.is_authenticated:
        messages.error(request, "Acción no permitida.")
        return redirect('login')

    user_sistema = request.user
    usuario_actual = Usuario.objects.get(correo=user_sistema.email)

    try:
        with transaction.atomic():
            # Obtener el ID de cliente del usuario actual
            with connection.cursor() as cursor:
                cursor.execute("SELECT idcliente FROM cliente WHERE idusuariofk = %s", [usuario_actual.idusuario])
                fila_cliente = cursor.fetchone()

            if not fila_cliente:
                raise Exception("Cliente no encontrado.")

            # Buscar la cita asegurando que pertenezca al cliente logueado (Seguridad)
            cita = Cita.objects.get(idCita=id_cita, idclientefk=fila_cliente[0])
            id_agenda = cita.idagendafk

            # Proceder a eliminar de la base de datos usando SQL Puro para mantener consistencia
            with connection.cursor() as cursor:
                # 1. Eliminar la cita
                cursor.execute("DELETE FROM cita WHERE idCita = %s", [id_cita])
                # 2. Eliminar de la agenda para liberar el espacio del barbero
                if id_agenda:
                    cursor.execute("DELETE FROM agenda WHERE idAgenda = %s", [id_agenda])

        messages.success(request, "Tu reserva ha sido cancelada exitosamente.")
    except Cita.DoesNotExist:
        messages.error(request, "La cita no existe o no tienes permisos para cancelarla.")
    except Exception as e:
        messages.error(request, f"Error al cancelar la cita: {e}")

    return redirect('mis_citas')


def cancelar_cita_admin(request, id_cita):
    # Validar que sea administrador
    user_sistema = request.user
    usuario_actual = Usuario.objects.get(correo=user_sistema.email)
    
    if not (usuario_actual.idrolfk_id == 1 or user_sistema.is_staff):
        messages.error(request, "No tienes permisos de administrador para realizar esta acción.")
        return redirect('mis_citas')

    try:
        with transaction.atomic():
            cita = Cita.objects.get(idCita=id_cita)
            id_agenda = cita.idagendafk

            with connection.cursor() as cursor:
                # 1. Eliminar la cita
                cursor.execute("DELETE FROM cita WHERE idCita = %s", [id_cita])
                # 2. Eliminar de la agenda
                if id_agenda:
                    cursor.execute("DELETE FROM agenda WHERE idAgenda = %s", [id_agenda])

        messages.success(request, f"La cita #{id_cita} ha sido cancelada por el Administrador.")
    except Cita.DoesNotExist:
        messages.error(request, "La cita especificada no existe.")
    except Exception as e:
        messages.error(request, f"Error administrativo: {e}")

    return redirect('mis_citas')

