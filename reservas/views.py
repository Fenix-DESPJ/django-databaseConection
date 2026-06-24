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
        # Capturamos las observaciones enviadas por el usuario de forma limpia
        observaciones = request.POST.get('observaciones', '').strip()
        
        # Si el usuario dejó el campo vacío, le ponemos un texto por defecto para la BD
        if not observaciones:
            observaciones = "Sin observaciones o notas especiales"

        # Validamos los campos obligatorios
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
                    
                    # 3. Buscar el barbero por id
                    cursor.execute("SELECT idBarbero FROM barbero WHERE idBarbero = %s", [barbero_id])
                    fila_barbero = cursor.fetchone()

                # Si el usuario con rol 2 no tiene fila en la tabla barbero, la creamos
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
                
                # 5. Insertar Agenda y Cita
                with connection.cursor() as cursor:
                    # Insertar en la tabla Agenda
                    cursor.execute(
                        "INSERT INTO agenda (idBarberoFk, fecha, horaInicio) VALUES (%s, %s, %s)",
                        [id_barbero_real, fecha_reserva, hora_objeto]
                    )
                    
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    id_agenda_creada = cursor.fetchone()[0]

                    # Insertar en la tabla Cita con la estructura exacta que me diste
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
                            observaciones
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
                # Consulta para el Administrador: Cruzamos idBarberoFk directamente con idUsuario
                cursor.execute("""
                    SELECT 
                        c.idCita, 
                        c.fecha, 
                        c.horaInicio, 
                        s.nombreServicio, 
                        u_barbero.nombre AS nombre_barbero, 
                        u_cliente.nombre AS nombre_cliente, 
                        c.observaciones
                    FROM cita c
                    LEFT JOIN servicio s ON c.idServicioFk = s.idServicio
                    LEFT JOIN usuario u_barbero ON c.idBarberoFk = u_barbero.idUsuario -- <-- CORREGIDO: Cruce directo
                    LEFT JOIN cliente cl ON c.idClienteFk = cl.idCliente
                    LEFT JOIN usuario u_cliente ON cl.idUsuarioFk = u_cliente.idUsuario
                    ORDER BY c.fecha DESC, c.horaInicio DESC
                """)
            else:
                # Consulta para el Cliente: Cruzamos idBarberoFk directamente con idUsuario
                cursor.execute("""
                    SELECT 
                        c.idCita, 
                        c.fecha, 
                        c.horaInicio, 
                        s.nombreServicio, 
                        u_barbero.nombre AS nombre_barbero, 
                        u_cliente.nombre AS nombre_cliente, 
                        c.observaciones
                    FROM cita c
                    LEFT JOIN servicio s ON c.idServicioFk = s.idServicio
                    LEFT JOIN usuario u_barbero ON c.idBarberoFk = u_barbero.idUsuario -- <-- CORREGIDO: Cruce directo
                    LEFT JOIN cliente cl ON c.idClienteFk = cl.idCliente
                    LEFT JOIN usuario u_cliente ON cl.idUsuarioFk = u_cliente.idUsuario
                    WHERE cl.idUsuarioFk = %s
                    ORDER BY c.fecha DESC, c.horaInicio DESC
                """, [usuario_actual.idusuario])
            
            filas = cursor.fetchall()
            for f in filas:
                citas.append({
                    'idCita': f[0],
                    'fecha': f[1],
                    'horainicio': f[2],
                    'servicio_nombre': f[3] if f[3] else "No asignado",
                    'barbero_nombre': f[4] if f[4] else "No asignado",
                    'cliente_nombre': f[5] if f[5] else "Cliente General", 
                    'observaciones': f[6] if f[6] else "",
                })
    except Exception as e:
        print(f"======= ERROR CRÍTICO AL TRAER CITAS =======")
        print(str(e))
        print("=============================================")

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

