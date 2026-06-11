from django.contrib import admin
from .models import Servicio, Cita, Pago # Estos SI están en servicios/models.py

admin.site.register(Servicio)
admin.site.register(Cita)
admin.site.register(Pago)