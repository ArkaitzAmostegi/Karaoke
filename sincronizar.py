"""Re-cronometra los .lrc usando la propia cancion.

La idea: el TEXTO del .lrc que ya tienes es bueno; lo que no cuadra son los
TIEMPOS. Asi que:

  1. Whisper escucha el mp3 y devuelve cada palabra que oye CON su instante.
     Las palabras salen con erratas (se canta con musica de fondo: solo acierta
     un 46%), pero los instantes de las que SI acierta son fiables.
  2. Se alinean las palabras del .lrc con las que oyo Whisper. Donde coinciden
     tenemos un ANCLA: "esta palabra del .lrc suena en el segundo X".
  3. Cada linea del .lrc coge el tiempo de su primera palabra. Las que no
     pegaron con ninguna ancla se interpolan entre las vecinas.

NUNCA se pisa el original: se escribe al lado un .lrc.nuevo.

    python sincronizar.py ken-zazpi-ilargia        una cancion
    python sincronizar.py --todas                  todas, con informe
"""
import sys
import re
import time
import difflib
from pathlib import Path

from faster_whisper import WhisperModel

CANCIONES = Path(__file__).parent / "canciones"
INFORME = Path(__file__).parent / "informe_sincronizacion.txt"
MODELO = "medium"          # large-v3 solo sube del 46% al 48% y tarda el doble

# Whisper marca las palabras un poco antes de que suenen: sus tiempos salen de
# la atencion del modelo, no de un detector del ataque de la nota.
# Medido a mano sobre 6 entradas: la correccion es ~0.5s.
DESFASE = 0.5

# Solo valen como ancla las rachas de al menos estas palabras seguidas. Con 1,
# palabras sueltas ("como", "un", "el") casan donde no deben.
MIN_RACHA = 3

# Separacion minima entre dos lineas: con el mismo sello, la segunda no se ve.
HUECO_MINIMO = 1.2


# --------------------------------------------------------------------------
def normalizar(palabra):
    p = palabra.lower()
    for a, b in zip("áéíóúü", "aeiouu"):
        p = p.replace(a, b)
    return re.sub(r"[^a-zñ]", "", p)


def leer_lineas(lrc):
    """Del .lrc saca solo los textos, en orden. Los tiempos viejos se tiran."""
    lineas = []
    for linea in lrc.read_text(encoding="utf-8").splitlines():
        if "]" not in linea:
            continue
        lineas.append(linea[linea.index("]") + 1:].strip())
    return lineas


def sello(segundos):
    segundos = max(segundos, 0)
    return "[%02d:%05.2f]" % (int(segundos // 60), segundos % 60)


def anclar(palabras_lrc, palabras_oidas, minimo):
    """{indice_de_palabra_del_lrc: instante}, solo con rachas fiables."""
    b = [p for p, _ in palabras_oidas]
    anclas = {}
    for i, j, n in difflib.SequenceMatcher(None, list(palabras_lrc), b,
                                           autojunk=False).get_matching_blocks():
        if n < minimo:
            continue
        for k in range(n):
            anclas[i + k] = palabras_oidas[j + k][1]
    return anclas


def descartar_imposibles(anclas, max_palabras_seg=4.0):
    """Tira anclas que implican una velocidad de canto imposible.

    Si entre dos anclas hay 60 palabras y 2 segundos, una miente: nadie canta a
    30 palabras por segundo. Pasa cuando un estribillo repetido en la letra casa
    con la unica vez que Whisper lo transcribio.
    """
    orden = sorted(anclas)
    if not orden:
        return {}
    buenas = {orden[0]: anclas[orden[0]]}
    ultimo = orden[0]
    for i in orden[1:]:
        dt = anclas[i] - anclas[ultimo]
        if dt <= 0 or (i - ultimo) / dt > max_palabras_seg:
            continue
        buenas[i] = anclas[i]
        ultimo = i
    return buenas


def interpolar(indice, anclas, orden):
    antes = [i for i in orden if i <= indice]
    despues = [i for i in orden if i >= indice]
    if not antes:
        return anclas[despues[0]]
    if not despues:
        return anclas[antes[-1]]
    i0, i1 = antes[-1], despues[0]
    if i0 == i1:
        return anclas[i0]
    return anclas[i0] + (anclas[i1] - anclas[i0]) * (indice - i0) / (i1 - i0)


def amontonadas(tiempos):
    """Maximo de lineas dentro de la misma ventana de 2s."""
    peor = 0
    for i, t in enumerate(tiempos):
        peor = max(peor, sum(1 for u in tiempos[i:] if u - t < 2.0))
    return peor


# --------------------------------------------------------------------------
def sincronizar(nombre, modelo, idioma=None, callado=False):
    """Devuelve un diccionario con el resultado, o None si no se pudo."""
    mp3 = CANCIONES / (nombre + ".mp3")
    lrc = CANCIONES / (nombre + ".lrc")
    if not mp3.exists() or not lrc.exists():
        return None

    lineas = leer_lineas(lrc)
    palabras, primera_palabra = [], []
    for texto in lineas:
        primera_palabra.append(len(palabras))
        for cruda in texto.split():
            limpia = normalizar(cruda)
            if limpia:
                palabras.append(limpia)

    if len(palabras) < 10:
        return None

    t0 = time.time()
    segs, info = modelo.transcribe(str(mp3), language=idioma, vad_filter=False,
                                   beam_size=5, condition_on_previous_text=False,
                                   word_timestamps=True)
    oidas = [(normalizar(w.word), w.start)
             for s in segs for w in (s.words or []) if normalizar(w.word)]
    tarda = time.time() - t0

    if not oidas:
        return {"nombre": nombre, "error": "Whisper no oyo nada"}

    for minimo in (MIN_RACHA, 2):
        anclas = anclar(palabras, oidas, minimo)
        if len(anclas) >= 10:
            break
    brutas = len(anclas)
    anclas = descartar_imposibles(anclas)
    orden = sorted(anclas)

    if len(anclas) < 5:
        return {"nombre": nombre, "error": "solo %d anclas" % len(anclas),
                "anclas": len(anclas), "palabras": len(palabras)}

    tiempos = []
    for n in range(len(lineas)):
        idx = primera_palabra[n]
        if idx >= len(palabras):
            tiempos.append(tiempos[-1] if tiempos else 0)
            continue
        tiempos.append((anclas.get(idx) or interpolar(idx, anclas, orden)) + DESFASE)

    for i in range(1, len(tiempos)):
        if tiempos[i] < tiempos[i - 1] + HUECO_MINIMO:
            tiempos[i] = tiempos[i - 1] + HUECO_MINIMO

    (CANCIONES / (nombre + ".lrc.nuevo")).write_text(
        "\n".join(sello(t) + txt for t, txt in zip(tiempos, lineas)), encoding="utf-8")

    return {
        "nombre": nombre, "error": None,
        "lineas": len(lineas), "palabras": len(palabras), "oidas": len(oidas),
        "anclas": len(anclas), "descartadas": brutas - len(anclas),
        "pct": 100 * len(anclas) / len(palabras),
        "juntas": amontonadas(tiempos),
        "primera": tiempos[0], "ultima": tiempos[-1], "duracion": info.duration,
        "idioma": info.language, "segundos": tarda,
    }


def sospecha(r):
    """Cuanto hay que desconfiar de este resultado. Mas alto = peor."""
    if r.get("error"):
        return 999
    puntos = 0
    if r["pct"] < 25:
        puntos += 3
    elif r["pct"] < 40:
        puntos += 1
    if r["juntas"] > 6:
        puntos += 3
    elif r["juntas"] > 4:
        puntos += 1
    if r["ultima"] > r["duracion"]:
        puntos += 3
    if r["primera"] > r["duracion"] * 0.35:
        puntos += 1
    return puntos


# --------------------------------------------------------------------------
def todas():
    canciones = sorted(p.stem for p in CANCIONES.glob("*.mp3")
                       if p.with_suffix(".lrc").exists())
    print("%d canciones. Cargando el modelo '%s'..." % (len(canciones), MODELO))
    modelo = WhisperModel(MODELO, device="cpu", compute_type="int8", cpu_threads=16)

    inicio = time.time()
    resultados = []
    for n, nombre in enumerate(canciones, 1):

        # ya hecha en una tanda anterior: se salta (asi se puede reanudar)
        if (CANCIONES / (nombre + ".lrc.nuevo")).exists():
            print("%3d/%d  %-45s  ya estaba" % (n, len(canciones), nombre[:45]))
            continue

        # una cancion que reviente NO puede tumbar la tanda entera
        try:
            r = sincronizar(nombre, modelo)
        except Exception as e:
            print("%3d/%d  %-45s  EXCEPCION: %s" % (n, len(canciones), nombre[:45], str(e)[:60]))
            resultados.append({"nombre": nombre, "error": "excepcion: %s" % str(e)[:60]})
            continue

        if r is None:
            print("%3d/%d  %-45s  saltada (sin letra utilizable)" % (n, len(canciones), nombre[:45]))
            continue
        resultados.append(r)
        transcurrido = time.time() - inicio
        queda = (transcurrido / n) * (len(canciones) - n)
        if r.get("error"):
            print("%3d/%d  %-45s  FALLO: %s   (quedan ~%.0f min)"
                  % (n, len(canciones), nombre[:45], r["error"], queda / 60))
        else:
            print("%3d/%d  %-45s  anclas %3.0f%%  juntas %2d  %s   (quedan ~%.0f min)"
                  % (n, len(canciones), nombre[:45], r["pct"], r["juntas"],
                     r["idioma"], queda / 60))

    resultados.sort(key=lambda r: (-sospecha(r), r["nombre"]))

    lineas = ["INFORME DE SINCRONIZACION",
              "%d canciones en %.0f minutos" % (len(resultados), (time.time() - inicio) / 60),
              "",
              "Ordenadas de MAS a MENOS sospechosa. Revisa las de arriba.",
              "Los .lrc originales NO se han tocado: el resultado esta en .lrc.nuevo",
              "",
              "%-45s %5s %6s %7s %8s %6s" % ("cancion", "sosp", "anclas", "juntas", "idioma", "lineas"),
              "-" * 86]
    for r in resultados:
        if r.get("error"):
            lineas.append("%-45s %5d   %s" % (r["nombre"][:45], sospecha(r), r["error"]))
        else:
            lineas.append("%-45s %5d %5.0f%% %7d %8s %6d"
                          % (r["nombre"][:45], sospecha(r), r["pct"], r["juntas"],
                             r["idioma"], r["lineas"]))
    INFORME.write_text("\n".join(lineas), encoding="utf-8")
    print("\ninforme en %s" % INFORME.name)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
    elif sys.argv[1] == "--todas":
        todas()
    else:
        modelo = WhisperModel(MODELO, device="cpu", compute_type="int8", cpu_threads=16)
        r = sincronizar(sys.argv[1], modelo,
                        sys.argv[2] if len(sys.argv) > 2 else None)
        print(r)
