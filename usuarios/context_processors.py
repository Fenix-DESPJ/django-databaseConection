# usuarios/context_processors.py
from django.conf import settings


def google_client_id(request):
    """
    Expone GOOGLE_CLIENT_ID en todos los templates sin tener que pasarlo
    manualmente en cada view. Se usa en el botón 'Iniciar con Google'.
    """
    return {'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID}