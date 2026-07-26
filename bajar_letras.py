import requests
from pathlib import Path
from mutagen.mp3 import MP3
from lrclib import buscar

CANCIONES = Path(__file__).parent / "canciones"

TOLERANCIA = 5          # segundos de diferencia que admito entre mi mp3 y la version de la API



def mejor(resultados, duracion):
    elegido = None
    distancia = None
    for res in resultados:
        if not res.get("syncedLyrics") or not res.get("duration"):
            continue
        d = abs(res["duration"] - duracion)
        if distancia is None or d < distancia:
            elegido = res
            distancia = d
    if elegido and distancia <= TOLERANCIA:
        return elegido
    return None


for mp3 in sorted(CANCIONES.glob("*.mp3")):
    lrc = mp3.with_suffix(".lrc")
    if lrc.exists() and lrc.stat().st_size > 0:
        print(f"{mp3.stem} -> ya tiene letra")
        continue

    duracion = MP3(mp3).info.length
    resultados = buscar(mp3.stem.replace("-", " "))
    elegido = mejor(resultados, duracion)

    if elegido is None:
        print(f"{mp3.stem} -> NO encontrada ({duracion:.0f}s, {len(resultados)} candidatos)")
        continue

    lrc.write_text(elegido["syncedLyrics"], encoding="utf-8")
    print(f"{mp3.stem} -> OK ({elegido['duration']:.0f}s | {elegido['albumName']})")