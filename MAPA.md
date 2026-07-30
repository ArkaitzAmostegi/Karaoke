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

## Pendiente

- [ ] Que se vea desde la tele o el móvil de la misma casa (`host="0.0.0.0"`).
- [ ] Cuenta atrás antes de que entre la primera frase.
- [ ] Que las líneas vacías (silencios) no se iluminen.

## Ideas para más adelante (de Arkaitz, 26-jul)

Estas son las que justificarían meter una base de datos. Hasta entonces, la carpeta `canciones/` hace de base de datos.

- [ ] **Cola de canciones**: varios en el salón añaden desde el móvil, "ahora canta X".
- [ ] **Sorteo**: a quién le toca cantar y con qué canción.
- [ ] **Buscador** por artista, título, etc. (hoy solo hay la lista completa).

---

## Formato LRC

Es el estándar de los karaokes desde los 90, y por eso las letras son portables a otros reproductores.

```
[00:13.76]Esaiozu euriari berriz, ez jauzteko
[00:20.12]esan bakardadeari gaur ez etortzeko
[00:28.10]
```

`[minutos:segundos.centésimas]` y detrás el texto. **Una línea con sello y sin texto marca un silencio** — es lo que hace que la última frase desaparezca de la pantalla en vez de quedarse congelada hasta el final de la canción.
