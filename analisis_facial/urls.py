# analisis_facial/urls.py
from django.urls import path
from . import views

# Sin app_name/namespace a propósito: se mantienen los mismos `name=` que ya
# usaba usuarios/urls.py, así {% url 'analisis_rostro' %} y
# {% url 'analizar_rostro_ajax' %} en tus templates NO necesitan cambiar.
urlpatterns = [
    path('', views.analisis_rostro_view, name='analisis_rostro'),
    path('procesar/', views.analizar_rostro_ajax, name='analizar_rostro_ajax'),
]