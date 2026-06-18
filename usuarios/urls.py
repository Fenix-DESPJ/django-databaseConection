from django.urls import path
from . import views

urlpatterns = [
    # Esta es la ruta para http://127.0.0.1:8000/
    path('', views.home, name='home'), 
    
    # Esta es la ruta para http://127.0.0.1:8000/registrarse/
    path('registrarse/', views.registrarse, name='registrarse'),
    path('panel-barbero/', views.panel_barbero, name='panel_barbero'),
    path('completar-cita/<int:cita_id>/', views.completar_cita, name='completar_cita'),
    path('login/', views.iniciar_sesion, name='login'),
    path('iniciar-sesion/', views.iniciar_sesion, name='iniciar_sesion'),
    path('cerrar-sesion/', views.cerrar_sesion, name='cerrar_sesion'),
]