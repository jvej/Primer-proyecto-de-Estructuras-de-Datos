# Feature Specification: Terreno, cazador e invalidación de rutas

**Feature Branch**: `001-terreno-cazador`  
**Created**: 2026-11-07  
**Status**: Clarified  
**Owner**: Mariano  
**Internal Target**: 2026-11-11  
**Backup Deadline**: 2026-11-15  
**Official Delivery**: 2026-11-18  
**Input**: Capacidad 001 de CRIPTA Parte II: terreno, costo variable de salidas, comportamiento de enemigo cazador con rango y búsqueda de ruta de costo mínimo, desempate determinista por menor ID de sala, e invalidación reactiva de rutas ante eventos del entorno.

---

## Clarifications

### Session 2026-11-07

- **Q: ¿El alcance de la capacidad 001 incluye la representación visual del cazador y los costos en la interfaz gráfica/consola, o se limita a la lógica del motor y sus pruebas?**
  - **Decision**: Mariano es responsable de las reglas del motor para la capacidad 001 (costos de terreno, agenda de eventos, comportamiento del cazador, equivalencia de rutas e invalidación reactiva), sus pruebas automatizadas, los benchmarks asociados, la integración de mediciones y la documentación técnica. La presentación visual en consola y Pygame corresponde al reparto de responsabilidades acordado con Axel y Kim.
  - **Rationale**: Mantiene una estricta separación de responsabilidades entre subsistemas, preserva la independencia del motor para ejecutar pruebas y mediciones de rendimiento sin interfaz gráfica ni dependencias visuales, y respeta los contratos de trabajo del equipo.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Costo de terreno y movimiento ponderado para todos los actores (Priority: P1)

Como jugador o entidad dentro de la cripta, quiero que atravesar una salida tome un tiempo proporcional a la dificultad del terreno y a la velocidad del actor, para que el mapa tenga pasos rápidos y pasos lentos que condicionen el avance táctico de todas las criaturas sin alterar la duración de otras acciones.

**Why this priority**: Es la base física del juego para la segunda parte. Todo el movimiento de actores (jugador, errante, rastreador y cazador) y la agenda de eventos dependen de que las salidas calculen el intervalo de reloj virtual hasta la siguiente actuación del actor en función del costo de terreno.

**Independent Test**: Asignar distintos costos y velocidades a salidas y actores; verificar que el intervalo programado en el reloj virtual coincide exactamente con la fórmula matemática y que las acciones sin movimiento conservan rigurosamente su duración base vigente.

**Acceptance Scenarios**:

1. **Given** un actor con velocidad alta (por ejemplo, velocidad 200 o superior) y una salida con costo de terreno igual a 1 iniciada en el instante $t$,  
   **When** el actor realiza la acción de cruzar dicha salida,  
   **Then** su siguiente actuación en el reloj virtual queda programada exactamente para el instante $t + 1$ (cumpliendo la cota mínima `max(1, 1 * 100 // velocidad)`).

2. **Given** un actor con velocidad 100 que en el instante $t = 0$ inicia el cruce de una salida de costo 300 (con su siguiente actuación programada para $t = 300$, dado que `300 * 100 // 100 = 300`),  
   **When** en el instante $t = 100$ sufre un efecto que reduce su velocidad a 50 (quedando un tiempo restante de 200 pulsos con la velocidad original),  
   **Then** aplicando la regla vigente de reprogramación proporcional de P1 §2.3 (`max(1, restante * velocidad_anterior // velocidad_nueva) = max(1, 200 * 100 // 50) = 400`), el tiempo restante pasa a ser de 400 pulsos y el evento de su siguiente actuación se reprograma exactamente para el instante $t = 100 + 400 = 500$.

3. **Given** una salida en el esqueleto de la cripta que no declara de forma explícita su campo de costo,  
   **When** cualquier actor decide atravesarla,  
   **Then** el intervalo hasta su siguiente actuación se calcula utilizando el costo predeterminado de 100 unidades de terreno.

4. **Given** una salida que conecta la sala A con la sala B con un costo asignado `C`,  
   **When** un actor se desplaza desde A hacia B, y posteriormente otro actor (o el mismo) se desplaza desde B hacia A con la misma velocidad,  
   **Then** en ambos casos el intervalo programado hasta su siguiente actuación es idéntico (simetría estricta de costo en ambos sentidos de la salida).

5. **Given** un actor en una sala con salidas de costos arbitrarios,  
   **When** ejecuta una acción distinta al movimiento,  
   **Then** el intervalo programado hasta su siguiente actuación conserva de forma estricta los costos base vigentes de la primera parte: costo 100 para atacar o esperar, costo 50 para usar o equipar un objeto, costo 25 para recoger o soltar un objeto y costo 50 para abrir una puerta (calculando el intervalo como `max(1, costo_base * 100 // velocidad)`), sin verse afectado por el terreno de las salidas contiguas.

6. **Given** un enemigo de tipo errante o rastreador en una sala con salidas de costos variables,  
   **When** llega su turno y elige su dirección según sus reglas de comportamiento existentes,  
   **Then** conserva su lógica original de selección de movimiento, pero el intervalo agendado hasta su siguiente turno refleja el costo de la salida atravesada.

---

### User Story 2 - Comportamiento de búsqueda y ataque del cazador (Priority: P1)

Como habitante hostil de la cripta de tipo cazador, quiero evaluar en mi turno la posición actual del jugador para atacarlo si estamos juntos o avanzar por el camino transitable más barato dentro de mi rango de alcance, para perseguirlo eficientemente sin desperdiciar turnos.

**Why this priority**: Es el comportamiento central del nuevo enemigo. Introduce la toma de decisiones por costo mínimo acumulado en lugar de simple conteo de salas.

**Independent Test**: Ubicar a un cazador y al jugador en diversas configuraciones de salas con salidas abiertas, cerradas y con costos dispares; verificar si ataca, avanza por la ruta de menor costo acumulado o espera según su rango.

**Acceptance Scenarios**:

1. **Given** un cazador y el jugador que se encuentran en la misma sala en el turno del cazador,  
   **When** el cazador ejecuta su turno,  
   **Then** ataca inmediatamente al jugador (según las reglas de combate P1 §2.8) en lugar de intentar desplazarse o buscar ruta.

2. **Given** un cazador en una sala sin ninguna ruta abierta hacia la sala actual del jugador (por ejemplo, todas las salidas intermedias están cerradas o no hay conectividad),  
   **When** el cazador ejecuta su turno,  
   **Then** no se mueve y realiza una acción de espera con costo base 100.

3. **Given** un cazador cuyo costo mínimo de ruta abierta hacia el jugador $d$ es estrictamente mayor que su rango asignado ($d > \text{rango}$),  
   **When** el cazador ejecuta su turno,  
   **Then** decide esperar consumiendo un costo base de 100 unidades sin realizar ningún desplazamiento.

4. **Given** un cazador cuyo costo mínimo de ruta abierta hacia el jugador $d$ es exactamente igual a su rango asignado ($d == \text{rango}$),  
   **When** el cazador ejecuta su turno,  
   **Then** decide avanzar un paso hacia la primera sala de dicha ruta de costo mínimo, agendando su siguiente actuación con el costo de la salida atravesada (prueba del límite del rango).

5. **Given** dos rutas alternativas abiertas entre el cazador y el jugador: una ruta A que requiere menos salas intermedias pero tiene un costo total mayor (por ejemplo, 1 paso directo de costo 300) y una ruta B que requiere más salas pero tiene un costo total menor (por ejemplo, 3 pasos de costo 50 cada uno, total 150),  
   **When** el cazador evalúa su movimiento,  
   **Then** elige avanzar hacia la primera sala vecina de la ruta B (la de menor costo acumulado total), ignorando que contenga más pasos.

6. **Given** dos salas vecinas inmediatas (por ejemplo, sala con ID 2 y sala con ID 5, según los enteros definidos en el contrato de datos) que forman parte de dos rutas diferentes pero que ambas alcanzan al jugador con el mismo costo mínimo total $d$,  
   **When** el cazador debe seleccionar su primer paso,  
   **Then** desempata de forma determinista eligiendo la vecina con menor identificador entero (sala con ID 2) y avanza hacia ella.

7. **Given** una cripta con salas cuya descripción de contenido no ha sido descargada y donde el jugador tiene niebla de guerra activa,  
   **When** el cazador toma su decisión de movimiento,  
   **Then** utiliza su conocimiento completo del esqueleto y del estado real de las puertas sin que su decisión sea bloqueada ni alterada por la niebla del jugador ni por la descarga diferida de contenido.

8. **Given** un cazador frente a una puerta cerrada que forma parte de la ruta geométrica más corta hacia el jugador,  
   **When** evalúa sus opciones de movimiento,  
   **Then** no abre la puerta cerrada y solo transita por salidas que se encuentren abiertas en ese instante.

---

### User Story 3 - Equivalencia con cálculo desde cero e invalidación reactiva de rutas (Priority: P2)

Como árbitro del juego y evaluador de determinismo, quiero que cada decisión del cazador refleje fielmente el estado dinámico de la cripta en el instante exacto de su turno, para que los cambios en puertas, movimientos de actores o retrocesos temporales produzcan decisiones idénticas a un recálculo limpio sin inconsistencias por datos desactualizados.

**Why this priority**: Garantiza que cualquier optimización interna (reutilización de búsquedas, cálculos compartidos o cachés de distancia) no introduzca discrepancias observables respecto a las reglas oficiales del juego.

**Independent Test**: Provocar eventos dinámicos (cierre de puertas automáticas, apertura con llaves, desplazamientos del jugador, uso de pergamino de retroceso) justo antes del turno del cazador y comprobar que su elección coincide al 100% con un cálculo fresco.

**Acceptance Scenarios**:

1. **Given** un cazador que en su turno en el instante $t_1$ determinó su ruta hacia la sala donde se encontraba el jugador (sala X) y avanzó un paso,  
   **When** antes del siguiente turno del cazador en $t_2$, el jugador realiza un movimiento y se traslada a una sala distinta (sala Y),  
   **Then** en el instante $t_2$ el cazador evalúa el costo mínimo tomando como destino la sala actual del jugador (sala Y) y su decisión coincide exactamente con la que resultaría de un cálculo desde cero hacia dicha sala.

2. **Given** un cazador que en su turno anterior comenzó a seguir una ruta abierta hacia el jugador,  
   **When** una puerta perteneciente a dicha ruta se cierra antes de que comience su siguiente turno,  
   **Then** en su nuevo turno el cazador detecta inmediatamente el bloqueo y decide su acción (buscar ruta alterna abierta o esperar si no existe dentro de su rango) exactamente como si hubiera calculado la ruta desde cero en ese instante.

3. **Given** un cazador que se encontraba esperando porque una puerta cerrada impedía toda ruta dentro de su rango,  
   **When** dicha puerta se abre (por interacción del jugador o evento del mapa) antes de su turno,  
   **Then** en su siguiente turno el cazador reconoce la nueva ruta abierta disponible y comienza a avanzar hacia el jugador sin demoras residuales.

4. **Given** una partida donde una puerta fue abierta por el jugador y el cazador adaptó su desplazamiento hacia esa apertura,  
   **When** el jugador utiliza un pergamino de retroceso que revierte las acciones hasta un punto donde la puerta estaba cerrada,  
   **Then** el estado de la puerta vuelve a estar cerrado y la siguiente decisión del cazador coincide exactamente con la que correspondía al estado previo al avance, respetando la restauración de la línea temporal.

5. **Given** una partida donde otros actores (enemigos errantes, rastreadores) se desplazan de sala o son derrotados,  
   **When** el cazador evalúa su ruta hacia el jugador,  
   **Then** su cálculo de ruta no se ve impedido por la presencia ni muerte de dichos actores en las salas intermedias, salvo por la posición actual del jugador objetivo.

---

### Edge Cases

- **Costo de salida igual a 1 con velocidad extrema**: Si un actor posee una velocidad de 1000 y cruza una salida con costo 1, el cálculo entero `1 * 100 // 1000` resulta en 0. El sistema debe garantizar que el intervalo agendado hasta su siguiente actuación sea al menos de 1 pulso de reloj (`max(1, 0)`).
- **Cazador sin salidas disponibles**: Si un cazador se encuentra en una sala sin salidas o donde todas sus salidas conectadas están cerradas, la distancia hacia el jugador es inalcanzable (infinita); el cazador debe esperar con costo base 100 sin generar errores de ejecución.
- **Empate múltiple de rutas de igual costo**: Si existen 3 o más salas vecinas que permiten llegar al jugador con el mismo costo mínimo total $d$, el desempate debe elegir de manera estricta y determinista la vecina con el menor ID numérico entero.
- **Puerta que cambia de estado repetidamente (cierre automático)**: Si una puerta se abre y se cierra automáticamente entre turnos, el cazador solo debe considerar el estado en el instante exacto en que le corresponde actuar.
- **Jugador en movimiento hacia el cazador**: Si el jugador y el cazador se mueven en direcciones opuestas por la misma salida, al completarse el evento que los ubica en la misma sala, en el siguiente turno del cazador este debe atacar y no intentar cruzar la salida de nuevo.
- **Rango cero o menor que cualquier salida**: Si un cazador tiene un rango asignado menor que el costo de la salida más económica que sale de su sala, no podrá avanzar y deberá esperar en cada turno.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir que cada salida declare un campo de costo de terreno con un entero mayor o igual que 1. Si dicho campo se omite en la definición de la salida, su costo DEBE establecerse en 100. El costo DEBE ser simétrico e idéntico en ambos sentidos de la salida.
- **FR-002**: El intervalo de tiempo en el reloj virtual hasta la siguiente actuación de cualquier actor que atraviesa una salida DEBE calcularse obligatoriamente mediante la fórmula `intervalo = max(1, costo_salida * 100 // velocidad)`. Los costos base de todas las demás acciones DEBEN conservar rigurosamente sus valores vigentes de la primera parte: atacar (costo base 100), esperar (costo base 100), usar o equipar un objeto (costo base 50), recoger o soltar un objeto (costo base 25) y abrir una puerta (costo base 50). Los enemigos errantes y rastreadores DEBEN conservar intacta su lógica de elección de movimiento, actualizando únicamente el intervalo de espera hasta su siguiente actuación según el costo de la salida transitada.
- **FR-003**: En su turno de acción, si el cazador comparte sala con el jugador, DEBE realizar una acción de ataque. En caso de no compartir sala, DEBE determinar el costo mínimo total de camino hasta la sala donde se encuentra el jugador en ese instante, transitando exclusivamente a través de salidas abiertas.
- **FR-004**: Si no existe ninguna ruta transitable hacia el jugador o si el costo mínimo total $d$ excede el rango del cazador ($d > \text{rango}$), el cazador DEBE ejecutar una acción de espera con costo base 100. Si el costo mínimo iguala exactamente el rango ($d == \text{rango}$), el cazador DEBE poder avanzar.
- **FR-005**: Si existe al menos una ruta abierta hacia el jugador con costo mínimo total $d \le \text{rango}$, el cazador DEBE avanzar exactamente un paso hacia la primera sala vecina de una ruta de costo mínimo. La acción de movimiento DEBE agendar su siguiente actuación utilizando como costo base el costo de la salida atravesada.
- **FR-006**: Cuando dos o más salas vecinas inmediatas del cazador permitan alcanzar la sala del jugador con el mismo costo mínimo total $d$, el cazador DEBE seleccionar como primer paso la sala vecina que posea el menor identificador entero (menor ID numérico según el contrato de datos).
- **FR-007**: El cazador DEBE poseer conocimiento global de todo el esqueleto de la cripta y del estado real y actual de todas las puertas. Su toma de decisiones NO DEBE depender de la niebla de guerra del jugador ni de si el contenido de una sala ha sido descargado desde el servicio. El cazador NUNCA DEBE abrir puertas cerradas.
- **FR-008**: La decisión observable de cada cazador en cada turno DEBE coincidir con la que resultaría de un cálculo recalculado desde cero en ese instante. El sistema DEBE reaccionar y ajustar las decisiones ante apertura y cierre de puertas, desplazamientos del jugador entre turnos, cambios de velocidad durante el tránsito de salidas, muerte de otros actores y reversión de acciones mediante pergamino de retroceso.

---

### Key Entities

- **Salida**: Vínculo bidireccional entre dos salas contiguas. Posee un atributo de costo de terreno (entero $\ge 1$, por defecto 100) simétrico para ambos sentidos y puede contener una puerta (abierta o cerrada).
- **Cazador**: Entidad enemiga hostil caracterizada por una velocidad, atributos de combate y un valor entero de `rango` (en unidades de costo). En su turno persigue al jugador siguiendo el camino de menor costo acumulado o ataca si comparte sala.
- **Actor**: Toda criatura con presencia en la cripta (jugador, errante, rastreador, cazador) que consume tiempo del reloj virtual al interactuar o desplazarse por el terreno según su velocidad.
- **Ruta de Costo Mínimo**: Secuencia ordenada de salidas abiertas consecutivas que minimiza la sumatoria de costos de terreno entre la sala del cazador y la sala del jugador en un instante determinado.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: **Determinismo estricto de partida**: Ante una misma cripta, la misma semilla aleatoria y la misma secuencia de órdenes del jugador, dos partidas ejecutadas de forma independiente producen exactamente la misma secuencia de eventos, movimientos de cazadores, daños y tiempos de reloj virtual (100% de reproducibilidad comprobable mediante `--replay`).
- **SC-002**: **Búsqueda acotada al alcance relevante**: Para un cazador con rango pequeño, el trabajo de búsqueda de camino no debe depender del tamaño global de la cripta, sino acotarse a la región pertinente comprendida dentro de su alcance. Cuando se apliquen cálculos compartidos entre múltiples cazadores con rangos dispares, la exploración debe acotarse al rango máximo de los cazadores activos. Los mecanismos concretos y su verificación se definirán en `plan.md`.
- **SC-003**: **Trazabilidad completa de requisitos**: El 100% de los requisitos funcionales (FR-001 a FR-008) y de los escenarios obligatorios cuentan con pruebas de aceptación automatizadas en el conjunto de pruebas, citando explícitamente el identificador del requisito en su nombre.

### Mediciones pendientes de validación (Benchmarking)

Las siguientes metas de rendimiento corresponden a hipótesis operativas y mediciones empíricas a contrastar mediante `python main.py --bench`:

- **SC-004**: **Límite de tiempo por ciclo de eventos**: El tiempo de procesamiento de cada ciclo completo entre dos decisiones sucesivas del jugador debe mantenerse inferior a 20 ms en el equipo local de referencia (sin solicitudes de red ni renderizado gráfico activo), en presencia de decenas de cazadores activos en la cripta de referencia. La evaluación de rendimiento debe instrumentarse para registrar ciclos pico o percentiles críticos que permitan detectar cualquier ciclo individual que exceda el límite, siendo insuficiente la media aritmética aislada. La metodología de medición se detallará en `plan.md`.
- **SC-005**: **Comparación empírica entre cálculo individual y compartido**: Se debe evaluar y comparar cuantitativamente el tiempo de procesamiento entre la estrategia de cálculo individual (búsqueda por cada cazador acotada a su rango) y la de cálculo compartido (búsqueda unificada desde el objetivo) evaluando diversas cantidades de cazadores (1, 10, 30 y 100 cazadores) y rangos (pequeño frente a grande). La decisión final y las condiciones operativas donde resulta ventajosa cada alternativa deben justificarse mediante mediciones reales.
- **SC-006**: **Comparación empírica de reutilización frente a recálculo**: Se debe comparar el costo computacional de la reutilización de rutas con invalidación selectiva frente a la alternativa de recalcular desde cero en cada turno, evaluando ambos esquemas en escenarios con puertas estables (sin cambios de conectividad) y con puertas inestables (frecuentes aperturas y cierres automáticos). Ambas alternativas deben comprobar en todo momento su equivalencia observable exacta, quedando sujeta a medición la mejora o sobrecosto de rendimiento.

---

## Assumptions

- **Calendario del responsable**: El objetivo de finalización interna de Mariano para esta capacidad es el 11 de noviembre de 2026. El límite de respaldo grupal es el 15 de noviembre de 2026, previo a la entrega oficial fijada para el 18 de noviembre de 2026.
- **Disponibilidad de datos del terreno**: El esqueleto de la cripta recibido desde el servicio web contiene o contendrá el campo `costo` en cada salida. Toda salida que omita dicho campo se asume de manera inequívoca con costo 100.
- **Contrato de identificadores**: Los identificadores de salas corresponden a números enteros según el contrato de datos del esqueleto de la cripta. Toda resolución de empates por "menor ID" se realiza comparando el orden numérico entero de las salas vecinas (`id_v1 < id_v2`).
- **Separación de conocimiento**: La niebla de guerra afecta de forma exclusiva la visualización y las decisiones del jugador y del comando «ir a». El cazador, al ser una entidad del motor de juego con percepción del entorno de la cripta, opera sobre el grafo real y las puertas reales sin consultar la memoria del jugador.
- **Frontera de responsabilidades del equipo**: La capacidad 001 cubre de forma autónoma las reglas del motor, la agenda de eventos ponderada, el comportamiento del cazador, la invalidación de rutas, sus pruebas unitarias/aceptación y los benchmarks de rendimiento. La presentación visual en consola y Pygame queda a cargo de las tareas de Axel y Kim (§7.3).
- **Orden de implementación**: La primera fase de código posterior a la especificación y planificación será la implementación del costo de movimiento para todos los actores (User Story 1), asegurando la compatibilidad con errantes y rastreadores antes de incorporar el algoritmo del cazador.
