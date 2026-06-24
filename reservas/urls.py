from django.urls import path
from . import views

urlpatterns = [
    path('', views.crear_reserva, name='crear_reserva'),
    path('agenda/', views.agenda_view, name='agenda'),
]