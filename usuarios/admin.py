from django.contrib import admin
from .models import Usuario, Rol  # Solo los modelos de usuarios

admin.site.register(Usuario)
admin.site.register(Rol)