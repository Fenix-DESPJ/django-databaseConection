import calendar
from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from usuarios.models import Usuario
from .models import ConfiguracionHorario, DiaHabilitado, BarberoDiaHabilitado

MESES_ES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
            "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


@login_required
def gestionar_agenda_admin(request):
    if request.session.get('usuario_rol_id') != 1:
        messages.error(request, "Acceso denegado. Solo el administrador puede gestionar la agenda.")
        return redirect('home')

    config, _ = ConfiguracionHorario.objects.get_or_create(pk=1)
    hoy = date.today()

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
            config.intervalo_minutos = int(request.POST.get('intervalo_minutos', 30))
            config.limite_citas_mensuales = int(request.POST.get('limite_citas_mensuales', 3))
            config.save()
            messages.success(request, "Horario de atención actualizado correctamente.")
            return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_gestion_str}")

        elif accion == 'aplicar_patron':
            patron = request.POST.get('patron')
            anio_p = int(request.POST.get('anio', anio))
            mes_p = int(request.POST.get('mes', mes))
            _, dias_en_mes = calendar.monthrange(anio_p, mes_p)
            for d in range(1, dias_en_mes + 1):
                dia = date(anio_p, mes_p, d)
                if dia < hoy:
                    continue
                dow = dia.weekday()  # 0=lunes
                if patron == 'todos':
                    habilitado = True
                elif patron == 'lv':
                    habilitado = dow <= 4
                elif patron == 'ls':
                    habilitado = dow <= 5
                else:
                    continue
                DiaHabilitado.objects.update_or_create(fecha=dia, defaults={'habilitado': habilitado})
            messages.success(request, "Patrón aplicado sobre el mes seleccionado.")
            anio, mes = anio_p, mes_p
            return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_gestion_str}")

        elif accion == 'toggle_dia':
            fecha_str = request.POST.get('fecha')
            dia_obj = DiaHabilitado.objects.filter(fecha=fecha_str).first()
            if dia_obj:
                dia_obj.habilitado = not dia_obj.habilitado
                dia_obj.save()
            else:
                DiaHabilitado.objects.create(fecha=fecha_str, habilitado=True)
            anio = int(request.POST.get('anio', anio))
            mes = int(request.POST.get('mes', mes))
            return redirect(f"{request.path}?anio={anio}&mes={mes}&fecha_gestion={fecha_gestion_str}")

        elif accion == 'limpiar_agenda':
            DiaHabilitado.objects.filter(fecha__gte=hoy).delete()
            messages.success(
                request,
                "Agenda limpiada. Todos los días quedaron deshabilitados hasta que apliques un patrón o los actives manualmente."
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
                })
        calendario_semanas.append(fila)

    mes_anterior = mes - 1 if mes > 1 else 12
    anio_anterior = anio if mes > 1 else anio - 1
    mes_siguiente = mes + 1 if mes < 12 else 1
    anio_siguiente = anio if mes < 12 else anio + 1

    total_habilitados_mes = sum(
        1 for fila in calendario_semanas for d in fila if d and d['habilitado']
    )

    # =========================================================================
    # Disponibilidad de barberos para el día seleccionado en "fecha_gestion"
    # =========================================================================
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
    })