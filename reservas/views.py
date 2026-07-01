from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from django.db import connection, transaction
import random
from datetime import datetime, timedelta, date
from servicios.models import Servicio, Pago
from usuarios.models import Usuario
from .models import Cita
from django.http import JsonResponse
from django.urls import reverse
from negocio.models import ConfiguracionHorario, DiaHabilitado, BarberoDiaHabilitado


def agenda_view(request):
    return render(request, 'agenda.html')


def _es_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _responder_error(request, mensaje, redirect_name='crear_reserva'):
    if _es_ajax(request):
        return JsonResponse({'ok': False, 'error': mensaje}, status=400)
    messages.error(request, mensaje)
    return redirect(redirect_name)


def crear_reserva(request):
    if not request.user.is_authenticated:
        return _responder_error(request, "Debes iniciar sesión para realizar una reserva.", 'login')

    if request.method == 'POST':
        fecha_reserva = request.POST.get('fecha')
        hora_reserva = request.POST.get('hora')
        servicio_id = request.POST.get('servicio')
        usuario_barbero_id = request.POST.get('barbero')  # idUsuario del barbero
        metodo_pago = request.POST.get('metodo_pago')
        observaciones = request.POST.get('observaciones', '').strip() or "Sin observaciones o notas especiales"

        if not all([fecha_reserva, hora_reserva, servicio_id, usuario_barbero_id, metodo_pago]):
            return _responder_error(request, "Por favor completa todos los campos.")

        try:
            fecha_obj = datetime.strptime(fecha_reserva, '%Y-%m-%d').date()
            hora_objeto = datetime.strptime(hora_reserva, '%H:%M').time()
        except ValueError:
            return _responder_error(request, "Fecha u hora inválida.")

        # --- 0. Rango permitido: solo desde hoy hasta un mes después ---
        hoy = date.today()
        if hoy.month == 12:
            fecha_maxima = hoy.replace(year=hoy.year + 1, month=1)
        else:
            try:
                fecha_maxima = hoy.replace(month=hoy.month + 1)
            except ValueError:
                # cubre meses con menos días (ej. 31 ene -> no existe 31 feb)
                fecha_maxima = (hoy.replace(day=1, month=hoy.month + 2) - timedelta(days=1))

        if not (hoy <= fecha_obj <= fecha_maxima):
            return _responder_error(
                request,
                "Solo puedes reservar citas entre hoy y un mes desde hoy."
            )

        # --- 1. Día habilitado por el admin ---
        if not DiaHabilitado.objects.filter(fecha=fecha_obj, habilitado=True).exists():
            return _responder_error(request, "Ese día no está habilitado para agendar. Elige otra fecha en el calendario.")

        # --- 2. Barbero habilitado ese día (no de vacaciones/falta) ---
        deshabilitado = BarberoDiaHabilitado.objects.filter(
            idusuariofk=usuario_barbero_id, fecha=fecha_obj, habilitado=False
        ).exists()
        if deshabilitado:
            return _responder_error(
                request,
                "Ese barbero no está disponible ese día. Por favor selecciona otro barbero u otra fecha."
            )

        try:
            with transaction.atomic():
                user_sistema = request.user
                usuario_actual = Usuario.objects.get(correo=user_sistema.email)
                servicio = Servicio.objects.get(idservicio=servicio_id)
                nombre_barbero_obj = Usuario.objects.filter(idusuario=usuario_barbero_id).first()
                nombre_barbero = nombre_barbero_obj.nombre if nombre_barbero_obj else "seleccionado"

                with connection.cursor() as cursor:
                    cursor.execute("SELECT idCliente FROM cliente WHERE idUsuarioFk = %s", [usuario_actual.idusuario])
                    fila_cliente = cursor.fetchone()

                    if not fila_cliente:
                        cursor.execute(
                            "INSERT INTO cliente (idUsuarioFk, direccion, contactoEmergencia) VALUES (%s, %s, %s)",
                            [usuario_actual.idusuario, 'Registrado desde la Web', 'No asignado']
                        )
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        id_cliente_real = cursor.fetchone()[0]
                    else:
                        id_cliente_real = fila_cliente[0]

                    # --- 3. El cliente ya tiene una cita ESE MISMO DÍA (con cualquier barbero) ---
                    cita_mismo_dia = Cita.objects.filter(idclientefk=id_cliente_real, fecha=fecha_obj).exists()
                    if cita_mismo_dia:
                        return _responder_error(
                            request,
                            "Ya tienes una cita agendada para ese día. Solo puedes reservar una cita por día."
                        )

                    # --- 4. Límite mensual de citas pendientes ---
                    config = ConfiguracionHorario.objects.first()
                    limite = config.limite_citas_mensuales if config else 3
                    inicio_mes = fecha_obj.replace(day=1)
                    if inicio_mes.month == 12:
                        fin_mes = inicio_mes.replace(year=inicio_mes.year + 1, month=1)
                    else:
                        fin_mes = inicio_mes.replace(month=inicio_mes.month + 1)

                    citas_pendientes_mes = Cita.objects.filter(
                        idclientefk=id_cliente_real,
                        fecha__gte=inicio_mes,
                        fecha__lt=fin_mes
                    ).exclude(observaciones__icontains='Completado').count()

                    if citas_pendientes_mes >= limite:
                        return _responder_error(
                            request,
                            f"Ya tienes {limite} citas pendientes este mes. Debes esperar la confirmación "
                            f"del barbero en alguna de tus citas antes de agendar otra."
                        )

                    cursor.execute("SELECT idBarbero FROM barbero WHERE idUsuarioFk = %s", [usuario_barbero_id])
                    fila_barbero = cursor.fetchone()

                    if not fila_barbero:
                        cursor.execute(
                            "INSERT INTO barbero (idUsuarioFk, especialidad) VALUES (%s, %s)",
                            [usuario_barbero_id, 'General']
                        )
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        id_barbero_real = cursor.fetchone()[0]
                    else:
                        id_barbero_real = fila_barbero[0]

                    # --- 5. Choque de horario POR DURACIÓN del servicio (no solo hora exacta) ---
                    nueva_inicio = datetime.combine(fecha_obj, hora_objeto)
                    nueva_fin = nueva_inicio + timedelta(minutes=servicio.duracion or 30)

                    citas_barbero_dia = Cita.objects.filter(
                        idbarberofk=id_barbero_real, fecha=fecha_obj
                    ).select_related('idserviciofk')

                    for c in citas_barbero_dia:
                        existente_inicio = datetime.combine(fecha_obj, c.horainicio)
                        existente_dur = c.idserviciofk.duracion if c.idserviciofk else 30
                        existente_fin = existente_inicio + timedelta(minutes=existente_dur)
                        if nueva_inicio < existente_fin and existente_inicio < nueva_fin:
                            return _responder_error(
                                request,
                                f'El barbero "{nombre_barbero}" ya ha sido reservado por otro cliente en ese horario. '
                                f'Por favor selecciona otra hora.'
                            )

                nuevo_pago = Pago.objects.create(
                    metodopago=metodo_pago,
                    montototal=servicio.precio,
                    fechapago=timezone.now(),
                    estadopago="PENDIENTE" if metodo_pago == "Efectivo" else "PAGADO",
                    codigofactura=f"FAC{random.randint(10000, 99999)}"
                )

                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO agenda (idBarberoFk, fecha, horaInicio) VALUES (%s, %s, %s)",
                        [id_barbero_real, fecha_reserva, hora_objeto]
                    )
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    id_agenda_creada = cursor.fetchone()[0]

                    cursor.execute(
                        """INSERT INTO cita (fecha, horaInicio, idServicioFk, idPagoFk,
                           idBarberoFk, idClienteFk, idAgendaFk, observaciones)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        [fecha_reserva, hora_objeto, servicio_id, nuevo_pago.idpago,
                         id_barbero_real, id_cliente_real, id_agenda_creada, observaciones]
                    )

            if _es_ajax(request):
                return JsonResponse({'ok': True, 'redirect': reverse('mis_citas')})
            messages.success(request, "¡Cita reservada y guardada exitosamente!")
            return redirect('mis_citas')

        except Exception as e:
            return _responder_error(request, f"Hubo un problema al guardar la reserva: {e}")

    return render(request, 'reservas.html', {
        'servicios': Servicio.objects.all(),
        'barberos': Usuario.objects.filter(idrolfk=2)
    })


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
                    LEFT JOIN barbero b ON c.idBarberoFk = b.idBarbero
                    LEFT JOIN usuario u_barbero ON b.idUsuarioFk = u_barbero.idUsuario
                    LEFT JOIN cliente cl ON c.idClienteFk = cl.idCliente
                    LEFT JOIN usuario u_cliente ON cl.idUsuarioFk = u_cliente.idUsuario
                    ORDER BY c.fecha DESC, c.horaInicio DESC
                """)
            else:
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
                    LEFT JOIN barbero b ON c.idBarberoFk = b.idBarbero
                    LEFT JOIN usuario u_barbero ON b.idUsuarioFk = u_barbero.idUsuario
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
        print("======= ERROR CRÍTICO AL TRAER CITAS =======")
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
            with connection.cursor() as cursor:
                cursor.execute("SELECT idcliente FROM cliente WHERE idusuariofk = %s", [usuario_actual.idusuario])
                fila_cliente = cursor.fetchone()

            if not fila_cliente:
                raise Exception("Cliente no encontrado.")

            cita = Cita.objects.get(idCita=id_cita, idclientefk=fila_cliente[0])
            id_agenda = cita.idagendafk

            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM cita WHERE idCita = %s", [id_cita])
                if id_agenda:
                    cursor.execute("DELETE FROM agenda WHERE idAgenda = %s", [id_agenda])

        messages.success(request, "Tu reserva ha sido cancelada exitosamente.")
    except Cita.DoesNotExist:
        messages.error(request, "La cita no existe o no tienes permisos para cancelarla.")
    except Exception as e:
        messages.error(request, f"Error al cancelar la cita: {e}")

    return redirect('mis_citas')


def cancelar_cita_admin(request, id_cita):
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
                cursor.execute("DELETE FROM cita WHERE idCita = %s", [id_cita])
                if id_agenda:
                    cursor.execute("DELETE FROM agenda WHERE idAgenda = %s", [id_agenda])

        messages.success(request, f"La cita #{id_cita} ha sido cancelada por el Administrador.")
    except Cita.DoesNotExist:
        messages.error(request, "La cita especificada no existe.")
    except Exception as e:
        messages.error(request, f"Error administrativo: {e}")

    return redirect('mis_citas')