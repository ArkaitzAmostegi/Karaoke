"""Desplaza TODOS los tiempos de un .lrc de golpe.

Para cuando la letra va bien pero entera adelantada o atrasada. No hay que
tocar linea por linea: es sumar el mismo numero a todos los sellos.

    python desfasar.py ken-zazpi-haizea 0.5     la letra va medio segundo MAS TARDE
    python desfasar.py ken-zazpi-haizea -0.3    tres decimas ANTES

Reescribe el .lrc en el sitio. Como es una suma, se deshace con el numero
contrario: si te pasas con 0.5, lo arreglas con -0.5.
"""
import sys
from pathlib import Path

CANCIONES = Path(__file__).parent / "canciones"


def sello(segundos):
    segundos = max(segundos, 0)          # nada puede sonar antes de empezar
    return "[%02d:%05.2f]" % (int(segundos // 60), segundos % 60)


def desfasar(nombre, ajuste):
    ruta = CANCIONES / (nombre + ".lrc")
    if not ruta.exists():
        print("no existe %s" % ruta.name)
        return

    salida, tocadas, primero, ultimo = [], 0, None, None

    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.startswith("["):
            salida.append(linea)          # lo que no lleva sello se copia igual
            continue
        try:
            cierre = linea.index("]")
            minutos, segundos = linea[1:cierre].split(":")
            t = int(minutos) * 60 + float(segundos) + ajuste
        except ValueError:
            salida.append(linea)          # sello corrupto: se deja tal cual
            continue

        salida.append(sello(t) + linea[cierre + 1:])
        tocadas += 1
        if primero is None:
            primero = t
        ultimo = t

    ruta.write_text("\n".join(salida), encoding="utf-8")
    print("%s: %+.2fs a %d lineas" % (nombre, ajuste, tocadas))
    if primero is not None:
        print("   ahora la primera entra en %.2fs y la ultima en %.2fs" % (primero, ultimo))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
    else:
        desfasar(sys.argv[1], float(sys.argv[2]))
