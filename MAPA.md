# MAPA de la app

Abre este fichero cuando no sepas dónde estás. Se actualiza cada vez que añadimos algo.

---

## Cómo funciona esto, en tres frases

1. **Cada página es una función de Python.** La URL es la dirección; la función, quien atiende. `@app.route("/cantar/<cancion_id>")` significa "cuando alguien pida esa dirección, ejecuta la función de debajo". Eso es Flask entero.
2. **Hay dos tipos de función**: las que devuelven algo *para mirar* (`render_template` → una página) y las que *hacen algo y te mandan a otro sitio* (`redirect`). Al escribir una nueva, la primera pregunta es cuál de las dos es.
3. **No hay base de datos.** Todo vive en `canciones/`: por cada canción un `.mp3` (la música) y un `.lrc` (la letra con tiempos). "Guardar" = escribir un fichero ahí. "Leer" = leerlo de ahí.

---

## Las páginas

| URL | Función | Qué es |
|---|---|---|
| `/` | `portada` | Lista de canciones, el botón de *a tutiplén* y el QR para los móviles. |
| `/cantar/<cancion>` | `cantar` | El karaoke: reproductor + letra en 3D. |
| `/movil` | `movil` | La misma letra, sincronizada, **sin audio**. Para los móviles. |
| `/editor/<cancion>` | `editar` | Sala de máquinas: buscar letra, corregirla a mano, sello de tiempo en vivo. |
| `/buscar/<cancion>` | `buscar_letra` | Las versiones de LRCLIB, con álbum y duración. Solo las que traen tiempos. |
| `/marcar/<cancion>` | `marcar` | **Sincronizar a mano** marcando con ESPACIO. Ver más abajo. |

## Las acciones (hacen algo y redirigen, o devuelven datos)

| URL | Función | Qué es |
|---|---|---|
| `/audio/<cancion>` | `sonar` | Entrega el MP3. **No la visitas tú**: la pide la etiqueta `<audio>`. |
| `/usar/<cancion>/<id>` | `usar_letra` | Baja esa versión de LRCLIB, la guarda y lleva a Cantar. |
| `/estado` | `estado` | Devuelve el diccionario `ESTADO` en JSON. Lo consultan los móviles. |
| `/poner/<cancion>` | `poner` | Fija la canción, pone `tiempo` a 0 y **sube `version`**. |
| `/latido` | `latido` | POST: la tele manda su `currentTime` una vez por segundo. |
| `/siguiente` | `siguiente` | Saca una canción de la baraja (para probar). |
| `/tutiplen` | `tutiplen` | Enciende el modo fiesta y salta a una al azar. **La misma ruta encadena.** |
| `/parar` | `parar` | Apaga el modo fiesta. |

## Cómo se llega de una a otra

```
Portada ──Cantar──────────> Cantar ──(el navegador pide)──> Audio
   │                          │  ▲
   │                          │  └── al acabar, si hay fiesta ──> /tutiplen
   ├──A tutiplen──> /tutiplen ─┘
   │
   └──Editar──> Editor ──Buscar en internet──> Versiones ──Usar esta──> Cantar
                   │
                   └──Sincronizar a mano──> /marcar ──Guardar y cantar──> Cantar

Cantar ──latido 1/s──> ESTADO en el servidor ──consulta 1/s──> Moviles
```

---

## Los ficheros

| Fichero | Para qué |
|---|---|
| `app.py` | El servidor: todas las rutas y el estado compartido. |
| `lrclib.py` | Hablar con la API de LRCLIB: `buscar()` y `descargar()`. |
| `static/karaoke.js` | El motor del karaoke, compartido por tele y móvil. |
| `static/marcar.js` | El sincronizador a mano. |
| `static/style.css` | Una sola hoja; el modo lo decide la clase del `<body>`. |
| `templates/` | Las seis páginas. |
| `canciones/` | Los datos: `.mp3` (fuera del repo) y `.lrc` (dentro). |

## Las herramientas de consola (no son parte de la web)

| Script | Para qué |
|---|---|
| `bajar_letras.py` | Baja de LRCLIB las letras que falten, eligiendo versión **por duración**. |
| `sincronizar.py` | **Re-cronometra** los `.lrc` escuchando la canción con Whisper. |
| `convertir_a_mp3.py` | Arregla las descargas que llevan `.mp3` pero por dentro son MP4/M4A. |

---

## Sincronizar: las tres vías, y cuándo usar cada una

Este fue el problema más largo del proyecto. El resumen:

**1. Bajar la letra ya sincronizada** — `bajar_letras.py` o *Editor → Buscar en internet*.
Es la primera opción siempre. **Elegir la versión por duración es crítico**: una misma canción tiene versiones que van de 185 a 237 segundos, y equivocarse desfasa la letra entera.

**2. Re-cronometrar automáticamente** — `python sincronizar.py --todas`.
Cuando el texto del `.lrc` es bueno pero los tiempos no cuadran con *tu* grabación. Whisper escucha, se emparejan sus palabras con las del `.lrc`, y donde coinciden queda un **ancla**. Lo demás se interpola.

**3. Marcar a mano** — `/marcar/<cancion>`.
Para lo que la máquina no puede: **euskera** y las canciones donde el alineador se pierde. Una escucha por canción marcando con ESPACIO.

### Lo que se midió, para no repetir el camino

| Prueba | Resultado |
|---|---|
| Reconocimiento sobre la mezcla (modelo `medium`) | **46%** de las palabras |
| Aislar la voz antes con **Demucs** | **38%** — *empeora*, y tarda el doble |
| Modelo **`large-v3`** en vez de `medium` | 48% — dos puntos por el doble de tiempo |
| Forzar el idioma correcto | **6% → 77%** en un caso |

**Conclusiones:**
- **Sacar la letra del audio no sirve**: con menos de la mitad de las palabras bien, habría que reescribirla entera. El texto sale del `.lrc`; de la canción salen solo los tiempos.
- **Demucs no ayuda al reconocimiento.** Whisper está entrenado con audio real, música incluida; una pista separada arrastra artefactos que le resultan más ajenos que la mezcla. *(Sí sirve para el instrumental de la dificultad 2.)*
- **El idioma mal detectado es el fallo que más daño hace.** Whisper detectó **ruso en tres canciones inglesas**. Si una canción sale con pocas anclas, lo primero es forzarle el idioma.

### Las reglas del alineador (`sincronizar.py`)

- **`DESFASE = 0.5`** — Whisper marca las palabras algo antes de que suenen. Medido a mano sobre 6 entradas: con la corrección puesta, el error medio quedó en **0,01 s**.
- **`MIN_RACHA = 3`** — solo valen como ancla las rachas de 3 palabras seguidas. Una coincidencia suelta ("como", "un", "el") casa por casualidad en el sitio equivocado.
- **Descarte por velocidad imposible** — si entre dos anclas hay 60 palabras y 2 segundos, una miente: nadie canta a 30 palabras por segundo. Este filtro fue el que arregló el amontonamiento de líneas.
- **`HUECO_MINIMO = 1.2`** — dos líneas con el mismo sello no se pueden cantar: la segunda no llega a verse.
- **El original no se pisa**: se escribe `.lrc.nuevo` al lado y se aplica solo si los números convencen.
- **El informe** (`informe_sincronizacion.txt`) ordena las canciones **de más a menos sospechosa**, para revisar solo las de arriba en vez de las 78.

---

## Hecho

- [x] Listar canciones leyendo la carpeta
- [x] Reproductor y letra en pantalla
- [x] Leer y trocear el formato `.lrc`
- [x] Buscar y descargar letras de LRCLIB eligiendo versión por duración
- [x] Iluminar la línea que toca, con scroll automático
- [x] Editor para corregir el `.lrc`, con sello de tiempo en vivo
- [x] Aspecto: fondo oscuro, letra en 3D, tarjetas
- [x] Se ve desde la tele y los móviles de la casa (`host="0.0.0.0"`)
- [x] Pantalla y mando: la tele suena, los móviles siguen la letra
- [x] Cuenta atrás en los huecos; los silencios no se iluminan
- [x] Todo el JavaScript en `static/`, compartido entre páginas
- [x] Modo **a tutiplén**: baraja aleatoria que encadena canciones
- [x] **Código QR** en la portada, con la IP calculada en cada visita
- [x] **Re-cronometrado automático** con Whisper
- [x] **Sincronizador a mano** (`/marcar`), con texto editable y líneas insertables

## Pendiente

- [ ] Acceso al marcador desde la portada (ahora solo se llega entrando al editor).
- [ ] Sincronizar a mano las que la máquina no pudo: las 9 en euskera y Bon Jovi.
- [ ] `desire-voyage-voyage` no tiene letra en LRCLIB — marcar a mano o buscarla por otro lado.
- [ ] Que `karaoke.js` se pida los datos él mismo (ruta `/letra/<cancion>` en JSON). Las plantillas se quedarían sin JavaScript y, de regalo, el móvil cambiaría de canción **sin recargar**.
- [ ] Empaquetar en `.exe` con PyInstaller. **Aparcado.** La trampa: `getattr(sys, "frozen", False)` para distinguirlo, `Path(sys.executable).parent` para las **canciones** (fuera, junto al .exe) y `Path(sys._MEIPASS)` para **templates/ y static/** (dentro del paquete), pasándolos a `Flask(template_folder=..., static_folder=...)`. Sin eso, el `.exe` busca los MP3 en su propia carpeta temporal.

## Ideas para más adelante

**Las que justificarían una base de datos.** Hasta entonces, la carpeta `canciones/` hace de base de datos.

- [ ] **Cola de canciones**: varios en el salón añaden desde el móvil, "ahora canta X".
- [ ] **Sorteo**: a quién le toca cantar y con qué canción.
- [ ] **Buscador** por artista o título (hoy solo hay la lista completa).

**Dificultad 2 y letra por palabras.**

- [ ] **Quitar la voz del cantante**: con **Demucs**, `python -m demucs --two-stems=vocals <mp3>`. Genera `vocals.wav` y `no_vocals.wav`; el segundo es el instrumental. Guardarlo como `cancion-karaoke.mp3` y que `/audio/<id>` sirva uno u otro según el modo.
- [ ] **Letra palabra a palabra**: el formato existe, se llama **LRC mejorado** (`[00:13.76]<00:13.76>palabra <00:14.31>siguiente`). Whisper ya devuelve marcas por palabra (`word_timestamps=True`), así que la base está. Con un 46% de acierto habría que apoyarse mucho en el marcador manual.
- Descartado: **sílabas**. Necesitaría alineación por fonemas y diccionario por idioma. Los karaokes comerciales van por palabra y nadie echa de menos más.

**Otras**

- [ ] **Vídeos con la letra incrustada**: `<video>` tiene la misma API que `<audio>`, así que `karaoke.js` no cambiaría. Habría que glob `*.mp4`, elegir etiqueta en la plantilla y ocultar la letra propia. Los móviles no podrían seguirla (la letra va quemada en la imagen).
- [ ] **El micro**: la monitorización de Windows tiene 50-200 ms de retardo, demasiado para cantar. La solución real es que la voz **no pase por el ordenador**: micro a un altavoz con entrada de micro, o interfaz USB con monitorización directa.

---

## Cosas que costaron sangre

**Pantalla y mando.** Cada navegador es un cliente independiente: si cada móvil reproduce su copia del MP3, se desincronizan por buffering y latencia de altavoz. El oído detecta 30 ms como eco. Por eso **suena en un solo sitio** y los móviles solo pintan letra: **la letra perdona décimas, el audio no.**

**El contador `version`.** Existe para que el móvil detecte una orden *nueva* aunque se repita la misma canción. Cuando cambia, el móvil hace `location.reload()` y el servidor regenera la letra entera — más tosco que repintar con JS, pero infalible.

**`/latido` solo acepta latidos de la canción puesta.** Sin ese filtro, una pestaña vieja de `/cantar` abierta en cualquier sitio machaca el estado cada segundo. Y si `ESTADO["cancion"]` es `None` (pasa en **cada reinicio**, porque el estado vive en memoria), `/latido` adopta la canción que llegue y sube `version`; sin eso, tras guardar un fichero los latidos se rechazan para siempre y el karaoke se congela sin avisar.

**`{cache: "no-store"}` en el `fetch` del móvil.** Los navegadores de móvil cachean agresivamente y sin eso `version` no cambia nunca.

**El QR se calcula en cada visita.** La IP que imprime Flask al arrancar se escribe **una sola vez** y se queda obsoleta en cuanto cambias de red, suspendes el portátil o el router renueva la dirección. Comprobado a las malas en una fiesta: el banner decía `.135`, la IP real era `.131`.

**Los ficheros de `static/` no pasan por Jinja.** Flask los sirve tal cual, así que las plantillas conservan un bloque `<script>` con los **datos** y el `.js` lleva **todo el comportamiento**.

**`python -u` para las tandas largas.** Python no vuelca el log hasta llenar 8 KB de buffer; si el proceso muere, ese buffer se pierde y te quedas sin el mensaje de error. Dos tandas fallaron sin dejar rastro por esto.

**Un fallo no puede tumbar una tanda.** Cada canción va dentro de un `try`. La primera versión perdió el trabajo de 50 canciones porque una reventó.

**Baraja, no dado.** El azar puro repite canciones antes de que suenen todas. Se baraja la lista entera y se recorre; solo al agotarla se vuelve a barajar.

---

## Formato LRC

El estándar de los karaokes desde los 90, y por eso las letras son portables a otros reproductores.

```
[00:13.76]primera frase de la cancion
[00:20.12]segunda frase
[00:28.10]
```

`[minutos:segundos.centésimas]` y detrás el texto. **Una línea con sello y sin texto marca un silencio** — es lo que hace que la última frase desaparezca de la pantalla en vez de quedarse congelada hasta el final.

## Convenciones de los ficheros

- Los MP3 se llaman `artista-titulo.mp3`: **minúsculas, guiones, sin acentos ni espacios**. Ese nombre es a la vez el identificador de la URL y la consulta que se manda a LRCLIB.
- Comprobar que un `.mp3` lo es **de verdad**: las descargas de vídeo suelen ser MP4/M4A con la extensión cambiada. `convertir_a_mp3.py` los detecta por los primeros bytes y los convierte.
- El `.gitignore` deja fuera el audio (`*.mp3`, `*.ogg`), los ficheros de trabajo (`*.lrc.old`, `*.lrc.nuevo`) y los registros. **Los `.lrc` sí se versionan**: ocupan nada y son trabajo tuyo.
