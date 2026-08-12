import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from reservas.models import Cita
from reservas.whatsapp_service import enviar_recordatorio_whatsapp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Busca citas que ocurren entre 50 y 60 minutos desde ahora, con "
        "recordatorio_enviado=False, y envía un recordatorio por WhatsApp."
    )

    def handle(self, *args, **options):
        ahora = timezone.localtime()
        ventana_inicio = ahora + timedelta(minutes=50)
        ventana_fin = ahora + timedelta(minutes=60)

        fechas_candidatas = {ventana_inicio.date(), ventana_fin.date()}

        citas_candidatas = (
            Cita.objects
            .filter(recordatorio_enviado=False, fecha__in=fechas_candidatas)
            .select_related('idserviciofk', 'idclientefk__idusuariofk')
        )

        enviados, fallidos, omitidos = 0, 0, 0

        for cita in citas_candidatas:
            cita_dt = timezone.make_aware(
                datetime.combine(cita.fecha, cita.horainicio),
                timezone.get_current_timezone(),
            )

            if not (ventana_inicio <= cita_dt <= ventana_fin):
                continue

            cliente = cita.idclientefk
            usuario = cliente.idusuariofk if cliente else None

            telefono = self._normalizar_telefono(getattr(usuario, 'numcelular', None))
            nombre_cliente = getattr(usuario, 'nombre', 'cliente')

            if not telefono:
                self.stdout.write(self.style.WARNING(
                    f"Cita {cita.idCita} sin teléfono válido, se omite."
                ))
                omitidos += 1
                continue

            nombre_servicio = cita.idserviciofk.nombreservicio if cita.idserviciofk else "tu servicio"
            hora_cita = cita.horainicio.strftime('%I:%M %p')

            try:
                exito, resultado = enviar_recordatorio_whatsapp(
                    telefono_destino=telefono,
                    nombre_cliente=nombre_cliente,
                    nombre_servicio=nombre_servicio,
                    hora_cita=hora_cita,
                )
            except Exception:
                logger.exception("Error inesperado enviando recordatorio de cita %s", cita.idCita)
                self.stdout.write(self.style.ERROR(f"Error inesperado en cita {cita.idCita}"))
                fallidos += 1
                continue

            if exito:
                cita.recordatorio_enviado = True
                cita.save(update_fields=['recordatorio_enviado'])
                enviados += 1
                self.stdout.write(self.style.SUCCESS(f"Recordatorio enviado: cita {cita.idCita}"))
            else:
                fallidos += 1
                self.stdout.write(self.style.ERROR(f"Falló envío cita {cita.idCita}: {resultado}"))

        self.stdout.write(self.style.SUCCESS(
            f"Terminado. Enviados: {enviados} | Fallidos: {fallidos} | Omitidos: {omitidos}"
        ))

    @staticmethod
    def _normalizar_telefono(telefono):
        """
        Deja el número solo con dígitos y le antepone el indicativo de
        Colombia (57) si no lo tiene, porque la API de WhatsApp exige
        formato E.164 sin '+', espacios ni guiones: ej. 573001234567.
        """
        if not telefono:
            return None
        digitos = ''.join(filter(str.isdigit, telefono))
        if not digitos:
            return None
        if not digitos.startswith('57'):
            digitos = '57' + digitos
        return digitos