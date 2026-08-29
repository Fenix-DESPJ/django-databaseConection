import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from reservas.models import Cita
from reservas.whatsapp_service import enviar_recordatorio_whatsapp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Busca citas que ocurrirán en 24 horas y en 1 hora, "
        "y envía el recordatorio por WhatsApp correspondiente."
    )

    def handle(self, *args, **options):
        ahora = timezone.localtime()

        # Ventana 1 hora (50 a 60 min desde ahora)
        v1h_inicio = ahora + timedelta(minutes=50)
        v1h_fin = ahora + timedelta(minutes=60)

        # Ventana 24 horas (23h 50m a 24h 00m desde ahora)
        v24h_inicio = ahora + timedelta(hours=23, minutes=50)
        v24h_fin = ahora + timedelta(hours=24)

        fechas_candidatas = {
            v1h_inicio.date(),
            v1h_fin.date(),
            v24h_inicio.date(),
            v24h_fin.date(),
        }

        # Citas a las que aún les falta enviar al menos uno de los dos recordatorios
        citas_candidatas = (
            Cita.objects.filter(
                Q(recordatorio_1h_enviado=False) | Q(recordatorio_24h_enviado=False),
                fecha__in=fechas_candidatas,
            ).select_related('idserviciofk', 'idclientefk__idusuariofk')
        )

        enviados, fallidos, omitidos = 0, 0, 0

        for cita in citas_candidatas:
            cita_dt = timezone.make_aware(
                datetime.combine(cita.fecha, cita.horainicio),
                timezone.get_current_timezone(),
            )

            # Identificar qué recordatorio corresponde procesar
            es_ventana_1h = v1h_inicio <= cita_dt <= v1h_fin and not cita.recordatorio_1h_enviado
            es_ventana_24h = v24h_inicio <= cita_dt <= v24h_fin and not cita.recordatorio_24h_enviado

            if not (es_ventana_1h or es_ventana_24h):
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
            tipo_recordatorio = "1h" if es_ventana_1h else "24h"

            try:
                exito, resultado = enviar_recordatorio_whatsapp(
                    telefono_destino=telefono,
                    nombre_cliente=nombre_cliente,
                    nombre_servicio=nombre_servicio,
                    hora_cita=hora_cita,
                    tipo_recordatorio=tipo_recordatorio,
                )
            except Exception:
                logger.exception("Error inesperado enviando recordatorio de cita %s", cita.idCita)
                self.stdout.write(self.style.ERROR(f"Error inesperado en cita {cita.idCita}"))
                fallidos += 1
                continue

            if exito:
                campos_a_actualizar = []
                if es_ventana_1h:
                    cita.recordatorio_1h_enviado = True
                    campos_a_actualizar.append('recordatorio_1h_enviado')
                elif es_ventana_24h:
                    cita.recordatorio_24h_enviado = True
                    campos_a_actualizar.append('recordatorio_24h_enviado')

                cita.save(update_fields=campos_a_actualizar)
                enviados += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Recordatorio ({tipo_recordatorio}) enviado: cita {cita.idCita}"
                ))
            else:
                fallidos += 1
                self.stdout.write(self.style.ERROR(
                    f"Falló envío cita {cita.idCita}: {resultado}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Terminado. Enviados: {enviados} | Fallidos: {fallidos} | Omitidos: {omitidos}"
        ))

    @staticmethod
    def _normalizar_telefono(telefono):
        """
        Deja el número solo con dígitos y le antepone el indicativo de
        Colombia (57) si no lo tiene.
        """
        if not telefono:
            return None
        digitos = ''.join(filter(str.isdigit, telefono))
        if not digitos:
            return None
        if not digitos.startswith('57'):
            digitos = '57' + digitos
        return digitos