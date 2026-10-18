# CRIPTA

Proyecto del curso Estructuras de Datos II, Universidad Nacional, Costa Rica, II Ciclo 2026.

CRIPTA es un juego de mazmorra dirigido por eventos, escrito en Python. Lo que se evalúa son las estructuras de datos elegidas y su justificación con mediciones propias.

---

## Antes de empezar

Necesitás Python 3.11 o superior (el equipo trabaja con 3.13). Verificá con:

```
python --version
```

Las dependencias son:
- `requests>=2.31` — para hablar con la API
- `pygame>=2.5` — solo si vas a usar la interfaz gráfica (`--gui`)

---

## Instalación

Cloná el repositorio y desde su raíz creá un entorno virtual limpio.

**Windows:**
```
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

**Linux/macOS:**
```
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

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

---

## Controles

### Consola

Escribí `ayuda` dentro de la partida para ver esta lista. Los números se cuentan desde 1.

| Orden | Efecto |
|---|---|
| `n` `s` `e` `o` (o `ir n`) | Moverse |
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
| F5 / F9 | Guardar / cargar |
| Esc | Salir |

---

## Modo sin conexión (`--offline`)

Útil para desarrollar o probar sin gastar solicitudes de red. El programa lee las respuestas desde disco con esta estructura:

```
CARPETA/
  criptas.json
  criptas/<id>/general.json
  criptas/<id>/version.json
  criptas/<id>/salas_<n>.json
  criptas/<id>/contenido_<sala>.json
  catalogo/<id_ficha>.json
  catalogo/version.json
```

Para crear un paquete de prueba con una cripta sintética y jugarlo de inmediato:

```
python -m tests.crear_paquete_prueba
python main.py --offline paquete_prueba/
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

Subsistemas disponibles: `agenda`, `red`, `cache`, `fichas`, `cripta`, `lista_ordenada`, `inventario`, `historial`, `ordenamiento`, `guardado`. Cada uno corresponde a un archivo en `bench/`.

---

## Pruebas

Cada archivo `test_*.py` de la carpeta `tests` se ejecuta como módulo desde la raíz:

```
python -m tests.test_almacen_cripta
python -m tests.test_almacen_fichas
python -m tests.test_almacen_local_cache
python -m tests.test_cache
python -m tests.test_controlador
python -m tests.test_guardado_binario
python -m tests.test_gui
python -m tests.test_inventario
python -m tests.test_inventario_partida
python -m tests.test_lista_ordenada
python -m tests.test_motor_base
python -m tests.test_ordenamiento
python -m tests.test_partida
python -m tests.test_red
python -m tests.test_replay_puntajes
python -m tests.test_revision
```

O todos juntos con:

```
python -m unittest discover -s tests -t .
```

---

## Archivos generados

Se crean dentro de `datos_cripta/` (o la carpeta que se indique con `--datos`). Esta carpeta no se sube al repositorio.

| Ruta | Contenido |
|---|---|
| `criptas/<id>__<version>.bin` | Esqueleto y contenido persistidos por versión |
| `catalogo/catalogo_<version>.bin` | Fichas del catálogo persistidas por versión |
| `partidas/<cripta>_<fecha>_<hora>.log` | Bitácora de cada partida; se reproduce con `--replay` |
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

El equipo registra los prompts utilizados en `PROMPTS_LLM.md` (§10.3).

---

## Equipo

| Integrante | Responsabilidades |
|---|---|
| Jeferson | Red, precarga, resolución del catálogo, bitácora en pantalla |
| Kim | Caché persistente, ordenamiento, guardado binario |
| Mariano | Motor: agenda de eventos, rastro, efectos, combate, retroceso |
| Axel | Inventario, replay, puntajes, controlador e interfaz |
