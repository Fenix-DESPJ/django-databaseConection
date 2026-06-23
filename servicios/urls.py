from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Solo lo relacionado a servicios
    path('lista/', views.servicios, name='servicios'), 
    path('individual/', views.servicios_ind, name='servicios_ind'),
    path('paquete-1/', views.servicios_paq, name='servicios_paq_1'),
    path('paquete-2/', views.servicios_paq_2, name='servicios_paq_2'),
    # Mantén esta redirección si la necesitas
    path('paquetes/1/', RedirectView.as_view(url='/servicios/paquete-1/')),
]