# CRIPTA

Proyecto del curso Estructuras de Datos II, Universidad Nacional, Costa Rica, II Ciclo 2026.

CRIPTA es un juego de mazmorra dirigido por eventos, escrito en Python. Lo que se evalúa son las estructuras de datos elegidas y su justificación con mediciones propias.

---

## Antes de empezar

El proyecto usa **Python 3.13** (cualquier 3.13.x; el enunciado pide 3.11 o superior). Todo el grupo usa la misma versión para que las pruebas y las mediciones de `--bench` sean comparables. No usen 3.14 todavía: pygame puede no tener instalador para esa versión. La versión queda fijada en `.python-version`.

Las dependencias son:
- `requests>=2.31` — para hablar con la API
- `pygame>=2.5` — solo si vas a usar la interfaz gráfica (`--gui`)

Herramientas de proceso (no son dependencias del programa):
- [uv](https://docs.astral.sh/uv/) — instala Python 3.13 y spec-kit
- **spec-kit `v1.0.10`** (`specify-cli`) — versión fija para todo el grupo
- **Google Antigravity** (IDE v2.0.0 o superior; usamos 2.29.0) — agente de programación hasta el 2026-11-08; en spec-kit su clave es `agy`
- **OpenAI Codex** (extensión de VS Code) — agente de programación desde el 2026-11-08, porque se agotó el cupo de Antigravity; usa las mismas skills de spec-kit
---

## Instalación

Instalá uv (Windows, PowerShell):
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
En macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`. Cerrá y abrí la terminal y verificá con `uv --version`.

Desde la raíz del repositorio, creá el entorno con Python 3.13:

**Windows:**
```
uv python install 3.13
uv venv --python 3.13 venv
venv\Scripts\activate
uv pip install -r requirements.txt
python --version
```

**Linux/macOS:**
```
uv python install 3.13
uv venv --python 3.13 venv
source venv/bin/activate
uv pip install -r requirements.txt
python --version
```

`python --version` debe decir 3.13.x. Prueba rápida: `python -m tests.test_partida` debe terminar con "Todas las pruebas pasaron".

---

## Desarrollo dirigido por especificaciones (spec-kit)

La segunda parte se desarrolla con [GitHub spec-kit](https://github.com/github/spec-kit), versión fija **v1.0.10**; se usó **Google Antigravity** (`agy`) y, desde el 2026-11-08, **OpenAI Codex**.

Instalar spec-kit (cada integrante, la misma versión):
```
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.0.10
specify version
```

El repositorio ya está inicializado con:
```
specify init --here --integration agy --script ps --ignore-agent-tools --extension git
```
(no hace falta repetirlo). Lo que genera se versiona:

| Ruta | Contenido |
|---|---|
| `.specify/memory/constitution.md` | Constitución del proyecto |
| `.specify/templates/`, `.specify/scripts/powershell/` | Plantillas y scripts de spec-kit |
| `.specify/extensions/git/` | Extensión que crea la rama `NNN-...` de cada especificación (auto-commit desactivado) |
| `.agents/skills/speckit-*/` | Comandos de spec-kit para Antigravity |
| `.agents/rules/cripta.md` | Reglas del proyecto que el agente aplica siempre |
| `AGENTS.md` | Las mismas reglas del proyecto, para Codex |
| `specs/NNN-capacidad/` | `spec.md`, `plan.md`, `tasks.md` y artefactos de cada capacidad |

En el chat de Antigravity (workspace abierto en la raíz del repositorio) los comandos se invocan con guion: `/speckit-constitution`, `/speckit-specify`, `/speckit-clarify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-analyze`, `/speckit-implement`. El agente no hace commits: el orden en Git es especificación → plan y tareas → código. Cada prompt se registra en `PROMPTS_LLM.md`.

En Codex (VS Code) los mismos comandos se invocan con `$`: `$speckit-implement`, `$speckit-analyze`, etc. Codex se usa en modo "Ask for approval" (nunca "Full access").
---

## Correr el juego

Todos los comandos se ejecutan desde la raíz del repositorio con el entorno activado.

**La forma más rápida de jugar:**
```
python main.py
```
Eso abre el juego en consola y se conecta al servicio web. Si preferís ventana gráfica:
```
python main.py --gui
```

Al terminar cada partida se imprime un reporte con las solicitudes realizadas, el presupuesto consumido y los aciertos/fallos de caché.

### Otros modos

| Comando | Qué hace |
|---|---|
| `python main.py` | Consola, contra el servicio web |
| `python main.py --gui` | Ventana Pygame; combinable con `--offline` |
| `python main.py --offline CARPETA` | Lee respuestas desde disco, sin gastar solicitudes |
| `python main.py --replay datos_cripta/partidas/ARCHIVO.log` | Reproduce una partida sin interacción |
| `python main.py --replay ARCHIVO.log --hasta T` | Reproduce hasta el instante `T` e imprime el estado en ese momento, sin interfaz |
| `python main.py --verificar CRIPTA` | Solo verifica si la cripta se puede ganar e imprime el reporte; no abre la interfaz. Combinable con `--offline` |
| `python main.py --bench` | Corre todas las mediciones |
| `python main.py --bench historial inventario` | Solo los subsistemas indicados |

### Opciones adicionales

| Opción | Descripción |
|---|---|
| `--cache-size N` | Fichas del catálogo en memoria (25 por defecto) |
| `--semilla N` | Semilla fija; por defecto se genera una nueva por partida |
| `--nombre TEXTO` | Nombre del jugador; si no se da, se pregunta al iniciar |
| `--datos CARPETA` | Dónde guardar los archivos generados (por defecto `datos_cripta`) |
| `--detalle` | Con `--replay`, muestra cada orden reproducida |
| `--forzar` | Permite jugar una cripta no resoluble o que no se pudo verificar |
| `--hasta T` | Con `--replay`, consulta el estado en el instante `T` |
| `--checkpoint-cada K` | Acciones entre puntos de control de la línea de tiempo (10 por defecto) |

---

## Controles

### Consola

Escribí `ayuda` dentro de la partida para ver esta lista. Los números se cuentan desde 1.

| Orden | Efecto |
|---|---|
| `n` `s` `e` `o` (o `ir n`) | Moverse |
| `ir a <sala>` | Viajar a una sala ya explorada por la ruta más barata conocida, paso a paso |
| `mapa` | Ver el mapa conocido y las puertas recordadas |
| `historia <t>` o `historia #k` | Consultar el estado en el instante `t` o justo antes de la acción número `k` (no consume tiempo) |
| `abrir n\|s\|e\|o` | Abrir una puerta |
| `atacar [N]` | Atacar a un enemigo |
| `esperar` o `x` | Esperar un turno |
| `recoger [N]` | Recoger un objeto del suelo |
| `usar\|equipar\|soltar [N]` | Actuar sobre un objeto; sin número, usa el del cursor |
| `inv` | Ver el inventario |
| `sig`, `ant`, `inicio` | Mover el cursor del inventario |
| `ordenar peso\|valor\|nombre [desc]` | Vista ordenada (no cambia el orden real) |
| `retroceso` o `r` | Usar el pergamino de retroceso |
| `puntajes` | Ver la tabla de puntajes |
| `guardar` / `cargar` | Guardar o cargar la partida |
| `salir` | Terminar |
| `ayuda` | Mostrar las órdenes |

### Interfaz gráfica (`--gui`)

| Tecla / acción | Efecto |
|---|---|
| Flechas | Moverse |
| Shift + flecha | Abrir puerta |
| Clic en una puerta | Moverse o abrirla |
| Tab o clic | Elegir enemigo |
| Espacio | Atacar |
| F o clic | Elegir objeto del suelo |
| G | Recoger |
| X | Esperar |
| R | Pergamino de retroceso |
| W / S | Cursor del inventario |
| Inicio | Ir al primer objeto |
| U / Q / T | Usar / equipar / soltar |
| 1 / 2 / 3 | Vista por peso / valor / nombre (con Shift: descendente) |
| I | Inventario |
| P | Puntajes |
| M o botón Mapa conocido | Abrir el mapa dibujado |
| Flechas o arrastre, dentro del mapa | Desplazar el dibujo |
| Rueda o + / -, dentro del mapa | Cambiar el zoom |
| C, dentro del mapa | Recentrar en el jugador |
| Esc o Enter, dentro del mapa | Cerrar el mapa y volver al juego |
| V | Ir a una sala explorada (Esc cancela el viaje; R cancela y usa un pergamino al terminar) |
| L | Historia: escribir `t` o `#k`, Enter consulta, Esc cierra |
| H / F1 | Ayuda |
| F5 / F9 | Guardar / cargar |
| Esc | Salir |

---

### Mapa dibujado y niebla de guerra

En consola, `mapa` sin argumentos dibuja las salas con caracteres ASCII:
`[id]` explorada, `[@id]` jugador y `(?)` avistada. Las conexiones usan `-` o
`|` para puerta recordada abierta, `X` para cerrada, `K` para cerrada con llave
y `?` para puerta no observada. Debajo aparecen los nombres, salidas, costos,
estados recordados, llaves ya conocidas y conteos. Los mapas anchos se dividen
en bloques; las conexiones desplazadas se enumeran bajo
`Conexiones fuera de la cuadricula`.

En la ventana, las exploradas muestran id y nombre abreviado; las avistadas
son recuadros de niebla con `?`. El jugador lleva borde resaltado y un círculo.
Verde significa abierta; rojo, cerrada; dorado, cerrada con llave; gris, puerta
no observada. Los rótulos muestran los costos. El mapa abre centrado en el
jugador. Los controles de desplazamiento y zoom solo actúan dentro del mapa.

La niebla radial con textura suave se cachea al abrir o cambiar el zoom; las avistadas conservan un «?» tenue y bordes difuminados, y lo desconocido no lleva formas para no revelar posiciones de salas.

La posición de las casillas usa exclusivamente conexiones conocidas. Las
avistadas nunca muestran su id o nombre, ni usan esos ids ocultos para ordenar
o resolver colisiones. El mapa respeta la última observación de cada puerta,
aunque esté desactualizada. Consultarlo no observa puertas, consume tiempo ni
escribe en el log. Tras un pergamino refleja el conocimiento vigente.

Prueba manual en Windows, con el paquete de prueba ya presente:

```powershell
venv\Scripts\python.exe main.py --offline paquete_prueba/ --gui
```

1. Introducir el nombre y elegir una cripta en los cuadros de inicio.
2. En la sala inicial, pulsar **M** o el botón **Mapa conocido**. Comprobar
   el recuadro del jugador centrado, su borde y círculo, y las vecinas con `?`.
3. Probar flechas y arrastre, rueda y `+`/`-`; pulsar **C** para recentrar.
4. Volver con **Esc** o **Enter**. Moverse por una salida abierta indicada
   en la sala; si hace falta abrir una puerta, usar sus controles habituales.
5. Abrir **M** de nuevo: la sala recién visitada debe mostrar id y nombre,
   el jugador debe estar marcado allí y los destinos aún avistados seguir con `?`.
6. Comprobar que abrir y cerrar el mapa no cambia el reloj ni ejecuta movimientos.

Estas instrucciones permiten la revisión humana; las pruebas automatizadas
del mapa gráfico usan `SDL_VIDEODRIVER=dummy`, sin abrir una ventana visible.

## Modo sin conexión (`--offline`)

Útil para desarrollar o probar sin gastar solicitudes de red. El programa lee las respuestas desde disco con esta estructura:

```
CARPETA/
  criptas.json
  criptas/<id>/general.json
  criptas/<id>/version.json
  criptas/<id>/salas_<n>.json
  criptas/<id>/contenido_<sala>.json
  criptas/<id>/llaves.json
  catalogo/<id_ficha>.json
  catalogo/version.json
```

Para crear un paquete de prueba con una cripta sintética y jugarlo de inmediato:

```
python -m tests.crear_paquete_prueba
python main.py --offline paquete_prueba/
```

---

## Verificación de resolubilidad

Antes de iniciar una partida nueva el programa comprueba si la cripta se puede ganar (conseguir `llave_salida` y entrar a `sala_salida` por una puerta que la pide). Usa el esqueleto y la consulta `/llaves`, que se guarda junto a la cripta y no se vuelve a pedir mientras no cambie la versión. El reporte se muestra en la interfaz activa:

```
ESTADO: RESOLUBLE | NO RESOLUBLE | NO VERIFICADA
ORDEN DE LLAVES:            (si es resoluble, por etapas)
LLAVES NO OBTENIBLES / FRONTERA BLOQUEADA / UBICACIÓN DE LLAVES / CICLOS DETECTADOS / MOTIVO
```

Si no es resoluble, o no se pudo verificar por falta de red o de presupuesto, la partida no inicia salvo con `--forzar`. Para verificar sin jugar:

```
python main.py --verificar CRIPTA
```

Código de salida: `0` resoluble, `1` no resoluble, `2` no verificada o cripta inexistente. Ni el replay ni la carga de una partida guardada vuelven a verificar.

---

## Línea de tiempo

Durante la partida, `historia <t>` (o la tecla L) muestra el estado en el instante `t`: reloj, sala, vida, estadísticas, inventario, efectos, enemigos de la sala y mapa conocido. `historia #k` muestra el estado justo antes de la acción número `k`. No consume tiempo, no se escribe en la bitácora y no cambia lo que el pergamino puede deshacer. Las acciones revertidas con un pergamino desaparecen de la historia, y guardar y cargar conserva la línea completa.

Se guarda un punto de control cada K acciones (10 por defecto, ajustable con `--checkpoint-cada K`). Para consultar una partida ya terminada:

```
python main.py --replay datos_cripta/partidas/ARCHIVO.log --hasta T
```

---

## Replay

Cada partida deja una bitácora en `datos_cripta/partidas/`. Para reproducirla:

```
python main.py --replay datos_cripta/partidas/ARCHIVO.log
```

Con `--detalle` se imprime cada orden reproducida:

```
python main.py --replay datos_cripta/partidas/ARCHIVO.log --detalle
```

---

## Mediciones (`--bench`)

```
python main.py --bench
python main.py --bench historial inventario
```

Subsistemas disponibles: `mapa_conocido`, `agenda`, `red`, `resolubilidad`, `cache`, `fichas`, `cripta`, `lista_ordenada`, `inventario`, `historial`, `linea_tiempo`, `ordenamiento`, `guardado`, `cazador`. Cada uno corresponde a un archivo en `bench/`.

Las criptas sintéticas de las mediciones salen de `bench/generador_criptas.py` (deterministas por semilla, topología en línea o cuadrícula, costos, cazadores con rango y cadenas de llaves).

---

## Pruebas

Cada archivo `test_*.py` de la carpeta `tests` se ejecuta como módulo desde la raíz, por ejemplo:

```
python -m tests.test_resolubilidad
```

Módulos disponibles:

```
python -m tests.test_almacen_cripta
python -m tests.test_almacen_fichas
python -m tests.test_almacen_local_cache
python -m tests.test_bench_linea_tiempo
python -m tests.test_bench_mapa_conocido_002
python -m tests.test_bench_resolubilidad
python -m tests.test_cache
python -m tests.test_carga_v4_002
python -m tests.test_cierre_instante_t
python -m tests.test_comentarios_ir_a_002
python -m tests.test_conocimiento
python -m tests.test_conocimiento_partida
python -m tests.test_controlador
python -m tests.test_esqueleto
python -m tests.test_fr010_generaciones_002
python -m tests.test_generador_criptas
python -m tests.test_guardado_binario
python -m tests.test_guardado_v4_002
python -m tests.test_gui
python -m tests.test_historia_interfaces
python -m tests.test_historia_persistencia
python -m tests.test_integracion_comentarios_002
python -m tests.test_inventario
python -m tests.test_inventario_partida
python -m tests.test_ir_a_compuesto
python -m tests.test_ir_a_grafico_002
python -m tests.test_linea_tiempo
python -m tests.test_lista_ordenada
python -m tests.test_mapa_consola
python -m tests.test_motor_base
python -m tests.test_niebla_ir_a
python -m tests.test_ordenamiento
python -m tests.test_partida
python -m tests.test_persistencia_cazador
python -m tests.test_planificador_rutas
python -m tests.test_red
python -m tests.test_replay_puntajes
python -m tests.test_resolubilidad
python -m tests.test_resolubilidad_integracion
python -m tests.test_resolubilidad_unitaria
python -m tests.test_revision
python -m tests.test_terreno_cazador
```

Todos juntos (PowerShell), con un resumen de fallos al final:

```
$fallos = 0; Get-ChildItem tests -Filter 'test_*.py' | ForEach-Object { python -m ("tests." + $_.BaseName); if ($LASTEXITCODE -ne 0) { $fallos++ } }; "Módulos con fallos: $fallos"
```

Las pruebas de interfaz gráfica (`test_gui`, `test_historia_interfaces`, `test_ir_a_grafico_002`) necesitan Pygame instalado.

---

## Archivos generados

Se crean dentro de `datos_cripta/` (o la carpeta que se indique con `--datos`). Esta carpeta no se sube al repositorio.

| Ruta | Contenido |
|---|---|
| `criptas/<id>__<version>.bin` | Esqueleto, contenido y llaves persistidos por versión |
| `catalogo/catalogo_<version>.bin` | Fichas del catálogo persistidas por versión |
| `partidas/<cripta>_<fecha>_<hora>.log` | Bitácora de cada partida; se reproduce con `--replay`. Las líneas `# ir a X` marcan observaciones de un viaje automático |
| `guardados/partida.bin` | Partida guardada (formato binario propio) |
| `puntajes.txt` | Tabla de puntajes local |

---

## Estructura del repositorio

| Carpeta / archivo | Contenido |
|---|---|
| `main.py` | Punto de entrada; solo arma las piezas |
| `modelo/juego` | Reglas del juego: partida, agenda de eventos, actores, salas, efectos, combate, inventario, registro para el retroceso |
| `modelo/estructuras` | Estructuras propias: caché, cola FIFO, lista doble, lista ordenada, ordenamiento |
| `modelo/datos` | Acceso a red y disco: cliente HTTP, cliente offline, precarga, resolutor del catálogo, presupuesto, almacenes, guardado binario, bitácora, puntajes |
| `controlador` | Controlador, aplicación, órdenes, replay y repeticiones |
| `vista` | Vista de consola, vista Pygame, sonidos e imágenes |
| `bench` | Mediciones de cada subsistema |
| `tests` | Pruebas y la cripta sintética de prueba |
| `herramientas` | Demostraciones y prueba rápida de la API |

La arquitectura es MVC: el modelo no conoce red, archivos ni interfaz.

---

## API

Los datos de cada cripta se obtienen de un servicio web de solo lectura con un presupuesto máximo de solicitudes por cripta:

- Endpoint: `https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1`
- Docs Swagger: `https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1/docs`
- Cada solicitud lleva el encabezado `X-Cripta-Client-Id` con un UUID que se genera una vez por ejecución.

---

## Uso de LLM

El equipo registra los prompts utilizados en `PROMPTS_LLM.md` (Parte I y Parte II), con fecha, autor, herramienta y modelo. Las decisiones de diseño y sus mediciones están en `DECISIONES.md`, y las especificaciones de la Parte II en `specs/001-…` a `specs/004-…`.

---

## Equipo

| Integrante | Parte I | Parte II |
|---|---|---|
| Jeferson | Red, precarga, resolución del catálogo, bitácora en pantalla | 003: datos nuevos del servicio (`/llaves`, costos, cazadores), generador de criptas sintéticas, verificación de resolubilidad, `--verificar` y `--forzar`; preparación de spec-kit |
| Kim | Caché persistente, ordenamiento, guardado binario | 002: mapa conocido y niebla, antorcha, Dijkstra propio, `ir a`, guardado v4 |
| Mariano | Motor: agenda de eventos, rastro, efectos, combate, retroceso | 001: costos de terreno, puertas, cazador e invalidación de rutas |
| Axel | Inventario, replay, puntajes, controlador e interfaz | 004: línea de tiempo (`historia`, `--hasta`, puntos de control) e interfaz |
