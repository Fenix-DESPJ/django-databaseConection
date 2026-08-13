# analisis_facial/views.py
"""
Vista de análisis de forma de rostro, movida 1:1 desde usuarios/views.py
(sección 8 original). Diferencias respecto al original:

1. Si mediapipe/cv2 no están instalados en este entorno (por el requisito
   de Python 3.11), analisis_rostro_view ahora renderiza directamente
   mantenimiento.html en vez de cargar la página de análisis con los
   controles deshabilitados a medias.
2. analizar_rostro_ajax responde 503 en JSON si falta la librería, para
   que el front-end (script.js) lo muestre en su propio errorBox si el
   usuario llega a esa vista con la librería disponible pero luego falla
   en tiempo de ejecución.
"""
import os
import uuid
import tempfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.templatetags.static import static
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from usuarios.models import Usuario

from .utils import (
    analizar_forma_rostro,
    RostroNoDetectadoError,
    FuncionNoDisponibleError,
    RECOMENDACIONES_POR_FORMA,
    MEDIAPIPE_DISPONIBLE,
)


def analisis_rostro_view(request):
    if not MEDIAPIPE_DISPONIBLE:
        return render(request, 'mantenimiento.html', {
            'feature_nombre': 'Análisis de forma de rostro',
            'mensaje': (
                'Esta función depende de un módulo de inteligencia artificial que '
                'no está disponible en este entorno ahora mismo. El agendamiento de '
                'citas, tu perfil y el resto del sitio siguen funcionando con normalidad.'
            ),
            'volver_url': 'home',
        }, status=503)

    return render(request, 'analisis_rostro.html', {
        'ia_disponible': MEDIAPIPE_DISPONIBLE,
    })


@login_required
@require_POST
def analizar_rostro_ajax(request):
    if not MEDIAPIPE_DISPONIBLE:
        return JsonResponse({
            'ok': False,
            'en_mantenimiento': True,
            'error': ('El análisis de rostro está en mantenimiento temporalmente '
                      '(requiere un entorno con Python 3.11 + mediapipe). '
                      'El resto del sitio funciona con normalidad.'),
        }, status=503)

    usar_perfil = request.POST.get('usar_perfil') == 'true'
    ruta_temporal = None
    es_archivo_temporal_propio = False

    try:
        if usar_perfil:
            try:
                usuario_actual = Usuario.objects.get(correo=request.user.email)
            except Usuario.DoesNotExist:
                return JsonResponse({
                    'ok': False,
                    'error': 'No encontramos tu perfil registrado. Intenta con la cámara en su lugar.'
                }, status=404)

            if not usuario_actual.foto_perfil:
                return JsonResponse({
                    'ok': False,
                    'error': 'Aún no tienes una foto de perfil registrada. Usa la cámara o sube una imagen para continuar.'
                }, status=400)

            ruta_fisica_perfil = os.path.join(settings.MEDIA_ROOT, str(usuario_actual.foto_perfil))
            if not os.path.exists(ruta_fisica_perfil):
                return JsonResponse({
                    'ok': False,
                    'error': 'Tu foto de perfil no se encuentra disponible en el servidor. Por favor usa la cámara o sube una nueva imagen.'
                }, status=404)

            ruta_temporal = ruta_fisica_perfil
            es_archivo_temporal_propio = False

        else:
            archivo = request.FILES.get('imagen')
            if not archivo:
                return JsonResponse({
                    'ok': False,
                    'error': 'No se recibió ninguna imagen. Captura una foto o selecciona un archivo.'
                }, status=400)

            extensiones_validas = ('.jpg', '.jpeg', '.png', '.webp')
            nombre_original = archivo.name.lower()
            if not nombre_original.endswith(extensiones_validas):
                return JsonResponse({
                    'ok': False,
                    'error': 'Formato de imagen no soportado. Usa JPG, PNG o WEBP.'
                }, status=400)

            if archivo.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'ok': False,
                    'error': 'La imagen es demasiado pesada (máximo 5MB).'
                }, status=400)

            carpeta_temporal = tempfile.gettempdir()
            extension = os.path.splitext(nombre_original)[1]
            nombre_temporal = f"analisis_rostro_{uuid.uuid4().hex}{extension}"
            ruta_temporal = os.path.join(carpeta_temporal, nombre_temporal)

            with open(ruta_temporal, 'wb+') as destino:
                for chunk in archivo.chunks():
                    destino.write(chunk)

            es_archivo_temporal_propio = True

        resultado = analizar_forma_rostro(ruta_temporal)
        forma_detectada = resultado['forma']
        info_recomendacion = RECOMENDACIONES_POR_FORMA.get(forma_detectada, {"texto": "", "cortes": []})

        cortes_con_url = []
        for corte in info_recomendacion.get("cortes", []):
            cortes_con_url.append({
                "nombre": corte["nombre"],
                "descripcion": corte["descripcion"],
                "imagen_url": static(corte["imagen"])
            })

        return JsonResponse({
            'ok': True,
            'forma': forma_detectada,
            'metricas': resultado['metricas'],
            'recomendacion': info_recomendacion.get("texto", ""),
            'cortes': cortes_con_url,
        })

    except RostroNoDetectadoError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=422)

    except FuncionNoDisponibleError as e:
        return JsonResponse({'ok': False, 'en_mantenimiento': True, 'error': str(e)}, status=503)

    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': f'Ocurrió un problema al procesar la imagen: {e}'
        }, status=500)

    finally:
        if ruta_temporal and es_archivo_temporal_propio and os.path.exists(ruta_temporal):
            try:
                os.remove(ruta_temporal)
            except OSError:
                pass