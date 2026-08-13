# negocio/utils_disponibilidad.py
"""
Mantiene la agenda pública (DiaHabilitado) extendida automáticamente en una
ventana móvil de "hoy hasta N días adelante", para que el calendario de
reservas SIEMPRE tenga disponibilidad más allá del mes calendario actual,
sin depender de que un administrador entre manualmente a "aplicar patrón"
cada vez que cambia el mes.

Es idempotente: sólo crea los DiaHabilitado que todavía no existan en el
rango. Si el admin ya generó o tocó a mano un día, se respeta tal cual está.
"""
from datetime import date, timedelta
from django.core.cache import cache

from .models import ConfiguracionHorario, DiaHabilitado

DIAS_ADELANTE = 32                 # ventana móvil (mes + margen de días no hábiles)
CACHE_KEY = "negocio:agenda_auto_extendida"
CACHE_TTL_SEGUNDOS = 60 * 60 * 6   # como máximo recalcula cada 6 horas


def _dia_habilitado_segun_patron(patron: str, dow: int) -> bool:
    """dow: 0=lunes ... 6=domingo (igual que date.weekday())."""
    if patron == 'todos':
        return True
    if patron == 'ls':
        return dow <= 5   # lunes a sábado
    return dow <= 4        # 'lv' (por defecto): lunes a viernes


def asegurar_dias_habilitados(forzar: bool = False) -> int:
    """
    Crea los DiaHabilitado faltantes desde hoy hasta hoy + DIAS_ADELANTE,
    usando el patrón automático guardado en ConfiguracionHorario
    (campo `patron_automatico`, ver instrucciones de migración).

    Devuelve cuántos registros nuevos creó (0 si no hizo nada, por ejemplo
    porque ya se había ejecutado hace menos de CACHE_TTL_SEGUNDOS).
    """
    if not forzar and cache.get(CACHE_KEY):
        return 0

    config, _ = ConfiguracionHorario.objects.get_or_create(pk=1)
    patron = getattr(config, 'patron_automatico', 'lv') or 'lv'

    hoy = date.today()
    limite = hoy + timedelta(days=DIAS_ADELANTE)

    fechas_existentes = set(
        DiaHabilitado.objects.filter(fecha__gte=hoy, fecha__lte=limite)
        .values_list('fecha', flat=True)
    )

    nuevos = []
    dia = hoy
    while dia <= limite:
        if dia not in fechas_existentes:
            habilitado = _dia_habilitado_segun_patron(patron, dia.weekday())
            nuevos.append(DiaHabilitado(fecha=dia, habilitado=habilitado))
        dia += timedelta(days=1)

    if nuevos:
        DiaHabilitado.objects.bulk_create(nuevos, ignore_conflicts=True)

    cache.set(CACHE_KEY, True, CACHE_TTL_SEGUNDOS)
    return len(nuevos)