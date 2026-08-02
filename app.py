from flask import Flask, render_template,send_from_directory, redirect, url_for, request
from pathlib import Path
from lrclib import buscar, descargar
from requests.exceptions import RequestException
from qrcode.constants import ERROR_CORRECT_L
import socket, random, qrcode, qrcode.image.svg


app = Flask(__name__)
CANCIONES = Path(__file__).parent / "canciones"
ESTADO = {"cancion": None, "tiempo": 0, "sonando": False, "version": 0, "fiesta": False, "listaCancionesPorSonar": []}
PUERTO = 5055



#Función para listar canciones
def listar_canciones():
    lista = []
    for f in sorted(CANCIONES.glob("*.mp3")):
        lista.append(f.stem)

    return lista


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


# Para poner un QR que conecte los moviles
def qr_movil():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    url = (f"http://{ip}:{PUERTO}/movil")

    q = qrcode.QRCode(error_correction=ERROR_CORRECT_L, border=4)
    q.add_data(url)
    q.make(fit=True)
    img = q.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    return img.to_string(encoding="unicode")




#Página principal
@app.route("/")
def portada():
    return render_template("lista.html", canciones=listar_canciones(), qr = qr_movil())


#Función para que suene la canción
@app.route("/audio/<cancion_id>")
def sonar(cancion_id):
    cancion = f"{cancion_id}.mp3"
    return send_from_directory(CANCIONES, cancion, conditional=True)


#Función para ir a la página de la canción seleccionada
@app.route("/cantar/<cancion_id>")
def cantar(cancion_id):
    return render_template("cantar.html", cancion = cancion_id,
                           lineas=leer_letra(cancion_id), fiesta=ESTADO["fiesta"])


#Página para editar las canciones, generar el texto de la letra
@app.route("/editor/<cancion_id>", methods=["GET", "POST"])
def editar(cancion_id):
    ruta = CANCIONES / f"{cancion_id}.lrc"       # la misma ruta hace falta en los dos caminos

    if request.method == "POST":
        #POST: guardar la letra que venga del formulario
        letra = request.form["letra"]
        ruta.write_text(letra, encoding="utf-8")
        return redirect(url_for("cantar", cancion_id=cancion_id))

    #GET: enseñar la letra que haya (o la caja vacia si la cancion aun no tiene)
    if ruta.exists():
        texto = ruta.read_text(encoding="utf-8")
    else:
        texto = ""

    return render_template("editor.html", cancion=cancion_id, texto=texto)


#Ruta para buscar letras e
@app.route("/buscar/<cancion_id>")
def buscar_letra(cancion_id):
    try:
        candidatos = buscar(cancion_id.replace("-", " "))
    except RequestException:
        return render_template("resultados.html", cancion=cancion_id, candidatos=[], error = 'No ha sido posible realizar la conexión')

    lista = []
    for candidato in candidatos:
        if candidato["syncedLyrics"]:
            lista.append(candidato)

    return render_template("resultados.html", cancion=cancion_id, candidatos=lista)


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

# Saca la siguiente cancion de la baraja, sin repetir hasta agotarlas todas.
# Baraja y no dado: al azar puro saldria dos veces la misma antes que otras muchas.
# No es ruta: la usan /siguiente (para probar) y /tutiplen (de verdad).
def sacar_siguiente():
    baraja = ESTADO["listaCancionesPorSonar"]

    if not baraja:                        # se acabaron: barajar de nuevo
        baraja = listar_canciones()
        random.shuffle(baraja)            # revuelve EN EL SITIO y devuelve None
        ESTADO["listaCancionesPorSonar"] = baraja

    return baraja.pop(0)                  # pop la devuelve Y la quita: por eso no se repite


@app.route("/siguiente")
def siguiente():
    cancion = sacar_siguiente()
    return {"cancion": cancion, "quedan": len(ESTADO["listaCancionesPorSonar"])}


# Arranca el modo fiesta y salta a una cancion al azar.
# Es la misma ruta que se llama al acabar cada cancion: por eso encadena.
@app.route("/tutiplen")
def tutiplen():
    ESTADO["fiesta"] = True
    return redirect(url_for("cantar", cancion_id=sacar_siguiente()))


# Corta la fiesta y vuelve a la portada
@app.route("/parar")
def parar():
    ESTADO["fiesta"] = False
    return redirect(url_for("portada"))


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
    app.run(debug=True, port=PUERTO, host="0.0.0.0")