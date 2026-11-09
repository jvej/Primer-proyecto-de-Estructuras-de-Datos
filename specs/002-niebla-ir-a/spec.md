# Feature Specification: Niebla de guerra, mapa conocido y viaje automático "ir a"

**Feature Branch**: `002-niebla-ir-a`

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: "Niebla de guerra, mapa conocido y viaje automático \"ir a\" para CRIPTA. Describe solo qué pasa en el juego, sin nombrar estructuras de datos, clases ni módulos."

---

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

### Edge Cases

- **Destino es la sala actual**: Si el jugador ingresa "ir a <sala_actual>", el sistema no debe realizar ningún movimiento, no debe consumir tiempo y debe informar que ya se encuentra en el destino.
- **Sin ruta conocida existente**: Si todas las salidas hacia una sala explorada conocida pasan por puertas recordadas como cerradas o zonas desconocidas, el sistema debe rechazar la orden antes del primer paso indicando que no hay ruta conocida disponible, sin consumir tiempo.
- **Ruta bloqueada a mitad de camino**: Si una puerta cambia de estado durante el viaje o se descubre cerrada al llegar a una sala intermedia y no existe camino alternativo conocido, el viaje se detiene exactamente en esa sala intermedia sin avanzar más ni consumir tiempo adicional.
- **Muerte o daño crítico durante el viaje**: Si un evento o trampa causa daño letal o inhabilita al jugador, el viaje automático se interrumpe en el instante del daño para permitir la resolución del estado final de la partida.
- **Entrada de comando inválido o inexistente**: Si se ingresa un identificador de sala que no existe en el universo de la cripta, el comando debe ser rechazado de inmediato sin costo temporal.

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

---

## Assumptions

- Se asume que el identificador numérico de cada sala es único y no negativo en cualquier cripta válida suministrada.
- Se asume que los costos de movimiento entre salas son enteros positivos mayores a cero.
- Se asume que la activación de enemigos dormidos al ingresar a una sala con ellos se procesa antes de que el jugador pueda decidir el siguiente movimiento voluntario, deteniendo cualquier secuencia automática.
- Se asume que el comando de visualización del mapa conocido en la consola o interfaz de texto muestra una representación comprensible (listado o diagrama de conexiones) accesible para el usuario en cualquier momento fuera del procesamiento de un paso.
- Un archivo de guardado de la primera parte no contiene datos de conocimiento del jugador ni de memoria de puertas, por lo que el sistema rechaza su carga reportando explícitamente incompatibilidad de formato.
