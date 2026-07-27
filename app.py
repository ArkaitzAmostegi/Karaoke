from flask import Flask, render_template,send_from_directory, redirect, url_for
from pathlib import Path
from lrclib import buscar, descargar


app = Flask(__name__)
CANCIONES = Path(__file__).parent / "canciones"


#Página principal
@app.route("/")
def portada():
    return render_template("lista.html", canciones=listar_canciones())


#Función para listar canciones
def listar_canciones():
    lista = []
    for f in sorted(CANCIONES.glob("*.mp3")):
        lista.append(f.stem)

    return lista

#Función para ir a la página de la canción seleccionada
@app.route("/cantar/<cancion_id>")
def cantar(cancion_id):
    return render_template("cantar.html", cancion = cancion_id, lineas=leer_letra(cancion_id))


#Función para que suene la canción
@app.route("/audio/<cancion_id>")
def sonar(cancion_id):
    cancion = f"{cancion_id}.mp3"
    return send_from_directory(CANCIONES, cancion, conditional=True)

# Escribiendo el texto
def leer_letra(cancion_id):
    ruta = CANCIONES / f"{cancion_id}.lrc"
    if not ruta.exists():
        return[]                                # Canción sin sincronizar: lista vacia, sin reventar

    lineas = []
    
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.startswith("["):
            continue                            # no es una linea con sello: a la siguiente
        cierre = linea.index("]")
        sello = linea[1:cierre]
        letra = linea[cierre+1:]
        minutos, segundos = sello.split(":")
        tiempo = (int(minutos)*60) + float(segundos)
        lineas.append({"tiempo":tiempo, "texto":letra})

    return (lineas)


#Página para editar las canciones, generar el texto de la letra
@app.route("/editor/<cancion_id>")
def editar(cancion_id):
    return render_template("editor.html", cancion=cancion_id)


@app.route("/buscar/<cancion_id>")
def buscar_letra(cancion_id):
    candidatos = buscar(cancion_id.replace("-", " "))
    return render_template("resultados.html", cancion=cancion_id, candidatos=candidatos)

@app.route("/usar/<cancion_id>/<int:lrclib_id>")
def usar_letra(cancion_id, lrclib_id):
    datos = descargar(lrclib_id)
    ruta = CANCIONES / f"{cancion_id}.lrc"
    ruta.write_text(datos["syncedLyrics"], encoding="utf-8")

    return redirect(url_for("cantar", cancion_id=cancion_id))


if __name__ == "__main__":
    app.run(debug=True, port=5055)