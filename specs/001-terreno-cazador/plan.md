# Implementation Plan: Terreno, cazador e invalidación de rutas

**Branch**: `001-terreno-cazador` | **Date**: 2026-11-07 | **Spec**: [specs/001-terreno-cazador/spec.md](spec.md)  
**Author**: Mariano (Motor del juego)

## Summary

La capacidad 001 incorpora el costo variable de terreno en todas las salidas ($\ge 1$, por defecto 100), calcula el intervalo temporal de movimiento de todos los actores en el reloj virtual (`max(1, costo_salida * 100 // velocidad)`), introduce el enemigo cazador con búsqueda de ruta de costo mínimo acotada a su rango hacia el jugador con desempate determinista por menor ID de sala vecina, e implementa la invalidación reactiva de rutas ante eventos del entorno (puertas, desplazamientos del jugador, retroceso). 

El enfoque técnico se basa en un cálculo compartido de Dijkstra acotado al rango máximo activo desde la posición del jugador, empleando un montículo binario propio sin `heapq` (contrato C3 con Kim), arreglos preasignados indexados por posición contigua de sala con marcas de búsqueda $O(1)$ sin reinicialización global, y un despachador unificado de cambios de estado de puertas (contrato C2) para la invalidación selectiva y sincronización con Axel y Kim.

---

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: `requests >= 2.31`, `pygame >= 2.5` (ninguna biblioteca nueva; `requirements.txt` se mantiene intacto).  
**Storage**: Persistencia propia y archivos binarios existentes; sin bases de datos externas.  
**Testing**: Conjunto de pruebas unitarias y de integración ejecutadas con `python -m tests.<modulo>`.  
**Target Platform**: Multiplataforma (Windows 11 / Linux / macOS), ejecución en consola para pruebas y `--bench`.  
**Project Type**: Motor de juego por eventos (arquitectura MVC).  
**Performance Goals**: Ciclo de eventos entre dos decisiones del jugador $< 20\text{ ms}$ en la cripta de referencia con decenas de cazadores activos (`SC-004`).  
**Constraints**: 
- Prohibición estricta de `dict` o `set` como índice o caché en problemas evaluados, `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` o cualquier biblioteca de grafos o rutas (Constitución Principio I y P2 §6.2).
- Prohibido `sorted()` y `list.sort()` en ordenamientos evaluados.
- Ningún dato de una cripta concreta en el código (Principio IV).
- Separación MVC estricta: el modelo no importa controlador ni vista (Principio III).
- Determinismo total: azar exclusivo de `partida.azar` y desempates por menor ID (Principio II).

---

## Constitution Check

| Principio | Estado | Justificación en este Plan |
|---|---|---|
| **I. Estructuras propias** | **CUMPLE** | La búsqueda de caminos utiliza un montículo binario propio sobre listas contiguas implementado por Kim (C3) sin `heapq`. No se usan tablas hash, `dict` ni `set` para indexar; se usan listas contiguas indexadas por `Sala.indice`. |
| **II. Determinismo** | **CUMPLE** | Todo desempate de ruta se realiza de forma estricta comparando el identificador numérico entero de las primeras salas vecinas (`id_v1 < id_v2`). El azar en enemigos errantes usa exclusivamente `partida.azar`. |
| **III. Separación MVC** | **CUMPLE** | La capacidad se implementa íntegramente en `modelo/juego/` y `bench/`. No se importa `controlador/` ni `vista/`. Las pruebas y benchmarks corren 100% en consola sin inicializar Pygame. |
| **IV. Ningún dato concreto** | **CUMPLE** | Los algoritmos operan sobre cualquier grafo generado sintéticamente o recibido de la API; ningún ID o costo está hardcodeado. |
| **V. Presupuesto solicitudes** | **CUMPLE** | No realiza solicitudes HTTP adicionales (la descarga del esqueleto es infraestructura previa). |
| **VI. Rendimiento medido** | **CUMPLE** | Se planifica `bench/bench_cazador.py` midiendo SC-004 (máximo y ciclos $>20\text{ ms}$), SC-005 (individual vs compartido) y SC-006 (reutilización vs recálculo), más la repetición de `bench_motor`. |
| **VII. Especificación antes de código** | **CUMPLE** | `spec.md` se confirmó y aclaró previo a la redacción de este plan y a cualquier modificación de código. |

---

## Project Structure

### Documentación de la capacidad
```text
specs/001-terreno-cazador/
├── spec.md              # Especificación funcional y de rendimiento
├── plan.md              # Este plan de implementación técnica
├── research.md          # Investigación de alternativas, pruebas matemáticas y contratos
├── data-model.md        # Modelo de entidades, campos, validaciones y ciclos de vida
└── tasks.md             # Desglose de tareas por historia de usuario
```

### Código fuente afectado
```text
modelo/juego/
├── sala.py              # Campo costo en Salida, Sala.indice contiguo
├── mapa.py              # Lectura de costo, asignación de indices, normalización de cazador
├── costos.py            # Preservación de costos base vigentes de P1
├── partida.py           # mover con costo, punto único de cambio de puertas (C2), caché de rutas
├── comportamiento.py    # Retorno de costo de acción, comportamiento cazador y desempate
├── motor_enemigos.py    # Programación de turno con costo retornado
├── agenda_eventos.py    # Validación de reprogramación de velocidad con costo alto
└── cazador.py           # (O módulo de apoyo) Lógica de cálculo compartido e invalidación

modelo/estructuras/
└── monticulo_min.py     # Montículo binario propio provisto por Kim (Contrato C3)

tests/
├── test_terreno_cazador.py  # Pruebas de aceptación automatizadas vinculadas a FR-001..FR-008
└── test_motor_base.py       # Pruebas de regresión del motor

bench/
├── bench_cazador.py     # Benchmarks de SC-004, SC-005 y SC-006
└── bench_motor.py       # Repetición de mediciones con carga de cazadores (§5.6)
```

---

## Plan de Trabajo por Bloques Técnicos

### Bloque 1: Costos de Movimiento (FR-001, FR-002)
1. **Modificación de Salida y Sala (`sala.py`)**:
   - `Salida.__init__`: Agregar parámetro `costo: int = 100`, con validación `costo >= 1`.
   - `Sala.conectar`: Agregar parámetro `costo: int = 100` y pasarlo a `Salida`. Al compartir la misma instancia de `Salida`, la simetría es absoluta ($costo(A \to B) == costo(B \to A)$).
   - `Sala.__init__`: Agregar campo `self.indice = None` para indexación contigua.
2. **Carga en Mapa (`mapa.py`)**:
   - Asignar `sala.indice = p` para cada sala en `esqueleto.ids`.
   - Leer `datos.get("costo", 100)` y validar `costo >= 1` al conectar salas.
   - Normalizar `ficha.get("comportamiento", "guardian").lower().strip()` para aceptar `"cazador"` sin problemas de mayúsculas ni tildes.
3. **Movimiento del Jugador (`partida.py`)**:
   - En `mover(direccion)`: sustituir `COSTO_MOVER` por `salida.costo`.
4. **Costo Real de Acción en Enemigos (`comportamiento.py` y `motor_enemigos.py`)**:
   - `resolver_turno(partida, enemigo, ahora) -> int`:
     - Retornar 100 al atacar o esperar.
     - Retornar `salida.costo` al desplazarse (errantes y rastreadores).
   - En `motor_enemigos.agendar_turno`: agendar siguiente turno con `ahora + costo_accion(costo_real, enemigo.velocidad)`.
5. **Verificación de Reprogramación de Velocidad (`agenda_eventos.py`)**:
   - Pruebas automatizadas de cambio de velocidad a mitad de cruce de salida costosa (ej. costo 300, velocidad 100 a 50 en $t=100$, evento reprogramado a $t=500$).

### Bloque 2: Puertas y Contrato C2 (FR-007, FR-008)
1. **Punto Central de Mutación de Puertas (`partida.py`)**:
   - Crear método `partida.cambiar_estado_puerta(salida, nuevo_estado)` que ejecuta `self.cambiar(salida, "estado", nuevo_estado)` y emite notificaciones a observadores registrados.
   - Modificar `partida.abrir()` y `efectos.programar_cierre()` para utilizar este método único.
2. **Registro de Notificaciones (Desacoplamiento)**:
   - Proveer lista de callbacks en `Partida` para que Kim (conocimiento) y Axel (línea de tiempo) se suscriban cuando implementen sus capacidades.
3. **Manejo de Pergamino de Retroceso**:
   - Durante `registro.deshacer()`, silenciar avisos individuales duplicados e invalidar completamente la caché de rutas al finalizar la reversión (`self.cache_rutas.invalidar_todo()`).

### Bloque 3: Cazador y Contrato C3 (FR-003, FR-004, FR-005, FR-006, FR-007)
1. **Acuerdo con Kim (Contrato C3)**:
   - Kim provee `modelo/estructuras/monticulo_min.py` y la función genérica `dijkstra_acotado`.
   - Se acordó la firma con filtro de salidas (`filtro_salida(salida) -> bool`), cota máxima de rango y arreglos reutilizables con marcas de búsqueda.
2. **Cálculo Compartido desde el Jugador**:
   - Realizar una única búsqueda Dijkstra desde la sala del jugador acotada a $R_{\max} = \max(\{c.rango\})$.
   - Cada cazador en sala $u$ consulta localmente sus salidas abiertas:
     $$d(u) = \min_{v \in vecinos(u)} (costo(u, v) + dist[v.indice])$$
   - Si $d(u) \le rango$, se mueve a la primera sala vecina $v$ que logra el costo mínimo.
   - Desempate: ante empates en el costo total $d(u)$, se elige la sala vecina con menor `v.id` entero.
3. **Arreglos con Marca de Búsqueda ($O(1)$ reinicio)**:
   - Mantener arreglos contiguos `dist` y `marca` de tamaño $N$.
   - Incrementar `token_busqueda += 1` en cada ejecución; solo los nodos con `marca[i] == token_busqueda` se consideran alcanzados.

### Bloque 4: Invalidación Reactiva y Mediciones (SC-001..SC-006)
1. **Criterios de Invalidación del Campo Compartido**:
   - El campo compartido es válido mientras el jugador no cambie de sala, $R_{\max}$ no aumente y ninguna puerta con al menos un extremo a distancia $\le R_{\max}$ cambie de estado.
   - Si una puerta lejana cambia (ambos extremos $> R_{\max}$), no se invalida la caché.
   - Si el jugador se mueve o una puerta relevante cambia, se invalida el campo y el siguiente cazador dispara el nuevo Dijkstra desde el jugador.
2. **Suite de Benchmarking (`bench/bench_cazador.py`)**:
   - **SC-004**: Medir tiempo de cada ciclo individual entre decisiones del jugador con 30 cazadores en cripta sintética grande; registrar tiempo máximo y conteo de ciclos $> 20\text{ ms}$.
   - **SC-005**: Comparar tiempo total por ciclo entre búsqueda individual y compartida para 1, 10, 30 y 100 cazadores con rangos pequeño y grande.
   - **SC-006**: Comparar reutilización vs. recálculo continuo en escenarios con puertas estables y con puertas inestables (autocierres continuos), verificando en cada paso equivalencia observable estricta.
   - **Revisión §5.6**: Repetir `bench_motor` con cazadores y costos variables, verificando que el heap de la agenda mantenga su rendimiento $O(\log E)$.
