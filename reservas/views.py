from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
import random
from datetime import datetime, timedelta, date
from servicios.models import Servicio, Pago
from usuarios.models import Usuario, Notificacion, Cliente
from negocio.models import Barbero, Agenda
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

                # --- Cliente: obtener o crear (igual que el INSERT original) ---
                cliente = Cliente.objects.filter(idusuariofk=usuario_actual).first()
                if not cliente:
                    cliente = Cliente.objects.create(
                        idusuariofk=usuario_actual,
                        direccion='Registrado desde la Web',
                        contactoemergencia='No asignado',
                    )

                # --- 3. El cliente ya tiene una cita ESE MISMO DÍA (con cualquier barbero) ---
                cita_mismo_dia = Cita.objects.filter(idclientefk=cliente, fecha=fecha_obj).exists()
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
                    idclientefk=cliente,
                    fecha__gte=inicio_mes,
                    fecha__lt=fin_mes
                ).exclude(observaciones__icontains='Completado').count()

                if citas_pendientes_mes >= limite:
                    return _responder_error(
                        request,
                        f"Ya tienes {limite} citas pendientes este mes. Debes esperar la confirmación "
                        f"del barbero en alguna de tus citas antes de agendar otra."
                    )

                # --- Barbero: obtener o crear (igual que el INSERT original) ---
                barbero = Barbero.objects.filter(idusuariofk_id=usuario_barbero_id).first()
                if not barbero:
                    barbero = Barbero.objects.create(
                        idusuariofk_id=usuario_barbero_id,
                        especialidad='General',
                    )

                # --- 5. Choque de horario POR DURACIÓN del servicio ---
                nueva_inicio = datetime.combine(fecha_obj, hora_objeto)
                nueva_fin = nueva_inicio + timedelta(minutes=servicio.duracion or 30)

                citas_barbero_dia = Cita.objects.filter(
                    idbarberofk=barbero, fecha=fecha_obj
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

                agenda_creada = Agenda.objects.create(
                    idbarberofk=barbero,
                    fecha=fecha_obj,
                    horainicio=hora_objeto,
                )

                Cita.objects.create(
                    fecha=fecha_obj,
                    horainicio=hora_objeto,
                    idserviciofk=servicio,
                    idpagofk=nuevo_pago,
                    idbarberofk=barbero,
                    idclientefk=cliente,
                    idagendafk=agenda_creada,
                    observaciones=observaciones,
                )

                # =============================================================
                # Notificaciones individuales por perfil
                # =============================================================
                fecha_legible = fecha_obj.strftime('%d/%m/%Y')

                Notificacion.objects.create(
                    idusuariofk=usuario_actual,
                    tipo='reserva_creada',
                    mensaje=(
                        f"Tu cita de {servicio.nombreservicio} quedó reservada para el "
                        f"{fecha_legible} a las {hora_reserva} con {nombre_barbero}."
                    )
                )

                if nombre_barbero_obj:
                    Notificacion.objects.create(
                        idusuariofk=nombre_barbero_obj,
                        tipo='nueva_cita',
                        mensaje=(
                            f"{usuario_actual.nombre} agendó el servicio de {servicio.nombreservicio} "
                            f"para el {fecha_legible} a las {hora_reserva}."
                        )
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
        qs = Cita.objects.select_related(
            'idserviciofk',
            'idbarberofk__idusuariofk',
            'idclientefk__idusuariofk',
        ).order_by('-fecha', '-horainicio')

        if not es_admin:
            qs = qs.filter(idclientefk__idusuariofk=usuario_actual)

        for c in qs:
            barbero_nombre = "No asignado"
            if c.idbarberofk and c.idbarberofk.idusuariofk:
                barbero_nombre = c.idbarberofk.idusuariofk.nombre

            cliente_nombre = "Cliente General"
            if c.idclientefk and c.idclientefk.idusuariofk:
                cliente_nombre = c.idclientefk.idusuariofk.nombre

            observaciones_texto = c.observaciones if c.observaciones else ""
            es_completada = "Completado" in observaciones_texto

            citas.append({
                'idCita': c.idCita,
                'fecha': c.fecha,
                'horainicio': c.horainicio,
                'servicio_nombre': c.idserviciofk.nombreservicio if c.idserviciofk else "No asignado",
                'barbero_nombre': barbero_nombre,
                'cliente_nombre': cliente_nombre,
                'observaciones': observaciones_texto,
                'es_completada': es_completada,
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
            cliente = Cliente.objects.filter(idusuariofk=usuario_actual).first()
            if not cliente:
                raise Exception("Cliente no encontrado.")

            cita = Cita.objects.get(idCita=id_cita, idclientefk=cliente)

            if cita.observaciones and "Completado" in cita.observaciones:
                messages.error(request, "No puedes cancelar una cita que ya fue completada por el barbero")
                return redirect('mis_citas')
            
            agenda = cita.idagendafk

            cita.delete()
            if agenda:
                agenda.delete()

        messages.success(request, "Tu reserva ha sido cancelada exitosamente.")
    except Cita.DoesNotExist:
        messages.error(request, "La cita no existe o no tienes permisos para cancelarla.")
    except Exception as e:
        messages.error(request, f"Error al cancelar la cita: {e}")

    return redirect('mis_citas')


def cancelar_cita_admin(request, id_cita):
    user_sistema = request.user
    usuario_actual = Usuario.objects.get(correo=user_sistema.email)

    # Validar permisos de Administrador
    if not (usuario_actual.idrolfk_id == 1 or user_sistema.is_staff):
        messages.error(request, "No tienes permisos de administrador para realizar esta acción.")
        return redirect('mis_citas')

    try:
        with transaction.atomic():
            # Traemos la cita con sus relaciones para construir un buen mensaje
            cita = Cita.objects.select_related(
                'idclientefk__idusuariofk',
                'idbarberofk__idusuariofk',
                'idserviciofk',
                'idagendafk'
            ).get(idCita=id_cita)

            # Extraemos los datos antes de borrar la cita
            cliente_usuario = cita.idclientefk.idusuariofk if cita.idclientefk else None
            barbero_nombre = cita.idbarberofk.idusuariofk.nombre if (cita.idbarberofk and cita.idbarberofk.idusuariofk) else "el barbero asignado"
            servicio_nombre = cita.idserviciofk.nombreservicio if cita.idserviciofk else "tu servicio"
            fecha_str = cita.fecha.strftime('%d/%m/%Y') if cita.fecha else ""
            hora_str = cita.horainicio.strftime('%H:%M') if cita.horainicio else ""

            # 1. Crear la notificación para el cliente si existe el usuario
            if cliente_usuario:
                Notificacion.objects.create(
                    idusuariofk=cliente_usuario,
                    tipo='cita_cancelada_admin',
                    mensaje=(
                        f"Tu cita de {servicio_nombre} para el {fecha_str} a las {hora_str} "
                        f"ha sido cancelada debido a que {barbero_nombre} no se encuentra disponible. "
                        f"Por favor ingresa al sistema y vuelve a reservar en otro horario o con otro barbero."
                    )
                )

            # 2. Borrar la agenda y la cita para liberar el espacio en el sistema
            agenda = cita.idagendafk
            cita.delete()
            if agenda:
                agenda.delete()

        messages.success(request, f"La cita #{id_cita} fue cancelada y se le notificó al cliente correctamente.")
    except Cita.DoesNotExist:
        messages.error(request, "La cita especificada no existe.")
    except Exception as e:
        messages.error(request, f"Error al cancelar la cita: {e}")

    return redirect('ver_todas_citas_admin')

def ver_todas_citas_admin(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para realizar esta acción.")
        return redirect('login')

    user_sistema = request.user
    usuario_actual = Usuario.objects.get(correo=user_sistema.email)

    # Validar permisos de Administrador
    if not (usuario_actual.idrolfk_id == 1 or user_sistema.is_staff):
        messages.error(request, "No tienes permisos de administrador para acceder a esta sección.")
        return redirect('mis_citas')

    # Consulta optimizada con select_related
    citas = Cita.objects.select_related(
        'idserviciofk',
        'idbarberofk__idusuariofk',
        'idclientefk__idusuariofk',
        'idagendafk'
    ).order_by('-fecha', '-horainicio')

    return render(request, 'ver_citas_admin.html', {
        'citas': citas
    })