# Feature Specification: Niebla de guerra, mapa conocido y viaje automático "ir a"

**Feature Branch**: `002-niebla-ir-a`

**Created**: 2026-11-08

**Status**: Capacidad previa implementada funcionalmente; aceptación de rendimiento pendiente. Corrección del mapa dibujado: origen estable y todas las puertas visibles (2026-11-18).

**Input**: User description: "Niebla de guerra, mapa conocido y viaje automático \"ir a\" para CRIPTA. Describe solo qué pasa en el juego, sin nombrar estructuras de datos, clases ni módulos."

---

## Estado de validación

La verificación sobre la revisión 18b9364 ejecutó 42/42 módulos de pruebas y
229/229 pruebas unittest conjuntas, sin fallos. Estas cifras describen la
evidencia funcional disponible y no equivalen a cobertura exhaustiva.
SC-001 sigue pendiente: falta identificar y medir la cripta oficial con todo
el mapa conocido. Las mediciones sintéticas de 10, 100 y 1000 salas no la
sustituyen. T030 y T031 conservan los pendientes documentados en tasks.md.
Los requisitos FR-001 a FR-024 y los umbrales SC-001 a SC-005 se mantienen sin cambios.
La ampliación del 2026-11-17 incorpora FR-025 a FR-038 y SC-006 a SC-008;
la evidencia anterior no acredita su implementación ni su aceptación.
Esta ampliación recoge las condiciones de los apartados 3.3, 3.4, 5.3 y 7.3
de la Parte II reproducidas en la solicitud de mapa dibujado.

## Clarifications

### Session 2026-11-08

- Q: ¿Qué información exacta debe revelarse al jugador sobre una sala en estado Avistada al consultar el mapa conocido? → A: Se muestra únicamente que existe una salida hacia una sala desconocida y su costo de conexión, sin revelar el identificador ni el nombre de la sala avistada.
- Q: ¿En qué momento se actualiza la memoria del estado de una puerta observada por el jugador? → A: En cada acción o turno del jugador mientras este permanezca en cualquiera de las dos salas que la puerta conecta (al entrar, esperar o realizar cualquier acción).
- Q: ¿Cómo deben tratarse el daño periódico por veneno y las salas con enemigos ya derrotados durante la ejecución del viaje automático "ir a"? → A: El daño por veneno detiene de inmediato el viaje automático tras el paso correspondiente; entrar a una sala con enemigos ya derrotados (muertos) no detiene el viaje y este continúa normalmente.
- Q: ¿Cómo debe comunicar la interfaz de usuario el motivo exacto por el cual se interrumpe o finaliza el viaje automático "ir a"? → A: Mediante un mensaje textual descriptivo y específico para cada causa concreta: llegada al destino, presencia de enemigos vivos, daño recibido, ruta bloqueada por puerta cerrada, o aviso de encontrarse ya en la sala destino sin consumir tiempo.
- Q: ¿Qué comportamiento exacto debe adoptar el sistema al intentar cargar un archivo de partida guardada correspondiente al formato de la primera parte? → A: Reportar explícitamente la incompatibilidad de formato mediante un mensaje de error claro indicando que corresponde a una versión previa sin soporte de niebla de guerra, y rechazar la carga sin modificar la sesión actual ni corromper datos.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Exploración progresiva y visibilidad del mapa conocido (Priority: P1)

Como jugador de CRIPTA, quiero que el mapa del juego refleje únicamente lo que he explorado y observado directamente, distinguiendo entre lo que ya conozco en detalle, lo que he avistado a la distancia y lo que permanece en la niebla de guerra, para poder orientarme y tomar decisiones estratégicas de navegación basadas en información real.

**Why this priority**: Es la base del sistema de niebla de guerra y del conocimiento del jugador. Define las reglas de visibilidad, la observación de puertas y la interfaz de consulta del mapa sobre la cual operan los demás sistemas.

**Independent Test**: Puede probarse de forma aislada iniciando una partida en la sala inicial: se comprueba que dicha sala es la única explorada en el instante 0, que sus salidas y puertas observadas son visibles, que sus salas contiguas figuran como avistadas y que todas las demás permanecen desconocidas. Al desplazarse a una vecina, el estado de conocimiento se actualiza.

**Acceptance Scenarios**:

1. **Given** una partida recién iniciada en el instante 0, **When** el jugador consulta el mapa conocido, **Then** la sala de inicio figura como Explorada (con nombre, salidas, costos y estado de puertas observadas), las salas conectadas a sus salidas figuran como Avistadas (el jugador solo sabe que existe una salida hacia una sala desconocida y su costo, sin revelar identificador ni nombre), y el resto de las salas de la cripta figuran como Desconocidas sin información visible.
2. **Given** el jugador en una sala conectada por una puerta hacia otra sala, **When** el jugador observa la puerta, **Then** el mapa conocido registra el estado actual de dicha puerta (abierta o cerrada).
3. **Given** una puerta cuyo estado fue observado como abierto y que posteriormente cambia a cerrado por un evento del entorno (como cierre automático) mientras el jugador no se encuentra en las salas que conecta, **When** el jugador consulta su mapa conocido sin haber regresado a las salas adyacentes, **Then** el mapa conserva y muestra el último estado observado (abierta) hasta que el jugador vuelva a una de las dos salas conectadas.

---

### User Story 2 - Viaje automático "ir a" con planificación segura (Priority: P1)

Como jugador explorador, quiero emitir la orden "ir a <sala>" para desplazarme automáticamente hacia una sala previamente explorada a través del camino más corto y seguro según lo que recuerdo del mapa, deteniéndome inmediatamente si surge algún peligro, cambio en el entorno o bloqueo, para evitar el tedio de ingresar movimientos manuales repetitivos sin perder control ante amenazas.

**Why this priority**: Representa el núcleo operativo del viaje automático y su interacción con las reglas de turno, costo de movimiento, peligros del entorno y condiciones de seguridad.

**Independent Test**: Puede probarse en un mapa con varias salas exploradas ordenando "ir a" hacia una sala explorada: el personaje avanza paso a paso consumiendo tiempo en cada paso, recalculando la ruta antes de cada acción y deteniéndose ante enemigos, trampas o bloqueos.

**Acceptance Scenarios**:

1. **Given** una sala destino que se encuentra en estado Desconocida o Avistada (no Explorada), **When** el jugador ingresa el comando "ir a <sala>", **Then** la orden se rechaza de inmediato con un mensaje informativo y no se consume tiempo del reloj de juego ni turnos de la partida.
2. **Given** una ruta planificada donde una puerta figura en el mapa conocido como abierta pero en la realidad del entorno se encuentra cerrada, **When** el jugador llega a una sala adyacente a la puerta y la observa, **Then** el mapa conocido actualiza el estado de la puerta a cerrada, recalcula la ruta hacia el destino y, si no existe una ruta alternativa con caminos conocidos y puertas abiertas, el viaje se detiene sin consumir tiempo adicional de movimiento.
3. **Given** un viaje automático en curso hacia una sala destino, **When** un paso del viaje hace ingresar al jugador a una sala con enemigos (ya sea que se encuentren activos o dormidos), **Then** los enemigos dormidos se activan, el viaje automático se detiene de inmediato antes de iniciar el siguiente paso y la interfaz informa el motivo de la detención.
4. **Given** un viaje automático en curso, **When** el jugador recibe daño durante un paso (por ejemplo, al activarse una trampa en la sala o por un evento del entorno), **Then** el viaje automático se cancela inmediatamente y se notifica el daño y la causa de la detención en la interfaz.
5. **Given** dos o más rutas alternativas hacia la sala destino que tienen exactamente la misma suma de costos conocidos, **When** el jugador ejecuta "ir a", **Then** el primer paso de la ruta se dirige deterministamente hacia la sala vecina que posea el menor identificador numérico.
6. **Given** una puerta cerrada en el camino planificado hacia el destino y el jugador posee la llave correspondiente en su inventario, **When** el viaje automático evalúa la ruta, **Then** nunca intenta abrir puertas de forma automática ni consume llaves, considerando intransitables las salidas cuyas puertas no se recuerden abiertas.

---

### User Story 3 - Iluminación y revelado de entorno mediante antorcha encendida (Priority: P2)

Como jugador equipado con una antorcha encendida, quiero que al entrar a una sala la luz revele las salas vecinas conectadas para ampliar mi conocimiento del mapa sin exponerme a riesgos prematuros de activación de trampas o enemigos a la distancia.

**Why this priority**: Enriquecimiento táctico del sistema de niebla de guerra. Permite acelerar la exploración del mapa conocido pero exige reglas precisas sobre qué se revela y qué no se activa.

**Independent Test**: Puede probarse equipando y encendiendo la antorcha antes de cruzar a una nueva sala: al ingresar, todas las salas vecinas (conectadas por cualquier salida, abierta o cerrada) pasan al estado Explorada con su nombre y salidas visibles, mientras que el contenido interno de esas vecinas (monstruos, cofres, trampas) permanece oculto e inactivo.

**Acceptance Scenarios**:

1. **Given** el jugador con la antorcha encendida, **When** entra a una sala, **Then** todas sus salas vecinas directas (por cualquier salida, esté abierta o cerrada) pasan al estado de Exploradas, revelándose su nombre, sus salidas y costos de conexión.
2. **Given** una sala vecina revelada por la luz de la antorcha que contiene trampas o enemigos (activos o dormidos), **When** se produce el revelado por la entrada del jugador a la sala adyacente, **Then** no se revela el contenido interior de dicha vecina y ningún enemigo o trampa de esa sala vecina se activa.

---

### User Story 4 - Persistencia, registro y reversión temporal del mapa conocido (Priority: P2)

Como jugador que utiliza pergaminos de reversión y guarda su progreso, quiero que mi mapa conocido forme parte integral del estado del juego, de modo que al guardar la partida se preserve exactamente lo que conozco, al revertir una acción se restaure fielmente el estado previo del mapa y al consultar el historial se detalle cada paso efectuado.

**Why this priority**: Garantiza la integridad del estado del juego, la separación arquitectónica y la coherencia de la mecánica de viaje en el tiempo / reversión y almacenamiento en archivo.

**Independent Test**: Puede probarse guardando y cargando una partida, utilizando un pergamino tras una entrada con antorcha o durante un viaje automático, y verificando el archivo de registro.

**Acceptance Scenarios**:

1. **Given** una entrada a una sala con la antorcha encendida que provocó la exploración de múltiples salas vecinas, **When** el jugador utiliza un pergamino para revertir la acción, **Then** el jugador regresa a la sala previa y todas las salas que fueron exploradas exclusivamente debido a la antorcha en ese paso vuelven a su estado previo de conocimiento (Avistadas o Desconocidas).
2. **Given** un viaje automático que ha avanzado varios pasos sucesivos, **When** el jugador utiliza un pergamino de reversión, **Then** se revierte exclusivamente el último paso individual de movimiento efectuado, el jugador queda en la sala previa y el viaje automático cancela cualquier paso restante.
3. **Given** una orden de viaje automático ejecutada, **When** se examina el archivo de registro de la partida (`partida.log`), **Then** cada paso individual realizado figura como un movimiento ordinario completo y la orden "ir a" original queda asentada como un comentario explicativo.
4. **Given** un archivo de guardado de partida generado en versiones de la primera parte del juego, **When** se intenta cargar dicho archivo, **Then** el sistema reporta de forma explícita la incompatibilidad de formato indicando que carece de datos de niebla de guerra y aborta la carga limpiamente, sin alterar la partida en curso ni corromper datos.

---

### User Story 5 - Consultar un mapa dibujado sin revelar información desconocida (Priority: P1)

Como jugador, quiero abrir un dibujo de las salas y sus conexiones, localizar mi posición y consultar los costos y puertas que recuerdo, para orientarme sin descubrir información que todavía no conozco ni alterar la partida.

**Why this priority**: Ver el mapa forma parte de la interfaz funcional mínima; una enumeración de salas no permite reconocer visualmente sus conexiones ni la posición del jugador.

**Independent Test**: Iniciar una partida, abrir el mapa en ambas interfaces y comprobar el dibujo, la marca del jugador, la niebla y las salidas recordadas; repetir después de explorar, iluminar vecinas y revertir un movimiento.

**Prueba prevista de independencia de identificadores ocultos**: `test_FR031_FR035_ids_ocultos_de_avistadas_no_cambian_layout` comparará dos criptas con las mismas salas exploradas y avistadas y las mismas conexiones conocidas, pero con identificadores ocultos distintos para las avistadas, incluidos casos que inviertan su orden numérico y provoquen colisiones. La disposición completa, el orden de casillas y conexiones y los textos mostrados DEBEN ser exactamente iguales en ambas, sin incluir esos identificadores ocultos.

**Acceptance Scenarios**:

1. **FR-025, FR-029 — Mapa dibujado**: **Given** una partida recién iniciada, **When** el jugador introduce `mapa` sin argumentos, **Then** ve casillas conectadas mediante un dibujo ASCII, con la sala inicial explorada desde el instante 0, sus vecinas avistadas y una leyenda; debajo aparecen la sala actual, las salidas conocidas y las cantidades de salas exploradas y avistadas.
2. **FR-026 — Avistada solo como existencia**: **Given** una salida conocida cuyo destino todavía no se ha explorado, **When** se abre el mapa en cualquiera de las interfaces, **Then** el destino aparece como una casilla `?`, sin identificador, nombre, contenido, enemigos ni otras salidas, y la salida desde la sala explorada identifica su destino únicamente como `?`.
3. **FR-025, FR-030 — Posición del jugador**: **Given** el jugador en una sala explorada, **When** abre el mapa, **Then** esa sala está marcada con `@` en consola y con borde resaltado e icono o círculo en la interfaz gráfica, que se abre centrada en ella.
4. **FR-027 — Puerta recordada desactualizada**: **Given** una puerta recordada como abierta que se cerró fuera de la observación del jugador, **When** se consulta el mapa, **Then** la conexión sigue mostrándose abierta, sin corregirla ni advertir o insinuar que el recuerdo difiere de la realidad.
5. **FR-026, FR-031, FR-035 — Niebla e independencia del entorno desconocido y de identificadores ocultos**: **Given** dos partidas con la misma posición y el mismo conocimiento, pero con distintas salas, conexiones, contenidos o puertas reales fuera de ese conocimiento, o con identificadores ocultos distintos para las mismas salas avistadas, **When** se abren sus mapas, **Then** coinciden exactamente las posiciones, conexiones, su orden de dibujo, etiquetas y cantidades mostradas, incluso si se invierte el orden numérico de los identificadores de las avistadas y hay colisiones; las salas desconocidas no aportan casillas ni información y el fondo permanece vacío o cubierto de niebla opaca.
6. **FR-033 — Mapa tras pergamino**: **Given** un movimiento que exploró una sala y reveló vecinas mediante la antorcha, **When** se revierte ese movimiento con un pergamino y se abre el mapa, **Then** la posición, el conocimiento y las puertas recordadas corresponden al estado restaurado; las salas reveladas exclusivamente por esa acción recuperan su condición previa, sin conservar etiquetas ni casillas que ya no correspondan.
7. **FR-032 — Consulta sin efectos**: **Given** una partida con reloj, registro, historial de retroceso, línea de tiempo y memoria de puertas establecidos, **When** el jugador abre, consulta y cierra el mapa repetidamente, incluyendo desplazamiento, zoom y recentrado en la interfaz gráfica, **Then** todos esos datos permanecen idénticos, no transcurre tiempo virtual, no se registra la consulta y no se observan puertas.
8. **FR-028 — Antorcha sin contenido remoto**: **Given** que una entrada con antorcha encendida exploró vecinas a través de puertas abiertas o cerradas, **When** se abre el mapa, **Then** se muestran sus identificadores, nombres, salidas y costos conocidos, sin revelar su contenido ni activar enemigos o trampas y sin completar estados de puertas que no se hayan observado.
9. **FR-034, FR-035 — Colisión de casillas sin identificadores ocultos**: **Given** conexiones conocidas que sitúan dos salas en la misma casilla, **When** se abre el mapa, **Then** entre exploradas conserva la casilla la de menor identificador, una explorada tiene prioridad sobre una avistada y, entre avistadas, conserva la casilla la descubierta primero al considerar las salas exploradas por menor identificador y sus salidas en orden N, S, E, O. La otra sala ocupa la casilla libre más cercana, buscando por anillos de distancia creciente y con un orden fijo dentro de cada anillo, independiente de identificadores ocultos; ambas siguen siendo distinguibles y las colisiones sucesivas respetan las mismas prioridades. Toda conexión que deja de ser adyacente conserva dirección, costo y estado recordado, mediante una línea gráfica o la relación de conexiones fuera de la cuadrícula en consola. Si una sala es avistada, su extremo se etiqueta `?` sin revelar su identificador ni usarlo para decidir posiciones, orden o textos.
10. **FR-027, FR-029, FR-030 — Costos y puertas**: **Given** salidas con distintos costos y puertas recordadas abiertas, cerradas y cerradas con llave, **When** se consulta el mapa, **Then** cada costo es consultable y se distinguen los tres estados mediante conectores y leyenda en consola y colores y rótulos en la interfaz gráfica; el identificador de una llave aparece únicamente si ya forma parte de la información visible del jugador.
11. **FR-030, FR-036 — Controles gráficos**: **Given** la interfaz gráfica de juego, **When** se pulsa `M`, se usan flechas o arrastre, rueda o `+`/`-`, `C` y finalmente `Esc` o `Enter`, **Then** el mapa se abre, se desplaza, cambia de escala, se recentra en el jugador y vuelve al juego, respectivamente; la leyenda permanece visible y los controles existentes conservan su función fuera del mapa.
12. **FR-029 — Mapa ancho**: **Given** un mapa cuyo dibujo supera el ancho disponible en la terminal, **When** se introduce `mapa`, **Then** el dibujo se presenta por bloques identificables sin omitir silenciosamente salas, conexiones ni etiquetas.
13. **FR-033 — Consulta histórica**: **Given** un instante o número de evento anterior con conocimiento distinto del actual, **When** se consulta `historia <t>` o `historia #k`, **Then** se sigue mostrando el mapa conocido en ese momento, sin incorporar descubrimientos posteriores ni modificar la partida vigente.
14. **FR-031, FR-034, FR-035 — Determinismo**: **Given** dos consultas con la misma posición y conocimiento, incluidas conexiones incompatibles con una cuadrícula y empates de ubicación, **When** se construyen los dibujos, **Then** las posiciones, conexiones, orden de dibujo y textos son idénticos y respetan las prioridades de exploradas y el orden de descubrimiento de avistadas especificados, sin utilizar identificadores de avistadas como criterio de orden o desempate.
15. **FR-027 — Estado de puerta sin observación**: **Given** una salida conocida para la que todavía no existe recuerdo del estado de la puerta, **When** se abre el mapa, **Then** su costo y dirección siguen visibles, su estado se indica como no observado y no se deduce del estado real ni de la posesión de llaves.
16. **FR-037 — Preparación por apertura**: **Given** un mapa abierto y su disposición ya calculada, **When** se desplaza, amplía y repinta varias veces, **Then** se conserva esa disposición sin volver a calcularla; al cerrarlo y abrirlo después de nuevos descubrimientos, se prepara una vez con el conocimiento actualizado.
17. **FR-038 — Compatibilidad y modos sin interfaz gráfica**: **Given** una partida guardada con el formato vigente y una ejecución sin interfaz gráfica, **When** se carga la partida, se consulta `mapa` o `historia` y se ejecutan reproducción, medición o verificación, **Then** se conserva la compatibilidad de guardado y registro, las consultas siguen disponibles y no se carga ni inicializa la interfaz gráfica.
18. **FR-034 — Posiciones estables al moverse**: **Given** el mismo conocimiento y varias salas exploradas, **When** el jugador abre el mapa desde cada una, **Then** todas las casillas conservan exactamente sus posiciones, la sala inicial conserva el origen y solo cambian la marca del jugador y el centrado de la vista.
19. **FR-027, FR-029, FR-030 — Cuatro salidas individuales**: **Given** una sala explorada con cuatro salidas N, S, E, O, dos hacia la misma sala, **When** se consulta el mapa, **Then** se ven las cuatro puertas en sus lados respectivos y las cuatro filas de salidas, sin fusionar conexiones repetidas.
20. **FR-027, FR-030 — Rótulos únicos y legibles**: **Given** puertas entre salas exploradas y conexiones cercanas, **When** se dibujan, **Then** cada puerta lleva un solo rótulo de costo y estado corto, sin duplicarlo desde el otro extremo, sin superponer rótulos y usando caracteres compatibles con la fuente; la llave solo aparece si es requerida y conocida.
21. **FR-026, FR-027, FR-030, FR-035 — Destino fuera de su dirección**: **Given** una salida cuyo destino no ocupa la casilla vecina en su dirección, **When** se dibuja, **Then** conserva su puerta en el lado correcto y una línea diferenciada con el destino indicado en la puerta; si el destino es avistado la línea termina en su casilla `?` sin revelar su identificador.
22. **FR-034, FR-035 — Colisión estable al moverse**: **Given** dos salas que reclaman la misma casilla y el conocimiento sin cambios, **When** el jugador cambia de sala explorada y vuelve a abrir el mapa, **Then** la sala desplazada y todas las demás conservan sus posiciones y prioridades de colisión.

---

### Edge Cases

- **Destino es la sala actual**: Si el jugador ingresa "ir a <sala_actual>", el sistema no debe realizar ningún movimiento, no debe consumir tiempo y debe informar que ya se encuentra en el destino.
- **Sin ruta conocida existente**: Si todas las salidas hacia una sala explorada conocida pasan por puertas recordadas como cerradas o zonas desconocidas, el sistema debe rechazar la orden antes del primer paso indicando que no hay ruta conocida disponible, sin consumir tiempo.
- **Ruta bloqueada a mitad de camino**: Si una puerta cambia de estado durante el viaje o se descubre cerrada al llegar a una sala intermedia y no existe camino alternativo conocido, el viaje se detiene exactamente en esa sala intermedia sin avanzar más ni consumir tiempo adicional.
- **Muerte o daño crítico durante el viaje**: Si un evento o trampa causa daño letal o inhabilita al jugador, el viaje automático se interrumpe en el instante del daño para permitir la resolución del estado final de la partida.
- **Entrada de comando inválido o inexistente**: Si se ingresa un identificador de sala que no existe en el universo de la cripta, el comando debe ser rechazado de inmediato sin costo temporal.
- **Mapa con una única sala explorada**: Se dibuja esa sala con la marca del jugador aunque no existan salidas; el recuento de avistadas puede ser cero.
- **Conexiones conocidas incompatibles con la cuadrícula**: No se superponen ni se descartan salas; los enlaces desplazados mantienen sus etiquetas y el anonimato de los destinos avistados.
- **Puerta sin recuerdo disponible**: El mapa indica que su estado no fue observado, sin consultar la realidad para completar el dibujo.
- **Salas exploradas sin enlace conocido desde la inicial**: Siguen apareciendo en el mapa, en una zona separada y ordenadas por menor identificador, sin inventar conexiones a través de la niebla.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Conocimiento del jugador y niebla de guerra
- **FR-001**: El sistema DEBE clasificar cada sala de la cripta en exactamente uno de tres estados de conocimiento para el jugador:
  - **Explorada**: Sala a la que el jugador ha entrado físicamente al menos una vez, o que ha sido explorada por el efecto de la antorcha.
  - **Avistada**: Sala que no ha sido explorada, pero que es destino directo de una salida de una sala explorada.
  - **Desconocida**: Sala que no cumple ninguna de las dos condiciones anteriores.
- **FR-002**: Al iniciar una partida en el instante 0, la sala de inicio DEBE quedar en estado Explorada, todas sus salas contiguas directas en estado Avistadas y las restantes en estado Desconocidas.
- **FR-003**: De cada sala Explorada, el jugador DEBE conocer su nombre, sus salidas, el costo de cada salida y el estado de sus puertas según la última vez que fueron observadas.
- **FR-004**: De cada sala Avistada, el jugador solo DEBE saber que existe una salida hacia una sala desconocida y su costo de conexión, sin conocer su identificador, su nombre ni su contenido interno.
- **FR-005**: De las salas Desconocidas, el jugador NO DEBE recibir ninguna información, y estas salas no pueden ser utilizadas para trazar rutas de viaje.
- **FR-006**: El sistema DEBE actualizar la memoria de estado de una puerta (abierta o cerrada) en cada acción o turno del jugador mientras este permanezca en cualquiera de las dos salas que dicha puerta conecta (incluyendo al entrar, esperar o realizar cualquier acción), manteniendo registrado ese último estado observado aunque la puerta cambie posteriormente sin la presencia del jugador.

#### Mecánica de la antorcha encendida
- **FR-007**: Cuando el jugador ingresa a una sala con la antorcha encendida, el sistema DEBE cambiar automáticamente al estado de Exploradas a todas las salas vecinas conectadas por cualquier salida (esté la salida abierta o cerrada), revelando de ellas su nombre y sus salidas con sus costos.
- **FR-008**: La exploración de salas vecinas por efecto de la luz de la antorcha NO DEBE revelar el contenido interno de dichas salas (enemigos, cofres, trampas) ni activar enemigos (dormidos o activos) ni trampas en esas salas vecinas.

#### Separación de información y comandos del mapa
- **FR-009**: La interfaz de usuario DEBE disponer de un comando específico para visualizar el mapa conocido, mostrando únicamente las salas exploradas, sus salidas y las salas avistadas.
- **FR-010**: Ningún componente de la interfaz de usuario ni de la planificación de viaje automático DEBE revelar o utilizar información de salas o puertas que el jugador no haya conocido directamente, con independencia de que el programa haya precargado la estructura completa de la cripta.
- **FR-011**: El estado completo de conocimiento del mapa (salas exploradas, salas avistadas y memoria de puertas) DEBE formar parte integral del estado de la partida y guardarse fielmente en el archivo de guardado de partida.
- **FR-012**: El sistema DEBE permitir que el pergamino de reversión revierta cualquier cambio en el estado de conocimiento del mapa producido por la acción o movimiento que se revierte, restaurando las salas y puertas a su estado de conocimiento exacto previo.
- **FR-013**: Cada modificación en el conocimiento del mapa conocido DEBE quedar registrada en la línea de tiempo de eventos de la partida.

#### Viaje automático "ir a <sala>"
- **FR-014**: El comando "ir a <sala>" DEBE verificar que la sala destino se encuentre en estado Explorada; si el destino no está explorado o no existe, la orden DEBE ser rechazada de inmediato sin consumir tiempo del reloj de juego ni acciones.
- **FR-015**: El sistema DEBE planificar la ruta de viaje automático utilizando exclusivamente salas en estado Exploradas y salidas cuyas puertas se recuerden como abiertas en el mapa conocido, seleccionando la secuencia de pasos que minimice la suma total de los costos de movimiento.
- **FR-016**: Si existen múltiples rutas con la misma suma de costos mínimos hacia el destino, el sistema DEBE resolver el empate deterministamente seleccionando en el primer paso la sala vecina con el menor identificador.
- **FR-017**: Cada paso del viaje automático DEBE ejecutarse como una acción de movimiento individual ordinaria del jugador, permitiendo que entre paso y paso transcurran los eventos normales del reloj de juego y del entorno.
- **FR-018**: El sistema DEBE recalcular la ruta restante antes de iniciar cada paso individual del viaje, empleando el conocimiento del mapa vigente en ese instante exacto.
- **FR-019**: El viaje automático DEBE interrumpirse inmediatamente ante cualquiera de las siguientes condiciones:
  - Se alcanza la sala destino.
  - El jugador ingresa a una sala que contiene enemigos vivos (ya sean activos o dormidos, provocando la activación de los dormidos; si los enemigos de la sala ya fueron derrotados y están muertos, el viaje no se detiene).
  - El jugador recibe daño de cualquier fuente, incluyendo daño recurrente por veneno al término de un paso.
  - Ya no existe una ruta conocida viable y abierta hacia el destino.
- **FR-020**: Al interrumpirse o finalizar un viaje automático, la interfaz de usuario DEBE emitir un mensaje textual descriptivo y específico indicando la causa exacta de la detención (llegada al destino, presencia de enemigos vivos, daño recibido, ruta bloqueada por puerta cerrada, o aviso informativo de encontrarse ya en la sala destino sin consumir tiempo).
- **FR-021**: El viaje automático NUNCA DEBE abrir puertas cerradas de forma automática, independientemente de si el jugador lleva en su inventario la llave adecuada.
- **FR-022**: En el archivo de registro de la partida (`partida.log`), cada paso del viaje automático DEBE asentarse como un movimiento individual ordinario, y la orden "ir a" original DEBE quedar documentada adicionalmente como un comentario.
- **FR-023**: Al utilizar un pergamino de reversión durante o tras un viaje automático, el sistema DEBE revertir exclusivamente el último paso individual ejecutado y no continuar automáticamente con el resto del viaje.

#### Compatibilidad de versiones
- **FR-024**: Al intentar cargar un archivo de guardado proveniente de versiones de la primera parte del juego (que carezca de los datos de conocimiento de niebla de guerra y memoria de puertas), el sistema DEBE reportar explícitamente la incompatibilidad de formato mediante un mensaje de error claro y rechazar la carga, evitando fallos silenciosos, cargas parciales o corrupción de datos.

#### Mapa dibujado y consulta sin efectos

- **FR-025**: El mapa DEBE representar las salas exploradas y avistadas mediante casillas conectadas en una cuadrícula en consola y en la interfaz gráfica, mostrando la posición del jugador. Una lista de texto por sí sola NO satisface este requisito. La sala inicial DEBE aparecer explorada desde el instante 0.
- **FR-026**: Cada sala avistada DEBE representarse exclusivamente como una casilla de niebla con `?`, sin identificador, nombre, contenido, enemigos ni salidas propias. Su identificador oculto NO DEBE determinar posiciones, orden de dibujo, textos ni desempates. Las salas desconocidas NO DEBEN dibujarse ni aportar información; su zona permanece vacía o bajo niebla opaca. Los recuentos solo DEBEN incluir salas exploradas y avistadas, sin revelar el total de salas desconocidas.
- **FR-027**: Cada sala explorada DEBE mostrar identificador, nombre y TODAS sus salidas conocidas como puertas individuales en el lado de su dirección (N, S, E, O), con costo y estado según la última observación. Dos salidas hacia la misma sala DEBEN conservarse como conexiones distintas. Una salida cuyo destino no ocupa la casilla vecina de su dirección DEBE conservar una conexión separada, diferenciada, con destino indicado en su puerta; hacia una avistada termina en su casilla `?`. Se DEBEN distinguir abierta, cerrada, cerrada que requiere llave y no observada. Cada puerta DEBE rotularse una sola vez, sin duplicar su costo desde el otro extremo, con costo y estado en formato corto, sin superponer rótulos y sin caracteres incompatibles con la fuente. La llave solo se indica si es requerida y su identificador ya es visible. Un recuerdo desactualizado DEBE mostrarse tal cual, sin corregirlo ni insinuar su discrepancia. Si no existe observación, NO se DEBE completar con información real.
- **FR-028**: Las vecinas exploradas por antorcha DEBEN figurar en el dibujo con su identificador, nombre, salidas y costos conocidos, igual que las exploradas mediante movimiento, sin revelar contenido remoto ni activar enemigos o trampas. Dibujar el mapa NO DEBE producir nuevas observaciones de puertas.
- **FR-029**: En consola, `mapa` sin argumentos DEBE producir un dibujo solo con caracteres ASCII: salas exploradas entre corchetes, `@` en la actual, avistadas como `(?)`, conectores `-` o `|` para abiertas, `X` para cerradas y `K` para cerradas con llave. Los estados no observados DEBEN tener una marca diferenciada explicada en la leyenda. Debajo DEBEN aparecer leyenda, identificador y nombre de la sala actual, una tabla de TODAS las salidas conocidas de cada sala explorada (dirección, destino explorado o `?`, costo y estado recordado), incluidas las repetidas hacia una misma sala y las conexiones fuera de la cuadrícula, y cantidades de exploradas y avistadas. Los costos pueden aparecer junto al conector o en esa tabla. Los nombres DEBEN adaptarse a ASCII para esta salida. Si el dibujo excede el ancho disponible, se DEBE presentar por bloques identificables sin truncamiento silencioso.
- **FR-030**: En la interfaz gráfica, cada explorada DEBE ser un recuadro con identificador y nombre abreviado; cada avistada, un recuadro de niebla con `?`; el fondo restante, niebla oscura. Cada salida conocida DEBE tener su marcador de puerta en el lado N, S, E u O, verde si se recuerda abierta, rojo si cerrada y dorado si cerrada con llave; las no observadas DEBEN distinguirse sin atribuirles un estado. Las conexiones adyacentes DEBEN usar líneas; las no adyacentes o repetidas hacia un destino DEBEN usar líneas diferenciadas y destino visible en su puerta (o `?` si es avistado). Cada puerta DEBE tener un único rótulo con fondo, costo y estado corto, llave solo si requiere llave y ya es conocida, caracteres compatibles con la fuente y desplazamiento de rótulos cuando choquen para evitar superposición. Debajo del dibujo DEBEN listarse la sala actual y TODAS sus salidas con dirección, destino, costo y estado. Una leyenda DEBE explicar colores y abreviaturas. La sala actual DEBE tener borde resaltado e icono o círculo del jugador. El mapa DEBE abrirse centrado en ella, mediante desplazamiento de la vista que no altera las casillas, y permitir flechas o arrastre, zoom mediante rueda o `+`/`-`, recentrado mediante `C` y retorno mediante `Esc` o `Enter`, sin requerir imágenes externas.
- **FR-031**: Los datos mostrados, las posiciones de las casillas, sus conexiones y su orden de dibujo DEBEN derivarse exclusivamente del conocimiento vigente del jugador, anclado en la sala inicial conocida. La posición del jugador solo DEBE determinar su marca, la lista de salidas actuales y el encuadre. NO se DEBE consultar la disposición completa de la cripta, las salas desconocidas, el contenido de salas, los enemigos ni el estado real de puertas para dibujar o ubicar casillas. Los identificadores ocultos de las avistadas NO DEBEN influir en las posiciones, conexiones, orden de dibujo, textos ni desempates. Dos partidas con igual conocimiento y posición DEBEN producir exactamente el mismo dibujo aunque difiera su entorno no conocido o cambien los identificadores ocultos de sus avistadas.
- **FR-032**: Abrir, consultar, desplazar, ampliar, recentrar y cerrar el mapa NO DEBE consumir tiempo virtual, escribir en el registro de partida, modificar el estado del juego, el historial de retroceso o la línea de tiempo, ni observar puertas. Los cambios de encuadre solo afectan a la presentación.
- **FR-033**: El dibujo DEBE reflejar el conocimiento vigente tras un pergamino, restaurando la posición y visibilidad anteriores, incluidos descubrimientos por antorcha o movimiento y recuerdos de puertas revertidos. Las consultas `historia <t>` y `historia #k` DEBEN conservar la representación del mapa conocido en el momento solicitado, sin filtrar conocimiento posterior ni alterar la partida actual.
- **FR-034**: La disposición DEBE comenzar en la sala inicial de la cripta, explorada desde el instante 0, y situar los destinos conocidos de sus salidas con norte arriba, sur abajo, este a la derecha y oeste a la izquierda, continuando por cercanía en número de conexiones conocidas entre salas exploradas. Las posiciones NO DEBEN depender de dónde esté el jugador: con iguales salas exploradas, avistadas y salidas conocidas, todas las casillas DEBEN conservar exactamente sus posiciones al moverse entre exploradas. El mapa se abre centrado en el jugador mediante el desplazamiento de la vista, sin alterar la disposición, y su marca indica dónde está. El orden de direcciones DEBE ser N, S, E, O y, dentro del mismo nivel de recorrido, solo las salas exploradas DEBEN considerarse por menor identificador. Para determinar el orden de descubrimiento de las avistadas, se DEBEN considerar todas las salas exploradas vigentes en orden de menor identificador y, para cada una, sus salidas en orden N, S, E, O; la primera salida que revele cada avistada determina su lugar en ese orden y su casilla adyacente inicial. Este orden se deriva del conocimiento vigente al abrir el mapa, sin utilizar identificadores de avistadas ni sus salidas propias. Las colisiones se resuelven según FR-035. Las exploradas no alcanzables mediante conexiones conocidas DEBEN incluirse separadamente, comenzando por el menor identificador y sin inventar enlaces. Explorar nuevas salas puede cambiar las posiciones por nuevas colisiones.
- **FR-035**: Si dos salas reclaman la misma casilla, entre exploradas DEBE conservarla la de menor identificador; una explorada DEBE tener prioridad sobre una avistada; y entre avistadas DEBE conservarla la descubierta primero según FR-034: salas exploradas por menor identificador y, para cada una, salidas N, S, E, O. Ningún criterio de desempate DEBE utilizar el identificador de una sala avistada. La sala desplazada DEBE ocupar la casilla libre más cercana a la reclamada, midiendo la distancia como la suma de desplazamientos horizontales y verticales y buscando por anillos de distancia creciente. Dentro de cada anillo se DEBE seguir un orden fijo de posiciones, independiente de identificadores ocultos, que deberá documentarse en la planificación. Las colisiones sucesivas DEBEN resolverse con las mismas prioridades y el mismo orden de búsqueda, sin eliminar salas. Las conexiones entre casillas no adyacentes DEBEN conservarse con dirección, costo y estado recordado: mediante líneas rotuladas en la interfaz gráfica y bajo `Conexiones fuera de la cuadricula:` en consola, en el formato `sala A <-> sala B (dir, costo, estado)`, sustituyendo cualquier extremo avistado por `?`.
- **FR-036**: La tecla `M` DEBE abrir el mapa durante el juego gráfico sin interferir con los controles existentes, incluidas `H`, `F1` y `L`. La ayuda y la documentación de controles DEBEN explicar cómo abrir, desplazar, ampliar, recentrar y cerrar el mapa, además de su leyenda. Los controles propios del mapa solo DEBEN actuar mientras este esté abierto.
- **FR-037**: La disposición de las casillas DEBE calcularse una vez por apertura del mapa; desplazar, ampliar o repintar la presentación NO DEBE reconstruirla. La preparación DEBE depender de las salas exploradas y avistadas y sus salidas conocidas, sin recorrer salas desconocidas ni reservar espacio en función del tamaño completo de la cripta.
- **FR-038**: La ampliación del mapa DEBE conservar el formato de guardado y del registro de partida y el funcionamiento de los modos sin interfaz gráfica. La consulta en consola y las consultas históricas DEBEN seguir disponibles sin cargar ni inicializar la interfaz gráfica.

---

### Key Entities *(sin nombres de implementación ni estructuras)*

- **Mapa conocido**: Representa la acumulación del saber del jugador sobre el entorno de la cripta a lo largo del tiempo. Registra qué salas han sido exploradas, cuáles permanecen en estado avistado, el nombre y las conexiones conocidas de las exploradas, y la memoria del estado de las puertas observadas.
- **Estado de conocimiento de sala**: Condición en la que se encuentra una sala respecto a la percepción del jugador: Explorada, Avistada o Desconocida.
- **Memoria de puerta**: Registro individual de una puerta que guarda su último estado observado (abierta o cerrada).
- **Plan de viaje automático**: Secuencia ordenada de movimientos ordinarios calculada dinámicamente sobre el mapa conocido para transitar desde la sala actual hasta la sala destino mediante el menor costo acumulado.
- **Registro de partida**: Bitácora histórica secuencial donde se asientan las acciones del jugador, comentarios operativos y eventos del entorno a lo largo de la expedición.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El cálculo o recálculo completo de la ruta para un paso de "ir a" se ejecuta en menos de 5 milisegundos cuando el mapa conocido contiene la totalidad de las salas y conexiones de la cripta de referencia del proyecto.
- **SC-002**: La consulta del estado de una sala o de una puerta recordada no depende del tamaño del mapa conocido y se respalda con `--bench`.
- **SC-003**: La operación de explorar una sala (revelar su información y actualizar salas vecinas) tiene un costo de tiempo proporcional únicamente a la cantidad de salas directamente reveladas en dicha acción, manteniéndose constante e independiente del tamaño acumulado del mapa conocido.
- **SC-004**: Registrar e invertir un cambio del mapa conocido no depende del tamaño del mapa conocido y se respalda con `--bench`.
- **SC-005**: El 100% de las rutas calculadas por "ir a" en pruebas automatizadas seleccionan la trayectoria de costo mínimo matemáticamente verificable sobre el conocimiento vigente, respetando sin excepción el desempate por menor identificador ante igualdad de costos.
- **SC-006**: En el 100% de los escenarios de mapa dibujado, ambas interfaces muestran todas las salas exploradas y todas sus puertas individuales, incluidas las repetidas o no adyacentes, las avistadas únicamente como existencia y ninguna información desconocida; las consultas repetidas dejan idénticos el tiempo, el registro y el estado de la partida. Cada puerta tiene un único rótulo legible y los rótulos no se superponen.
- **SC-007**: Las mediciones de preparación del dibujo DEBEN cubrir 10, 100, 1000 y 5000 salas conocidas con casos reproducibles, registrar tiempo y memoria y comparar con la alternativa descartada. Mantener fijo el conocimiento y aumentar exclusivamente el entorno desconocido NO DEBE aumentar el número de salas o salidas examinadas para preparar el dibujo.
- **SC-008**: El 100% de las consultas con igual conocimiento producen las mismas ubicaciones, conexiones y orden de dibujo, incluidos los casos de colisión, aunque cambie la sala del jugador entre exploradas; solo cambian su marca, la lista de salidas actuales y el encuadre. Con igual posición también coinciden los textos. Dos criptas con las mismas salas exploradas y avistadas y las mismas conexiones conocidas y sala inicial, pero con identificadores ocultos distintos para las avistadas, DEBEN producir exactamente la misma disposición y salida visible, incluso si cambia el orden numérico de esos identificadores. Tras un pergamino o una consulta histórica, el mapa coincide con el conocimiento correspondiente sin descubrimientos posteriores.

---

## Assumptions

- Se asume que el identificador numérico de cada sala es único y no negativo en cualquier cripta válida suministrada.
- Se asume que los costos de movimiento entre salas son enteros positivos mayores a cero.
- Se asume que la activación de enemigos dormidos al ingresar a una sala con ellos se procesa antes de que el jugador pueda decidir el siguiente movimiento voluntario, deteniendo cualquier secuencia automática.
- El mapa dibujado se consulta fuera del procesamiento de un paso; su dibujo es obligatorio y puede acompañarse de una tabla de salidas, que no lo sustituye.
- Un archivo de guardado de la primera parte no contiene datos de conocimiento del jugador ni de memoria de puertas, por lo que el sistema rechaza su carga reportando explícitamente incompatibilidad de formato.
