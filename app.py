from flask import Flask, render_template,send_from_directory, redirect, url_for, request
from pathlib import Path
from lrclib import buscar, descargar
from requests.exceptions import RequestException


app = Flask(__name__)
CANCIONES = Path(__file__).parent / "canciones"
ESTADO = {"cancion": None, "tiempo": 0, "sonando": False, "version": 0}


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
        try:
            tiempo = round((int(minutos)*60) + float(segundos),2)
            lineas.append({"tiempo":tiempo, "texto":letra})
        except ValueError:
            continue

    return (lineas)


#Página para editar las canciones, generar el texto de la letra
@app.route("/editor/<cancion_id>", methods=["GET", "POST"])
def editar(cancion_id):
    if (request.method == "POST"):
        #POST escribir la letra
        letra = request.form["letra"]
        ruta = CANCIONES / f"{cancion_id}.lrc"
        ruta.write_text(letra, encoding="utf-8")
        return redirect (url_for("cantar", cancion_id=cancion_id))
    else:
        #GET mirar la letra
        ruta = CANCIONES / f"{cancion_id}.lrc"
        texto = ruta.read_text(encoding="utf-8")
        return render_template("editor.html", cancion = cancion_id, texto = texto)


#Ruta para buscar letras e
@app.route("/buscar/<cancion_id>")
def buscar_letra(cancion_id):
    try:
        candidatos = buscar(cancion_id.replace("-", " "))
    except RequestException:
        return render_template("resultados.html", cancion=cancion_id, candidatos=[], error = 'No ha sido posible realizar la conexión')
    return render_template("resultados.html", cancion=cancion_id, candidatos=candidatos)


# Ruta para escribir la letra del lrclib 
@app.route("/usar/<cancion_id>/<int:lrclib_id>")
def usar_letra(cancion_id, lrclib_id):
    datos = descargar(lrclib_id)
    ruta = CANCIONES / f"{cancion_id}.lrc"
    ruta.write_text(datos["syncedLyrics"], encoding="utf-8")

    return redirect(url_for("cantar", cancion_id=cancion_id))

# Ruta que devuelve un diccionario nos dice el estado
@app.route("/estado")
def estado():
    return (ESTADO)

# Cambia la canción pone el tiempo suma 1 a la versión
@app.route("/poner/<cancion_id>")
def poner(cancion_id):
    ESTADO["cancion"] = cancion_id
    ESTADO["tiempo"] = 0
    ESTADO["version"] += 1
    return (ESTADO)

# Recibe el json y devuelve el estado de la canción en vivo
@app.route("/latido", methods = ["POST"])
def latido():
    datos = request.get_json()
    if ESTADO["cancion"] is None:
        ESTADO["cancion"] = datos["cancion"]
        ESTADO["version"] += 1
        
    if datos["cancion"] == ESTADO["cancion"]:
        ESTADO["tiempo"] = datos["tiempo"]
        ESTADO["sonando"] = datos["sonando"]
        return {"ok": True}
    
    else:
        return {"ok": False}


# Conexión del móvil a la app
@app.route("/movil")
def movil():
    cancion = ESTADO["cancion"]
    if cancion is None:
        # todavia no han puesto nada: sin letra, pero con version
        return render_template("movil.html", cancion=None, lineas=[], version=ESTADO["version"])
    return render_template("movil.html", cancion=cancion, lineas=leer_letra(cancion), version=ESTADO["version"])

if __name__ == "__main__":
    app.run(debug=True, port=5055, host="0.0.0.0")