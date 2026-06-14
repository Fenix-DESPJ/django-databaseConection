"""
URL configuration for barbershopmya project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# Importa las vistas solo si vas a usarlas directamente en este archivo
# Aunque, para mantener el orden, lo ideal es que cada app gestione sus propias rutas.
from servicios import views 

urlpatterns = [
    # 1. Administración
    path('admin/', admin.site.urls),
    
    # 2. Rutas de tus aplicaciones (usando include)
    path('servicios/', include('servicios.urls')),
    path('reservas/', include('reservas.urls')),
    
    # 3. Rutas específicas (Solo si son excepciones o páginas sueltas)
    path('servicios-ind/', views.servicios_ind, name='servicios_ind'),
    
    # 4. Rutas raíz al final
    path('', include('usuarios.urls')), 
]

# 5. Configuración de archivos estáticos (esto siempre va al final)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])