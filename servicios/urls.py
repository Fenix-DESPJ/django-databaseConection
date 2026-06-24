from django.urls import path
from . import views

urlpatterns = [
    path('lista/', views.servicios, name='servicios'), 
    path('individual/', views.servicios_ind, name='servicios_ind'),
    path('paquete-1/', views.servicios_paq, name='servicios_paq_1'),
    path('agenda/', views.agenda_view, name='agenda'), # Ahora debe funcionar
]