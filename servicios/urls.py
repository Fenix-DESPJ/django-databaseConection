from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('lista/', views.servicios, name='servicios'), 
    path('individual/', views.servicios_ind, name='servicios_ind'),
    path('paquete-1/', views.servicios_paq, name='servicios_paq_1'),
    path('agenda/', views.agenda_view, name='agenda'), # Ahora debe funcionar
    path('servicio/nuevo/', views.crear_servicio, name='crear_servicio'),
    path('servicio/editar/<int:pk>/', views.editar_servicio, name='editar_servicio'),
    path('servicio/eliminar/<int:pk>/', views.eliminar_servicio, name='eliminar_servicio'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)