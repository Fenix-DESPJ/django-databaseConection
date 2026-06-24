from django.urls import path
from . import views

urlpatterns = [
    path('', views.crear_reserva, name='crear_reserva'),
    path('agenda/', views.agenda_view, name='agenda'),
    path('mis-citas/', views.mis_citas_view, name='mis_citas'),
    path('cancelar/<int:id_cita>/', views.cancelar_cita_cliente, name='cancelar_cita_cliente'),
    path('admin-cancelar/<int:id_cita>/', views.cancelar_cita_admin, name='cancelar_cita_admin'),
]