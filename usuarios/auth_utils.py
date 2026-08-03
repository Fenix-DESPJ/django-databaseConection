# usuarios/auth_utils.py
import random
import string
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def generar_password_provisional():
    """
    Genera una contraseña temporal fácil de recordar (ej: 'MYABarber4821').
    A propósito NO es súper segura: el usuario debe poder saberla de
    memoria para iniciar sesión tradicional si quiere, mientras tanto
    siempre puede entrar con Google sin usarla.
    """
    sufijo = ''.join(random.choices(string.digits, k=4))
    return f"MYABarber{sufijo}"
