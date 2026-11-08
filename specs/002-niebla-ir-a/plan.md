# Implementation Plan: Niebla de guerra, mapa conocido y viaje automático "ir a"

**Branch**: `002-niebla-ir-a` | **Date**: 2026-11-08 | **Spec**: [specs/002-niebla-ir-a/spec.md](spec.md)  
**Author**: Kim (Estructuras de Datos y Mapa Conocido)

---

## Summary

La capacidad 002 implementa el sistema de niebla de guerra de tres estados (Desconocida, Avistada, Explorada), el mapa conocido con memoria del estado de puertas observadas, el efecto de iluminación de la antorcha encendida al entrar a una sala, el viaje automático "ir a <sala>" con recálculo dinámico paso a paso sobre caminos explorados de costo mínimo y puertas recordadas abiertas, la protección estricta contra filtración de información en las interfaces de usuario (consola y Pygame), el formato de persistencia binaria versión 4 con rechazo explícito e inocuo de la versión 3, y la búsqueda de caminos mínimos compartida con el cazador de Mariano (Contrato C3).

El diseño técnico se apoya en arreglos contiguos de tamaño fijo $N$ indexados en $O(1)$ por `Sala.indice` (`estado_salas` y `memoria_puertas`), contadores de exploración y avistamiento en $O(1)$ para la línea de tiempo de Axel (C6), reversibilidad total de mutaciones a través del método único `partida.cambiar` integrado en `Registro` (C1), una cola de prioridad propia `MonticuloMin` con eliminación perezosa y desempate determinista sin `heapq` ni tablas hash, una función compartida y sin estado `dijkstra_acotado(origen, mapa, filtro_salida, cota_rango, ...)` alineada con Mariano (C3) donde cada llamador es dueño de sus propios arreglos de distancias, búsqueda inversa desde el destino hacia el jugador para resolver desempates deterministas por menor identificador de sala vecina, y descomposición de "ir a" en el controlador como orden compuesta fuera de `ORDENES_DE_PARTIDA`, asentando la intención como comentario y ejecutando movimientos individuales ordinarios en `partida.log` (C4).

---

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: `requests >= 2.31`, `pygame >= 2.5` (estrictamente sin librerías externas adicionales; `requirements.txt` intacto).  
**Storage**: Guardado binario en archivo propio (`VERSION_FORMATO = 4`), compatible con el esquema de empaquetado estructurado previo. Rechazo explícito con `ErrorFormato` / `ErrorCarga` ante archivos de versión 3. El campo `rango` del cazador se reconstruye desde el catálogo sin alterar el bloque de enemigos (C7).  
**Testing**: Pruebas de aceptación automatizadas ejecutadas con `python -m tests.test_niebla_ir_a` y suites de regresión con `python -m tests.<modulo>`.  
**Target Platform**: Multiplataforma (Windows, Linux, macOS). Pruebas y `--bench` 100% en consola sin inicializar Pygame.  
**Project Type**: Motor de juego por eventos con arquitectura MVC estricta.  
**Performance Goals**:
- Recálculo de ruta completa para un paso de "ir a" $< 5\text{ ms}$ en la cripta de referencia de 1000 salas (`SC-001`).
- Consulta de estado de sala y puerta recordada en tiempo constante $O(1)$ independiente de $N$ (`SC-002`).
- Exploración de sala proporcional exclusivamente al número de salidas de la sala (`SC-003`).
- Registro y reversión de cambios de conocimiento en $O(1)$ por sala/puerta (`SC-004`).
- Determinismo matemático de 100% en la selección de ruta de costo mínimo con desempate por menor ID (`SC-005`).  
**Constraints**:
- Prohibición estricta de `dict` o `set` como índice o caché, `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` o cualquier biblioteca de grafos o rutas (Constitución Principio I).
- Prohibido `sorted()` y `list.sort()` en ordenamientos evaluados.
- Ningún dato de una cripta concreta en el código (Principio IV).
- Separación MVC estricta: el modelo no importa controlador ni vista; la vista no filtra información secreta del modelo (Principio III).
- Determinismo total: azar exclusivo de `partida.azar` y empates resueltos por menor identificador numérico entero (Principio II).
- Toda mutación de estado pasa por los métodos únicos de `Partida` para su reversión limpia con pergaminos (C1).

---

## Constitution Check

| Principio | Estado | Justificación en este Plan |
|---|---|---|
| **I. Estructuras propias** | **CUMPLE** | Se implementa `MonticuloMin` desde cero sobre listas contiguas en `modelo/estructuras/monticulo_min.py` con eliminación perezosa. El conocimiento usa arreglos contiguos indexados por `Sala.indice`. No se usan tablas hash, `dict` ni `set` para indexar o mapear. |
| **II. Determinismo** | **CUMPLE** | Todo desempate en la búsqueda de caminos se resuelve deterministamente por el menor `id` numérico entero (`id_v1 < id_v2`). Las tuplas en el montículo `(distancia, id_sala)` y la evaluación de vecinas desde la búsqueda inversa garantizan determinismo estricto. |
| **III. Separación MVC** | **CUMPLE** | El modelo (`modelo/juego/conocimiento.py`, `partida.py`, `modelo/estructuras/`) no importa controlador ni vista. Las vistas (`vista_consola.py`, `vista_pygame.py`) solo leen el modelo y enmascaran salas no exploradas. `--bench` y `--replay` no crean la vista gráfica. |
| **IV. Ningún dato concreto** | **CUMPLE** | Todo opera sobre el esqueleto genérico recibido o criptas sintéticas generadas proceduralmente; ningún ID, costo ni nombre de sala está cableado en el código. |
| **V. Presupuesto solicitudes** | **CUMPLE** | No introduce llamadas de red adicionales. El ruteo y la niebla de guerra son enteramente locales. |
| **VI. Rendimiento medido** | **CUMPLE** | Se introduce `bench/bench_mapa_conocido.py` para medir SC-001..SC-004 y se repiten los benchmarks existentes (`cache`, `lista_ordenada`, `ordenamiento`, `guardado`). |
| **VII. Especificación antes de código** | **CUMPLE** | `spec.md` se ratificó y aclaró antes de redactar este plan y antes de generar las tareas de implementación. |

---

## Project Structure

### Documentación de la capacidad
```text
specs/002-niebla-ir-a/
├── spec.md              # Especificación funcional y de rendimiento
├── plan.md              # Este plan de implementación técnica corregido
├── research.md          # Investigación de alternativas, justificaciones y contratos
├── data-model.md        # Modelo de entidades, campos, validaciones y diagramas
├── quickstart.md        # Guía rápida de ejecución y validación
└── contracts/           # Contratos formales de interfaces
    ├── contrato_c3_dijkstra.md     # Contrato C3 con Mariano (MonticuloMin y Dijkstra acotado unificado)
    ├── contrato_c2_puertas.md      # Contrato C2 de puertas y actualización de memoria real
    ├── contrato_ir_a.md            # Contrato C4 de viaje automático, controlador y bitácora
    └── contrato_guardado_v4.md     # Contrato C7 de formato binario v4 y compatibilidad cazador
```

### Código fuente afectado
```text
modelo/estructuras/
├── monticulo_min.py     # Montículo binario propio de mínimos con eliminación perezosa (C3)
└── dijkstra.py          # Función compartida dijkstra_acotado sin estado con marcas de búsqueda (C3)

modelo/juego/
├── conocimiento.py      # Entidad ConocimientoMapa (arreglos contiguos, contadores O(1) para C6)
├── partida.py           # Integración de conocimiento, mutación reversible con cambiar() (C1), salidas_visibles()
├── sala.py              # Validación de Sala.indice y Salida.costo
├── efectos.py           # Revelado de vecinas por antorcha encendida al entrar a sala
└── registro.py          # Soporte de mutación indexada de listas en Registro.cambiar

controlador/
├── orden.py             # Definición de Orden(IR_A, destino) fuera de ORDENES_DE_PARTIDA (C4)
├── controlador.py       # Ejecución paso a paso de IR_A, parada reactiva y aviso descriptivo
└── aplicacion.py        # Despachador de comentarios para bitácora de replay

modelo/datos/
├── bitacora_partida.py  # Método anotar_comentario(# ...) y omisión de comentarios en leer_log (C4)
└── guardado_binario.py  # Formato versión 4 con estados de salas y puertas; rechazo de versión 3 (C7)

vista/
├── vista_consola.py     # Ocultamiento de ID/nombre en salas avistadas y comando 'mapa'
└── vista_pygame.py      # Corrección de _dibujar_puerta para no filtrar IDs de salas avistadas

bench/
└── bench_mapa_conocido.py # Mediciones oficiales de SC-001, SC-002, SC-003 y SC-004

main.py                  # Integración del benchmark 'mapa_conocido' en BENCHES

tests/
└── test_niebla_ir_a.py  # Suite completa de aceptación vinculada a FR-001..FR-024
```

---

## Plan de Trabajo por Bloques Técnicos

### Bloque 1: Conocimiento en Arreglos Indexados por `Sala.indice`, Mutaciones C1 y Resumen C6
1. **Entidad `ConocimientoMapa` (`modelo/juego/conocimiento.py`)**:
   - Arreglos contiguos preasignados: `self.estado_salas = [ESTADO_DESCONOCIDA] * N` y `self.memoria_puertas = [PUERTA_DESCONOCIDA] * (4 * N)`.
   - Contadores $O(1)$ para la línea de tiempo de Axel (C6): `self.num_exploradas: int = 0` y `self.num_avistadas: int = 0`.
   - Método `resumen() -> tuple[int, int]`: retorna `(self.num_exploradas, self.num_avistadas)` en tiempo constante $O(1)$.
   - Mapeo directo $O(1)$: `pos_puerta = sala.indice * 4 + dir_idx`.
   - Métodos de consulta $O(1)$: `es_explorada(sala)`, `es_avistada(sala)`, `estado_sala(sala)`, `puerta_recordada(sala, dir_idx)`.
2. **Soporte de Mutación Indexada en `Registro` y Principio C1 (`modelo/juego/registro.py`, `partida.py`)**:
   - En `Registro.cambiar(objeto, campo, valor)`: si `isinstance(objeto, list)` y `isinstance(campo, int)`, guardar el valor anterior `objeto[campo]`, mutar `objeto[campo] = valor` y apilar en el grupo abierto el lambda inverso `lambda: objeto.__setitem__(campo, anterior)`.
   - Toda mutación de conocimiento pasa por `partida.cambiar(...)` (C1):
     - `partida.cambiar(self.conocimiento.estado_salas, sala.indice, ESTADO_EXPLORADA)`.
     - `partida.cambiar(self.conocimiento, "num_exploradas", self.conocimiento.num_exploradas + 1)`.
   - **Regla estricta contra conteos duplicados**: Al explorar una sala $u$, sus vecinas directas solo incrementan `num_avistadas` si previamente se encontraban en `ESTADO_DESCONOCIDA`.
   - Reversibilidad total con pergamino (`deshacer_ultimo()`).
3. **Inicialización y Visión en `Partida` (`modelo/juego/partida.py`)**:
   - En `iniciar()` (instante 0): marcar `sala_inicial` como Explorada (`num_exploradas = 1`). Por cada salida hacia vecina desconocida, marcarla como Avistada (`num_avistadas += 1`) y registrar en `memoria_puertas` el estado actual de la puerta observada.
   - En `_entrar(destino)`: actualizar la visión de la sala actual y sus vecinas.
   - En cada acción del jugador (`_accion`): sincronizar la memoria de puertas de todas las salidas de la sala actual (FR-006).
   - Suscribir `ConocimientoMapa` al despachador de puertas (Contrato C2): cuando `cambiar_estado_puerta` emite aviso a `_observadores_puertas`, si el jugador se encuentra en `salida.sala_a` o `salida.sala_b`, actualizar la memoria.
4. **Pruebas de Aceptación vinculadas**:
   - `test_FR001_clasificacion_estados_conocimiento`
   - `test_FR002_estado_inicial_instante_cero`
   - `test_FR003_sala_explorada_revela_nombre_y_conexiones`
   - `test_FR004_sala_avistada_no_revela_id_ni_nombre`
   - `test_FR005_sala_desconocida_oculta_sin_ruteo`
   - `test_FR006_actualizacion_memoria_puertas_en_acciones`
   - `test_FR012_reversion_conocimiento_con_pergamino`
   - `test_FR013_registro_eventos_conocimiento`

---

### Bloque 2: Búsqueda de Rutas Compartida en `modelo/estructuras/` (Contrato C3)
1. **Montículo de Mínimos con Eliminación Perezosa (`modelo/estructuras/monticulo_min.py`)**:
   - Clase `MonticuloMin` sobre lista contigua.
   - Inserción y extracción en $O(\log K)$.
   - Desempate determinista natural por menor `id_sala` mediante tuplas `(distancia, id_sala)`.
   - Eliminación perezosa: los llamadores descartan tuplas obsoletas si `dist > dist[sala.indice]` sin requerir `decrease_key` ni tablas hash prohibidas.
2. **Función Compartida `dijkstra_acotado` (`modelo/estructuras/dijkstra.py`)**:
   - Firma unificada exacta con Capacidad 001:
     ```python
     def dijkstra_acotado(origen, mapa, filtro_salida, cota_rango=None, token_busqueda=1, arreglo_dist=None, arreglo_marca=None) -> tuple[list[int], list[int]]:
     ```
   - `filtro_salida: Callable[[Salida], bool]` recibe **únicamente la instancia de `Salida`**.
   - Algoritmo completamente stateless.
   - Marcas de búsqueda: un nodo no visitado tiene `arreglo_marca[v.indice] != token_busqueda`, permitiendo reinicio $O(1)$ sin reinicializar arreglos.
3. **Administración de Arreglos por Llamador**:
   - Mariano (cazador) mantiene su propio par `self._dist_cazador`, `self._marca_cazador`, `self._token_cazador`.
   - Kim ("ir a") mantiene su propio par `self._dist_navegacion`, `self._marca_navegacion`, `self._token_navegacion`.
   - Cero interferencias en la memoria o en la caché de rutas del cazador entre búsquedas del mismo ciclo.
4. **Pruebas de Aceptación vinculadas**:
   - `test_C3_monticulo_min_operaciones_y_desempate`
   - `test_C3_dijkstra_acotado_determinismo_y_marcas`
   - `test_C3_llamadores_independientes_sin_interferencia`

---

### Bloque 3: Viaje Automático "ir a", Controlador y Bitácora (C4, FR-014..FR-023)
1. **Búsqueda Inversa desde el Destino**:
   - Para calcular el primer paso desde `sala_actual` hacia `sala_destino`, se ejecuta `dijkstra_acotado` con `origen = sala_destino` y `filtro_salida` según `ConocimientoMapa` (`es_explorada(salida.sala_a) and es_explorada(salida.sala_b) and puerta_recordada_abierta(salida)`).
   - El jugador en `sala_actual` evalúa los candidatos vecinos $v$:
     $$C(v) = salida.costo + dist[v.indice]$$
     Selecciona el que minimiza $C(v)$, desempatando deterministamente por $\min(v.id)$ (FR-016).
2. **Ampliación de `Orden` y Clasificación Estricta (C4) (`controlador/orden.py`)**:
   - Añadir `IR_A = "ir_a"`.
   - **`IR_A` NO pertenece a `ORDENES_DE_PARTIDA`**. `Orden(IR_A, destino).es_de_partida()` retorna `False`.
   - No se escribe en el log como orden atómica ni se envía a `a_texto()`.
3. **Ejecución Paso a Paso en `Controlador` (`controlador/controlador.py`)**:
   - Método `_ejecutar_ir_a(orden)` dentro de las órdenes compuestas:
     - Validación preliminar ($O(1)$): destino explorado, distinto a la sala actual, ruta inicial factible.
     - Registro de comentario en la bitácora mediante `Aplicacion.registrar_comentario(f"ir a {id_destino}")`.
     - Bucle paso a paso:
       - Recalcular distancias desde `destino` con conocimiento vigente.
       - Si llegó al destino $\to$ detener con mensaje de éxito (FR-019).
       - Seleccionar dirección óptima $D$.
       - Ejecutar orden ordinaria `self._ejecutar_de_partida(Orden(MOVER, D))`.
       - Verificar interrupciones inmediatas:
         - Presencia de enemigos vivos en la sala $\to$ detener ("presencia de enemigos").
         - Daño sufrido por el jugador (trampa, veneno) $\to$ detener ("has recibido daño").
         - Puerta cerrada descubierta o bloqueo $\to$ detener ("ruta bloqueada").
       - Notificar el motivo descriptivo exacto mediante `self._avisar(motivo)` (FR-020).
4. **Bitácora y Replay (`modelo/datos/bitacora_partida.py`)**:
   - Incorporar en `BitacoraPartida` el método público:
     ```python
     def anotar_comentario(self, texto: str) -> None:
         if self._archivo is not None:
             self._escribir("# " + _limpio(texto))
     ```
   - En `leer_log(ruta)`: omitir líneas que inician con `#` o vacías. Replay ejecuta deterministamente los movimientos individuales `mover <dir>`.
5. **Pruebas de Aceptación vinculadas**:
   - `test_FR014_ir_a_destino_no_explorado_rechazado`
   - `test_FR015_ir_a_camino_costo_minimo`
   - `test_FR016_desempate_menor_id_en_vecina`
   - `test_FR017_pasos_individuales_avanzan_reloj`
   - `test_FR018_recalculo_ruta_en_cada_paso`
   - `test_FR019_interrupciones_viaje_automatico`
   - `test_FR020_mensajes_descriptivos_detencion`
   - `test_FR021_ir_a_nunca_abre_puertas_automaticamente`
   - `test_FR022_log_asienta_pasos_y_comentario`
   - `test_FR023_reversion_pergamino_deshace_solo_ultimo_paso`

---

### Bloque 4: Mecánica de la Antorcha Encendida (FR-007, FR-008)
1. **Revelado de Vecinas al Entrar (`modelo/juego/efectos.py`, `partida.py`)**:
   - Al entrar a una sala (`_entrar`): si `jugador.antorcha_encendida` es `True`:
     - Todas las salas vecinas directas conectadas por cualquier salida (abierta o cerrada) cambian al estado `ESTADO_EXPLORADA`.
     - Se revelan de ellas sus salidas y costos.
     - **Invariante de seguridad**: No se cargan actores ni objetos de esas salas, no se activan enemigos (permanecen dormidos) ni trampas en esas vecinas (FR-008).
2. **Reversión con Pergamino**:
   - Como los cambios de estado y contadores pasan por `partida.cambiar(...)` dentro del grupo de la acción de movimiento, un pergamino revierte las salas reveladas por la antorcha a su estado anterior (`ESTADO_AVISTADA` o `ESTADO_DESCONOCIDA`) y restaura los contadores `num_exploradas` y `num_avistadas`.
3. **Pruebas de Aceptación vinculadas**:
   - `test_FR007_antorcha_enciende_vecinas_sin_activar_contenido`
   - `test_FR008_antorcha_no_activa_trampas_ni_enemigos_en_vecinas`

---

### Bloque 5: Protección de Información en las Vistas (FR-009, FR-010)
1. **Filtrado en el Modelo para la Vista (`partida.py`)**:
   - Modificar `salidas_visibles()` para que retorne tuplas de información que respeten el conocimiento del jugador:
     `(direccion, estado_recordado, id_vecino if explorada else None, llave if observada else None, costo)`
2. **Ajuste en `vista/vista_consola.py`**:
   - En `_texto_salidas`: si el vecino no está explorado, emitir:
     `f"{direccion} -> desconocida (costo {costo}, {detalle})"`
     sin revelar el ID numérico ni el nombre.
   - En comando `mapa`: mostrar únicamente salas exploradas con sus puertas recordadas y salidas hacia desconocidas.
3. **Ajuste en `vista/vista_pygame.py`**:
   - En `_dibujar_puerta`: si el vecino no está explorado (`id_vecino is None`), dibujar etiqueta `f"{direccion}: desconocida (costo {costo})"` en lugar de `f"{direccion}: sala {id_vecino}"`.
4. **Pruebas de Aceptación vinculadas**:
   - `test_FR009_comando_ver_mapa_conocido`
   - `test_FR010_vistas_no_filtran_ids_de_salas_avistadas`

---

### Bloque 6: Guardado Binario Versión 4, Incompatibilidad v3 y Cazadores C7 (FR-024)
1. **Actualización de Versión (`modelo/datos/guardado_binario.py`)**:
   - Establecer `VERSION_FORMATO = 4`.
2. **Serialización del Conocimiento**:
   - Añadir en el bloque general: $N$ bytes para `estado_salas` y las entradas activas de `memoria_puertas`.
   - En deserialización: reconstruir fielmente `Partida.conocimiento` y sus contadores $O(1)$.
3. **Coordinación C7 sobre `Enemigo.rango`**:
   - El atributo `rango` del cazador es estático de ficha de catálogo y **NO se almacena en el bloque binario de enemigos** de `SalaGuardada`.
   - Se mantiene intacta la estructura binaria de `_empaquetar_sala` y `_desempaquetar_sala`. Al cargar, `mapa.incorporar` asigna `rango = ficha.get("rango", 0)` desde el catálogo local.
4. **Rechazo Explícito de Versión 3 (FR-024)**:
   - En `_leer_encabezado`: si `version != VERSION_FORMATO`:
     - Si `version == 3`: lanzar `ErrorFormato("versión de formato 3 incompatible (se esperaba 4): formato previo sin soporte de niebla de guerra")`.
     - Si otra versión: lanzar mensaje estándar de versión incompatible.
   - En `persistencia_partida.py`: capturar y emitir `ErrorCarga`, manteniendo la partida en curso intacta.
5. **Pruebas de Aceptación vinculadas**:
   - `test_FR024_guardado_v3_reporta_incompatibilidad_explicta`
   - `test_FR024_guardado_v4_serializa_y_restaura_conocimiento`

---

### Bloque 7: Suite de Benchmarks y Repeticiones (SC-001..SC-004)
1. **Nuevo Módulo de Benchmarking (`bench/bench_mapa_conocido.py`)**:
   - **SC-001**: Medición del tiempo de recálculo de Dijkstra acotado sobre el grafo completo de 1000 salas. Meta: $< 5.0\text{ ms}$.
   - **SC-002**: Medición de consultas $O(1)$ a `estado_salas`, `memoria_puertas` y contadores `resumen()` con $10^6$ operaciones sobre criptas de 10, 100 y 1000 salas.
   - **SC-003**: Medición del tiempo de exploración por entrada y por antorcha.
   - **SC-004**: Medición del tiempo de reversión con pergamino sobre cambios de conocimiento.
2. **Integración en `main.py`**:
   - Agregar `("mapa_conocido", "bench_mapa_conocido.py")` a `BENCHES`.
3. **Repetición de Benchmarks de Regresión**:
   - Ejecutar y documentar `cache`, `lista_ordenada`, `ordenamiento` y `guardado`.

---

## Análisis de Complejidad Temporal y Espacial

| Componente / Operación | Complejidad Temporal | Complejidad Espacial | Justificación |
|---|---|---|---|
| **Consulta de estado de sala** | $O(1)$ | $O(1)$ | Indexación directa por entero en arreglo contiguo `estado_salas[sala.indice]`. |
| **Consulta de puerta recordada** | $O(1)$ | $O(1)$ | Acceso aritmético directo `memoria_puertas[sala.indice * 4 + dir_idx]`. |
| **Resumen para línea de tiempo (C6)** | $O(1)$ | $O(1)$ | Lectura de atributos contadores `num_exploradas` y `num_avistadas`. |
| **Actualización de visión (sin antorcha)** | $O(\text{salidas}) = O(1)$ | $O(1)$ | A lo sumo 4 salidas evaluadas y actualizadas en los arreglos. |
| **Actualización de visión (con antorcha)** | $O(\sum \text{salidas}_{\text{vecinas}}) \le 16$ | $O(1)$ | Revela como exploradas hasta 4 vecinas y actualiza sus salidas en tiempo constante acotado. |
| **Reversión con pergamino (C1)** | $O(1)$ por cambio | $O(1)$ | Ejecución directa del lambda inverso apilado en `Registro`. |
| **MonticuloMin: insertar / extraer** | $O(\log K)$ | $O(K)$ | Operaciones sobre árbol binario contiguo sin reindexación. |
| **Dijkstra acotado ("ir a" y cazador)** | $O((V + E) \log V)$ | $O(V)$ | Relajación de aristas transitables con eliminación perezosa y marcas $O(1)$. |
| **Paso individual de "ir a"** | $O((V_E + E_E) \log V_E)$ | $O(V_E)$ | Acotado exclusivamente a las salas y aristas en estado `Explorada` ($V_E \le V$). |
| **Serialización / Deserialización v4** | $O(N + P)$ | $O(N + P)$ | Lectura y escritura contigua de $N$ bytes de estados y $P$ puertas recordadas. |

---

## Matriz de Módulos Afectados

| Módulo | Tipo de Cambio | Responsabilidad y Modificación |
|---|---|---|
| `modelo/estructuras/monticulo_min.py` | **NUEVO** | Montículo binario propio de mínimos con eliminación perezosa (C3). |
| `modelo/estructuras/dijkstra.py` | **NUEVO** | Función compartida `dijkstra_acotado(origen, mapa, filtro_salida, ...)` (C3). |
| `modelo/juego/conocimiento.py` | **NUEVO** | Clase `ConocimientoMapa` con arreglos contiguos y contadores $O(1)$ para C6. |
| `modelo/juego/partida.py` | Modificado | Atributo `conocimiento`, actualización en `_entrar` y `_accion`, filtro en `salidas_visibles` (C1). |
| `modelo/juego/efectos.py` | Modificado | Revelado de salas vecinas al cruzar sala con antorcha encendida. |
| `modelo/juego/registro.py` | Modificado | Soporte de mutación indexada de arreglos en `Registro.cambiar`. |
| `controlador/orden.py` | Modificado | Nueva orden `IR_A` (fuera de `ORDENES_DE_PARTIDA`, C4). |
| `controlador/controlador.py` | Modificado | Bucle paso a paso de `_ejecutar_ir_a`, detención reactiva y aviso descriptivo. |
| `controlador/aplicacion.py` | Modificado | Método `registrar_comentario` para delegar en `BitacoraPartida`. |
| `modelo/datos/bitacora_partida.py` | Modificado | Método `anotar_comentario(# ...)` y omisión de comentarios en `leer_log` (C4). |
| `modelo/datos/guardado_binario.py` | Modificado | Formato v4 con datos de niebla; rechazo explícito con `ErrorFormato` a v3; rango cazador desde catálogo (C7). |
| `vista/vista_consola.py` | Modificado | Ocultar ID y nombre en salas avistadas; comando `mapa`. |
| `vista/vista_pygame.py` | Modificado | Corrección en `_dibujar_puerta` para no dibujar `id_vecino` en salas avistadas. |
| `bench/bench_mapa_conocido.py` | **NUEVO** | Benchmark oficial de niebla de guerra, consultas $O(1)$ y Dijkstra acotado. |
| `main.py` | Modificado | Registro de `mapa_conocido` en `BENCHES`. |
| `tests/test_niebla_ir_a.py` | **NUEVO** | Pruebas de aceptación automatizadas vinculadas a FR-001..FR-024. |

---

## Matriz de Riesgos y Mitigaciones

| Riesgo Identificado | Impacto | Probabilidad | Mitigación Técnica |
|---|---|---|---|
| **Colisión de búsquedas en el mismo ciclo** | Alto | Media | Cada llamador (Mariano y Kim) posee y administra sus propios arreglos `dist` y `marca`, garantizando total aislamiento y preservando la validez de la caché de cazador. |
| **Uso accidental de estructuras prohibidas (`dict`, `set`, `heapq`)** | Crítico | Baja | Se prohíben explícitamente en el diseño; `MonticuloMin` se programa a mano sobre `list` y el conocimiento usa indexación directa por enteros en arreglos preasignados. |
| **Fuga de datos no explorados en la interfaz** | Alto | Media | `partida.salidas_visibles()` entrega información filtrada (`id_vecino` como `None` si la vecina solo está avistada), y las vistas muestran explícitamente "desconocida". |
| **Corrupción de partidas guardadas previas (v3)** | Medio | Baja | `guardado_binario.py` verifica estrictamente la versión del encabezado y lanza `ErrorFormato` descriptivo, impidiendo lecturas parciales o sobreescrituras accidentales. |
| **Ciclo infinito en "ir a" por cambio de entorno** | Medio | Baja | El destino debe estar explorado, la ruta se recalcula antes de cada paso, cada paso consume tiempo en el reloj virtual y cualquier obstáculo detiene el viaje de inmediato. |
| **Desincronización en reversión con pergamino** | Alto | Baja | Todo cambio en los arreglos de conocimiento y contadores pasa por `partida.cambiar`, registrando el inverso exacto en `Registro` para restaurarse limpiamente en marcha atrás. |
