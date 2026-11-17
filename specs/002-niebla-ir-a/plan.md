# Implementation Plan: Niebla de guerra, mapa conocido y viaje automático "ir a"

## Estado verificado en la integracion 002 + 003 + 004

Base revisada: `75cc63eae09b3c7c85d388f44457086ba443da8a`, rama
`integracion-002-003` (2026-11-13). Implementacion funcional de conocimiento,
antorcha, consola/Pygame, viaje compuesto, FR-010 de 004, codec v4 y T046.
La auditoria ejecuto 39 modulos: 35 aprobados y cuatro fallidos, con 13 fallos
conocidos ajenos al benchmark: nueve interfaces historicas, dos replay `hasta`,
uno de eventos simultaneos y un falso positivo de busqueda textual GUI.
No se declara completa 004 ni aprobada SC-001. La referencia oficial no esta
identificada; T030 carece de linea base equivalente. Evidencia y mediciones:
[DECISIONES.md](DECISIONES.md#trazabilidad-y-evidencia-de-la-integracion).

Las menciones C1 de 002 (mutacion indexada) y C1 de 004 (captura historica)
son contratos distintos que coexisten. FR-010 de 002 significa privacidad;
FR-010 de 004 significa conservar observaciones permanentes al deshacer.


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
- Recálculo de ruta completa para un paso de "ir a" $< 5\text{ ms}$ en la cripta oficial de referencia (`SC-001`), todavía no identificada; no se presupone que tenga 1000 salas.
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
└── bench_mapa_conocido.py # Instrumentación sintética SC-001..SC-004; aceptación oficial pendiente

main.py                  # Integración del benchmark 'mapa_conocido' en BENCHES

tests/
└── test_niebla_ir_a.py  # Pruebas C3; aceptacion distribuida en suites de la matriz DECISIONES.md
```

---

## Plan de Trabajo por Bloques Técnicos

### Bloque 1: Conocimiento en Arreglos Indexados por `Sala.indice`, Mutaciones C1 y Resumen C6

**Aclaración confirmada T003/T004**: constructor
`ConocimientoMapa(n, salas_por_indice, mapa)`, conservando referencias. Consultas
por Sala e índices O(1); por ID O(log N) usando Mapa. El módulo solo almacena y
consulta; la integracion existente en Partida actualiza ambos extremos de una
puerta observada mediante `partida.cambiar`, sin modificar el conocimiento de las
salas conectadas. Véanse las decisiones y límites de visibilidad en `data-model.md`.
Pruebas unitarias: `python -m tests.test_conocimiento`. La aceptación integral de
T004 esta cubierta por test_conocimiento y test_conocimiento_partida; ver tasks.md.

1. **Entidad `ConocimientoMapa` (`modelo/juego/conocimiento.py`)**:
   - Arreglos contiguos preasignados: `self.estado_salas = [ESTADO_DESCONOCIDA] * N` y `self.memoria_puertas = [PUERTA_DESCONOCIDA] * (4 * N)`.
   - Contadores $O(1)$ para la línea de tiempo de Axel (C6): `self.num_exploradas: int = 0` y `self.num_avistadas: int = 0`.
   - Método `resumen() -> tuple[int, int]`: retorna `(self.num_exploradas, self.num_avistadas)` en tiempo constante $O(1)$.
   - Mapeo directo $O(1)$: `pos_puerta = sala.indice * 4 + dir_idx`.
   - Métodos de consulta $O(1)$: `es_explorada(sala)`, `es_avistada(sala)`, `estado_sala(sala)`, `puerta_recordada(sala, dir_idx)`.
2. **Soporte de Mutación Indexada en `Registro` y Principio C1 (`modelo/juego/registro.py`, `partida.py`)**:
   - En `Registro.cambiar(objeto, campo, valor)`: si `isinstance(objeto, list)` y `isinstance(campo, int)`, guardar el valor anterior, capturar C1 historico antes de escribir y preparar el inverso; solo memoria_puertas usa inversos condicionados por generacion. Fuera de grupo incrementa su generacion, incluso sin cambio de valor, antes de escribir.
   - Toda mutación de conocimiento pasa por `partida.cambiar(...)` (C1):
     - `partida.cambiar(self.conocimiento.estado_salas, sala.indice, ESTADO_EXPLORADA)`.
     - `partida.cambiar(self.conocimiento, "num_exploradas", self.conocimiento.num_exploradas + 1)`.
   - **Regla estricta contra conteos duplicados**: Al explorar una sala $u$, sus vecinas directas solo incrementan `num_avistadas` si previamente se encontraban en `ESTADO_DESCONOCIDA`.
   - Reversion por grupo con pergamino; preservar observaciones permanentes posteriores mediante FR-010 de 004.
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
     - Validacion preliminar: ID por busqueda O(log N) y ruta por Dijkstra; no es O(1) para el proceso completo.
     - Tras callbacks/cancelacion, emitir una marca por observacion exterior, justo antes de observar; no una unica marca al inicio.
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
   - leer_log ordinario omite comentarios; el lector de reconstruccion 004 conserva marcas IR_A y repite solo observaciones, junto con movimientos atomicos.
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
   - Codec decodifica fotografia; T045/T046 reconstruye por replay y compara arreglos y contadores por recuento O(N) dentro del contexto, sin reemplazar listas ni inversos.
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
   - **SC-001**: Medición del tiempo de recálculo de Dijkstra acotado sobre el grafo completo de 1000 salas. Meta oficial: $< 5.0\text{ ms}$ solo en la cripta de referencia, aun no identificada; la cuadricula de 1000 salas es sintetica.
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
| **Paso individual de "ir a"** | $O((V_r + E_r) \log(V_r+1))$ | $O(N + E_r)$ | Planificador conserva distancias/marcas de N salas; Dijkstra usa monticulo temporal O(E_r+1) con entradas perezosas. V_r/E_r son el componente conocido alcanzable. La seleccion de vecino agrega espacio O(1); no se atribuye O(V_E) al espacio total. |
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
| `bench/bench_mapa_conocido.py` | **NUEVO** | Adaptador del benchmark sintetico de conocimiento y rutas; no es una certificacion oficial y SC-001 sigue pendiente. |
| `main.py` | Modificado | Registro de `mapa_conocido` en `BENCHES`. |
| `tests/test_niebla_ir_a.py` | **NUEVO** | Pruebas C3. Para FR-001..FR-024, consultar la matriz y suites distribuidas en DECISIONES.md. |

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

## Ajustes de ensamblado comprobados

Orden reside en modelo/juego/orden.py y controlador/orden.py lo reexporta.
PlanificadorRutas posee arreglos y tokens de navegacion; Controlador lo recrea
al cambiar la partida. La captura historica se integra mediante Registro y
resumen_historico, no mediante un hipotetico notificar_conocimiento(resumen).
Las marcas IR_A se emiten despues de callbacks/cancelacion e inmediatamente
antes de cada observacion exterior. La politica vigente se detalla en C4.
El adaptador bench/bench_mapa_conocido.py llama main([]) del benchmark existente;
la entrada BENCHES esta integrada y probada. SC-001 y comparacion T030 pendientes.
Los nombres de pruebas propuestos en este plan son historicos; la matriz de
DECISIONES.md y tasks.md identifica los modulos realmente ejecutados.

## Ampliacion US5: mapa dibujado (FR-025..FR-038, SC-006..SC-008)

Fecha: 2026-11-17. La spec confirmada es la fuente normativa; no se modifica.
Se conserva el diseño anterior para historia, persistencia y rutas. Esta sección
planifica únicamente el mapa dibujado y sus pruebas/documentos.

### Contrato y separación MVC

- `modelo/juego/mapa_dibujado.py`: registros de entrada de conocimiento, casillas,
  conexiones y resultado; función pura `calcular_layout(conocidas, actual)`.
  No recibe Partida, mapa completo, actores ni puertas vivas. No imprime.
- `ConocimientoMapa` conserva exactamente el almacenamiento de f600fdd: lista simple
  de estados, sin subclase, enlaces ni directorio derivado. Esta revisión autorizada
  retira el diseño anterior para evitar ampliar la lógica de escrituras e inversos
  de una estructura compartida por todas las mecánicas del juego.
- `Partida.mapa_dibujado()`: obtiene una fotografía compacta de exploradas y sus
  salidas conocidas. Al abrir, la foto recorre una sola vez la lista estado_salas;
  solo accede al objeto de sala cuando el estado es EXPLORADA. No consulta topología,
  ids, nombres o contenido de salas desconocidas para filtrar o ubicar casillas.
  Deduplica destinos por identidad/índice, sin consultar ids ni nombres de avistadas.
  Usa ListaOrdenada propia construida en bloque para traducir índices a referencias
  compactas. El índice solo identifica extremos: nunca decide el orden visible.
- Salidas públicas: casillas `(x,y,estado,id,nombre,es_jugador)`; avistadas con id y
  nombre None. Conexiones con referencias compactas a casillas, dirección, costo,
  memoria de puerta y llave ya expuesta. Conteos de exploradas y avistadas.
- Controlador MAPA suministra esta foto a la vista. `mapa_conocido()` y
  `lineas_mapa_conocido()` conservan su contrato para historia y clientes anteriores.
- Consola dibuja ASCII por bloques horizontales y tabla de salidas, sin truncamiento.
  Pygame solo transforma coordenadas para encuadrar, desplazar y ampliar; recibe un
  layout ya calculado una vez. Usa primitivas y las fuentes/colores existentes.

### Recorrido y colisiones

1. Ordenar únicamente las exploradas por id con el ordenamiento propio. Preparar
   el orden de avistadas recorriendo esas exploradas y sus salidas N,S,E,O; la primera
   salida conocida que revele una avistada fija su referencia anónima y origen.
2. BFS desde la actual solo por exploradas. Desplazamientos N=(0,-1), S=(0,1),
   E=(1,0), O=(-1,0). Cada nivel procesa exploradas por menor id y cada sala sus
   salidas N,S,E,O. Una cola es almacenamiento contiguo con cursor, sin quitar al
   principio. Para componentes desconectadas, comenzar por la menor id pendiente,
   separando sus coordenadas de las anteriores sin inventar conexiones.
3. Resolver posiciones reclamadas en prioridad global: exploradas por menor id,
   luego avistadas por su orden de descubrimiento. Así una reserva posterior de menor
   prioridad nunca desplaza a otra de mayor prioridad. Las avistadas se proponen
   adyacentes a su primera salida reveladora, desde la posición final de su origen.
4. Para una posición ocupada, buscar anillos de distancia Manhattan r=1,2,...
   respecto a la reclamada. Dentro de cada anillo, probar primero los ejes N,S,E,O:
   (0,-r),(0,r),(r,0),(-r,0). Después, para a=1..r-1, probar
   (a,-(r-a)), (a,r-a), (-a,r-a), (-a,-(r-a)). Ese orden incluye todo el anillo,
   no repite casillas y nunca depende de ids ocultos. Conservar todos los enlaces;
   marcar como fuera de cuadrícula los que no coincidan con el desplazamiento de
   su dirección, aunque accidentalmente terminen adyacentes en otra orientación.
5. Ocupación: índice propio balanceado sobre arreglos contiguos de nodos, clave
   (x,y), con búsqueda/inserción O(log K). Alternativa: ListaOrdenada propia, cuya
   inserción desplaza O(K) elementos. Medir ambas sin introducir dict/set.

### Complejidad y mediciones previstas

K = exploradas + avistadas; E = salidas conocidas; C = posiciones candidatas
examinadas al resolver colisiones; N = longitud de estado_salas. La revisión
solicitada barre N estados escalares una vez por apertura, con tiempo O(N).
Después de filtrar, solo se leen objetos de salas exploradas y sus salidas conocidas;
el dominio de la foto compacta y del layout es proporcional a K+E. La BFS cuesta
O(K+E), además del ordenamiento de niveles. Foto: O(N + (K+E) log K).
Con índice balanceado, apertura: O(N + (K+E+C) log K) tiempo; layout puro:
O((K+E+C) log K). Ambos usan O(K+E) espacio temporal. Los anillos
pueden elevar C en criptas inconsistentes; no se promete O(K+E) estricto para esas
colisiones ni se oculta el costo de ordenar. No hay enlaces persistentes adicionales.
El cálculo nunca reserva arreglos nuevos de tamaño N ni lee objetos desconocidos.
El barrido de estados no se repite por fotograma. Esta decisión conserva el aislamiento
de información y las reglas de dibujo, pero retira la independencia temporal de N
que proponía el directorio anterior; no se declara esa propiedad para la apertura.
La spec no se cambia para ocultar esta limitación del barrido expresamente solicitado.

Medir tiempo mediano sin trazador y pico de memoria en corridas separadas con
10,100,1000,5000 salas conocidas sintéticas; comparar índice balanceado y
ListaOrdenada con la misma entrada, función y salida. Registrar también candidatos
para interpretar colisiones; distinguir layout puro de construcción de la foto.
Comando: `venv\Scripts\python.exe main.py --bench mapa_conocido`.

### Validación y constitución

Primero crear `tests/test_mapa_dibujado_002.py` y ejecutar en rojo. Cubrir los 17
escenarios US5, en especial ids ocultos distintos (incluido cambio de índices),
entorno desconocido distinto, colisiones entre las tres combinaciones de estados,
puertas sin observar/desactualizadas, antorcha, pergamino y ausencia de efectos.
Comparar fotos completas y salidas ASCII; probar GUI con eventos y superficie real
bajo SDL_VIDEODRIVER=dummy, sin importar la biblioteca gráfica fuera de las pruebas
que la necesitan. Ejecutar las 43 suites con el mismo script de auditoría,
cada módulo en un proceso independiente desde una carpeta temporal externa y con
bytecode deshabilitado. No modificar spec, archivos de guardado ni log. Verificar
que conocimiento.py tiene diff vacío contra HEAD y partida.py solo agrega su método.
Checklist de requisitos existente: 16/16 marcados. Sin dependencias nuevas.
Los hooks opcionales de commit se omiten por prohibición explícita del usuario.
No se ejecutan scripts que reemplacen artefactos ni se crean ramas/commits.

### Evidencia después de restaurar la lista simple (2026-11-17)

`venv\Scripts\python.exe main.py --bench mapa_conocido`: código 0, 35,5 s.
Python 3.13.18, Windows 11; cinco muestras, mediana sin trazador y pico separado.
Son medidas del layout puro: excluyen la foto y no miden el nuevo filtrado O(N).
La función pura y la entrada sintética del benchmark no cambian en esta revisión;
las diferencias frente a la corrida anterior no se atribuyen al barrido de estados.

| Conocidas | AVL, ms | ListaOrdenada, ms | AVL, pico KiB | ListaOrdenada, pico KiB |
|---:|---:|---:|---:|---:|
| 10 | 0,089 | 0,225 | 8,4 | 7,6 |
| 100 | 1,264 | 1,097 | 78,5 | 70,5 |
| 1000 | 22,125 | 46,742 | 865,1 | 758,6 |
| 5000 | 123,594 | 759,674 | 4444,2 | 3872,0 |

Las 43 suites, ejecutadas con el mismo script de auditoría y carpetas temporales
externas, terminaron con código 0 (168,937 s acumulados). `conocimiento.py` es
idéntico a f600fdd; `partida.py` solo agrega seis líneas para mapa_dibujado.
La guarda de sprites se conserva como arreglo ajeno al mapa: el método original
de f600fdd reproduce el AttributeError en la fixture parcial; la guarda lo evita.
Detalles de reproducción y decisión en DECISIONES.md §17.7.
