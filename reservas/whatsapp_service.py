import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppSendError(Exception):
    """Se lanza cuando el envío a la API de WhatsApp falla."""
    pass


def enviar_recordatorio_whatsapp(telefono_destino, nombre_cliente, nombre_servicio, hora_cita):
    """
    Envía un mensaje de plantilla (template) por WhatsApp Cloud API.

    IMPORTANTE: al ser un mensaje iniciado por el negocio (no es respuesta
    a un mensaje del cliente en las últimas 24h), Meta EXIGE usar un
    "message template" pre-aprobado. No puedes mandar texto libre aquí.

    Args:
        telefono_destino (str): número en formato E.164 sin '+', ej: '573001234567'
        nombre_cliente (str)
        nombre_servicio (str)
        hora_cita (str): hora formateada, ej: '3:00 PM'

    Returns:
        (bool, dict|str): (éxito, respuesta_o_error)
    """
    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}"
        f"/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono_destino,
        "type": "template",
        "template": {
            "name": settings.WHATSAPP_TEMPLATE_RECORDATORIO,
            "language": {"code": "es_CO"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": nombre_cliente},
                        {"type": "text", "text": nombre_servicio},
                        {"type": "text", "text": hora_cita},
                    ],
                }
            ],
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("WhatsApp enviado a %s | respuesta: %s", telefono_destino, data)
        return True, data

    except requests.exceptions.HTTPError as e:
        logger.error(
            "HTTPError enviando WhatsApp a %s: %s | body: %s",
            telefono_destino, e, response.text,
        )
        return False, response.text

    except requests.exceptions.Timeout:
        logger.error("Timeout enviando WhatsApp a %s", telefono_destino)
        return False, "timeout"

    except requests.exceptions.RequestException as e:
        logger.error("Error de conexión enviando WhatsApp a %s: %s", telefono_destino, e)
        return False, str(e)