"""Convierte a MP3 de verdad los ficheros que llevan .mp3 pero por dentro son
otra cosa (tipico de las descargas de video: MP4/M4A con la extension cambiada).

Se detectan por los primeros bytes del fichero, no por la extension.
El original se guarda con .original hasta que compruebes que suena.

    python convertir_a_mp3.py
"""
from pathlib import Path

import av

CANCIONES = Path(__file__).parent / "canciones"


def es_mp3_de_verdad(ruta):
    """Un MP3 empieza por 'ID3' (etiqueta) o por 0xFF (trama MPEG)."""
    with open(ruta, "rb") as f:
        cabecera = f.read(12)
    if cabecera[:3] == b"ID3" or (len(cabecera) and cabecera[0] == 0xFF):
        return True
    return False


def convertir(origen, destino):
    entrada = av.open(str(origen))
    salida = av.open(str(destino), "w", format="mp3")

    pista = salida.add_stream("mp3", rate=44100)
    pista.bit_rate = 192000

    remuestreador = av.AudioResampler(format="s16p", layout="stereo", rate=44100)

    for trama in entrada.decode(audio=0):
        for t in remuestreador.resample(trama):
            for paquete in pista.encode(t):
                salida.mux(paquete)

    for paquete in pista.encode(None):        # vaciar lo que quede en el codificador
        salida.mux(paquete)

    salida.close()
    entrada.close()


if __name__ == "__main__":
    malos = [p for p in sorted(CANCIONES.glob("*.mp3")) if not es_mp3_de_verdad(p)]
    if not malos:
        print("todos los .mp3 son MP3 de verdad")

    for ruta in malos:
        print("%-45s convirtiendo..." % ruta.name, end=" ", flush=True)
        temporal = ruta.with_suffix(".convertido")
        try:
            convertir(ruta, temporal)
        except Exception as e:
            print("FALLO: %s" % str(e)[:60])
            temporal.unlink(missing_ok=True)
            continue

        ruta.rename(ruta.with_suffix(".original"))   # el de antes, por si acaso
        temporal.rename(ruta)
        print("hecho (%.1f MB)" % (ruta.stat().st_size / 1024 / 1024))
