from django.urls import path
from . import views

urlpatterns = [
    # Esta es la ruta para http://127.0.0.1:8000/
    path('', views.home, name='home'), 
    
    # Esta es la ruta para http://127.0.0.1:8000/registrarse/
    path('registrarse/', views.registrarse, name='registrarse'),
]