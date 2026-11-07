# Tasks: Terreno, cazador e invalidación de rutas

**Feature**: `001-terreno-cazador`  
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**Author**: Mariano (Motor del juego)

## Format: `[ID] [P?] [Story] Description (FR-xxx) -> Verificación`
- **[P]**: Tarea paralelizable (archivos distintos, sin dependencias mutuas directas).
- **[Story]**: Historia de usuario correspondiente (`[US1]`, `[US2]`, `[US3]`, `[BENCH]`).

---

## Phase 1: Pruebas de Aceptación Iniciales (Test-First)

**Propósito**: Escribir las pruebas automatizadas de aceptación que definen el comportamiento de costos antes de tocar el código de producción. *(Secuenciales sobre `tests/test_terreno_cazador.py`)*.

- [ ] T001 [US1] Crear archivo de pruebas `tests/test_terreno_cazador.py` e implementar pruebas de costo por defecto (100), validación estricta de costo (rechazo de booleanos, decimales, cadenas, cero y negativos) y simetría de salida (FR-001). -> `python -m tests.test_terreno_cazador`
- [ ] T002 [US1] Implementar pruebas en `tests/test_terreno_cazador.py` para la cota mínima de intervalo `max(1, costo*100//v)` con velocidad alta y costo 1 (FR-002). -> `python -m tests.test_terreno_cazador`
- [ ] T003 [US1] Implementar prueba en `tests/test_terreno_cazador.py` para la reprogramación por cambio de velocidad en salida costosa ($t=0$, costo 300, $v=100 \to 50$ en $t=100$, nuevo $t=500$) (FR-002). -> `python -m tests.test_terreno_cazador`
- [ ] T004 [US1] Implementar prueba en `tests/test_terreno_cazador.py` que compruebe que las acciones sin movimiento (atacar, esperar, usar, recoger, abrir) conservan sus costos base vigentes de P1 (FR-002). -> `python -m tests.test_terreno_cazador`
- [ ] T005 [US1] Implementar prueba de compatibilidad de errantes y rastreadores con salidas de costos variables en `tests/test_terreno_cazador.py`, verificando movimientos reales en la agenda (FR-002). -> `python -m tests.test_terreno_cazador`

---

## Phase 2: Infraestructura Fundacional y Bloque 1 (Costos de Movimiento)

**Propósito**: Implementar el soporte de costos en el motor y conectar la agenda temporal. **(Autónomo: Mariano puede ejecutarlo de inmediato sin dependencias de otros integrantes)**.

- [ ] T006 [US1] Extender `Salida.__init__` y `Sala.conectar` en `modelo/juego/sala.py` agregando `costo: int = 100` al final de la firma con validación estricta (`type(costo) is int and costo >= 1`), y agregar `Sala.indice` (FR-001). -> `python -m tests.test_terreno_cazador`
- [ ] T007 [US1] Modificar `modelo/juego/mapa.py` para leer `datos.get("costo", 100)`, asignar `sala.indice = p` contiguo desde el esqueleto, y normalizar cadenas de comportamiento contemplando mayúsculas, espacios y tildes (FR-001). -> `python -m tests.test_motor_base`
- [ ] T008 [US1] Modificar `partida.mover` en `modelo/juego/partida.py` para pasar `salida.costo` en lugar de la constante `COSTO_MOVER` a `self._accion` (FR-002). -> `python -m tests.test_terreno_cazador`
- [ ] T009 [US1] Modificar `modelo/juego/comportamiento.py` para que `resolver_turno` retorne el costo de la acción ejecutada (`COSTO_ATACAR`, `COSTO_ESPERAR` o `salida.costo`) en todas sus rutas de ejecución (FR-002). -> `python -m tests.test_terreno_cazador`
- [ ] T010 [US1] Actualizar `modelo/juego/motor_enemigos.py` para agendar el próximo turno del enemigo usando el costo retornado por `resolver_turno` y su velocidad (FR-002). -> `python -m tests.test_terreno_cazador`

**Checkpoint US1**: Ejecutar `python -m tests.test_terreno_cazador`, `python -m tests.test_motor_base` y `python -m tests.test_partida`. Todos deben pasar limpiamente.

---

## Phase 3: Bloque 2 - Punto Central de Puertas y Contrato C2 (Test-First)

**Propósito**: Unificar el control de estado de puertas y preparar el sistema de notificación para rutas, mapa conocido e historia. **(Autónomo)**.

- [ ] T011 [US3] Escribir pruebas de aceptación de centralización de puertas y restauración tras `deshacer_ultimo()` en `tests/test_terreno_cazador.py` (FR-008). -> `python -m tests.test_terreno_cazador`
- [ ] T012 [US3] Crear método `partida.cambiar_estado_puerta(salida, nuevo_estado)` en `modelo/juego/partida.py` que centraliza la mutación y emite avisos a observadores registrados (FR-008). -> `python -m tests.test_terreno_cazador`
- [ ] T013 [US3] Refactorizar `partida.abrir` en `modelo/juego/partida.py` y `efectos.programar_cierre` en `modelo/juego/efectos.py` para canalizar las mutaciones exclusivamente a través de `cambiar_estado_puerta` (FR-008). -> `python -m tests.test_partida`
- [ ] T014 [US3] Implementar en `partida.py` la gestión de retroceso: silenciar notificaciones individuales durante `deshacer_ultimo()` y emitir invalidación global de rutas al concluir el retroceso (FR-008). -> `python -m tests.test_terreno_cazador`

---

## Phase 4: Bloque 3 - Comportamiento del Cazador y Búsqueda (Contrato C3)

**Propósito**: Integrar la búsqueda de costo mínimo con montículo propio y desempate determinista por menor ID. *(Dependencia: Requiere entrega de C3 de Kim para `monticulo_min.py` - PENDIENTE)*.

- [ ] T015 [US2] Escribir pruebas de aceptación del cazador en `tests/test_terreno_cazador.py`: ataque al compartir sala, espera por falta de ruta, espera por $d > rango$, avance en límite exacto $d == rango$, preferencia de ruta más barata con más pasos y desempate por menor ID entero (FR-003, FR-004, FR-005, FR-006, FR-007). -> `python -m tests.test_terreno_cazador`
- [ ] T016 [US2] Incorporar campo `rango: int = 0` en `Enemigo` (`modelo/juego/actor.py`) y cargarlo desde la ficha en `mapa.py` coordinado con C5, identificando la compatibilidad de guardado/carga con Kim (FR-004). -> `python -m tests.test_terreno_cazador`
- [ ] T017 [US2] Integrar `monticulo_min.py` y función `dijkstra_acotado` provistos por Kim (Contrato C3 - PENDIENTE) en `modelo/estructuras/` (FR-005). -> `python -m tests.test_terreno_cazador`
- [ ] T018 [US2] Implementar en `modelo/juego/cazador.py` el cálculo compartido desde la posición del jugador acotado a $R_{\text{utilizado}}$, con arreglos contiguos de tamaño $N$ indexados por `Sala.indice` y token de búsqueda $O(1)$ sin reinicialización (FR-005). -> `python -m tests.test_terreno_cazador`
- [ ] T019 [US2] Implementar en `modelo/juego/comportamiento.py` la función `_cazador(partida, enemigo)`: verificar sala compartida (atacar), consultar distancia mínima hacia el jugador, verificar $d \le rango$, desempatar por menor `id` entero de sala vecina abierta y avanzar agendando con `salida.costo` (FR-003, FR-004, FR-005, FR-006). -> `python -m tests.test_terreno_cazador`
- [ ] T020 [US2] Agregar prueba de aceptación de cazador operando con salas no descargadas y niebla de guerra activa del jugador, validando que no abre puertas cerradas (FR-007). -> `python -m tests.test_terreno_cazador`

---

## Phase 5: Bloque 4 - Invalidación Reactiva de Rutas (Test-First)

**Propósito**: Garantizar la equivalencia observable estricta con un cálculo desde cero ante eventos dinámicos.

- [ ] T021 [US3] Agregar pruebas de aceptación en `tests/test_terreno_cazador.py` para:
  - Puerta de la ruta cerrada entre dos turnos del cazador (Apéndice B).
  - Apertura de puerta que desbloquea ruta previamente inaccesible dentro del rango.
  - Desplazamiento del jugador a una nueva sala entre turnos del cazador.
  - Activación de cazador que requiere $R_{\text{activo}} > R_{\text{utilizado}}$ (FR-008). -> `python -m tests.test_terreno_cazador`
- [ ] T022 [US3] Implementar en `modelo/juego/cazador.py` la lógica de invalidación reactiva diferenciando $R_{\text{activo}}$ y $R_{\text{utilizado}}$, conservando distancias si el jugador no se movió, no aumenta el rango requerido y ninguna puerta con extremo $\le R_{\text{utilizado}}$ cambió de estado (FR-008). -> `python -m tests.test_terreno_cazador`
- [ ] T023 [US3] Conectar el despachador de puertas de `Partida` (Contrato C2) con la caché de rutas del cazador (FR-008). -> `python -m tests.test_terreno_cazador`

---

## Phase 6: Benchmarks, Integración y Documentación (SC-004, SC-005, SC-006, §5.6)

**Propósito**: Validar empíricamente los presupuestos y documentar las decisiones de diseño.

- [ ] T024 [P] [BENCH] Integrar el comando `--bench cazador` en `main.py` dentro de `SUBSISTEMAS_BENCH` (SC-004..SC-006). -> `python main.py --bench cazador`
- [ ] T025 [BENCH] Crear `bench/bench_cazador.py` instrumentando la medición del tiempo de cada ciclo individual entre decisiones del jugador (sintético y preparado para cripta de referencia de cátedra), reportando `tiempo_maximo_ms` y conteo de ciclos que exceden los 20 ms (SC-004). -> `python main.py --bench cazador`
- [ ] T026 [BENCH] Implementar en `bench/bench_cazador.py` la comparación sistemática entre cálculo individual y compartido variando densidad (1, 10, 30 y 100 cazadores) y rangos (pequeño frente a grande) sobre criptas sintéticas deterministas (SC-005). -> `python main.py --bench cazador`
- [ ] T027 [BENCH] Implementar en `bench/bench_cazador.py` la comparación entre reutilización con invalidación y recálculo continuo en escenarios con puertas estables e inestables, verificando equivalencia observable en cada paso (SC-006). -> `python main.py --bench cazador`
- [ ] T028 [BENCH] Repetir `bench/bench_motor.py` con cazadores activos y costos variables para contrastar el rendimiento de la agenda de eventos contra las mediciones de la primera parte (§5.6). -> `python -m bench.bench_motor`
- [ ] T029 [P] [BENCH] Redactar las secciones de Mariano en `DECISIONES.md` (§5.1, §5.2 y la revisión §5.6 del motor) enlazando `spec.md` y `plan.md`.
