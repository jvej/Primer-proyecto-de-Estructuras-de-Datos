# Feature Specification: Verificación de Resolubilidad y Extensión del Servicio Web

**Feature Branch**: `003-resolubilidad`  
**Created**: 2026-11-07  
**Status**: Draft  
**Input**: User description: "Cambios al servicio web y verificación de resolubilidad de CRIPTA. Describe solo el comportamiento, sin nombres de estructuras de datos, clases ni módulos."

---

## Clarifications

### Session 2026-11-07
- Q: ¿Cómo debe formalizarse el orden de obtención y el desempate de llaves cuando varias de ellas se vuelven alcanzables simultáneamente? (FR-013) → A: Ordenar por etapas de alcanzabilidad topológica y desempatar lexicográficamente (como cadenas de texto) únicamente entre llaves que se vuelven obtenibles al mismo tiempo.
- Q: ¿Dónde y a través de qué interfaces debe desplegarse el reporte de resolubilidad al iniciar una partida regular frente a la ejecución con `--verificar`? (FR-015, FR-016) → A: Al iniciar una partida normal (con o sin `--forzar`), el reporte se muestra en la interfaz que esté activa: como texto en el modo consola y como pantalla en Pygame en el modo `--gui`. Si la cripta no es resoluble y no hay `--forzar`, se muestra el reporte y la partida no inicia (en Pygame se vuelve a la selección de cripta). Con `--verificar`, el reporte se imprime en la salida estándar y no se crea ninguna vista, ni de consola ni de Pygame.
- Q: ¿Qué debe hacer el sistema si la consulta `GET /criptas/<id>/llaves` falla por red/servidor o si el `presupuesto_solicitudes` se agota antes de poder realizar la verificación? (FR-003) → A: (1) Si hay datos de llaves guardados localmente y su versión coincide con la de la cripta, se usan para verificar sin hacer la consulta HTTP (en modo `--offline` siempre se usan los datos guardados). (2) Si no los hay y la consulta falla o no queda `presupuesto_solicitudes`, el programa no se cae: muestra en la interfaz activa un mensaje claro de que la verificación no pudo completarse y por qué (red o presupuesto), y la partida no inicia, igual que una cripta no resoluble, salvo que se use `--forzar`. (3) Con `--verificar` se imprime ese mensaje en la salida estándar y el programa termina con un código de salida distinto de cero.
- Q: ¿Cómo deben tratarse durante la verificación de resolubilidad las salidas marcadas como cerradas que no indican ninguna llave requerida en el esqueleto? (FR-010) → A: Se consideran permanentemente infranqueables durante toda la verificación (igual que en el juego) y, si son adyacentes a la región alcanzable, se incluyen en la frontera bloqueada del reporte indicando que no tienen llave asociada.
- Q: ¿Qué debe reportar el sistema si `llave_salida` existe pero ninguna puerta que la pide da a `sala_salida`? (FR-011, FR-014) → A: Se clasifica como no resoluble y el reporte indica explícitamente que no existe ninguna puerta hacia `sala_salida` que requiera `llave_salida`, junto con lo demás que pide el reporte (llaves no obtenibles y frontera bloqueada, si las hay).
- Q: ¿Cómo debe formatearse y representarse en el reporte un ciclo de dependencia circular que involucre más de dos llaves? (FR-014) → A: Se representa como una cadena orientada de dependencias (donde la flecha X -> Y significa "la llave X está detrás de una puerta que pide la llave Y", es decir, X necesita a Y) que empieza y termina en la llave del ciclo con menor id de texto (ej. itm_a -> itm_c -> itm_b -> itm_a), indicando junto a cada flecha la puerta que bloquea (sala y dirección). Si hay varios ciclos, se reporta al menos uno, elegido siempre de la misma forma (por menor id de llave inicial) para que dos ejecuciones den el mismo resultado.
- Q: ¿Puede la sala inicial contener llaves (en el suelo o portadas por enemigos que inician en ella), y cómo deben procesarse en la secuencia de obtención? (FR-010, FR-012) → A: Sí puede contener llaves (en el suelo o en la suelta de enemigos que inician en ella) y se consideran obtenibles desde el principio. Pertenecen a la etapa 0, que es toda la región alcanzable sin usar llaves, y se ordenan por id de texto junto con las demás llaves de esa etapa; no necesariamente encabezan la secuencia.
- Q: ¿Qué debe hacer el comando `--verificar <cripta>` cuando se solicita verificar una cripta que no existe en el servicio ni en el almacenamiento local? (FR-017) → A: Imprime un mensaje claro de error en la salida estándar y termina con código de salida 2. Se fijan estos códigos de salida para `--verificar`: 0 si la cripta es resoluble, 1 si no es resoluble, y 2 si no se pudo verificar (cripta inexistente, falla de red o falta de `presupuesto_solicitudes`). En ningún caso se crea una vista.
- Q: ¿Cuál debe ser el formato exacto del reporte en texto tanto para el caso resoluble como para el no resoluble? (FR-012, FR-014) → A: Plantilla exacta con secciones omitibles si están vacías (salvo ESTADO): ESTADO: RESOLUBLE | NO RESOLUBLE | NO VERIFICADA; ORDEN DE LLAVES: (etapa N: itm_...); LLAVES NO OBTENIBLES: itm_...; FRONTERA BLOQUEADA: (- sala X (DIR) -> sala Y: pide K | sin llave asociada); UBICACIÓN DE LLAVES: (- itm_...: sala S | sala S (suelta del enemigo E)); CICLOS DETECTADOS: (- itm_a -> itm_b [sala S (DIR)] -> itm_a [sala S' (DIR')]); MOTIVO: <texto explicativo>. Reglas de determinismo: frontera por id de sala y luego por dirección en orden N, S, E, O; ubicaciones por id de llave; llaves en cada etapa por id de texto; direcciones N, S, E, O. La consola muestra este texto tal cual y Pygame muestra las mismas secciones.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verificación previa al inicio del juego y modo de inspección CLI (Priority: P1)

Como jugador o explorador, antes de que inicie una expedición en una cripta, deseo que el sistema determine de forma automática si la cripta puede ser ganada a partir del esqueleto y la ubicación inicial de las llaves, impidiendo el inicio de partidas irresolubles salvo que se fuerce su arranque de manera explícita. Asimismo, como usuario de consola, deseo poder ejecutar esta verificación de manera aislada (`--verificar <cripta>`) sin inicializar la interfaz gráfica de usuario.

**Why this priority**: Evita que el jugador gaste tiempo o presupuesto de solicitudes en calabozos topológicamente imposibles de resolver y proporciona una herramienta de diagnóstico en frío sin sobrecarga gráfica.

**Independent Test**: Puede probarse de forma independiente invocando el comando de verificación directa o iniciando partidas sobre criptas con condiciones de victoria alcanzables y no alcanzables, comprobando el inicio o bloqueo de la partida y la no creación de la interfaz en modo `--verificar`.

**Acceptance Scenarios**:

1. **Given** una cripta no resoluble y la ausencia del modificador `--forzar`, **When** el usuario intenta iniciar la partida normal, **Then** la partida no inicia; el sistema presenta el reporte de no resolubilidad en la interfaz activa (como texto en modo consola, o como pantalla en Pygame en modo `--gui` retornando luego a la selección de cripta), y en consola la aplicación termina con mensaje informativo.
2. **Given** una cripta no resoluble y la presencia del modificador `--forzar`, **When** el usuario ejecuta la orden de inicio, **Then** el sistema presenta el reporte de no resolubilidad en la interfaz activa (como texto en consola o pantalla en Pygame) y permite iniciar la partida para continuar la expedición normalmente.
3. **Given** una invocación con el modificador `--verificar <cripta>`, **When** el sistema procesa la verificación, **Then** imprime el reporte completo en la salida estándar y finaliza sin inicializar ni crear ninguna vista (ni de consola ni de Pygame), retornando código de salida 0 si es resoluble, 1 si no es resoluble, o 2 si la verificación no pudo completarse (cripta inexistente, error de red o falta de `presupuesto_solicitudes`).

---

### User Story 2 - Reporte determinista de cripta resoluble con orden de llaves (Priority: P2)

Como jugador y estratega, cuando una cripta sea resoluble, deseo recibir en el reporte un orden de obtención de llaves válido donde cada llave aparezca estrictamente después de las llaves necesarias para desbloquear el camino hacia ella, garantizando que si existen varios órdenes válidos el sistema produzca siempre el mismo resultado reproducible en ejecuciones sucesivas.

**Why this priority**: Asegura que el explorador disponga de una ruta de navegación garantizada y que el sistema cumpla con determinismo estricto para depuración, repetición y pruebas automáticas.

**Independent Test**: Se evalúa analizando criptas resolubles con múltiples caminos y bifurcaciones de llaves, comprobando que la secuencia de llaves cumple las dependencias de apertura de puertas y que múltiples corridas independientes con la misma entrada generan exactamente la misma secuencia de llaves.

**Acceptance Scenarios**:

1. **Given** una cripta resoluble que admite múltiples órdenes de obtención de llaves topológicamente válidos, **When** se ejecutan dos o más verificaciones consecutivas sobre dicha cripta, **Then** ambas ejecuciones producen exactamente la misma secuencia de llaves, agrupando por etapas de alcanzabilidad topológica y desempatando de manera determinista por orden lexicográfico de sus identificadores de texto únicamente entre llaves que se vuelven obtenibles al mismo tiempo.
2. **Given** una cripta resoluble estándar, **When** concluye la verificación, **Then** el reporte indica que la cripta es resoluble y lista una secuencia ordenada de llaves donde toda llave precedente desbloquea las puertas que permiten alcanzar a las llaves sucesivas hasta llegar a la llave de salida y la sala final.

---

### User Story 3 - Diagnóstico de cripta no resoluble y detección de ciclos (Priority: P3)

Como explorador o diseñador de calabozos, cuando una cripta no sea resoluble, deseo recibir un reporte detallado que explique de forma precisa por qué no puede ganarse: cuáles llaves no pueden alcanzarse, qué puertas de la frontera bloqueada impiden el avance junto con la llave que pide cada una, en qué sala o enemigo se halla cada una de esas llaves, y si existe un ciclo concreto de dependencia circular de llaves (por ejemplo, una llave cerrada detrás de puertas que solo ella misma puede abrir).

**Why this priority**: Brinda retroalimentación clara y accionable sobre los puntos de estancamiento del calabozo y permite detectar deadlocks estructurales o fallos de diseño en la generación de calabozos.

**Independent Test**: Se prueba con criptas sintéticas con bloqueos de frontera y con criptas que contengan dependencias circulares (cerraduras autorreferenciales o cadenas cíclicas), comprobando que el reporte lista las salas alcanzables, las puertas frontera, las llaves faltantes y el ciclo específico.

**Acceptance Scenarios**:

1. **Given** una cripta donde la `llave_salida` se encuentra ubicada detrás de la única puerta que ella misma abre, **When** se ejecuta la verificación de resolubilidad, **Then** el sistema califica la cripta como no resoluble y el reporte señala explícitamente el ciclo concreto formado entre dicha puerta y la llave (ej. `llave_salida -> llave_salida` con sala y dirección de la puerta bloqueante).
2. **Given** una cripta con una cadena circular de llaves (la llave A está detrás de una puerta que pide B, y B detrás de una puerta que pide A, ambas inaccesibles), **When** se verifica la cripta, **Then** el reporte clasifica la cripta como no resoluble e incluye la identificación precisa del ciclo ordenado empezando por la llave con menor identificador lexicográfico (ej. `itm_a -> itm_b -> itm_a`), indicando la sala y dirección de cada puerta bloqueante.
3. **Given** una cripta donde el avance queda truncado por puertas cerradas cuyas llaves están en zonas aún no alcanzadas pero sin formar ciclos, **When** se ejecuta la verificación, **Then** el reporte enumera las puertas que componen la frontera bloqueada adyacente a la zona alcanzable, la llave requerida por cada una y la ubicación (sala o enemigo inicial) donde reposa cada una de dichas llaves.

---

### User Story 4 - Obtención e integración de llaves, enemigos y nuevos atributos del servicio web (Priority: P4)

Como sistema de exploración, requiero consultar el servicio web para obtener la ubicación de las llaves (`GET /criptas/<id>/llaves`), considerar que las llaves portadas por enemigos se obtienen en la sala donde estos inician, admitir costos opcionales en salidas del esqueleto (100 por defecto si no vienen), incorporar fichas de catálogo con comportamiento "cazador" y rango, gestionar el presupuesto de solicitudes ante reintentos y consultas de llaves, e invalidar datos cacheados por versión en vez de borrado manual, operando de idéntica manera en modo `--offline`.

**Why this priority**: Asegura la interoperabilidad completa con la API actualizada del servidor de criptas, contemplando las nuevas entidades y manteniendo la fidelidad de datos tanto en línea como desconectado.

**Independent Test**: Se prueba simulando respuestas del servicio web para `/llaves`, con llaves en salas fijas y llaves en enemigos, verificando el decremento del presupuesto de solicitudes, la persistencia local de los datos de llaves, y comprobando que en modo `--offline` el sistema procesa los mismos datos sin conexiones remotas.

**Acceptance Scenarios**:

1. **Given** una cripta donde una llave figura en el campo `suelta` de una instancia de enemigo errante devuelta por `GET /criptas/<id>/llaves`, **When** el sistema procesa la información para la verificación de resolubilidad, **Then** ubica la disponibilidad de dicha llave en la sala donde dicho enemigo inicia.
2. **Given** una solicitud al endpoint `GET /criptas/<id>/llaves`, **When** se ejecuta la consulta (incluyendo cualquier reintento por limitación de tasa o código 429), **Then** cada intento cuenta y reduce en uno el `presupuesto_solicitudes` disponible de la partida.
3. **Given** un esqueleto de cripta recibido donde ciertas salidas no declaran el campo `costo`, **When** se interpreta el esqueleto, **Then** el sistema asigna automáticamente un costo de 100 a dichas salidas.
4. **Given** datos de cripta guardados localmente correspondientes a una versión previa, **When** se recibe del servidor una versión distinta de la cripta, **Then** el sistema invalida automáticamente los datos guardados mediante comparación de versión, reemplazándolos por los nuevos sin requerir la eliminación manual de archivos en disco.
5. **Given** la invocación del sistema con el modificador `--offline`, **When** se procesan criptas y llaves previamente almacenadas, **Then** el sistema ofrece exactamente la misma estructura de datos (costos de salidas, llaves, enemigos cazadores y rangos) y ejecuta la verificación idénticamente que en línea.

---

### Edge Cases

- **Cripta sin llave de salida o sin puerta hacia la salida**: Si el esqueleto o la consulta de llaves no contienen la llave requerida para la salida, o si existiendo la llave de salida ninguna puerta hacia la sala de salida la requiere, la cripta se clasifica como no resoluble y el reporte indica explícitamente dicha anomalía (por ejemplo, que no existe ninguna puerta hacia `sala_salida` que requiera `llave_salida`), detallando además las llaves no obtenibles y la frontera bloqueada que existan.
- **Sala inicial coincide con sala de salida**: Si la sala inicial es la misma que la sala de salida y la puerta de escape requiere `llave_salida`, la cripta requiere de todas formas obtener dicha `llave_salida` y abrir la puerta para considerarse resoluble.
- **Enemigo con llave ubicado en una sala inalcanzable**: La llave portada por el enemigo solo se computa como adquirida si la sala inicial de dicho enemigo resulta alcanzable desde la región explorada.
- **Llaves en la sala inicial y región inicial (etapa 0)**: La sala inicial puede albergar llaves directamente en el suelo o en el campo `suelta` de enemigos que inicien en ella. Estas llaves, junto con todas las situadas en cualquier sala alcanzable inicialmente sin usar llaves, pertenecen a la etapa 0 de exploración y se ordenan lexicográficamente por su identificador de texto junto con las demás llaves de dicha etapa.
- **Agotamiento de presupuesto o fallo de red en la consulta de llaves**: Si la consulta a `GET /criptas/<id>/llaves` no puede completarse por falta de presupuesto de solicitudes o fallo de comunicación, el sistema utiliza los datos locales si su versión coincide con la de la cripta. Si no se dispone de datos locales válidos, el sistema no se cae: informa en la interfaz activa el motivo exacto (red o presupuesto) e impide iniciar la partida (salvo con `--forzar`); bajo `--verificar`, imprime el error en la salida estándar y finaliza con código de salida distinto de cero.
- **Salidas cerradas sin llave asociada**: Si una salida figura como cerrada pero no especifica llave requerida en el calabozo, se considera permanentemente infranqueable durante toda la verificación (igual que en el juego, donde una puerta cerrada sin llave no se puede abrir). Si es adyacente a la región alcanzable, se incluye en la frontera bloqueada del reporte indicando explícitamente que no tiene llave asociada.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE proveer la consulta al endpoint `GET /criptas/<id>/llaves`, la cual devuelve para cada llave su identificador (`id`), la sala donde está ubicada (`sala`), y opcionalmente el campo de instancia enemiga (`enemigo`).
- **FR-002**: Cuando la consulta de llaves incluya el campo `enemigo`, el sistema DEBE determinar que la llave está contenida en el campo `suelta` de dicha instancia de enemigo, y que su sala de obtención para la verificación corresponde a la sala donde ese enemigo inicia.
- **FR-003**: Toda solicitud HTTP realizada al endpoint de llaves DEBE contabilizarse dentro del contador `presupuesto_solicitudes`, incluyendo reintentos y solicitudes que reciban código de estado 429. Si existen datos locales de llaves cuya versión coincide con la versión reportada de la cripta (o si se ejecuta bajo el modo `--offline`), el sistema DEBE reutilizar dichos datos guardados sin realizar una nueva consulta HTTP.
- **FR-004**: Los datos obtenidos de la consulta de llaves DEBEN considerarse válidos mientras coincida la versión reportada de la cripta, y DEBEN poder persistirse localmente junto con los demás datos de la cripta. Si la consulta falla o no resta `presupuesto_solicitudes` y no hay datos locales válidos, el programa NO DEBE caerse: DEBE emitir un mensaje en la interfaz activa explicando el motivo (red o presupuesto) e impedir el inicio de la partida (salvo con `--forzar`), o terminar con código distinto de cero bajo `--verificar`.
- **FR-005**: La invalidación de datos almacenados localmente de versiones anteriores DEBE realizarse automáticamente mediante la validación y discrepancia del identificador de versión de la cripta, sin requerir el borrado manual de archivos en el sistema de archivos.
- **FR-006**: El modo de ejecución fuera de línea (`--offline`) DEBE ofrecer exactamente la misma disponibilidad y estructura de datos (esqueleto, costos, llaves y catálogo de enemigos) que el modo en línea a partir de los datos previamente almacenados.
- **FR-007**: Si una salida en el esqueleto de la cripta no contiene el campo `costo`, el sistema DEBE asignarle de forma predeterminada un costo de valor 100.
- **FR-008**: El sistema DEBE admitir en las fichas del catálogo de enemigos el comportamiento "cazador" y el atributo numérico de rango.
- **FR-009**: Antes de iniciar una partida, el sistema DEBE ejecutar un proceso de verificación de resolubilidad de la cripta utilizando exclusivamente la información del esqueleto de salas/salidas y la ubicación inicial de las llaves.
- **FR-010**: La verificación de resolubilidad DEBE operar bajo los siguientes supuestos formales:
  1. Se puede atravesar cualquier salida que se encuentre abierta.
  2. Se puede atravesar cualquier salida cerrada cuya llave ya haya sido obtenida. Toda salida cerrada que no especifique llave requerida se considera estrictamente infranqueable durante la verificación.
  3. Las llaves no se consumen al abrir salidas/puertas.
  4. Todo enemigo presente en una sala puede ser derrotado.
  5. Una llave ubicada en una sala (en el suelo o portada por un enemigo que inicia en ella) se considera inmediatamente obtenible al alcanzar dicha sala. Las llaves presentes en la región alcanzable desde el inicio sin usar llaves (incluyendo la sala inicial) constituyen la etapa 0 y se ordenan lexicográficamente por su identificador de texto junto con las demás llaves de esa etapa.
  6. Las trampas y los mecanismos de cierre automático no bloquean el paso en la verificación.
- **FR-011**: El sistema DEBE calificar una cripta como resoluble si y solo si, partiendo desde la sala inicial, es posible obtener la `llave_salida` y alcanzar la `sala_salida` atravesando una puerta que requiere dicha llave. Si existe `llave_salida` pero ninguna puerta que la requiere conduce hacia `sala_salida`, la cripta DEBE clasificarse como no resoluble.
- **FR-012**: Si la cripta es resoluble, el reporte emitido por el sistema DEBE presentar un orden de obtención de llaves en el que cada llave aparezca estrictamente después de las llaves requeridas para alcanzarla.
- **FR-013**: Si existen múltiples órdenes de obtención de llaves válidos para una cripta resoluble, el sistema DEBE agrupar las llaves por etapas de alcanzabilidad topológica y resolver los empates de forma determinista para producir exactamente la misma secuencia ordenada en cualquier ejecución independiente sobre la misma cripta, aplicando orden lexicográfico de texto en sus identificadores (`id`) únicamente entre llaves que se vuelven obtenibles en la misma etapa.
- **FR-014**: Si la cripta no es resoluble, el reporte emitido por el sistema DEBE detallar obligatoriamente:
  1. La lista de llaves que no pueden ser obtenidas.
  2. Las puertas de la frontera bloqueada (puertas cerradas adyacentes a la región de salas alcanzable) indicando la llave requerida por cada una (o señalando que no tienen llave asociada si carecen de ella).
  3. La ubicación (sala o enemigo inicial) donde se encuentra cada una de las llaves requeridas por la frontera bloqueada.
  4. Si una llave se encuentra detrás de puertas que solo ella misma abre (de forma directa o a través de una cadena de llaves interdependientes), el ciclo concreto representado como una cadena orientada de dependencias (donde la flecha X -> Y indica que la llave X está detrás de una puerta que pide la llave Y, es decir, X necesita a Y), empezando y terminando en la llave del ciclo con menor identificador de texto e indicando junto a cada flecha la puerta que bloquea (sala y dirección). Si existen múltiples ciclos, el sistema DEBE reportar deterministamente al menos uno desempatando por el menor identificador de llave inicial.
  5. Si existe `llave_salida` pero ninguna puerta hacia `sala_salida` la requiere, la indicación explícita de dicha anomalía topológica.
- **FR-015**: Si la cripta resulta no resoluble, el sistema DEBE impedir el inicio de la partida y mostrar el reporte de no resolubilidad en la interfaz que esté activa (como texto en modo consola, y como pantalla en Pygame en modo `--gui` volviendo a la selección de cripta), salvo que el usuario haya especificado la opción `--forzar`.
- **FR-016**: Al recibir la opción de línea de comandos `--forzar`, el sistema DEBE emitir el reporte de resolubilidad en la interfaz activa (como texto en consola o pantalla en Pygame) y proceder a iniciar la partida aun cuando la cripta haya sido calificada como no resoluble.
- **FR-017**: La opción de línea de comandos `--verificar <cripta>` DEBE ejecutar únicamente la verificación de resolubilidad sobre la cripta especificada, imprimir el reporte completo en la salida estándar y salir inmediatamente sin crear ni inicializar ninguna vista (ni de consola ni de Pygame). Se fijan obligatoriamente los siguientes códigos de salida:
  - Código `0`: La cripta es resoluble.
  - Código `1`: La cripta no es resoluble.
  - Código `2`: La verificación no pudo completarse (por cripta inexistente, error de comunicación/red o agotamiento de `presupuesto_solicitudes`).
- **FR-018**: El reporte emitido en la consola (y las secciones mostradas en la pantalla de Pygame bajo el modo `--gui`) DEBE ajustarse estrictamente a la siguiente estructura y plantilla textual (omitiendo las secciones que resulten vacías, excepto `ESTADO:` que es siempre obligatoria):
  ```text
  ESTADO: RESOLUBLE | NO RESOLUBLE | NO VERIFICADA
  ORDEN DE LLAVES:
    etapa 0: itm_a, itm_b
    etapa 1: itm_c
  LLAVES NO OBTENIBLES: itm_x, itm_y
  FRONTERA BLOQUEADA:
    - sala 4 (E) -> sala 7: pide itm_x
    - sala 5 (N) -> sala 9: sin llave asociada
  UBICACIÓN DE LLAVES:
    - itm_x: sala 12
    - itm_y: sala 9 (suelta del enemigo e-1203)
  CICLOS DETECTADOS:
    - itm_a -> itm_b [sala 3 (S)] -> itm_a [sala 8 (O)]
  MOTIVO: <texto explicativo>
  ```
  El sistema DEBE aplicar las siguientes reglas canónicas para asegurar un reporte determinista y reproducible:
  1. Las direcciones se escriben únicamente con las siglas canónicas `N`, `S`, `E`, `O`.
  2. Las puertas de la sección `FRONTERA BLOQUEADA:` se ordenan de forma ascendente por el identificador numérico de la sala de origen, y en caso de empate, por la dirección en el orden estricto `N`, `S`, `E`, `O`.
  3. Los elementos de `UBICACIÓN DE LLAVES:` se ordenan por el identificador de texto de la llave.
  4. Las llaves dentro de cada línea de `etapa X:` en `ORDEN DE LLAVES:` se ordenan lexicográficamente por su identificador de texto (`id`).
  5. En `CICLOS DETECTADOS:`, el ciclo comienza y termina en la llave con menor identificador de texto, indicando entre corchetes la sala de origen y la dirección de la puerta bloqueante (ej. `[sala 3 (S)]`).
  6. La consola muestra este formato de texto tal cual, y la interfaz gráfica de Pygame expone exactamente los mismos contenidos seccionales.

---

### Key Entities *(include if feature involves data)*

- **Cripta**: Entidad central del calabozo que contiene el identificador único, la versión actual de la cripta, la sala inicial de expedición, la sala de salida, la llave requerida para salir y el presupuesto total de solicitudes HTTP asignado.
- **Salida / Puerta**: Conexión entre dos salas con un costo de desplazamiento (por defecto 100 si no se explicita), estado de apertura (abierta o cerrada), y la referencia a la llave requerida para abrirla si está cerrada.
- **Llave**: Objeto identificado de forma unívoca capaz de abrir una o varias puertas específicas; puede ubicarse directamente en una sala del calabozo o estar en poder de una instancia enemiga al inicio.
- **Enemigo**: Ficha con tipo del catálogo, asignación a una sala inicial, posible botín en su campo `suelta` (que puede contener una llave), y atributos de comportamiento ("cazador", "errante", etc.) y rango.
- **Reporte de Resolubilidad**: Resultado estructurado del análisis de alcanzabilidad que contiene la condición de resoluble o no resoluble, el orden secuencial de adquisición de llaves (si es resoluble), y el desglose de frontera bloqueada, llaves inalcanzables y ciclos detectados (si es no resoluble).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La verificación de resolubilidad DEBE completarse en un tiempo inferior a 200 milisegundos en la cripta publicada más grande disponible en el servicio web.
- **SC-002**: El costo temporal total de la verificación DEBE crecer de forma aproximadamente lineal en relación con el número de salas, salidas y llaves de la cripta, sin realizar exploraciones completas repetidas de toda la cripta por cada llave descubierta.
- **SC-003**: La construcción del reporte de una cripta no resoluble (incluyendo llaves inalcanzables, puertas de frontera y ciclos) DEBE generarse a partir de la misma pasada de recorrido de la verificación, sin reiniciar el recorrido de la cripta.
- **SC-004**: La detección y reporte de ciclos en calabozos irresolubles DEBE ser estrictamente determinista, produciendo el mismo ciclo idéntico en corridas repetidas con la misma cripta.
- **SC-005**: La opción `--bench resolubilidad` DEBE comparar de forma cuantitativa el tiempo de ejecución del recorrido incremental frente a la alternativa de recorrido repetido por llave sobre criptas sintéticas que contengan cadenas extensas de llaves encadenadas.

---

## Assumptions

- La versión de la cripta devuelta por la API permite al cliente verificar si la información en disco coincide con la del servidor; ante cualquier diferencia de versión, los archivos cacheados se actualizan mediante sobrescritura controlada sin necesidad de intervención manual del usuario.
- En la verificación de resolubilidad, se asume que todo enemigo puede ser derrotado sin restricciones de vida ni combate, y que las llaves contenidas en su campo `suelta` están disponibles de inmediato al alcanzar la sala inicial de dicho enemigo.
- El costo numérico asignado a las salidas (100 por defecto) no altera la transitabilidad lógica ni la resolubilidad topológica del calabozo; se emplea en etapas posteriores de cálculo de rutas y ponderación.
- Los cierres automáticos temporales o trampas de las salas no imposibilitan permanentemente la transitabilidad topológica en el modelo de verificación previa.
- Todas las salidas registradas en el esqueleto que se encuentren abiertas, o cuyas llaves ya hayan sido recolectadas en la región alcanzable, se consideran transitables de forma consistente según el grafo de adyacencias del calabozo.
