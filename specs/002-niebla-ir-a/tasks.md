# Tasks: Niebla de guerra, mapa conocido y viaje automático "ir a"

**Input**: Design documents from `specs/002-niebla-ir-a/`

**Prerequisites**: `plan.md` ✓ | `spec.md` ✓ | `research.md` ✓ | `data-model.md` ✓ | `contracts/` ✓ | `quickstart.md` ✓ | `constitution.md` ✓

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

- [ ] T001 Extender `Registro.cambiar(objeto, campo, valor)` en `modelo/juego/registro.py` para soportar mutación indexada de listas: añadir al inicio del método la rama `if isinstance(objeto, list) and isinstance(campo, int):` que guarda `anterior = objeto[campo]`, aplica `objeto[campo] = valor` y, **si `self._abierto is not None`**, apila la operación inversa `lambda: objeto.__setitem__(campo, anterior)`; si `self._abierto is None`, simplemente muta sin registrar inversión (igual que el comportamiento actual para atributos fuera de grupo abierto); actualizar la anotación del parámetro de `campo: str` a `campo: str | int` en la firma del método (C1, FR-012, SC-004). -> `python -m tests.test_niebla_ir_a`
- [ ] T002 Crear el archivo de pruebas de aceptación `tests/test_niebla_ir_a.py` con la estructura de módulo y los imports necesarios; sin pruebas aún (andamiaje para el enfoque test-first). -> `python -m tests.test_niebla_ir_a`

**Checkpoint — Phase 1**: `Registro.cambiar` soporta listas y el módulo de pruebas existe. Se puede continuar con Phase 2.

---

## Phase 2: Foundational — `ConocimientoMapa` y Contrato C3

**Propósito**: Implementar las dos estructuras de datos bloqueantes: la entidad `ConocimientoMapa` (arreglos contiguos con contadores O(1) para C6) y la búsqueda de caminos compartida `MonticuloMin` + `dijkstra_acotado` (Contrato C3 con Mariano). Ninguna historia de usuario puede comenzar hasta que esta fase esté completa.

> **⚠️ CRÍTICO**: Phase 3, 4, 5 y 6 dependen de esta fase. US2 depende además de C3.

### ConocimientoMapa (bloquea US1, US2, US3, US4)

- [ ] T003 [P] Implementar `ConocimientoMapa` en `modelo/juego/conocimiento.py` con: arreglos contiguos preasignados `self.estado_salas = [ESTADO_DESCONOCIDA] * N` y `self.memoria_puertas = [PUERTA_DESCONOCIDA] * (4 * N)` (donde `ESTADO_DESCONOCIDA = 0`, `ESTADO_AVISTADA = 1`, `ESTADO_EXPLORADA = 2`, `PUERTA_DESCONOCIDA = 0`, `PUERTA_ABIERTA = 1`, `PUERTA_CERRADA = 2`); contadores reversibles `self.num_exploradas: int = 0` y `self.num_avistadas: int = 0`; `self.salas_por_indice: list[Sala]` asignado como **referencia directa a `mapa.salas`** (no copia — cero memoria adicional), pasado en el constructor como `ConocimientoMapa(n, salas_por_indice=mapa.salas)`; mapeo de puertas `pos = sala.indice * 4 + dir_idx`; métodos de consulta O(1) `es_explorada(sala)`, `es_avistada(sala)`, `estado_sala(sala)`, `puerta_recordada(sala, dir_idx)` (todos reciben instancia de `Sala`, no ID); método `estado_por_id(id_sala)` que resuelve la sala via `mapa.sala(id_sala)` usando el `Mapa` recibido en el constructor (sin dict ni O(N) — `mapa.sala` usa `esqueleto.posicion` internamente), retornando `estado_salas[sala.indice]` o `ESTADO_DESCONOCIDA` si la sala no existe; y método `resumen() -> tuple[int, int]` que retorna `(self.num_exploradas, self.num_avistadas)` (C6, FR-001..FR-005, SC-002, SC-003). -> `python -m tests.test_niebla_ir_a`
- [ ] T004 Escribir pruebas test-first en `tests/test_niebla_ir_a.py` para `ConocimientoMapa`: `test_FR001_clasificacion_tres_estados`, `test_FR002_estado_inicial_instante_cero`, `test_FR003_sala_explorada_revela_nombre_y_conexiones`, `test_FR004_sala_avistada_no_revela_id_ni_nombre`, `test_FR005_sala_desconocida_oculta_sin_ruteo`; verificar que `num_avistadas` NO se duplica cuando una sala tiene múltiples accesos; verificar `resumen()` O(1) (C6, SC-002, SC-004). -> `python -m tests.test_niebla_ir_a`

### MonticuloMin y dijkstra_acotado — Contrato C3 (bloquea US2)

- [ ] T005 [P] Implementar `MonticuloMin` en `modelo/estructuras/monticulo_min.py` sobre lista contigua (`_datos: list[tuple[int, int]]`, `_tamano: int`) con métodos `insertar(elemento: tuple[int, int]) -> None` O(log K), `extraer_min() -> tuple[int, int]` O(log K) con lanzamiento de `IndexError` si vacío, `es_vacio() -> bool` y `__len__() -> int`; invariante de eliminación perezosa (no se implementa `decrease_key`; los llamadores descartan tuplas obsoletas con `dist > arreglo_dist[sala.indice]`); desempate determinista natural por menor `id_sala` mediante el comparador lexicográfico de tuplas `(distancia, id_sala)` sin `heapq`, `bisect` ni tablas hash (Constitución Principio I y II, Contrato C3). -> `python -m tests.test_niebla_ir_a`
- [ ] T006 [P] Implementar función `dijkstra_acotado` en `modelo/estructuras/dijkstra.py` con la firma exacta unificada con Capacidad 001: `dijkstra_acotado(origen: Sala, mapa: Mapa, filtro_salida: Callable[[Salida], bool], cota_rango: Optional[int] = None, token_busqueda: int = 1, arreglo_dist: Optional[List[int]] = None, arreglo_marca: Optional[List[int]] = None) -> tuple[List[int], List[int]]`; `filtro_salida` recibe **únicamente** la instancia `salida`; función completamente stateless; marcas de búsqueda enteras para reinicio O(1) sin reinicializar arreglos; retorna la tupla `(arreglo_dist, arreglo_marca)` (Contrato C3, SC-001, SC-005). -> `python -m tests.test_niebla_ir_a`
- [ ] T007 Escribir pruebas test-first en `tests/test_niebla_ir_a.py` para C3: `test_C3_monticulo_min_insertar_extraer_orden_correcto`, `test_C3_monticulo_min_desempate_por_menor_id`, `test_C3_dijkstra_acotado_camino_minimo_correcto`, `test_C3_dijkstra_acotado_cota_rango`, `test_C3_dijkstra_acotado_determinismo_empates`, `test_C3_arreglos_llamadores_independientes_sin_interferencia` (Contrato C3, SC-001, SC-005). -> `python -m tests.test_niebla_ir_a`

**Checkpoint — Phase 2**: `ConocimientoMapa`, `MonticuloMin` y `dijkstra_acotado` operativos. Todas las pruebas T004 y T007 deben pasar. Se puede continuar con las historias de usuario.

---

## Phase 3: User Story 1 — Exploración Progresiva y Visibilidad del Mapa Conocido (Priority: P1) ⭐ MVP

**Goal**: El jugador ve únicamente lo que ha explorado u observado directamente, distinguiendo entre salas Exploradas, Avistadas y Desconocidas. Las interfaces no filtran datos prohibidos.

**Independent Test**: Iniciar partida en sala de inicio, verificar que solo esa sala aparece como Explorada, sus vecinas como Avistadas y el resto como Desconocidas. Desplazarse a una vecina y verificar que el estado se actualiza correctamente.

### Pruebas de Aceptación — US1

- [ ] T008 [US1] Escribir pruebas test-first en `tests/test_niebla_ir_a.py`: `test_FR006_actualizacion_memoria_puertas_en_acciones`, `test_FR006_memoria_puerta_persiste_sin_jugador_adyacente`, `test_FR012_reversion_conocimiento_con_pergamino`, `test_FR013_registro_eventos_conocimiento`, `test_FR009_comando_mapa_muestra_solo_exploradas`, `test_FR010_vistas_no_revelan_id_ni_nombre_de_avistadas` (FR-006, FR-009, FR-010, FR-012, FR-013, SC-002, SC-003). -> `python -m tests.test_niebla_ir_a`

### Implementación — US1

- [ ] T009 [US1] Integrar `ConocimientoMapa` en `modelo/juego/partida.py`: añadir atributo `self.conocimiento`; en `iniciar()` marcar sala de inicio como `ESTADO_EXPLORADA` vía `partida.cambiar(conocimiento.estado_salas, inicio.indice, ESTADO_EXPLORADA)` y `partida.cambiar(conocimiento, "num_exploradas", 1)`; por cada vecina desconocida $v$ marcar `ESTADO_AVISTADA` vía `partida.cambiar` sin duplicar conteo si $v$ ya fue avistada; registrar `memoria_puertas` del estado actual de puertas de las salidas de la sala inicial (C1, FR-001, FR-002, FR-003, FR-004, FR-005). -> `python -m tests.test_niebla_ir_a`
- [ ] T010 [US1] Implementar actualización de visión en `_entrar(destino)` en `modelo/juego/partida.py`: si destino estaba `ESTADO_AVISTADA`, decrement `num_avistadas` y cambiar a `ESTADO_EXPLORADA` incrementando `num_exploradas` vía `partida.cambiar`; para cada vecina $w$ de destino: solo si `estado_salas[w.indice] == ESTADO_DESCONOCIDA`, cambiar a `ESTADO_AVISTADA` e incrementar `num_avistadas` vía `partida.cambiar`; actualizar `memoria_puertas` de todas las salidas de destino (C1, FR-001..FR-006, SC-003). -> `python -m tests.test_niebla_ir_a`
- [ ] T011 [US1] Implementar sincronización de `memoria_puertas` en `_accion` en `modelo/juego/partida.py`: en cada acción voluntaria del jugador, iterar sobre las salidas de la sala actual y actualizar `memoria_puertas` con el estado físico real vía `partida.cambiar(conocimiento.memoria_puertas, pos, estado_real)`; suscribir observador de `ConocimientoMapa` en `_observadores_puertas` para actualizar la memoria cuando se cambie el estado de una puerta cuya salida conecte la sala actual del jugador (Contrato C2, FR-006). -> `python -m tests.test_niebla_ir_a`
- [ ] T012 [US1] Modificar `salidas_visibles()` en `modelo/juego/partida.py` para enmascarar información según el conocimiento: si la sala vecina está en `ESTADO_AVISTADA` o `ESTADO_DESCONOCIDA`, retornar `id_vecino = None` y `nombre_vecino = None`; retornar el estado de puerta recordado en lugar del estado real (`puerta_recordada` del `conocimiento`) (FR-004, FR-010). -> `python -m tests.test_niebla_ir_a`
- [ ] T013 [P] [US1] Actualizar `vista/vista_consola.py`: en `_texto_salidas`, si `id_vecino is None`, formatear como `f"{direccion} -> desconocida (costo {costo})"` sin revelar ID ni nombre; implementar comando `mapa` que muestre solo salas exploradas con sus salidas y puertas recordadas, formateando salas avistadas como destino desconocido (FR-004, FR-009, FR-010). -> `python -m tests.test_niebla_ir_a`
- [ ] T014 [P] [US1] Corregir `_dibujar_puerta` en `vista/vista_pygame.py`: comprobar si `id_vecino is None` (sala avistada o desconocida); si es así, renderizar etiqueta genérica `f"{direccion}: desconocida (costo {costo})"` sin dibujar el ID numérico ni el nombre de la sala vecina (FR-004, FR-010). -> `python -m tests.test_niebla_ir_a`

**Checkpoint — US1**: Visibilidad de niebla de guerra completamente funcional. Ejecutar `python -m tests.test_niebla_ir_a` — todas las pruebas T004, T008 y el subconjunto US1 de T009..T014 deben pasar.

---

## Phase 4: User Story 2 — Viaje Automático "ir a" con Planificación Segura (Priority: P1)

**Goal**: El jugador puede emitir `ir a <sala>` y el personaje avanza automáticamente paso a paso por el camino de costo mínimo conocido, deteniéndose de inmediato ante cualquier peligro o bloqueo.

**Independent Test**: Con varias salas exploradas, ordenar `ir a <destino>`: el personaje avanza consumiendo tiempo en cada paso, recalcula la ruta antes de cada acción y se detiene con mensaje descriptivo ante enemigos, trampas o bloqueos.

### Pruebas de Aceptación — US2

- [ ] T015 [US2] Escribir pruebas test-first en `tests/test_niebla_ir_a.py`: `test_FR014_ir_a_destino_no_explorado_rechazado`, `test_FR014_ir_a_destino_inexistente_rechazado`, `test_FR014_ir_a_destino_es_sala_actual`, `test_FR015_ir_a_camino_costo_minimo`, `test_FR016_desempate_menor_id_en_vecina`, `test_FR017_pasos_individuales_avanzan_reloj`, `test_FR018_recalculo_ruta_en_cada_paso`, `test_FR019_interrupcion_por_enemigos_vivos`, `test_FR019_interrupcion_por_dano`, `test_FR019_interrupcion_ruta_bloqueada`, `test_FR020_mensajes_descriptivos_detencion`, `test_FR021_ir_a_nunca_abre_puertas_automaticamente`, `test_FR022_log_asienta_pasos_y_comentario`, `test_FR023_reversion_pergamino_deshace_solo_ultimo_paso` (FR-014..FR-023, SC-005). -> `python -m tests.test_niebla_ir_a`

### Implementación — US2

- [ ] T016 [P] [US2] Extender `controlador/orden.py`: definir constante `IR_A = "ir_a"`; verificar que `IR_A` NO se añade a `ORDENES_DE_PARTIDA`; implementar `Orden(IR_A, destino).es_de_partida() == False`; añadir parseo de `"ir a <id>"` e `"ir <id>"` en `interpretar_orden` retornando `Orden(IR_A, id_destino)` (Contrato C4, FR-014). -> `python -m tests.test_niebla_ir_a`
- [ ] T017 [P] [US2] Implementar `anotar_comentario(self, texto: str) -> None` en `modelo/datos/bitacora_partida.py` escribiendo `"# " + _limpio(texto)` al archivo si `self._archivo is not None`; actualizar `leer_log(ruta)` reemplazando la condición `if linea != "":` por `if linea and not linea.startswith("#"):` en el bucle de órdenes (**esta modificación va ANTES del `try/except`**, de modo que las líneas de comentario `# ir a <destino>` se descartan sin intentar parsearlas como órdenes, evitando que replay lance `ErrorLog`) (Contrato C4, FR-022). -> `python -m tests.test_niebla_ir_a`
- [ ] T018 [P] [US2] Añadir método `registrar_comentario(self, texto: str) -> None` en `controlador/aplicacion.py` que invoca `self.log.anotar_comentario(texto)` si `self.log is not None` (Contrato C4, FR-022). -> `python -m tests.test_niebla_ir_a`
- [ ] T019 [US2] Implementar `_ejecutar_ir_a(orden)` en `controlador/controlador.py` siguiendo el protocolo C4: (1) Validación previa sin costo de tiempo: rechazar si `id_destino` no existe, si `estado_por_id(id_destino) != ESTADO_EXPLORADA` o si no existe ruta conocida inicial; avisar si ya está en la sala destino. (2) Registrar comentario `# ir a <id_destino>` vía `registrar_comentario`. (3) Bucle paso a paso: incrementar `self._token_navegacion`, ejecutar `dijkstra_acotado(origen=sala_destino, mapa=..., filtro_salida=filtro_jugador, cota_rango=None, token_busqueda=self._token_navegacion, arreglo_dist=self._dist_navegacion, arreglo_marca=self._marca_navegacion)` donde `filtro_jugador = lambda salida: conocimiento.es_explorada(salida.sala_a) and conocimiento.es_explorada(salida.sala_b) and conocimiento.puerta_recordada_abierta(salida)`; si ya está en destino: terminar con `"Has llegado a tu destino."`; seleccionar vecina con menor `salida.costo + dist[v.indice]` desempatando por menor `v.id` (FR-016); registrar `vida_antes`; despachar `self._ejecutar_de_partida(Orden(MOVER, dir_paso))`; evaluar paradas reactivas (FR-019, FR-020); notificar motivo con `self._avisar` (Contrato C3, Contrato C4, FR-014..FR-021, SC-005). -> `python -m tests.test_niebla_ir_a`
- [ ] T020 [US2] Integrar los arreglos propietarios de navegación en el controlador (`self._dist_navegacion`, `self._marca_navegacion`, `self._token_navegacion = 0`) de tamaño $N$ con `self._token_navegacion` gestionado de forma que nunca colisione con los arreglos del cazador de Mariano (`self._dist_cazador`, `self._marca_cazador`) (Contrato C3, §4.2). -> `python -m tests.test_niebla_ir_a`

**Checkpoint — US2**: Viaje automático completamente funcional. Ejecutar `python -m tests.test_niebla_ir_a` — pruebas T007 y T015 deben pasar. Verificar con `python main.py --replay partida.log`.

---

## Phase 5: User Story 3 — Iluminación y Revelado de Entorno mediante Antorcha Encendida (Priority: P2)

**Goal**: Al ingresar a una sala con la antorcha encendida, todas las salas vecinas directas pasan a estado Explorada, revelando su nombre y salidas, sin activar su contenido interno.

**Independent Test**: Equipar y encender la antorcha antes de cruzar a una sala nueva; al ingresar, todas las vecinas pasan a Exploradas con sus datos, pero los enemigos y trampas de esas vecinas permanecen inactivos.

### Pruebas de Aceptación — US3

- [ ] T021 [US3] Escribir pruebas test-first en `tests/test_niebla_ir_a.py`: `test_FR007_antorcha_revela_vecinas_como_exploradas`, `test_FR007_antorcha_revela_salidas_y_costos_de_vecinas`, `test_FR008_antorcha_no_activa_enemigos_en_vecinas`, `test_FR008_antorcha_no_activa_trampas_en_vecinas`, `test_FR012_reversion_antorcha_restaura_estados_previos` (FR-007, FR-008, FR-012). -> `python -m tests.test_niebla_ir_a`

### Implementación — US3

- [ ] T022 [US3] Modificar `_entrar(destino)` en `modelo/juego/partida.py` y/o `modelo/juego/efectos.py`: si `jugador.antorcha_encendida == True`, iterar sobre todas las salidas de `destino` (abiertas **y** cerradas); para cada sala vecina $w$: si `estado_salas[w.indice] != ESTADO_EXPLORADA`, cambiar a `ESTADO_EXPLORADA` vía `partida.cambiar` actualizando los contadores reversibles `num_exploradas` y `num_avistadas`; **no** cargar actores ni contenido de $w$, **no** activar enemigos ni trampas de $w$ (FR-007, FR-008). -> `python -m tests.test_niebla_ir_a`

**Checkpoint — US3**: Iluminación por antorcha funcional y reversible. Ejecutar `python -m tests.test_niebla_ir_a` — pruebas T021 deben pasar.

---

## Phase 6: User Story 4 — Persistencia, Registro y Reversión Temporal del Mapa Conocido (Priority: P2)

**Goal**: El mapa conocido se guarda y carga fidedignamente en formato v4; los archivos v3 se rechazan explícitamente; el pergamino revierte exactamente el último paso de movimiento.

**Independent Test**: Guardar partida, cerrar y recargar; el estado de conocimiento debe ser idéntico. Intentar cargar un archivo v3: debe producirse error claro sin corromper la sesión actual.

### Pruebas de Aceptación — US4

- [ ] T023 [US4] Escribir pruebas test-first en `tests/test_niebla_ir_a.py`: `test_FR011_guardado_incluye_estado_conocimiento`, `test_FR024_guardado_v3_reporta_incompatibilidad_explicita`, `test_FR024_guardado_v4_serializa_y_restaura_conocimiento`, `test_FR024_carga_v3_no_corrompe_partida_en_curso`, `test_FR023_reversion_pergamino_tras_viaje_deshace_solo_ultimo`, `test_FR013_cada_mutacion_conocimiento_queda_en_registro` (FR-011, FR-012, FR-013, FR-023, FR-024, SC-004). -> `python -m tests.test_niebla_ir_a`

### Implementación — US4

- [ ] T024 [US4] Actualizar `modelo/datos/guardado_binario.py`: establecer `VERSION_FORMATO = 4`; en `_leer_encabezado`: lanzar `ErrorFormato("versión de formato 3 incompatible (se esperaba 4): formato previo sin soporte de niebla de guerra")` cuando `version == 3`, y el mensaje estándar de versión incompatible para cualquier otra versión distinta de 4 (Contrato C7, FR-024). -> `python -m tests.test_niebla_ir_a`
- [ ] T025 [US4] Implementar serialización del conocimiento en `modelo/datos/guardado_binario.py`: ampliar `_empaquetar_general` añadiendo `n_salas: uint16`, `estados_salas: N bytes` (un byte por sala en orden de índice, `0`=Desconocida, `1`=Avistada, `2`=Explorada), `n_puertas_recordadas: uint16` y por cada puerta recordada con estado no-cero: `indice_sala: uint16`, `direccion: uint8` (0–3), `estado_recordado: uint8`; mantener intacto el bloque binario de enemigos `[instancia, tipo, vida, tiempo_siguiente]` sin incluir `rango` (Contrato C7). -> `python -m tests.test_niebla_ir_a`
- [ ] T026 [US4] Implementar deserialización del conocimiento en `modelo/datos/guardado_binario.py`: en `_desempaquetar_general`, leer el bloque de niebla de guerra y reconstruir `partida.conocimiento.estado_salas` y `memoria_puertas`; recalcular en $O(N)$ los contadores `num_exploradas` y `num_avistadas` al reconstruir (no usar `partida.cambiar` para este recalcular inicial, solo para mutaciones posteriores); `rango` del cazador se reconstruye desde catálogo en `mapa.incorporar` (Contrato C7, FR-011). -> `python -m tests.test_niebla_ir_a`
- [ ] T027 [US4] Actualizar `modelo/datos/persistencia_partida.py`: capturar `ErrorFormato` y convertirlo en `ErrorCarga`; reportar el mensaje descriptivo al controlador sin alterar la partida en curso ni corromper datos; garantizar que la sesión activa permanece intacta si la carga falla (FR-024). -> `python -m tests.test_niebla_ir_a`

**Checkpoint — US4**: Persistencia v4 completa y rechazo v3 funcional. Ejecutar `python -m tests.test_niebla_ir_a` — pruebas T023 deben pasar. Verificar con `python main.py --verificar`.

---

## Phase 7: Polish & Cross-Cutting Concerns — Benchmarks, Integración y Validación

**Propósito**: Instrumentar y verificar cuantitativamente SC-001..SC-004, integrar el nuevo benchmark en `main.py`, repetir suites de regresión y validar la guía de inicio rápido de `quickstart.md`.

- [ ] T028 [P] [BENCH] Crear `bench/bench_mapa_conocido.py` instrumentando las cuatro métricas de rendimiento: **SC-001** (recálculo completo de Dijkstra acotado sobre cripta de 1000 salas, meta `< 5.0 ms`); **SC-002** ($10^6$ consultas O(1) a `estado_salas`, `memoria_puertas` y `resumen()` sobre grafos de 10, 100 y 1000 salas); **SC-003** (exploración de sala sin y con antorcha, costo proporcional únicamente al número de salidas); **SC-004** (registro y reversión con pergamino en $O(1)$ por cambio) (SC-001, SC-002, SC-003, SC-004). -> `python main.py --bench mapa_conocido`
- [ ] T029 [P] [BENCH] Registrar `("mapa_conocido", "bench_mapa_conocido.py")` en la lista `BENCHES` dentro de `main.py` para habilitar `python main.py --bench mapa_conocido` (SC-001..SC-004). -> `python main.py --bench mapa_conocido`
- [ ] T030 [BENCH] Ejecutar y documentar las mediciones de regresión de los benchmarks existentes: `python main.py --bench cache`, `python main.py --bench lista_ordenada`, `python main.py --bench ordenamiento`, `python main.py --bench guardado`; verificar ausencia de regresiones de rendimiento introducidas por los cambios de esta capacidad (Constitución Principio VI). -> `python main.py --bench <subsistema>`
- [ ] T031 Ejecutar la suite completa de pruebas de aceptación `python -m tests.test_niebla_ir_a` y suites de regresión `python -m tests.test_motor_base`, `python -m tests.test_partida`; verificar cobertura del 100% de FR-001..FR-024 y SC-001..SC-005 conforme a los escenarios de `quickstart.md`. -> `python -m tests.test_niebla_ir_a`

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
