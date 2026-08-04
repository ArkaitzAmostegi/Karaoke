/* =========================================================
   SINCRONIZAR A MANO

   Suena la cancion y con ESPACIO se marca el instante en que entra cada
   frase. Es la salida para las canciones que el reconocimiento automatico
   no puede tocar (euskera) o donde se pierde.

   El texto se puede corregir sobre la marcha, y se pueden anadir o quitar
   lineas: la letra descargada a veces se deja frases que la version que
   tienes si canta.

   Recibe de la plantilla:
       CANCION   identificador de la cancion
       LINEAS    los textos, en orden (sin tiempos)
   ========================================================= */

const audio     = document.getElementById("reproductor");
const sello     = document.getElementById("sello");
const lista     = document.getElementById("lista");
const avance    = document.getElementById("avance");
const aviso     = document.getElementById("aviso");
const bGuardar  = document.getElementById("guardar");
const velocidad = document.getElementById("velocidad");
const bAnadir   = document.getElementById("anadirFinal");

// Todo el estado vive aqui. La lista de la pagina se dibuja a partir de esto,
// nunca al reves: asi anadir, quitar o reordenar es tocar un array y redibujar.
let filas = LINEAS.map(t => ({ texto: t, tiempo: null }));
let actual = 0;                       // la linea que toca marcar ahora


/* 73.4 -> "[01:13.40]", el mismo formato del .lrc */
function selloLrc(segundos) {
    const min = Math.floor(segundos / 60);
    const seg = segundos % 60;
    return "[" + String(min).padStart(2, "0") + ":" + seg.toFixed(2).padStart(5, "0") + "]";
}


/* ---------- dibujar ---------- */

function construir() {
    lista.innerHTML = "";
    filas.forEach(function (fila, i) {
        const li = document.createElement("li");
        li.className = "marcador-linea";
        li.dataset.n = i;
        li.innerHTML =
            '<span class="marcador-sello">--:--</span>' +
            '<span class="marcador-texto" contenteditable="true" spellcheck="false"></span>' +
            '<button class="mini" data-accion="insertar" title="Insertar una linea debajo">+</button>' +
            '<button class="mini" data-accion="borrar"   title="Quitar esta linea">&times;</button>';
        li.querySelector(".marcador-texto").textContent = fila.texto;
        lista.appendChild(li);
    });
    pintar();
}

function pintar() {
    [...lista.children].forEach(function (li, i) {
        li.classList.toggle("actual", i === actual);
        li.classList.toggle("marcada", filas[i].tiempo !== null);
        li.querySelector(".marcador-sello").textContent =
            filas[i].tiempo === null ? "--:--" : selloLrc(filas[i].tiempo);
    });

    const hechas = filas.filter(f => f.tiempo !== null).length;
    avance.textContent = hechas + " de " + filas.length + " marcadas";
    bGuardar.disabled = hechas === 0;

    if (actual < lista.children.length) {
        lista.children[actual].scrollIntoView({ block: "center", behavior: "smooth" });
    }
}


/* ---------- acciones ---------- */

function marcar() {
    if (actual >= filas.length) return;
    filas[actual].tiempo = audio.currentTime;
    actual++;
    pintar();
}

function deshacer() {
    if (actual === 0) return;
    actual--;
    filas[actual].tiempo = null;
    pintar();
}

function saltar() {
    if (actual >= filas.length) return;
    filas[actual].tiempo = null;
    actual++;
    pintar();
}

function insertar(donde) {
    filas.splice(donde, 0, { texto: "", tiempo: null });
    construir();
    actual = donde;
    pintar();
    // el cursor listo para escribir la frase que falta
    lista.children[donde].querySelector(".marcador-texto").focus();
}

function borrar(cual) {
    if (filas.length <= 1) return;
    filas.splice(cual, 1);
    if (actual >= filas.length) actual = filas.length - 1;
    construir();
}

function reiniciar() {
    filas.forEach(f => { f.tiempo = null; });
    actual = 0;
    audio.pause();
    audio.currentTime = 0;
    aviso.textContent = "";
    pintar();
}


/* ---------- teclado ---------- */

function escribiendo(e) {
    // si el foco esta en un texto editable, las teclas son para escribir
    return e.target.isContentEditable ||
           ["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName);
}

document.addEventListener("keydown", function (e) {
    if (escribiendo(e)) return;

    // el reproductor se traga el ESPACIO para dar al play: se lo quitamos
    if (["Space", "ArrowLeft", "ArrowDown", "KeyR", "KeyI"].includes(e.code)) {
        e.preventDefault();
    }
    if (e.code === "Space")           marcar();
    else if (e.code === "ArrowLeft")  deshacer();
    else if (e.code === "ArrowDown")  saltar();
    else if (e.code === "KeyI")       insertar(actual);
    else if (e.code === "KeyR")       reiniciar();
});

audio.addEventListener("play", function () { audio.blur(); });

audio.addEventListener("timeupdate", function () {
    sello.textContent = selloLrc(audio.currentTime);
});

velocidad.addEventListener("change", function () {
    audio.playbackRate = parseFloat(velocidad.value);
});


/* ---------- raton ---------- */

lista.addEventListener("click", function (e) {
    const li = e.target.closest(".marcador-linea");
    if (!li) return;
    const n = parseInt(li.dataset.n, 10);

    const accion = e.target.dataset.accion;
    if (accion === "insertar") { insertar(n + 1); return; }
    if (accion === "borrar")   { borrar(n); return; }

    // pinchar en el texto es para editarlo, no para cambiar de linea
    if (e.target.classList.contains("marcador-texto")) return;

    actual = n;
    pintar();
});

// cada tecleo en el texto se guarda en el array al momento
lista.addEventListener("input", function (e) {
    if (!e.target.classList.contains("marcador-texto")) return;
    const n = parseInt(e.target.closest(".marcador-linea").dataset.n, 10);
    filas[n].texto = e.target.textContent.trim();
});

bAnadir.addEventListener("click", function () { insertar(filas.length); });


/* ---------- guardar ---------- */

bGuardar.addEventListener("click", function () {
    bGuardar.disabled = true;
    aviso.textContent = "guardando...";

    fetch("/marcar/" + encodeURIComponent(CANCION), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            lineas:  filas.map(f => f.texto),
            tiempos: filas.map(f => f.tiempo)
        })
    })
        .then(r => r.json())
        .then(function (r) {
            // guardado: a cantarla, que es lo que venias a hacer
            aviso.textContent = "guardadas " + r.lineas + " lineas, vamos alla";
            location.href = "/cantar/" + encodeURIComponent(CANCION);
        })
        .catch(function () {
            aviso.textContent = "no se pudo guardar";
            bGuardar.disabled = false;
        });
});

construir();
