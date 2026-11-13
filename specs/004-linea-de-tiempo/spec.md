# Feature Specification: Línea de tiempo de CRIPTA

**Feature Branch**: `004-linea-de-tiempo`

**Created**: 2026-11-13

**Status**: Aclarada; lista para la fase plan.

**Input**: Línea de tiempo independiente del pergamino de retroceso, consultas históricas y reproducción hasta un instante, conservación al guardar y cargar, límites de memoria y rendimiento medidos, y presentación de información de la partida.

## Clarifications

### Session 2026-11-13

- Q: ¿Cómo se numeran las acciones después de un pergamino? → A: Por su posición en la historia vigente: las revertidas desaparecen y la siguiente acción toma su número, igual que el contador de acciones de la partida (FR-003).
- Q: ¿Cuándo se conservan puntos de control? → A: En el instante 0 y luego exactamente cada K acciones del jugador; nunca más de una copia completa por cada K acciones ni más de K acciones entre dos puntos de control (FR-012).
- Q: ¿Se mantiene el requisito sobre números de sala con ids que no terminan en número? → A: Se elimina FR-018, junto con su escenario y su caso límite, sin renumerar los demás FR. Los ids de sala son enteros en el contrato de datos; el problema de la primera parte correspondía a etiquetas de enemigos y ya está resuelto.
- Q: ¿Qué cuenta como acción número k? → A: Solo una acción aceptada del jugador que avanza el contador de acciones. Las órdenes rechazadas, historia, ayuda, inventario y mapa no cuentan; cada paso de un viaje «ir a» sí cuenta (FR-003).
- Q: ¿Qué consultas iniciales, actuales e inválidas se admiten? → A: `historia #1` muestra el estado inicial; si N es el número de acciones realizadas en la historia vigente, `historia #(N+1)` muestra el estado actual, justo antes de la próxima acción. Un k menor que 1 o mayor que N+1 se rechaza con un mensaje. Un t negativo o no entero se rechaza con un mensaje; `historia 0` muestra el estado del instante 0 (FR-003, FR-006).
- Q: ¿Cómo se presenta un estado histórico con derrota o victoria? → A: Si en el instante consultado el jugador ya había sido derrotado o había ganado, el resumen lo indica (FR-004).
- Q: ¿Cuándo se puede consultar historia y qué ocurre con el resultado? → A: Durante la partida y en la pantalla final; consultar nunca cambia el resultado (FR-019).
- Q: ¿Cómo se consulta historia en cada interfaz? → A: En Pygame, H abre un cuadro donde se escribe t o #k y un panel con el resumen; Escape lo cierra sin afectar la partida. En consola se usan `historia <t>` e `historia #k` (FR-020).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar el pasado sin alterar la partida (Priority: P1)

Como jugador, quiero consultar el estado desde el inicio por tiempo o por número de acción para revisar lo ocurrido sin cambiar mi partida ni gastar el retroceso disponible.

**Why this priority**: La consulta fiel y sin efectos sobre la partida es el propósito principal de la línea de tiempo.

**Independent Test**: Comparar los resúmenes históricos con los estados observados al jugar y comprobar que consultar conserva la partida, su reloj, su registro y sus posibilidades de retroceso.

**Acceptance Scenarios**:

1. **test_FR001_historia_desde_inicio**: **Given** una partida con más de cinco acciones, **When** se consulta un instante desde el inicio anterior a las últimas cinco acciones, **Then** se muestra el estado de ese instante aunque el pergamino siga limitado a cinco acciones.
2. **test_FR002_eventos_mismo_instante**: **Given** varios eventos con el mismo tiempo t, **When** se ejecuta `historia <t>`, **Then** el resumen corresponde al estado después de todos esos eventos.
3. **test_FR002_estado_antes_decision**: **Given** un instante t que corresponde a una decisión del jugador, **When** se consulta t, **Then** se muestra el estado tras los eventos con tiempo menor o igual que t y justo antes de tomar esa decisión.
4. **test_FR003_historia_por_accion**: **Given** una acción aceptada número k de la historia vigente, **When** se ejecuta `historia #k`, **Then** se muestra el estado justo antes de esa acción, numerada por su posición en la historia vigente y de acuerdo con el contador de acciones de la partida.
5. **test_FR004_resumen_historico_completo**: **Given** un instante con inventario, efectos, enemigos y conocimiento del mapa, **When** se consulta, **Then** aparecen el reloj, la sala del jugador, su vida y estadísticas, el inventario en su orden de ese instante, los efectos activos, los enemigos de esa sala con su vida, las salas exploradas y avistadas, y el estado recordado de las puertas de ese momento.
6. **test_FR005_consulta_sin_efectos**: **Given** una partida con acciones que el pergamino puede deshacer, **When** se consulta su historia, **Then** no transcurre tiempo virtual, no se cuenta una acción, no se agrega nada a `partida.log` y permanecen idénticos el estado y el historial de retroceso.
7. **test_FR006_rechazo_instante_futuro**: **Given** un reloj actual menor que t, **When** se ejecuta `historia <t>`, **Then** la consulta se rechaza con un mensaje.
8. **test_FR003_numeracion_tras_pergamino**: **Given** un pergamino que eliminó las últimas acciones, **When** el jugador realiza otra acción aceptada, **Then** esta ocupa el siguiente número de la historia vigente, reutilizando el número de la primera acción eliminada y coincidiendo con el contador de la partida.
9. **test_FR003_solo_acciones_aceptadas**: **Given** una partida, **When** se realizan acciones aceptadas, órdenes rechazadas y consultas de historia, ayuda, inventario y mapa, **Then** solo las acciones aceptadas que avanzan el contador se numeran; cada paso de un viaje «ir a» cuenta como una acción.
10. **test_FR003_primera_y_proxima_accion**: **Given** N acciones realizadas en la historia vigente, **When** se consulta `historia #1` y `historia #(N+1)`, **Then** se muestran respectivamente el estado inicial y el estado actual justo antes de la próxima acción.
11. **test_FR003_rechazo_numero_fuera_rango**: **Given** N acciones realizadas en la historia vigente, **When** se consulta un k menor que 1 o mayor que N+1, **Then** se rechaza con un mensaje.
12. **test_FR006_rechazo_tiempo_negativo_o_no_entero**: **Given** una partida, **When** se consulta `historia <t>` con t negativo o no entero, **Then** se rechaza con un mensaje.
13. **test_FR006_historia_cero**: **Given** una partida, **When** se ejecuta `historia 0`, **Then** se muestra el estado del instante 0.
14. **test_FR004_resumen_derrota_o_victoria**: **Given** un instante en el que el jugador ya había sido derrotado o había ganado, **When** se consulta ese instante, **Then** el resumen indica la derrota o la victoria correspondiente.
15. **test_FR019_historia_durante_y_al_final**: **Given** una partida en curso o su pantalla final, **When** se consulta historia, **Then** la consulta está disponible y no cambia el resultado de la partida.
16. **test_FR020_historia_en_pygame_y_consola**: **Given** la interfaz de Pygame, **When** se pulsa H y se escribe t o #k, **Then** se muestra el resumen en un panel que se cierra con Escape sin afectar la partida; **Given** la consola, **When** se introduce `historia <t>` o `historia #k`, **Then** se muestra el resumen correspondiente.

---

### User Story 2 - Consultar la historia que permanece tras un retroceso (Priority: P1)

Como jugador, quiero que la historia refleje únicamente lo que sigue siendo parte de mi partida después de usar un pergamino, conservando los cambios que este no revierte.

**Why this priority**: El pasado consultable debe ser coherente con la partida que continúa después del retroceso.

**Independent Test**: Revertir acciones y contrastar la historia resultante, incluyendo una revelación por antorcha y un cambio de memoria fuera de una acción.

**Acceptance Scenarios**:

1. **test_FR009_historia_sin_acciones_revertidas**: **Given** acciones ejecutadas y después revertidas con un pergamino, **When** se consulta la historia que permanece, **Then** no aparecen esas acciones ni sus cambios revertidos.
2. **test_FR009_antorcha_revertida**: **Given** una entrada con antorcha que reveló salas y luego fue revertida por un pergamino, **When** se consulta la historia resultante, **Then** no se muestran como reveladas las salas cuyo conocimiento procedía de esa entrada revertida.
3. **test_FR010_memoria_fuera_de_accion**: **Given** una actualización de la memoria de una puerta observada durante un viaje automático, fuera de una acción del jugador y sin consumir tiempo, **When** se consulta su instante, **Then** esa actualización forma parte del estado histórico y permanece después de un pergamino que no la revierte.

---

### User Story 3 - Reproducir y conservar la historia completa (Priority: P2)

Como jugador, quiero reproducir una partida hasta un instante sin interfaz y conservar toda su línea de tiempo cuando guardo y cargo.

**Why this priority**: Permite revisar la misma información histórica fuera de la sesión en la que se jugó.

**Independent Test**: Comparar el resumen de reproducción con la consulta histórica correspondiente y comparar las consultas antes y después de guardar y cargar.

**Acceptance Scenarios**:

1. **test_FR007_replay_hasta_instante**: **Given** un `partida.log` y un instante t de la partida, **When** se ejecuta `--replay partida.log --hasta <t>`, **Then** se reproduce hasta t y se imprime el mismo resumen que la consulta histórica correspondiente, sin crear una interfaz.
2. **test_FR008_replay_posterior_al_final**: **Given** una partida terminada antes de t, **When** se ejecuta `--replay partida.log --hasta <t>`, **Then** se imprime el resumen del estado final y se indica que la partida terminó antes del instante solicitado.
3. **test_FR014_guardar_cargar_historia_completa**: **Given** una partida con historia desde el inicio, acciones revertidas y cambios fuera de acciones, **When** se guarda y se carga, **Then** se conserva la línea de tiempo completa que permanecía al guardar y sus consultas devuelven los mismos estados.

---

### User Story 4 - Consultar partidas extensas con recursos acotados (Priority: P2)

Como jugador, quiero consultar rápidamente una partida extensa, con un uso de memoria ligado a sus cambios y con una frecuencia de puntos de control configurable y respaldada por mediciones.

**Why this priority**: La consulta de toda la partida debe seguir siendo útil cuando ya se han realizado miles de acciones.

**Independent Test**: Medir tiempos y memoria en una partida de al menos 5000 acciones y verificar los límites de trabajo por consulta y de almacenamiento.

**Acceptance Scenarios**:

1. **test_FR011_configurar_checkpoint_cada**: **Given** un valor K para la frecuencia de puntos de control, **When** se inicia con `--checkpoint-cada K`, **Then** se utiliza ese valor; al omitir la opción, se utiliza el valor por defecto justificado por las mediciones.
2. **test_FR012_copias_solo_en_puntos_control**: **Given** una partida con K configurado, **When** comienza y avanza, **Then** existe un punto de control en el instante 0 y después uno exactamente cada K acciones del jugador, sin copias completas intermedias ni más de K acciones entre dos puntos de control.
3. **test_FR013_conservar_solo_cambios_entre_puntos**: **Given** el intervalo entre dos puntos de control, **When** se conserva su historia, **Then** fuera de los puntos de control solo se guarda lo necesario para reconstruir los cambios.
4. **test_SC001_historia_menos_50ms**: **Given** una partida de al menos 5000 acciones y el K por defecto, **When** se mide una consulta `historia`, **Then** responde en menos de 50 ms.
5. **test_SC002_consulta_limite_K_acciones**: **Given** una historia con K configurado, **When** se consulta cualquier estado disponible, **Then** la consulta no aplica ni deshace cambios de más de K acciones del jugador.
6. **test_SC003_memoria_segun_cambios**: **Given** partidas con distintos números de acciones y tamaños de estado, **When** se mide la memoria histórica, **Then** su crecimiento corresponde a los cambios ocurridos más un punto de control cada K acciones, sin crecer como el número de acciones multiplicado por el tamaño del estado.
7. **test_SC004_recorte_sin_recorrer_historia**: **Given** una partida con historia extensa, **When** se usa un pergamino, **Then** la línea se recorta sin recorrer toda la historia.
8. **test_SC005_comparar_valores_K**: **Given** las mediciones de `--bench`, **When** se comparan las alternativas, **Then** se presentan memoria y tiempo de consulta para al menos tres valores de K y para la alternativa sin puntos de control, y se justifica con esos resultados el K por defecto.

---

### User Story 5 - Ver información de inicio y de la sala actual (Priority: P2)

Como jugador, quiero ver el reporte de resolubilidad al iniciar, el costo de cada salida y la diferencia visual entre cazadores y otros enemigos para interpretar la situación.

**Why this priority**: Estos datos permiten entender el inicio de la expedición y la información presentada durante el juego.

**Independent Test**: Revisar el inicio y una sala con varias salidas y tipos de enemigos.

**Acceptance Scenarios**:

1. **test_FR015_reporte_inicio**: **Given** el resultado de resolubilidad de una cripta, **When** se presenta el inicio de una partida, **Then** el reporte aparece en la interfaz activa siguiendo FR-015 y la plantilla y reglas de FR-018 de `specs/003-resolubilidad/spec.md`.
2. **test_FR016_costos_salidas**: **Given** una sala actual con salidas de distintos costos, **When** se muestra la sala, **Then** se muestra el costo correspondiente a cada salida.
3. **test_FR017_cazadores_distinguibles**: **Given** cazadores y otros enemigos, **When** se muestran, **Then** los cazadores se distinguen visualmente del resto.

### Edge Cases

- Varios eventos comparten el tiempo consultado: se incluyen todos (FR-002).
- El tiempo consultado corresponde a una decisión: se muestra el estado justo antes de tomarla (FR-002).
- El instante consultado supera el reloj actual: `historia` lo rechaza con un mensaje (FR-006).
- El instante solicitado en una reproducción supera el final: se muestra el estado final con la indicación de terminación anterior (FR-008).
- El pergamino revierte conocimiento de salas reveladas por una antorcha: ese conocimiento revertido no aparece en la historia restante (FR-009).
- Un cambio fuera de una acción no consume tiempo y no es revertido por el pergamino: permanece en su instante histórico (FR-010).
- El jugador pide `historia #k` después de un retroceso: los números corresponden a la historia vigente; la próxima acción reutiliza el número de la primera eliminada (FR-003).
- No se ha realizado ninguna acción: `historia #1` muestra el estado inicial, que también es el actual (FR-003).
- Con N acciones vigentes, k menor que 1 o mayor que N+1 se rechaza; k igual a N+1 muestra el estado actual (FR-003).
- Un t negativo o no entero se rechaza; t igual a 0 muestra el estado del instante 0 (FR-006).
- El estado consultado ya corresponde a una derrota o victoria: el resumen lo indica (FR-004).
- Se consulta desde la pantalla final: historia sigue disponible y no cambia el resultado (FR-019).
- Se cierra el panel histórico de Pygame con Escape: la partida no se ve afectada (FR-020).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La línea de tiempo DEBE permitir consultar, sin modificar la partida, su estado en cualquier instante desde el inicio, independientemente del pergamino de retroceso, que sigue limitado a cinco acciones.
- **FR-002**: El estado en t DEBE ser el resultante después de ejecutar todos los eventos con tiempo menor o igual que t, incluidos todos los que comparten t. Si t corresponde a una decisión del jugador, DEBE ser el estado justo antes de tomarla.
- **FR-003**: El jugador DEBE poder consultar con `historia <t>` y con `historia #k`; esta última forma muestra el estado justo antes de su acción número k. Solo cuenta como acción una acción aceptada del jugador que avanza el contador de acciones; las órdenes rechazadas, historia, ayuda, inventario y mapa no cuentan, y cada paso de un viaje «ir a» sí cuenta. Las acciones DEBEN numerarse por su posición en la historia vigente, de acuerdo con el contador de acciones de la partida: tras un pergamino, las revertidas desaparecen y la próxima acción toma el número de la primera eliminada. Si N es el número de acciones realizadas en la historia vigente, `historia #1` DEBE mostrar el estado inicial y `historia #(N+1)` el estado actual justo antes de la próxima acción. Un k menor que 1 o mayor que N+1 DEBE rechazarse con un mensaje.
- **FR-004**: Cada consulta DEBE mostrar, como mínimo, el reloj, la sala del jugador, su vida y estadísticas, el inventario en el orden que tenía, los efectos activos, los enemigos de esa sala con su vida y el mapa conocido de ese instante, diferenciando salas exploradas, salas avistadas y estado recordado de las puertas. Si en ese instante el jugador ya había sido derrotado o había ganado, el resumen DEBE indicarlo.
- **FR-005**: Consultar la historia NO DEBE consumir tiempo virtual, contar como acción, escribirse en `partida.log`, modificar el estado ni modificar el historial o las posibilidades de retroceso del pergamino.
- **FR-006**: `historia <t>` DEBE rechazar con un mensaje cualquier t negativo, no entero o posterior al reloj actual. `historia 0` DEBE mostrar el estado en el instante 0.
- **FR-007**: `--replay partida.log --hasta <t>` DEBE reproducir la partida hasta t e imprimir el mismo resumen histórico, con la misma interpretación del instante, sin crear una interfaz.
- **FR-008**: Si t es posterior al final de la partida reproducida, `--replay partida.log --hasta <t>` DEBE mostrar el estado final e indicar que la partida terminó antes del instante solicitado.
- **FR-009**: Las acciones revertidas por un pergamino y sus cambios revertidos DEBEN dejar de existir en la línea de tiempo. Esto incluye el conocimiento de salas reveladas por una entrada con antorcha que haya sido revertida.
- **FR-010**: Los cambios ocurridos fuera de una acción del jugador DEBEN formar parte de la línea de tiempo en su instante, aunque no consuman tiempo. Si el pergamino no los revierte, DEBEN permanecer en ella, incluida la actualización de memoria de una puerta observada durante un viaje automático.
- **FR-011**: La frecuencia K de puntos de control DEBE configurarse con `--checkpoint-cada K`. Su valor por defecto DEBE justificarse con las mediciones de rendimiento.
- **FR-012**: DEBE existir un punto de control en el instante 0 y luego uno exactamente cada K acciones del jugador. Después del punto inicial, NO DEBE haber más de una copia completa por cada K acciones ni más de K acciones entre dos puntos de control.
- **FR-013**: Fuera de los puntos de control solo DEBE guardarse lo necesario para reconstruir los cambios.
- **FR-014**: Guardar y cargar una partida DEBE conservar su línea de tiempo completa.
- **FR-015**: Al iniciar una partida se DEBE mostrar el reporte de resolubilidad en la interfaz activa conforme a FR-015 y a la plantilla y reglas de FR-018 de `specs/003-resolubilidad/spec.md`.
- **FR-016**: Se DEBE mostrar el costo de cada salida de la sala actual.
- **FR-017**: Los cazadores DEBEN distinguirse visualmente del resto de enemigos.
- **FR-019**: Historia DEBE poder consultarse durante la partida y en la pantalla final, sin cambiar nunca el resultado de la partida.
- **FR-020**: En Pygame, la tecla H DEBE abrir un cuadro donde se escribe t o #k y un panel con el resumen; Escape DEBE cerrar el panel sin afectar la partida. En consola, la consulta DEBE realizarse con `historia <t>` o `historia #k`.

### Key Entities *(include if feature involves data)*

- **Estado histórico**: Situación de la partida en un instante, con la información del jugador, su inventario, efectos, enemigos de su sala y conocimiento del mapa.
- **Acción del jugador**: Acción aceptada que avanza el contador de acciones, numerada por su posición en la historia vigente. Cada paso de un viaje «ir a» cuenta; las órdenes rechazadas y las consultas de historia, ayuda, inventario y mapa no cuentan. Su estado inmediatamente anterior puede consultarse y puede quedar eliminada de la historia por un pergamino.
- **Evento**: Cambio con un tiempo de ocurrencia, dentro o fuera de una acción del jugador.
- **Línea de tiempo**: Historia vigente desde el inicio, con las acciones y cambios que permanecen tras los retrocesos.
- **Punto de control**: Copia completa del estado conservada en el instante 0 y después exactamente cada K acciones del jugador.
- **Resumen histórico**: Información mínima de FR-004, compartida por las consultas y la reproducción hasta un instante.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `historia` DEBE responder en menos de 50 ms en una partida de al menos 5000 acciones con el K por defecto.
- **SC-002**: Una consulta NO DEBE aplicar ni deshacer cambios de más de K acciones del jugador.
- **SC-003**: La memoria total de la línea de tiempo DEBE crecer con los cambios ocurridos más un punto de control cada K acciones, nunca con el producto del número de acciones por el tamaño del estado.
- **SC-004**: Al usar un pergamino, la línea de tiempo DEBE recortarse sin recorrer toda la historia.
- **SC-005**: `--bench` DEBE medir memoria y tiempo de consulta para al menos tres valores de K y para la alternativa sin puntos de control; esas mediciones DEBEN justificar el valor de K por defecto.

## Assumptions

- La presentación del reporte de resolubilidad depende de los resultados y del contrato de presentación ya definidos en `specs/003-resolubilidad/spec.md`, especialmente FR-015 y FR-018; esta feature no redefine la verificación.
- Los puntos de control y los límites de almacenamiento y consulta se incluyen porque son restricciones expresas de la solicitud; su diseño se deja para la planificación.
- Los ids de sala son enteros conforme al contrato de datos. La corrección de etiquetas de enemigos de la primera parte ya está resuelta y queda fuera del alcance de esta feature.
