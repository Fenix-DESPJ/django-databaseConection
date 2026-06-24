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
        barbero_id = request.POST.get('barbero') # Este recibe el ID del usuario seleccionado (ej: 2)
        metodo_pago = request.POST.get('metodo_pago')
        
        if not all([fecha_reserva, hora_reserva, servicio_id, barbero_id, metodo_pago]):
            messages.error(request, "Por favor completa todos los campos.")
            return redirect('crear_reserva')
            
        try:
            with transaction.atomic():
                # 1. Obtener datos del usuario logueado en Django
                user_sistema = request.user
                usuario_actual = Usuario.objects.get(correo=user_sistema.email)
                hora_objeto = datetime.strptime(hora_reserva, '%H:%M').time()
                servicio = Servicio.objects.get(idservicio=servicio_id)
                
                with connection.cursor() as cursor:
                    # 2. Buscar ID del cliente real (si no existe en la tabla cliente, se crea)
                    cursor.execute("SELECT idCliente FROM cliente WHERE idUsuarioFk = %s", [usuario_actual.idusuario])
                    fila_cliente = cursor.fetchone()
                    
                    if not fila_cliente:
                        cursor.execute(
                            "INSERT INTO cliente (idUsuarioFk, nombre, correo) VALUES (%s, %s, %s)",
                            [usuario_actual.idusuario, user_sistema.get_full_name() or user_sistema.username, user_sistema.email]
                        )
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        id_cliente_real = cursor.fetchone()[0]
                    else:
                        id_cliente_real = fila_cliente[0]
                    
                    # 3. BUSCAR EL BARBERO CON EL NOMBRE EXACTO DE TU COLUMNA EN EL SQL (`idBarbero`)
                    cursor.execute("SELECT idBarbero FROM barbero WHERE idBarbero = %s", [barbero_id])
                    fila_barbero = cursor.fetchone()

                # Si por alguna razón de pruebas el usuario con rol 2 no tiene fila en la tabla barbero, la creamos
                if not fila_barbero:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO barbero (idBarbero, especialidad) VALUES (%s, %s)",
                            [barbero_id, 'General']
                        )
                        id_barbero_real = barbero_id
                else:
                    id_barbero_real = fila_barbero[0]

                # 4. Guardar Pago usando el ORM de Django
                nuevo_pago = Pago.objects.create(
                    metodopago=metodo_pago,
                    montototal=servicio.precio,
                    fechapago=timezone.now(),
                    estadopago="PENDIENTE" if metodo_pago == "Efectivo" else "PAGADO",
                    codigofactura=f"FAC{random.randint(10000, 99999)}"
                )
                
                # 5. Insertar Agenda y Cita removiendo la columna conflictiva del estado
                with connection.cursor() as cursor:
                    # Insertar en la tabla Agenda
                    cursor.execute(
                        "INSERT INTO agenda (idBarberoFk, fecha, horaInicio) VALUES (%s, %s, %s)",
                        [id_barbero_real, fecha_reserva, hora_objeto]
                    )
                    
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    id_agenda_creada = cursor.fetchone()[0]

                    # Insertar en la tabla Cita omitiendo la columna de estado para evitar el error 1054
                    cursor.execute(
                        """INSERT INTO cita (fecha, horaInicio, idServicioFk, idPagoFk, 
                           idClienteFk, idBarberoFk, idAgendaFk, observaciones) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        [
                            fecha_reserva, 
                            hora_objeto, 
                            servicio_id, 
                            nuevo_pago.idpago, 
                            id_cliente_real, 
                            id_barbero_real, 
                            id_agenda_creada, 
                            "Reserva realizada desde la web"
                        ]
                    )
                
            messages.success(request, "¡Cita reservada y guardada exitosamente!")
            return redirect('mis_citas')
            
        except Exception as e:
            print("======= ERROR EN LA CONSULTA DE RESERVAS =======")
            print(str(e))
            print("=================================================")
            messages.error(request, f"Hubo un problema al guardar la reserva: {e}")
            return redirect('crear_reserva')

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
    es_admin = usuario_actual.idrolfk_id == 1 or user_sistema.is_staff

    citas = []
    try:
        with connection.cursor() as cursor:
            if es_admin:
                # Consulta global para el administrador
                cursor.execute("""
                    SELECT c.idCita, c.fecha, c.horaInicio, s.nombre, u.nombre, cl.nombre, c.observaciones
                    FROM cita c
                    INNER JOIN servicio s ON c.idServicioFk = s.idServicio
                    INNER JOIN barbero b ON c.idBarberoFk = b.idBarbero
                    INNER JOIN usuario u ON b.idBarbero = u.idUsuario
                    INNER JOIN cliente cl ON c.idClienteFk = cl.idCliente
                    ORDER BY c.fecha DESC, c.horaInicio DESC
                """)
            else:
                # Consulta específica para el cliente actual
                cursor.execute("""
                    SELECT c.idCita, c.fecha, c.horaInicio, s.nombre, u.nombre, cl.nombre, c.observaciones
                    FROM cita c
                    INNER JOIN servicio s ON c.idServicioFk = s.idServicio
                    INNER JOIN barbero b ON c.idBarberoFk = b.idBarbero
                    INNER JOIN usuario u ON b.idBarbero = u.idUsuario
                    INNER JOIN cliente cl ON c.idClienteFk = cl.idCliente
                    WHERE cl.idUsuarioFk = %s
                    ORDER BY c.fecha DESC, c.horaInicio DESC
                """, [usuario_actual.idusuario])
            
            filas = cursor.fetchall()
            for f in filas:
                citas.append({
                    'idCita': f[0],
                    'fecha': f[1],
                    'horainicio': f[2],
                    'servicio_nombre': f[3],
                    'barbero_nombre': f[4],
                    'cliente_nombre': f[5],
                    'observaciones': f[6],
                })
    except Exception as e:
        print(f"Error al traer citas: {e}")

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

