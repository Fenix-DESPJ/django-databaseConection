import sys
from django.apps import AppConfig


class ReservasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservas'

    def ready(self):
        # Evita que el planificador intente arrancar durante comandos de migración o tests
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return

        # Inicia el planificador automáticamente al arrancar Django de forma normal
        try:
            from .scheduler import start
            start()
        except Exception:
            pass