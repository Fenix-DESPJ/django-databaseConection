# usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'), 
    path('registrarse/', views.registrarse, name='registrarse'),
    path('panel-barbero/', views.panel_barbero, name='panel_barbero'),
    path('completar-cita/<int:cita_id>/', views.completar_cita, name='completar_cita'),
    path('iniciar-sesion/', views.iniciar_sesion, name='iniciar_sesion'),
    path('cerrar-sesion/', views.cerrar_sesion, name='cerrar_sesion'),
    path('olvide-contrasena/', views.olvide_contrasena, name='olvide_contrasena'),
    path('cambiar-contrasena/<str:token>/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('perfil/guardar/', views.guardar_perfil, name='guardar_perfil'),
    path('perfil/foto/', views.gestionar_foto_perfil, name='gestionar_foto_perfil'),
    path('notificaciones/lista/', views.listar_notificaciones, name='listar_notificaciones'),
    path('notificaciones/marcar-leidas/', views.marcar_notificaciones_leidas, name='marcar_notificaciones_leidas'),

    # Rutas del Panel de Administración para perfiles
    path('dashboard/perfiles/', views.editar_perfiles_admin, name='editar_perfiles'),
    path('dashboard/perfiles/eliminar/<int:usuario_id>/', views.eliminar_perfil, name='eliminar_perfil'),
    
    #Ruta propia del Dashboard de Administrador
    path('admin-dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('usuarios/admin-dashboard/todas-citas/', views.ver_todas_citas_admin, name='ver_todas_citas_admin'),
]