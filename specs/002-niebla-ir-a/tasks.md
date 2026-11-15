# Tasks: Niebla de guerra, mapa conocido y viaje automático "ir a"

**Input**: Design documents from `specs/002-niebla-ir-a/`

**Prerequisites**: `plan.md` ✓ | `spec.md` ✓ | `research.md` ✓ | `data-model.md` ✓ | `contracts/` ✓ | `quickstart.md` ✓ | `constitution.md` ✓

## Verificación funcional posterior

Sobre 18b9364 se ejecutaron nuevamente 42/42 módulos, sin fallos, y
229/229 unittest conjuntos, sin errores, en 140,442 s. Los 13 fallos citados
en la auditoría histórica de abajo ya fueron corregidos. Dos corridas nuevas
de mapa_conocido y los cuatro benchmarks de T030 terminaron con código 0;
la comparación con Parte I y sus límites están en DECISIONES.md de la raíz,
sección 17.5. SC-001, T030 y T031 siguen pendientes de evidencia suficiente.
Esta edición documental no ejecuta otra vez las pruebas.

## Estado histórico de la auditoría 002 + 003 + 004

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

**Tests**: Se incluyen tareas de prueba test-first para cada componente, alineadas con FR-001..FR-024 y SC-001..SC-005 conforme al plan y a la spec.

**Organización**: Las tareas se agrupan por historia de usuario para habilitar implementación y prueba independiente de cada historia. Las dependencias de fase son estrictas.

## Formato: `[ID] [P?] [Story] Descripción con ruta de archivo -> Verificación`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias mutuas directas).
- **[Story]**: Historia de usuario correspondiente (`[US1]`, `[US2]`, `[US3]`, `[US4]`, `[BENCH]`).
- Rutas ajustadas al árbol real del proyecto conforme a `plan.md`.

---

## Phase 1: Setup — Infraestructura Compartida

**Propósito**: Habilitar la mutación indexada reversible de listas en `Registro.cambiar` (C1) y crear el archivo de pruebas `tests/test_niebla_ir_a.py` vacío como punto de entrada test-first. Esta fase bloquea todo lo demás.

> **⚠️ CRÍTICO**: Ninguna historia de usuario puede comenzar hasta que esta fase esté completa.

- [x] T001 Soporte indexado en Registro.cambiar, con captura historica previa y generaciones solo para memoria_puertas. -> Evidencia: `test_niebla_ir_a, test_fr010_generaciones_002`.
- [x] T002 Modulo de pruebas C3 existente; la aceptacion funcional se distribuye en modulos especificos, no solo en test_niebla_ir_a. -> Evidencia: `test_niebla_ir_a`.

**Checkpoint — Phase 1**: `Registro.cambiar` soporta listas y el módulo de pruebas existe. Se puede continuar con Phase 2.

---

## Phase 2: Foundational — `ConocimientoMapa` y Contrato C3

**Propósito**: Implementar las dos estructuras de datos bloqueantes: la entidad `ConocimientoMapa` (arreglos contiguos con contadores O(1) para C6) y la búsqueda de caminos compartida `MonticuloMin` + `dijkstra_acotado` (Contrato C3 con Mariano). Ninguna historia de usuario puede comenzar hasta que esta fase esté completa.

> **⚠️ CRÍTICO**: Phase 3, 4, 5 y 6 dependen de esta fase. US2 depende además de C3.

### ConocimientoMapa (bloquea US1, US2, US3, US4)

**Aclaración confirmada que precisa T003/T004**: la firma del constructor es
`ConocimientoMapa(n, salas_por_indice, mapa)`, sin copias. La consulta por ID es
O(log N); las consultas por Sala/índice y resumen son O(1). Las decisiones sobre
memoria simétrica y límites de visibilidad están en `data-model.md`. Las pruebas
unitarias se ejecutan con `python -m tests.test_conocimiento`; los escenarios de
aceptacion con Partida/vistas esta implementada y probada; ver T004/T008.
el ejemplo incompleto del constructor en T003.

- [x] T003 ConocimientoMapa(n, salas_por_indice, mapa), referencias sin copia, estados, memoria y contadores O(1); consulta por ID O(log N). -> Evidencia: `test_conocimiento`.
- [x] T004 Pruebas de estados, privacidad, inicio y contadores en test_conocimiento y test_conocimiento_partida; no se afirma una cronologia test-first no demostrada. -> Evidencia: `test_conocimiento, test_conocimiento_partida`.

### MonticuloMin y dijkstra_acotado — Contrato C3 (bloquea US2)

- [x] T005 MonticuloMin propio sobre lista contigua; orden lexicografico, extraccion minima y error al estar vacio. -> Evidencia: `test_niebla_ir_a`.
- [x] T006 dijkstra_acotado stateless con firma C3, filtro de una salida, cota inclusiva y arreglos/tokens del llamador. -> Evidencia: `test_niebla_ir_a`.
- [x] T007 Pruebas C3 de monticulo, costos, cota, filtro, desempate y arreglos independientes. -> Evidencia: `test_niebla_ir_a`.

**Checkpoint — Phase 2**: `ConocimientoMapa`, `MonticuloMin` y `dijkstra_acotado` operativos. Todas las pruebas T004 y T007 deben pasar. Se puede continuar con las historias de usuario.

---

## Phase 3: User Story 1 — Exploración Progresiva y Visibilidad del Mapa Conocido (Priority: P1) ⭐ MVP

**Goal**: El jugador ve únicamente lo que ha explorado u observado directamente, distinguiendo entre salas Exploradas, Avistadas y Desconocidas. Las interfaces no filtran datos prohibidos.

**Independent Test**: Iniciar partida en sala de inicio, verificar que solo esa sala aparece como Explorada, sus vecinas como Avistadas y el resto como Desconocidas. Desplazarse a una vecina y verificar que el estado se actualiza correctamente.

### Pruebas de Aceptación — US1

- [x] T008 Aceptacion US1 distribuida: puertas locales/remotas, retroceso, mapa filtrado y ausencia de identificadores de salas no exploradas. -> Evidencia: `test_conocimiento_partida, test_mapa_consola`.

### Implementación — US1

- [x] T009 Inicializacion de conocimiento en Partida.iniciar: inicio explorado, vecinas avistadas y puertas locales observadas. -> Evidencia: `test_conocimiento_partida`.
- [x] T010 Exploracion al entrar, contadores sin duplicados y cambios mediante Partida.cambiar. -> Evidencia: `test_conocimiento_partida`.
- [x] T011 Observacion antes/despues de acciones y suscripcion al despachador C2; los cambios remotos no revelan informacion. -> Evidencia: `test_conocimiento_partida, test_terreno_cazador`.
- [x] T012 salidas_visibles devuelve cinco campos: direccion, memoria, ID o None, llave permitida y costo; no lee apertura fisica para presentar memoria. -> Evidencia: `test_mapa_consola`.
- [x] T013 Consola: mapa, salidas anonimas con costos e ir a <id> antes de ir <direccion>. -> Evidencia: `test_mapa_consola`.
- [x] T014 Pygame: etiquetas privadas, costos, mapa M, viaje V y cancelacion Escape/R con orden pendiente fuera del callback. -> Evidencia: `test_ir_a_grafico_002, test_bench_mapa_conocido_002; test_gui tiene un falso positivo ajeno a estos casos`.

**Checkpoint US1**: Conocimiento, puertas y privacidad: ejecutar con el Python del venv los modulos tests.test_conocimiento, tests.test_conocimiento_partida, tests.test_mapa_consola y tests.test_terreno_cazador. La evidencia se distribuye entre esas suites, no solo en C3.

---

## Phase 4: User Story 2 — Viaje Automático "ir a" con Planificación Segura (Priority: P1)

**Goal**: El jugador puede emitir `ir a <sala>` y el personaje avanza automáticamente paso a paso por el camino de costo mínimo conocido, deteniéndose de inmediato ante cualquier peligro o bloqueo.

**Independent Test**: Con varias salas exploradas, ordenar `ir a <destino>`: el personaje avanza consumiendo tiempo en cada paso, recalcula la ruta antes de cada acción y se detiene con mensaje descriptivo ante enemigos, trampas o bloqueos.

### Pruebas de Aceptación — US2

- [x] T015 Aceptacion del planificador y viaje: validacion, ponderacion, empate, recalculo, interrupciones, log y pergamino. -> Evidencia: `test_planificador_rutas, test_ir_a_compuesto`.

### Implementación — US2

- [x] T016 IR_A e interpretar_ir_a en modelo/juego/orden.py, reexportados por controlador/orden.py; fuera de ORDENES_DE_PARTIDA. Sintaxis ir a <id>, sin alias ir <id>. -> Evidencia: `test_ir_a_compuesto, test_mapa_consola`.
- [x] T017 BitacoraPartida.anotar_comentario; leer_log ordinario omite comentarios. El lector de reconstruccion 004 conserva y aplica marcas IR_A sin ejecutarlas como movimientos. -> Evidencia: `test_ir_a_compuesto, test_comentarios_ir_a_002, test_historia_persistencia (casos FR014 y FR010)`.
- [x] T018 Aplicacion registra comentarios en el log activo y en lineas intercaladas; main conecta una suscripcion. -> Evidencia: `test_integracion_comentarios_002`.
- [x] T019 Controlador ejecuta pasos ordinarios y recalcula mediante PlanificadorRutas; despues de callbacks/cancelacion emite una marca por cada observacion exterior efectiva, aun sin movimiento. -> Evidencia: `test_ir_a_compuesto, test_comentarios_ir_a_002`.
- [x] T020 PlanificadorRutas posee distancias, marcas y token propios; se recrea al sustituir la partida, sin compartirlos con cazador. -> Evidencia: `test_planificador_rutas, test_ir_a_compuesto`.

**Checkpoint US2**: Planificacion y viaje compuesto: ejecutar con el Python del venv tests.test_planificador_rutas, tests.test_ir_a_compuesto, tests.test_comentarios_ir_a_002, tests.test_integracion_comentarios_002 y tests.test_ir_a_grafico_002. Para replay usar un log real generado por la partida; no asumir que partida.log existe.

---

## Phase 5: User Story 3 — Iluminación y Revelado de Entorno mediante Antorcha Encendida (Priority: P2)

**Goal**: Al ingresar a una sala con la antorcha encendida, todas las salas vecinas directas pasan a estado Explorada, revelando su nombre y salidas, sin activar su contenido interno.

**Independent Test**: Equipar y encender la antorcha antes de cruzar a una sala nueva; al ingresar, todas las vecinas pasan a Exploradas con sus datos, pero los enemigos y trampas de esas vecinas permanecen inactivos.

### Pruebas de Aceptación — US3

- [x] T021 Pruebas de antorcha: vecinas incluso por salida cerrada, ausencia de activacion remota y reversion. -> Evidencia: `test_conocimiento_partida`.

### Implementación — US3

- [x] T022 Partida._entrar revela vecinas con antorcha usando _explorar_sala; no observa puertas remotas ni carga contenido por iluminarlas. -> Evidencia: `test_conocimiento_partida`.

**Checkpoint US3**: Antorcha y reversion: ejecutar con el Python del venv tests.test_conocimiento_partida; cubre revelado de vecinas sin observar puertas remotas, ausencia de activacion de contenido y restauracion de estados/contadores.

---

## Phase 6: User Story 4 — Persistencia, Registro y Reversión Temporal del Mapa Conocido (Priority: P2)

**Goal**: El mapa conocido se guarda y carga fidedignamente en formato v4; los archivos v3 se rechazan explícitamente; el pergamino revierte exactamente el último paso de movimiento.

**Independent Test**: Guardar partida, cerrar y recargar; el estado de conocimiento debe ser idéntico. Intentar cargar un archivo v3: debe producirse error claro sin corromper la sesión actual.

### Pruebas de Aceptación — US4

- [x] T023 Aceptacion v4 y retroceso: fotografia independiente, rechazo v3, rollback, comentarios, pergaminos y referencias de inversos. -> Evidencia: `test_guardado_v4_002, test_carga_v4_002, test_fr010_generaciones_002`.

### Implementación — US4

- [x] T024 VERSION_FORMATO=4 y rechazo explicito de v3 mediante ErrorFormato convertido a ErrorCarga. -> Evidencia: `test_guardado_v4_002, test_carga_v4_002`.
- [x] T025 Codec escribe N uint16, N estados, P uint16 y P entradas <HBB>; omite cero y cuenta posiciones de memoria, no puertas unicas. Bloque de enemigos intacto. -> Evidencia: `test_guardado_v4_002`.
- [x] T026 Codec deserializa fotografia; persistencia reconstruye mediante T045 y compara arreglos/contadores dentro del contexto. No sustituye ConocimientoMapa, sus arreglos ni Registro. Contadores mantenidos por el replay y comprobados con recuento O(N). -> Evidencia: `test_carga_v4_002, test_historia_persistencia (casos FR014)`.
- [x] T027 ErrorCarga y rechazo transaccional: conserva partida, log y recursos anteriores; no verifica resolubilidad al cargar. -> Evidencia: `test_carga_v4_002, test_resolubilidad_integracion`.

**Checkpoint US4**: Persistencia v4 y rechazo v3 verificados mediante las pruebas reales de T023. Ejecutar con el entorno virtual:

```powershell
.\venv\Scripts\python.exe -B -m tests.test_guardado_v4_002
.\venv\Scripts\python.exe -B -m tests.test_carga_v4_002
```

Ambas suites deben aprobar; comprueban codec, conocimiento, rechazo v3, reconstruccion y rollback. Si el worktree no tiene venv propio, usar el ejecutable absoluto del entorno del proyecto original manteniendo el directorio actual del worktree.

---

## Phase 7: Polish & Cross-Cutting Concerns — Benchmarks, Integración y Validación

**Propósito**: Instrumentar y verificar cuantitativamente SC-001..SC-004, integrar el nuevo benchmark en `main.py`, repetir suites de regresión y validar la guía de inicio rápido de `quickstart.md`.

- [x] T028 Instrumentacion sintetica SC001-SC004 en tests/bench_niebla_ir_a.py y adaptador bench/bench_mapa_conocido.py: consultas, exploracion sin/con antorcha, registro/inversion por celda y pergamino real. Instrumentacion ejecutada; SC-001 oficial sigue pendiente. -> Evidencia: `test_bench_mapa_conocido_002; main.py --bench mapa_conocido`.
- [x] T029 Registro mapa_conocido en main.py:BENCHES; adaptador main([]) aisla argumentos externos, sin cambiar otros benchmarks. -> Evidencia: `test_bench_mapa_conocido_002`.
- [ ] T030 Ejecutados cache, lista_ordenada, ordenamiento y guardado en temporal externo, codigo 0. Pendiente comparacion de regresiones: no hay linea base equivalente; no afirmar ausencia de degradacion. -> Evidencia: `mediciones en DECISIONES.md`.
- [ ] T031 Regresiones nuevas sobre 18b9364: 42/42 módulos y 229/229 unittest aprobados; fallos compartidos anteriores corregidos. Pendiente cierre integral FR/SC, SC-001 oficial y comparación equivalente T030; no declarar cobertura del 100%. -> Evidencia: `DECISIONES.md de la raíz, 17.5; matriz local de trazabilidad`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 — Setup**: Sin dependencias — puede comenzar de inmediato.
- **Phase 2 — Foundational**: Depende de la finalización de Phase 1 — **bloquea US1, US2, US3 y US4**.
- **Phase 3 (US1)**: Depende de Phase 2 — **bloquea US2, US3 y US4** (el conocimiento debe estar integrado).
- **Phase 4 (US2)**: Depende de Phase 2 (C3) y Phase 3 (US1) — `dijkstra_acotado` y `ConocimientoMapa` integrados en `Partida`.
- **Phase 5 (US3)**: Depende de Phase 3 (US1) — el conocimiento debe estar operativo en `partida`.
- **Phase 6 (US4)**: Depende de Phase 3 (US1) — el conocimiento debe estar definido para serializarlo.
- **Phase 7 — Polish**: Depende de las historias deseadas (mínimo US1 para MVP de benchmark).

### User Story Dependencies

- **US1 (P1)**: Puede comenzar tras Phase 2 — sin dependencias de otras historias.
- **US2 (P1)**: Requiere US1 completa (conocimiento integrado en `Partida`) y C3 completo (montículo y Dijkstra).
- **US3 (P2)**: Requiere US1 completa (antorcha actualiza el conocimiento vía `partida.cambiar`).
- **US4 (P2)**: Requiere US1 completa (el guardado serializa `ConocimientoMapa`).

### Parallel Opportunities

- **T003, T005, T006**: Archivos distintos — pueden implementarse en paralelo dentro de Phase 2.
- **T013, T014**: Vista consola y vista Pygame — archivos distintos, pueden implementarse en paralelo.
- **T016, T017, T018**: `orden.py`, `bitacora_partida.py`, `aplicacion.py` — archivos distintos.
- **T028, T029**: `bench_mapa_conocido.py` y `main.py` — paralelizables.
- Una vez completa Phase 2, US1 (P1) y US4 (P2) pueden avanzar en paralelo si hay capacidad.

---

## Parallel Example: User Story 1

```bash
# Ejecutar conjuntamente (archivos distintos):
Task T013: "Actualizar vista/vista_consola.py"
Task T014: "Corregir vista/vista_pygame.py"

# Tras T009 y T010 — en paralelo:
Task T011: "Sincronización de memoria_puertas en _accion"
Task T012: "Enmascarar salidas_visibles()"
```

---

## Implementation Strategy

### MVP First (US1 Únicamente)

1. Completar Phase 1 — Setup.
2. Completar Phase 2 — Foundational (C3 y `ConocimientoMapa`).
3. Completar Phase 3 — US1.
4. **DETENER y VALIDAR**: Verificar US1 de forma independiente con `python -m tests.test_niebla_ir_a`.
5. Presentar MVP con niebla de guerra y mapa conocido sin viaje automático.

### Incremental Delivery

1. Setup + Foundational → Base lista.
2. US1 → Niebla de guerra y mapa conocido → MVP demostrable.
3. US2 → Viaje automático "ir a" → Incremento de navegación.
4. US3 + US4 → Antorcha + Persistencia → Finalización.
5. Polish → Benchmarks y validación de regresión.

---

## Notes

- **[P]** = archivos distintos, sin dependencias — pueden ejecutarse en paralelo.
- **[Story]** mapea la tarea a una historia de usuario específica para trazabilidad con `spec.md`.
- Cada historia de usuario es independientemente implementable y verificable.
- Las pruebas test-first deben escribirse y **fallar** antes de la implementación.
- **Restricciones constitucionales estrictas**: prohibido `dict` o `set` como índice/caché, `heapq`, `bisect`, `collections`, `networkx`, `sorted()`, `list.sort()`. Solo `list` como almacenamiento contiguo.
- Toda mutación de conocimiento pasa por `partida.cambiar(...)` para reversibilidad C1.
- `IR_A` es orden compuesta del controlador y **NO pertenece a `ORDENES_DE_PARTIDA`**.
- Los arreglos de búsqueda `_dist_navegacion` y `_marca_navegacion` pertenecen exclusivamente al controlador de Kim; los de Mariano son independientes — cero interferencia entre búsquedas del mismo ciclo.

## Interpretacion del cierre de tareas

T001-T029 tienen implementacion y evidencia; las rutas/nombres de pruebas del
plan inicial se sustituyen por los modulos reales citados arriba. Las tareas de
pruebas completadas acreditan escenarios ejecutados, no que se haya verificado
retrospectivamente el orden test-first. T028 completa instrumentacion, no la
certificacion de SC-001. T030 y T031 permanecen abiertas. Los checkpoints y
comandos del plan inicial son guias, no certificaciones de suite completa.
