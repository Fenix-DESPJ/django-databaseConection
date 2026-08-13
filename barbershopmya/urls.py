"""
URL configuration for barbershopmya project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for barbershopmya project.
"""
"""
URL configuration for barbershopmya project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

from negocio.views import gestionar_agenda_admin
from servicios import views
from servicios import views as servicios_views
from usuarios import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    # La Raíz (Home)
    path('', usuarios_views.home, name='home'),

    path('servicios/', include('servicios.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('reservas/', include('reservas.urls')),
    path('servicios-ind/', views.servicios_ind, name='servicios_ind'),
    path('gestionar-agenda/', gestionar_agenda_admin, name='gestionar_agenda_admin'),
    path('reservas/disponibilidad/', servicios_views.disponibilidad_ajax, name='disponibilidad_ajax'),
]

# ---------------------------------------------------------------------------
# Módulo de IA (análisis de forma de rostro) — AISLADO.
# Si la carpeta analisis_facial/ no existe (por ejemplo la borraste mientras
# pruebas otra cosa) o algo revienta al importar sus urls, esta ruta cae en
# la plantilla mantenimiento.html en vez de tumbar el arranque de TODO el
# proyecto (agendamiento, clientes, login, etc.).
#
# mantenimiento.html vive en templates/ (raíz del proyecto), NO dentro de
# analisis_facial/, así que sigue disponible incluso si esa app desaparece.
# ---------------------------------------------------------------------------
try:
    urlpatterns += [
        path('usuarios/analisis-rostro/', include('analisis_facial.urls')),
    ]
except Exception:
    def _analisis_rostro_en_mantenimiento(request, *args, **kwargs):
        return render(request, 'mantenimiento.html', {
            'feature_nombre': 'Análisis de forma de rostro',
            'mensaje': (
                'Esta función depende de un módulo de inteligencia artificial que '
                'no está disponible en este entorno ahora mismo. El agendamiento de '
                'citas, tu perfil y el resto del sitio siguen funcionando con normalidad.'
            ),
            'volver_url': 'home',
        }, status=503)

    urlpatterns += [
        path('usuarios/analisis-rostro/', _analisis_rostro_en_mantenimiento, name='analisis_rostro'),
        path('usuarios/analisis-rostro/procesar/', _analisis_rostro_en_mantenimiento, name='analizar_rostro_ajax'),
    ]

# Archivos estáticos (siempre al final)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)