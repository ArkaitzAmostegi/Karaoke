# MAPA de la app

Abre este fichero cuando no sepas dónde estás. Se actualiza cada vez que añadimos algo.

---

## Cómo funciona esto, en tres frases

1. **Cada página es una función de Python.** La URL es la dirección; la función, quien atiende. `@app.route("/cantar/<cancion_id>")` significa "cuando alguien pida esa dirección, ejecuta la función de debajo". Eso es Flask entero.
2. **Hay dos tipos de función**: las que devuelven algo *para mirar* (`render_template` → una página) y las que *hacen algo y te mandan a otro sitio* (`redirect`). Al escribir una nueva, la primera pregunta es cuál de las dos es.
3. **No hay base de datos.** Todo vive en `canciones/`: por cada canción un `.mp3` (la música) y un `.lrc` (la letra con tiempos). "Guardar" = escribir un fichero ahí. "Leer" = leerlo de ahí.

---

## Las páginas (lo que ve una persona)

| URL | Función | Qué es |
|---|---|---|
| `/` | `portada` | Lista de canciones. Dos enlaces por canción: **Cantar** y **Sincronizar**. |
| `/cantar/<cancion>` | `cantar` | El karaoke: reproductor + letra. |
| `/editor/<cancion>` | `editar` | Sala de máquinas de una canción. Hoy casi vacía. |
| `/buscar/<cancion>` | `buscar_letra` | Las versiones que existen en LRCLIB, con álbum y duración. |

## Las acciones (hacen algo y te redirigen)

| URL | Función | Qué es |
|---|---|---|
| `/usar/<cancion>/<id>` | `usar_letra` | Descarga esa versión, la guarda como `.lrc` y te lleva a Cantar. |
| `/audio/<cancion>` | `sonar` | Entrega el MP3. **No la visitas tú**: la pide la etiqueta `<audio>` del navegador. |

## Cómo se llega de una a otra

```
Portada ──Cantar──────────> Cantar ──(el navegador pide)──> Audio
   │
   └──Sincronizar────────> Editor ──Buscar letra──> Versiones
                                                        │
                                            Usar esta ──┘
                                                        │
                                                        v
                                                     Cantar
```

---

## Los ficheros del proyecto

| Fichero | Para qué |
|---|---|
| `app.py` | El servidor web: todas las rutas. |
| `lrclib.py` | Hablar con la API de LRCLIB: `buscar()` y `descargar()`. |
| `bajar_letras.py` | Script de consola: baja de golpe las letras que falten. No es parte de la web. |
| `templates/` | Las plantillas HTML: `lista`, `cantar`, `editor`, `resultados`. |
| `canciones/` | Los datos: `.mp3` (fuera del repo) y `.lrc` (dentro del repo). |

## Las funciones que no son rutas

| Función | Qué hace |
|---|---|
| `listar_canciones()` | Mira `canciones/` y devuelve los nombres de los `.mp3`. |
| `leer_letra(cancion_id)` | Lee el `.lrc` y lo convierte en `[{"tiempo": 13.76, "texto": "..."}]`. |

---

## Hecho

- [x] Listar canciones leyendo la carpeta
- [x] Página de cantar con reproductor funcionando
- [x] Leer y trocear el formato `.lrc`
- [x] Enseñar la letra en pantalla (quieta, sin sincronizar)
- [x] Buscar letras en LRCLIB y elegir la versión por duración
- [x] Descargar y guardar la letra desde la web

- [x] Iluminar la línea que toca, con scroll automático (JS + el reloj del audio)
- [x] Editor: corregir el `.lrc` a mano y guardarlo
- [x] Aspecto: fondo oscuro, letra en 3D, tarjetas

- [x] Que se vea desde la tele y los móviles de la casa (`host="0.0.0.0"`)

## Pantalla y mando — HECHO (26-jul)

**Rutas nuevas:** `/estado` (GET, devuelve el diccionario) · `/poner/<cancion>` (elige canción, pone `tiempo` a 0 y sube `version`) · `/latido` (POST, la tele manda su `currentTime` una vez por segundo) · `/movil` (la letra sin audio, lee la canción del estado).

**Reglas que costaron sangre:**
- El contador `version` existe para que el móvil detecte una orden *nueva* aunque se repita la misma canción. Cuando cambia, el móvil hace `location.reload()` y el servidor le regenera la letra entera — más tosco que repintar con JS, pero infalible.
- **`/latido` solo acepta latidos de la canción que está puesta.** Sin ese filtro, una pestaña vieja de `/cantar` abierta en cualquier sitio sigue mandando latidos cada segundo y machaca el estado — y como `latido` no toca `version`, el móvil no se entera y muestra la letra buena con los tiempos de otra canción.
- Si `ESTADO["cancion"]` es `None` (pasa en **cada reinicio del servidor**, porque el estado vive en memoria), `/latido` adopta la canción que le llegue y sube `version`. Sin eso, tras guardar un fichero los latidos se rechazan para siempre y el karaoke se congela sin avisar.
- En el móvil, el `fetch` lleva `{cache: "no-store"}`: los navegadores de móvil cachean agresivamente y sin eso `version` no cambia nunca.

## (histórico) Por qué pantalla y mando

El problema que lo motiva: **cada navegador es un cliente independiente**. Si cada móvil reproduce su copia del MP3, se desincronizan (buffering y latencia de altavoz distintos) y suena a eco. El oído detecta desfases de 30 ms.

Decisión (Arkaitz, 26-jul): **suena en un solo sitio.**

| Aparato | Qué hace |
|---|---|
| La tele / el portátil | Elige canción. **Suena aquí y solo aquí.** Muestra la letra. |
| Los móviles | Muestran la misma letra sincronizada. **Sin audio.** Si te conectas tarde, entras por donde va. |

La clave: **la letra perdona décimas, el audio no.** Por eso los móviles sí pueden mostrar la letra en sincronía, pero no reproducir.

- [ ] **1. Estado compartido** en el servidor: `ESTADO = {"cancion", "tiempo", "sonando", "version"}` + rutas `/estado` y `/poner/<cancion_id>`. El contador `version` existe para que la tele detecte una orden *nueva* aunque se repita la misma canción.
- [ ] **2. La tele** manda su `currentTime` al servidor mientras suena.
- [ ] **3. El móvil** pregunta cada poco y pinta la letra por donde toca (polling; SSE y WebSockets serían más elegantes pero para un salón sobra).

- [x] Cuenta atrás en los huecos y silencios que no se iluminan (26-jul)

**Criterio de la cuenta atrás (decisión de Arkaitz):** no depende de que el `.lrc` marque los silencios con líneas vacías —LRCLIB casi nunca lo hace—, sino del **hueco real hasta la siguiente línea con letra**: si faltan menos de `AVISO` segundos (hoy 10), se cuenta. Funciona con cualquier `.lrc` venga como venga. Aparte, si la línea que toca está vacía no se ilumina ninguna (`indice = -1`).

- [x] Todo el JavaScript en `static/karaoke.js`, compartido por las dos páginas (26-jul)

**El reparto:** los ficheros de `static/` **no pasan por Jinja** (Flask los sirve tal cual), así que las plantillas conservan un único bloque `<script>` con los **datos** que solo sabe Python (`MODO`, `LINEAS`, `CANCION`, `VERSION`) y `karaoke.js` lleva **todo el comportamiento**. Al final del fichero, un `if (MODO === "tele")` decide qué arrancar. La función `pintar(t)` es común; lo único que cambia entre tele y móvil es de dónde sale la `t`.

- [x] Sello de tiempo en el editor, en formato `[mm:ss.cc]` listo para copiar al `.lrc` (26-jul)

## EN CURSO — Dos modos de juego y el QR

**Modo "a tutiplén"** (idea de Arkaitz, 26-jul): además de elegir canción a mano, un modo que arranca y va encadenando canciones al azar con unos segundos de descanso.

- **Baraja, no dado.** Elegir al azar de verdad repite canciones antes de que suenen todas. Se baraja la lista entera y se recorre; solo al agotarla se vuelve a barajar.
- **La baraja vive en el servidor**, no en el navegador: al cambiar de canción la página se recarga y el navegador perdería el estado.
- **Solo canciones con letra.** Las 10 que no la tienen están apartadas en `canciones/_sin_letra/` (invisibles para la app, porque `glob("*.mp3")` no entra en subcarpetas).
- **Riesgo conocido:** los navegadores bloquean la reproducción automática con sonido sin interacción previa. Si molesta, la solución es cambiar de canción **sin recargar** (ver el pendiente de `/letra/<cancion>`).

**Código QR en la pantalla de la tele**: dictar `192.168.0.42:5055/movil` a cinco personas en un salón es un incordio. Con la librería `qrcode` de Python, una ruta que devuelva la imagen. Para averiguar la IP local sin depender de la configuración: abrir un socket UDP hacia 8.8.8.8 y leer `getsockname()` — no envía nada ni necesita internet, solo hace que el sistema elija la interfaz de salida.

## Pendiente

- [ ] Empaquetar en `.exe` con PyInstaller. **Aparcado el 26-jul.** El paso 1 (que estaba a medias) es que `app.py` distinga si va empaquetado: con `getattr(sys, "frozen", False)`, `BASE = Path(sys.executable).parent` para las **canciones** (fuera, junto al .exe) y `RECURSOS = Path(sys._MEIPASS)` para **templates/ y static/** (dentro del paquete), pasándolos a `Flask(template_folder=..., static_folder=...)`. Sin eso, el `.exe` busca los MP3 dentro de su propia carpeta temporal.
- [ ] Que `karaoke.js` se pida los datos él mismo (ruta `/letra/<cancion>` en JSON). Las plantillas se quedarían sin nada de JavaScript, y de regalo el móvil cambiaría de canción **sin recargar**.
- [ ] Empaquetar en un `.exe` con PyInstaller, para llevarlo a casas sin Python (hay que incluir `templates/` y `static/` a mano). **Después** de pantalla+mando, para no empaquetar dos veces.

## Ideas para más adelante (de Arkaitz, 26-jul)

**Las que justificarían una base de datos.** Hasta entonces, la carpeta `canciones/` hace de base de datos.

- [ ] **Cola de canciones**: varios en el salón añaden desde el móvil, "ahora canta X".
- [ ] **Sorteo**: a quién le toca cantar y con qué canción.
- [ ] **Buscador** por artista, título, etc. (hoy solo hay la lista completa).

**Dificultad 2 y letra por palabras.** Las dos se apoyan en la misma herramienta.

- [ ] **Quitar la voz del cantante** (dificultad 2): con **Demucs** (`pip install demucs`, código abierto). Se procesa una vez por canción —minutos en CPU— y se guarda un tercer fichero hermano, `cancion-karaoke.mp3`. Luego `/audio/<id>` sirve uno u otro. Alternativa con ventana gráfica: Ultimate Vocal Remover.
- [ ] **Letra palabra a palabra**: el formato ya existe, se llama **LRC mejorado** (`[00:13.76]<00:13.76>Esaiozu <00:14.31>euriari`). LRCLIB solo sirve nivel línea y los que tienen palabra a palabra son de pago, así que hay que generarlo: **alineación forzada** (dar audio + letra conocida y que calcule los tiempos) con **WhisperX**, sobre la pista de voz que saca Demucs.
- Descartado: **sílabas**. Necesitaría alineación por fonemas (Montreal Forced Aligner) y diccionario por idioma. Los karaokes comerciales van por palabra y nadie echa de menos más.
- Aviso: Whisper conoce el euskera pero flojo (idioma con pocos datos). En castellano o inglés saldrá bastante mejor.

---

## Formato LRC

Es el estándar de los karaokes desde los 90, y por eso las letras son portables a otros reproductores.

```
[00:13.76]Esaiozu euriari berriz, ez jauzteko
[00:20.12]esan bakardadeari gaur ez etortzeko
[00:28.10]
```

`[minutos:segundos.centésimas]` y detrás el texto. **Una línea con sello y sin texto marca un silencio** — es lo que hace que la última frase desaparezca de la pantalla en vez de quedarse congelada hasta el final de la canción.
