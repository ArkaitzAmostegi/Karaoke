/* =========================================================
   KARAOKE ARAMAR — toda la logica del karaoke, en un sitio.

   Este fichero NO pasa por Jinja (los ficheros de static/ se sirven tal cual),
   asi que los datos que solo sabe Python los recibe de la plantilla, que
   define antes de cargarnos:

       MODO     "tele" o "movil"
       LINEAS   [{tiempo, texto}, ...]
       CANCION  el identificador de la cancion (null en el movil si no hay)
       VERSION  solo en el movil: la version del estado al cargar la pagina

   La tele MANDA (reproduce y avisa por donde va).
   El movil ESCUCHA (pregunta y pinta, sin audio).
   ========================================================= */

const ELEMENTOS   = document.querySelectorAll(".linea");
const cuentaAtras = document.getElementById("cuentaAtras");

const AVISO = 10;        // si faltan menos de estos segundos para la siguiente frase, se cuenta

let anterior = -1;       // que linea estaba marcada la ultima vez que pintamos


/* ---------------------------------------------------------
    EL MOTOR: dado un segundo t, actualizar la pantalla.
    Lo usan las dos paginas; lo unico que cambia es de donde sale t.
   --------------------------------------------------------- */
function pintar(t) {

    // 1. que linea toca: la ultima cuyo tiempo ya ha pasado
    let indice = -1;
    for (let i = 0; i < LINEAS.length; i++) {
        if (LINEAS[i].tiempo <= (t + 1)) {
            indice = i;
        }
    }

    // 2. la siguiente linea CON letra (puede haber varios silencios seguidos)
    let siguiente = -1;
    for (let i = indice + 1; i < LINEAS.length; i++) {
        if (LINEAS[i].texto.trim() !== "") {
            siguiente = i;
            break;
        }
    }

    // 3. estamos en silencio si no hay linea o la que toca no tiene letra
    const enSilencio = (indice < 0) || (LINEAS[indice].texto.trim() === "");
    if (enSilencio) {
        indice = -1;                     // que no se ilumine ninguna
    }

    // 4. cuanto falta para la siguiente frase; si es menos de AVISO, se cuenta
    cuentaAtras.textContent = "";
    if (siguiente >= 0) {
        const falta = LINEAS[siguiente].tiempo - t;
        if (falta > 0 && falta <= AVISO) {
            cuentaAtras.textContent = Math.ceil(falta);
        }
    }

    // 5. pintar: solo la que toca lleva la clase "actual"
    for (let j = 0; j < ELEMENTOS.length; j++) {
        ELEMENTOS[j].classList.toggle("actual", j === indice);
    }

    // 6. mover la pantalla solo cuando CAMBIA de linea, no en cada tic
    if (indice !== anterior) {
        anterior = indice;
        if (indice >= 0) {
            ELEMENTOS[indice].scrollIntoView({ block: "center", behavior: "smooth" });
        }
    }
}


/* ---------------------------------------------------------
    LA TELE: reproduce, pinta con su propio reloj y avisa al servidor.
   --------------------------------------------------------- */
function arrancarTele() {
    const audio = document.getElementById("reproductor");

    // avisar de que ESTA es la cancion puesta: sube la version y los moviles recargan
    fetch("/poner/" + encodeURIComponent(CANCION));

    // aqui el reloj lo da el propio reproductor
    audio.addEventListener("timeupdate", function () {
        pintar(audio.currentTime);
    });

    // latido: una vez por segundo, decirle al servidor por donde vamos
    setInterval(function () {
        fetch("/latido", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                cancion: CANCION,
                tiempo:  audio.currentTime,
                sonando: !audio.paused
            })
        });
    }, 1000);
}


/* ---------------------------------------------------------
    EL MOVIL: no reproduce nada. Pregunta al servidor una vez por segundo
    y entre consulta y consulta lleva su propio reloj, para que la letra
    no vaya a tirones. Es lo mismo que hace un GPS entre señal y señal.
   --------------------------------------------------------- */
function arrancarMovil() {
    let tiempoServidor = 0;      // ultimo tiempo que dijo el servidor (SEGUNDOS)
    let instante = 0;            // performance.now() de cuando lo dijo (MILISEGUNDOS)
    let sonando = false;

    // LENTO: preguntar y APUNTAR lo que dice
    setInterval(function () {
        fetch("/estado", { cache: "no-store" })     // no-store: los moviles cachean mucho
            .then(r => r.json())
            .then(function (e) {

                // han puesto otra cancion: recargar para traer la letra nueva
                if (e.version !== VERSION) {
                    location.reload();
                    return;
                }

                tiempoServidor = e.tiempo;
                instante = performance.now();
                sonando = e.sonando;
            });
    }, 1000);

    // RAPIDO: ESTIMAR que hora es ahora y pintar
    setInterval(function () {
        let t = tiempoServidor;
        if (sonando) {                               // en pausa el reloj no avanza
            t = tiempoServidor + (performance.now() - instante) / 1000;
        }
        pintar(t);
    }, 100);
}


/* --------------------------------------------------------- */
if (MODO === "tele") {
    arrancarTele();
} else {
    // ojo: tambien cuando no hay cancion (LINEAS vacio), porque es preguntando
    // como el movil se entera de que alguien ha puesto una
    arrancarMovil();
}
