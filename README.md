# 🎤 Karaoke Aramar

Karaoke casero en red local: la letra se ilumina al ritmo de la canción en la tele, y todos los móviles de la casa siguen la misma letra sincronizada desde el navegador. Nadie instala nada, y una vez arrancado no hace falta internet para cantar.

Hecho con **Flask** y JavaScript sin librerías.

---

## Qué hace

- **Lee la carpeta de canciones** y monta el catálogo solo: cada canción son dos ficheros hermanos, el `.mp3` y su letra `.lrc`.
- **Resalta la línea que toca cantar** sobre un escenario en 3D, con scroll automático y **cuenta atrás** en los huecos, para saber cuándo entrar.
- **Dos modos de juego**: elegir canción a mano, o **karaoke a tutiplén** — arranca y va encadenando canciones al azar, sin repetir ninguna hasta que hayan sonado todas.
- **Código QR en la portada** para que los móviles se enganchen sin dictar direcciones IP.
- **Descarga las letras sincronizadas** de [LRCLIB](https://lrclib.net), eligiendo la versión cuya duración coincide con tu MP3.
- **Editor de letras** para corregir tiempos a mano, con un sello `[mm:ss.cc]` en vivo listo para copiar.

## Cómo está montado

```mermaid
flowchart LR
    P["Portada"] -->|Cantar| C["Tele<br>/cantar/:cancion"]
    P -->|"A tutiplen"| T["/tutiplen<br>saca de la baraja"]
    T --> C
    C -.->|"al acabar la cancion"| T
    P -->|Editar| E["Editor<br>/editor/:cancion"]
    E -->|Buscar letra| V["Versiones<br>/buscar/:cancion"]
    V -->|Usar esta| C
    C -->|"latido, 1 por segundo"| S[("ESTADO<br>en el servidor")]
    S -->|"consulta, 1 por segundo"| M["Moviles<br>/movil"]
    C -.->|"pide el mp3"| A["/audio/:cancion"]
```

### Las decisiones que explican el diseño

**El audio suena en un solo sitio.** Si cada móvil reprodujera su copia del MP3, se desincronizarían por el buffering y la latencia del altavoz, y el oído detecta desfases de 30 ms como eco. Los móviles solo pintan letra: **la letra perdona décimas, el audio no.**

**El móvil lleva su propio reloj.** Pregunta al servidor una vez por segundo, pero repinta diez veces por segundo estimando cuánto ha pasado desde la última respuesta. Sin eso, la letra avanzaría a saltos de un segundo. Es lo mismo que hace un GPS entre señal y señal.

**Baraja, no dado.** El modo aleatorio no tira un dado en cada canción: baraja la lista entera y la recorre, y solo al agotarla vuelve a barajar. Con azar puro saldría dos veces la misma antes de que sonaran otras muchas.

**El QR se calcula en cada visita, no al arrancar.** La IP que imprime Flask en la terminal se escribe una sola vez y se queda obsoleta en cuanto cambias de red, suspendes el portátil o el router renueva la dirección. El QR pregunta al sistema por la IP en el momento de servir la página, así que siempre apunta a la buena.

**Sin base de datos.** La carpeta `canciones/` es la fuente de la verdad: si borras un MP3, la canción desaparece de la app. No hay dos sitios que puedan desincronizarse.

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install flask requests mutagen qrcode
python app.py
```

En `http://localhost:5055`. Ya arranca con `host="0.0.0.0"`, así que la tele y los móviles de la casa entran con la IP del ordenador — **o directamente escaneando el QR de la portada**, que es para lo que está.

> Si `pip` te lo bloquea una política del sistema, usa `python -m pip` en lugar de `pip` a secas: así se ejecuta el intérprete (que sí está firmado) en vez de `pip.exe`.

## Añadir canciones

1. Copia el `.mp3` a `canciones/` con el nombre en minúsculas y separado por guiones: `artista-titulo.mp3`. Ese nombre es a la vez el identificador de la URL y la consulta que se manda a LRCLIB, así que conviene que esté limpio.
2. Baja las letras que falten:

```bash
python bajar_letras.py
```

Salta las que ya tengan `.lrc`, así que puedes repetirlo sin miedo. Las que no encuentre —o que solo existan con otra duración— se resuelven desde *Editar → Buscar en internet*, eligiendo la versión a mano.

## Ficheros

| | |
|---|---|
| `app.py` | El servidor: todas las rutas y el estado compartido |
| `lrclib.py` | Cliente de la API de LRCLIB |
| `bajar_letras.py` | Script de consola: descarga de letras en lote |
| `static/karaoke.js` | Todo el motor del karaoke, compartido por tele y móvil |
| `static/style.css` | Una sola hoja, dos modos según la clase del `<body>` |
| `templates/` | Las cinco páginas |
| `canciones/` | Los datos: `.mp3` (fuera del repo) y `.lrc` |
| `MAPA.md` | Mapa del proyecto: qué hay hecho, qué falta y por qué está cada decisión |

## El formato LRC

El estándar de los karaokes desde los 90, y por eso las letras son portables a otros reproductores:

```
[00:13.76]primera frase de la cancion
[00:20.12]segunda frase
[00:28.10]
```

`[minutos:segundos.centésimas]` y detrás el texto. Una línea con sello y **sin texto** marca un silencio: es lo que hace que la última frase desaparezca de la pantalla en vez de quedarse congelada hasta el final del MP3.

## Nota

Los MP3 no se versionan (`.gitignore`): pesan y no son míos. Los `.lrc` sí, porque ocupan nada y varios están corregidos a mano.

Proyecto de aprendizaje: Python, Flask, Jinja, JavaScript y algo de CSS.
