# usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('registrarse/', views.registrarse, name='registrarse'),
    path('panel-barbero/', views.panel_barbero, name='panel_barbero'),
    path('citas/<int:cita_id>/editar-pago/', views.editar_metodo_pago, name='editar_metodo_pago'),
    path('completar-cita/<int:cita_id>/', views.completar_cita, name='completar_cita'),
    path('iniciar-sesion/', views.iniciar_sesion, name='iniciar_sesion'),
    path('google-iniciar/<str:rol>/', views.seleccionar_rol_google, name='seleccionar_rol_google'),  # NUEVO
    path('cerrar-sesion/', views.cerrar_sesion, name='cerrar_sesion'),
    # ... el resto igual, SIN la línea de 'google-login/' vieja
    path('olvide-contrasena/', views.olvide_contrasena, name='olvide_contrasena'),
    path('cambiar-contrasena/<str:token>/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('perfil/guardar/', views.guardar_perfil, name='guardar_perfil'),
    path('perfil/foto/', views.gestionar_foto_perfil, name='gestionar_foto_perfil'),
    path('notificaciones/lista/', views.listar_notificaciones, name='listar_notificaciones'),
    path('notificaciones/marcar-leidas/', views.marcar_notificaciones_leidas, name='marcar_notificaciones_leidas'),
    path('calificacion/pendiente/', views.verificar_calificacion_pendiente, name='verificar_calificacion_pendiente'),
    path('calificacion/guardar/', views.guardar_calificacion, name='guardar_calificacion'),
    path('calificacion/omitir/', views.omitir_calificacion, name='omitir_calificacion'),
    path('dashboard/perfiles/', views.editar_perfiles_admin, name='editar_perfiles'),
    path('dashboard/perfiles/eliminar/<int:usuario_id>/', views.eliminar_perfil, name='eliminar_perfil'),
    path('analisis-rostro/', views.analisis_rostro_view, name='analisis_rostro'),
    path('analisis-rostro/procesar/', views.analizar_rostro_ajax, name='analizar_rostro_ajax'),
    path('admin-dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('editar-contenido-index/', views.editar_contenido_index, name='editar_contenido_index'),
    path('usuarios/admin-dashboard/todas-citas/', views.ver_todas_citas_admin, name='ver_todas_citas_admin'),
    path('eliminar-mi-cuenta/', views.eliminar_mi_cuenta, name='eliminar_mi_cuenta'),
]