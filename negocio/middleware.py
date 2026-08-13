# negocio/middleware.py
from .utils_disponibilidad import asegurar_dias_habilitados


class AutoExtenderAgendaMiddleware:
    """
    En cada request se asegura (con caché de 6h, así que en la práctica es
    casi gratis) de que la agenda pública tenga habilitados los próximos
    ~32 días. Así el calendario de reservas SIEMPRE avanza junto con la
    fecha real, sin depender de que un admin entre a "aplicar patrón".

    Nunca debe tumbar el sitio: si algo falla aquí, se ignora y se
    reintenta en el siguiente request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            asegurar_dias_habilitados()
        except Exception:
            pass
        return self.get_response(request)