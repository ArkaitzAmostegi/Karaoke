from flask import Flask, render_template
from pathlib import Path


app = Flask(__name__)
CANCIONES = Path(__file__).parent / "canciones"

#Página principal
@app.route("/")
def portada():
    return render_template("lista.html")


#Función para listar canciones
def listar_canciones():
    lista = []
    for f in sorted(CANCIONES.glob("*.mp3")):
        lista.append(f.stem)

    return lista



if __name__ == "__main__":
    app.run(debug=True, port=5055)