import cv2
import numpy as np
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh

# =========================================================================
# Índices de landmarks de MediaPipe Face Mesh (468 puntos)
# =========================================================================
LM_TOP_FRENTE = 10
LM_MENTON = 152
LM_POMULO_IZQ = 234
LM_POMULO_DER = 454

# RECALIBRADO: 132/361 quedaban a un solo paso de los pómulos en el
# contorno facial (FACEMESH_FACE_OVAL), por eso el ratio nunca bajaba de
# 0.94 sin importar la mandíbula real. 172/397 están más adentro, hacia
# el mentón, y sí deberían mostrar variación real entre un maxilar
# cuadrado y uno afinado.
LM_MANDIBULA_IZQ = 172
LM_MANDIBULA_DER = 397

# RECALIBRADO: 103/332 quedaban pegados al punto central superior (10),
# midiendo casi lo mismo en todos los rostros (0.72-0.76 en tus 10 pruebas).
# 21/251 están más hacia el lateral, a la altura de ceja/sien, que es
# donde de verdad se mide el "ancho de frente" con cinta métrica.
LM_FRENTE_IZQ = 21
LM_FRENTE_DER = 251


class RostroNoDetectadoError(Exception):
    """Se lanza cuando MediaPipe no logra detectar un rostro en la imagen."""
    pass


def _distancia(p1, p2):
    return float(np.hypot(p1[0] - p2[0], p1[1] - p2[1]))


def analizar_forma_rostro(ruta_imagen: str) -> dict:
    imagen = cv2.imread(ruta_imagen)
    if imagen is None:
        raise RostroNoDetectadoError("No se pudo leer el archivo de imagen.")

    alto, ancho, _ = imagen.shape
    imagen_rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    ) as face_mesh:
        resultados = face_mesh.process(imagen_rgb)

    if not resultados.multi_face_landmarks:
        raise RostroNoDetectadoError(
            "No se detectó ningún rostro en la imagen. Intenta con mejor iluminación y de frente."
        )

    landmarks = resultados.multi_face_landmarks[0].landmark

    def punto(idx):
        lm = landmarks[idx]
        return (lm.x * ancho, lm.y * alto)

    top_frente = punto(LM_TOP_FRENTE)
    menton = punto(LM_MENTON)
    pomulo_izq = punto(LM_POMULO_IZQ)
    pomulo_der = punto(LM_POMULO_DER)
    mandibula_izq = punto(LM_MANDIBULA_IZQ)
    mandibula_der = punto(LM_MANDIBULA_DER)
    frente_izq = punto(LM_FRENTE_IZQ)
    frente_der = punto(LM_FRENTE_DER)

    largo_rostro = _distancia(top_frente, menton)
    ancho_pomulos = _distancia(pomulo_izq, pomulo_der)
    ancho_mandibula = _distancia(mandibula_izq, mandibula_der)
    ancho_frente = _distancia(frente_izq, frente_der)

    if ancho_pomulos == 0:
        raise RostroNoDetectadoError("No se pudieron calcular las proporciones del rostro correctamente.")

    forma = _clasificar_forma(largo_rostro, ancho_pomulos, ancho_mandibula, ancho_frente)

    return {
        'forma': forma,
        'metricas': {
            'ratio_largo_ancho': round(largo_rostro / ancho_pomulos, 2),
            'ratio_mandibula_pomulo': round(ancho_mandibula / ancho_pomulos, 2),
            'ratio_frente_pomulo': round(ancho_frente / ancho_pomulos, 2),
        }
    }


def _clasificar_forma(largo, pomulos, mandibula, frente):
    """
    Umbrales recalibrados con proporciones típicas de literatura de
    forma de rostro (Oval ~1.4-1.6 largo/ancho, Redondo/Cuadrado ~1.0-1.15,
    Alargado >1.6). ADVERTENCIA: son un punto de partida razonado, no
    todavía validado con tus fotos reales — corré calibrar_landmarks.py
    con estos mismos pares (21/251 y 172/397) y ajustamos TOL si hace falta.
    """
    r_largo = largo / pomulos
    r_mandibula = mandibula / pomulos
    r_frente = frente / pomulos

    TOL = 0.06

    d_frente_pomulo = r_frente - 1.0
    d_mandibula_pomulo = r_mandibula - 1.0
    d_frente_mandibula = r_frente - r_mandibula

    ancho_max = max(r_frente, 1.0, r_mandibula)

    # 1. TRIANGULAR: mandíbula más ancha que pómulos y que frente
    if (r_mandibula >= ancho_max - 0.01
            and d_mandibula_pomulo > TOL * 0.5
            and d_frente_mandibula < -TOL):
        return "Triangular"

    # 2. CORAZÓN: frente más ancha, mandíbula notablemente afinada
    if (r_frente >= ancho_max - 0.01
            and d_frente_mandibula > TOL
            and d_frente_pomulo > -TOL * 0.5):
        return "Corazón"

    # 3. DIAMANTE: pómulos son lo más ancho; frente y mandíbula angostas y similares
    if (d_frente_pomulo < -TOL
            and d_mandibula_pomulo < -TOL
            and abs(d_frente_mandibula) < TOL
            and r_largo > 1.3):
        return "Diamante"

    anchos_similares = abs(d_frente_pomulo) < TOL and abs(d_mandibula_pomulo) < TOL

    # 4. ALARGADO: notablemente más largo que ancho
    if r_largo > 1.65:
        return "Alargado"

    # 5. CUADRADO: anchos similares, proporción corta/media
    if anchos_similares and r_largo <= 1.4:
        return "Cuadrado"

    # 6. REDONDO: corto y ancho, frente y mandíbula angostas frente a pómulos
    if (r_largo < 1.35
            and d_mandibula_pomulo < -TOL * 0.7
            and d_frente_pomulo < -TOL * 0.7):
        return "Redondo"

    # 7. OVALADO: caso equilibrado
    return "Ovalado"


RECOMENDACIONES_POR_FORMA = {
    "Ovalado": "Tu rostro es equilibrado: casi cualquier corte te queda bien. Prueba degradados clásicos o texturizados.",
    "Redondo": "Busca cortes con volumen arriba y laterales cortos para alargar visualmente el rostro (ej. pompadour, undercut).",
    "Cuadrado": "Los cortes con textura suave en los laterales suavizan la mandíbula (ej. quiff, flow con fade).",
    "Alargado": "Evita mucho volumen arriba; prueba flequillos y cortes con más ancho lateral (ej. crop francés).",
    "Corazón": "Cortes que reduzcan volumen en la frente y aporten en la zona de la mandíbula funcionan mejor (ej. side part).",
    "Diamante": "Cortes con volumen moderado en la frente y mandíbula equilibran los pómulos marcados (ej. textured crop).",
    "Triangular": "Cortes con volumen en la parte superior y laterales más cerrados equilibran una mandíbula marcada (ej. pompadour corto, quiff).",
}