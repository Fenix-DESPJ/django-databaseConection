import calendar
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from usuarios.models import Usuario
from .models import ConfiguracionHorario, DiaHabilitado, BarberoDiaHabilitado
from .utils_disponibilidad import asegurar_dias_habilitados

MESES_ES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
            "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

PATRONES_VALIDOS = {'todos', 'lv', 'ls'}

DIAS_VENTANA_PATRON = 32  # hoy -> ~1 mes adelante


@login_required
def gestionar_agenda_admin(request):
    if request.session.get('usuario_rol_id') != 1:
        messages.error(request, "Acceso denegado. Solo el administrador puede gestionar la agenda.")
        return redirect('home')

    config, _ = ConfiguracionHorario.objects.get_or_create(pk=1)
    hoy = date.today()

    # Se asegura que la ventana móvil (hoy -> +32 días) esté siempre al día,
    # sin importar si el admin nunca visitó este panel.
    asegurar_dias_habilitados()

    anio = int(request.GET.get('anio', hoy.year))
    mes = int(request.GET.get('mes', hoy.month))
    fecha_gestion_str = request.GET.get('fecha_gestion', hoy.isoformat())
    try:
        fecha_gestion = date.fromisoformat(fecha_gestion_str)
    except ValueError:
        fecha_gestion = hoy
        fecha_gestion_str = hoy.isoformat()

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'guardar_horario':
            config.hora_apertura = request.POST.get('hora_apertura')
            config.hora_cierre = request.POST.get('hora_cierre')

            # Sanitizar y validar intervalo_minutos (mínimo 10, máximo 60)
            intervalo_input = int(request.POST.get('intervalo_minutos', 30))
            config.intervalo_minutos = max(10, min(60, intervalo_input))

            config.limite_citas_mensuales = max(1, int(request.POST.get('limite_citas_mensuales', 3)))

            patron_automatico = request.POST.get('patron_automatico', 'lv')
            if patron_automatico in PATRONES_VALIDOS:
                config.patron_automatico = patron_automatico

            config.save()
            messages.success(request, "Horario de atención actualizado correctamente.")
            return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_gestion_str}")

        elif accion == 'aplicar_patron':
            patron = request.POST.get('patron')

            if patron not in PATRONES_VALIDOS:
                messages.error(request, "Patrón inválido.")
                return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_gestion_str}")

            # Este patrón queda guardado como el "patrón automático" de la
            # agenda: así, cada día nuevo que vaya entrando a la ventana
            # móvil (hoy -> +32 días) se habilitará solo, sin que el admin
            # tenga que volver a tocar nada.
            config.patron_automatico = patron
            config.save()

            # Aplica el patrón de inmediato sobre TODA la ventana móvil
            # (hoy -> +32 días adelante), sin importar qué mes se esté
            # viendo actualmente en el calendario.
            for offset in range(DIAS_VENTANA_PATRON + 1):
                dia = hoy + timedelta(days=offset)
                dow = dia.weekday()  # 0=lunes
                if patron == 'todos':
                    habilitado = True
                elif patron == 'lv':
                    habilitado = dow <= 4
                else:  # 'ls'
                    habilitado = dow <= 5
                DiaHabilitado.objects.update_or_create(fecha=dia, defaults={'habilitado': habilitado})

            messages.success(
                request,
                "Patrón aplicado desde hoy hasta un mes adelante. A partir de ahora, "
                "los próximos días se habilitarán automáticamente siguiendo este mismo patrón."
            )
            return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_gestion_str}")

        elif accion == 'regenerar_agenda':
            # Fuerza la regeneración inmediata de la ventana móvil (hoy -> +32
            # días) ignorando la caché de 6h, útil justo después de cambiar
            # el patrón automático en "guardar_horario".
            creados = asegurar_dias_habilitados(forzar=True)
            messages.success(
                request,
                f"Agenda regenerada: se crearon {creados} día(s) nuevo(s) en la ventana de reserva."
            )
            return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_gestion_str}")

        elif accion == 'toggle_dia':
            fecha_str = request.POST.get('fecha')
            dia_obj = DiaHabilitado.objects.filter(fecha=fecha_str).first()

            if dia_obj and dia_obj.habilitado:
                # Va a quedar deshabilitado: no permitirlo si es el último
                # día habilitado de toda la agenda (desde hoy en adelante).
                dias_habilitados_totales = DiaHabilitado.objects.filter(
                    habilitado=True, fecha__gte=hoy
                ).count()
                if dias_habilitados_totales <= 1:
                    messages.error(
                        request,
                        "No puedes deshabilitar este día: la agenda debe tener siempre al menos un día habilitado."
                    )
                    anio = int(request.POST.get('anio', anio))
                    mes = int(request.POST.get('mes', mes))
                    return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_gestion_str}")
                dia_obj.habilitado = False
                dia_obj.save()
            elif dia_obj:
                dia_obj.habilitado = True
                dia_obj.save()
            else:
                DiaHabilitado.objects.create(fecha=fecha_str, habilitado=True)

            anio = int(request.POST.get('anio', anio))
            mes = int(request.POST.get('mes', mes))
            return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_gestion_str}")

        elif accion == 'limpiar_agenda':
            DiaHabilitado.objects.filter(fecha__gte=hoy).delete()
            # La agenda nunca puede quedar sin ningún día habilitado:
            # se reactiva automáticamente el día de hoy.
            DiaHabilitado.objects.update_or_create(fecha=hoy, defaults={'habilitado': True})
            messages.success(
                request,
                "Agenda limpiada. El día de hoy se mantuvo habilitado automáticamente, ya que la agenda siempre debe tener al menos un día disponible."
            )
            return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_gestion_str}")

        elif accion == 'guardar_barberos_dia':
            fecha_str = request.POST.get('fecha_gestion')
            barberos_activos = set(request.POST.getlist('barberos_activos'))
            for b in Usuario.objects.filter(idrolfk=2):
                habilitado = str(b.idusuario) in barberos_activos
                BarberoDiaHabilitado.objects.update_or_create(
                    idusuariofk=b.idusuario, fecha=fecha_str, defaults={'habilitado': habilitado}
                )
            messages.success(request, "Disponibilidad de barberos actualizada para ese día.")
            return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_str}")

        # Si llega una acción desconocida, simplemente recargamos la página tal cual
        return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_gestion_str}")

    # =========================================================================
    # GET: construcción de la grilla del calendario
    # =========================================================================
    cal = calendar.Calendar(firstweekday=0)  # lunes primero
    semanas = cal.monthdayscalendar(anio, mes)

    dias_habilitados_bd = set(
        DiaHabilitado.objects.filter(habilitado=True).values_list('fecha', flat=True)
    )

    fechas_con_incapacidad = set(
        BarberoDiaHabilitado.objects.filter(
            habilitado=False, fecha__year=anio, fecha__month=mes
        ).values_list('fecha', flat=True)
    )

    calendario_semanas = []
    for semana in semanas:
        fila = []
        for d in semana:
            if d == 0:
                fila.append(None)
            else:
                fecha_actual = date(anio, mes, d)
                fila.append({
                    'numero': d,
                    'fecha': fecha_actual,
                    'habilitado': fecha_actual in dias_habilitados_bd,
                    'pasado': fecha_actual < hoy,
                    'hoy': fecha_actual == hoy,
                    'con_incapacidad': fecha_actual in fechas_con_incapacidad,
                })
        calendario_semanas.append(fila)

    mes_anterior = mes - 1 if mes > 1 else 12
    anio_anterior = anio if mes > 1 else anio - 1
    mes_siguiente = mes + 1 if mes < 12 else 1
    anio_siguiente = anio if mes < 12 else anio + 1

    total_habilitados_mes = sum(
        1 for fila in calendario_semanas for d in fila if d and d['habilitado']
    )

    deshabilitados_ese_dia = set(
        BarberoDiaHabilitado.objects.filter(fecha=fecha_gestion, habilitado=False)
        .values_list('idusuariofk', flat=True)
    )
    barberos_lista = [
        {'id': b.idusuario, 'nombre': b.nombre, 'activo': b.idusuario not in deshabilitados_ese_dia}
        for b in Usuario.objects.filter(idrolfk=2)
    ]

    return render(request, 'agenda_admin.html', {
        'config': config,
        'calendario_semanas': calendario_semanas,
        'nombre_mes': MESES_ES[mes - 1],
        'anio': anio, 'mes': mes,
        'mes_anterior': mes_anterior, 'anio_anterior': anio_anterior,
        'mes_siguiente': mes_siguiente, 'anio_siguiente': anio_siguiente,
        'total_habilitados_mes': total_habilitados_mes,
        'fecha_gestion': fecha_gestion,
        'barberos_lista': barberos_lista,
        'patron_automatico': getattr(config, 'patron_automatico', 'lv'),
    })