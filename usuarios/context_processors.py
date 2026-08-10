# usuarios/context_processors.py
import re

from django.conf import settings
from .models import ContenidoIndex


def google_client_id(request):
    """
    Expone GOOGLE_CLIENT_ID en todos los templates sin tener que pasarlo
    manualmente en cada view. Se usa en el botón 'Iniciar con Google'.
    """
    return {'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID}

def contenido_global(request):
    """
    Hace disponible el contenido editable del index (y en particular el
    número de WhatsApp de la barbería) en TODOS los templates que extienden
    base.html, sin que cada vista tenga que pasarlo manualmente en su
    contexto. Se usa, por ejemplo, para el botón flotante de WhatsApp.
    """
    contenido = ContenidoIndex.cargar()

    # Limpia el número guardado (ej: "+57 300 123 4567" -> "573001234567")
    # para que sirva como parámetro válido de un link https://wa.me/...
    whatsapp_numero = re.sub(r'\D', '', contenido.whatsapp or '')

    return {
        'contenido_global': contenido,
        'whatsapp_link': f"https://wa.me/{whatsapp_numero}" if whatsapp_numero else None,
    }