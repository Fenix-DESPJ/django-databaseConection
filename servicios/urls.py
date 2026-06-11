from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('agenda/', views.agenda, name='agenda'),
    path('perfil/', views.perfil, name='perfil'),
    path('reservas/', views.reservas, name='reservas'),
    path('servicios/', views.servicios, name='servicios'),
    path('servicios-ind/', views.servicios_ind, name='servicios_ind'),
    path('servicios-paq-1/', views.servicios_paq, name='servicios_paq_1'),
    path('servicios-paq-2/', views.servicios_paq_2, name='servicios_paq_2'),
    path('servicios/paquetes/1/', RedirectView.as_view(url='/servicios-paq-1/')),
    path('iniciar-sesion/', views.iniciar_sesion, name='iniciar_sesion'),
    path('registrarse/', views.registrarse, name='registrarse'),
]