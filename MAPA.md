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

## EN CURSO — Pantalla y mando

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

## Pendiente

- [ ] Cuenta atrás antes de que entre la primera frase.
- [ ] Que las líneas vacías (silencios) no se iluminen.
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
