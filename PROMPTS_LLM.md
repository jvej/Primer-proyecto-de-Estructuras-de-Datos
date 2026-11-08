# Bitácora de uso de LLM 

| | |
|---|---|
| **Proyecto** | CRIPTA |
| **Curso** | Estructuras de Datos II — Universidad Nacional, Costa Rica |
| **Periodo** | II Ciclo 2026 |

Este documento reúne los registros de uso de modelos de lenguaje (LLM) de cada integrante del grupo, organizados según la parte del proyecto que tuvo a cargo. Cada sección indica los apartados del enunciado que cubre y la herramienta utilizada.

**Convenciones**

- Los prompts se transcriben en bloques de cita (`>`).
- Lo que aparece entre `[corchetes]` es un espacio que se reemplaza en cada uso (nombre de módulo, salida de consola, apartado del enunciado, etc.).
- **Uso** resume para qué sirvió el prompt o qué decisión se tomó a partir de él.
- En los bancos de prompts se conserva la numeración original de cada integrante.

---

## Índice

1. [Red y datos remotos — Jeferson](#1-red-y-datos-remotos--jeferson)
2. [Caché, persistencia, ordenamiento y guardado binario — Kimberly](#2-caché-persistencia-ordenamiento-y-guardado-binario--kimberly)
3. [Motor del juego — Mariano](#3-motor-del-juego--mariano)
4. [Inventario, retroceso, replay, controlador y vista — Axel](#4-inventario-retroceso-replay-controlador-y-vista--axel)
5. [Recursos visuales, sonido y repeticiones — Jeferson](#5-recursos-visuales-sonido-y-repeticiones--jeferson)

---

## 1. Red y datos remotos — Jeferson

| | |
|---|---|
| **Integrante** | Jeferson |
| **Apartados** | §3.1, §3.4, §4.2, §4.3, §4.8, §5.1 |
| **Tipo de registro** | Banco de prompts de guía |

**Modo de uso**

1. Pegar primero el *prompt base* al iniciar la conversación.
2. Adjuntar el enunciado (`Primer_Proyecto_Estructuras_de_Datos_II_2026.md`), el reparto (`Cripta_Explicacion_y_Reparto_Detallado.md`) y el código actual del repositorio.
3. Elegir el prompt necesario y reemplazar lo que esté entre `[corchetes]`.
4. Si el LLM entrega el módulo completo, pedirle que lo convierta en pistas, pseudocódigo o preguntas guía.

### Prompt base

> Actúa como tutor de programación en Python 3.11+. Voy a escribir yo el código de mi parte del proyecto CRIPTA. Te adjunto el enunciado, el reparto y el repositorio actual. Tu papel es:
> - Explicarme qué exige el enunciado en cada apartado (cita el número de § en que te basas).
> - Ayudarme a decidir el diseño: responsabilidades de cada módulo, interfaces y estructuras de datos.
> - Darme pistas, pseudocódigo o fragmentos mínimos, NO el módulo completo.
> - Revisar el código que yo te comparta, señalar errores o incumplimientos y explicar por qué.
> - Decirme qué módulos dependen de otros integrantes y no asumir su implementación.
> - Preguntarme cuando falte información.
>
> Debo poder explicar cada módulo en la defensa (§9), así que prioriza que yo entienda.

### A. Planificación y alcance

#### 1. Qué me toca y qué depende de otros

> Según el documento de reparto y el enunciado, lista mis módulos y clasifícalos en: (a) los que puedo implementar solo, (b) los que dependen de otro integrante (indica de quién y qué necesito). Explica el orden recomendado para implementarlos y por qué.

#### 2. Entender cada módulo antes de escribirlo

> Para el módulo [nombre]: explícame su propósito, qué apartado del enunciado lo exige, qué interfaz debe exponer y qué otros módulos lo usan. Dame preguntas que debo poder responder antes de empezar a codificar.

#### 3. Plan por pasos

> Dame un plan por pasos para implementar [módulo o conjunto de módulos], con criterios para saber cuándo cada paso está terminado y cómo probarlo.

### B. Guía por módulo

#### 4. `errores.py`

> Ayúdame a diseñar la jerarquía de excepciones de la capa de red. ¿Qué tipos de error distingue el enunciado (presupuesto agotado, fallo de red, respuesta inválida, etc.) y cuál debería ser la excepción base?

#### 5. `presupuesto_red.py`

> Explícame qué exige el enunciado sobre el presupuesto de solicitudes (por ejemplo [N] por cripta). ¿Qué estado debe llevar la clase, qué operaciones debe ofrecer y qué debe pasar cuando se agota? Dame pseudocódigo, no el código final.

#### 6. `fuente_datos.py`

> Ayúdame a decidir cómo definir la interfaz común de fuentes de datos (clase abstracta o protocolo). ¿Qué métodos mínimos debe tener para que `cliente_http` y `cliente_offline` sean intercambiables? Explícame las ventajas y desventajas de cada opción.

#### 7. `cliente_http.py`

> Guíame para consumir la API según el enunciado: construcción de URLs, manejo de timeouts, validación de las respuestas y conteo contra el presupuesto. ¿Qué casos de error debo considerar? Dame pistas sobre cómo manejarlos con mis excepciones.

#### 8. `cliente_offline.py`

> Explícame qué debe hacer el modo offline según el enunciado y de dónde salen sus datos. ¿Cómo garantizo que respete exactamente la misma interfaz que el cliente HTTP?

#### 9. `fabrica_fuentes.py`

> Ayúdame a razonar cómo elegir entre fuente HTTP y offline (patrón fábrica): ¿qué parámetro o configuración decide? ¿Dónde conviene leerlo? Muéstrame las opciones y sus trade-offs.

#### 10. `bitacora_pantalla.py`

> Explícame qué debe mostrar la bitácora en pantalla según el enunciado (§[X]) y qué información debo registrar por cada solicitud. Sugiéreme una estructura de datos adecuada y cómo evitar que crezca sin límite.

#### 11. `cola_fifo.py`

> Quiero implementar yo mismo una cola FIFO. Explícame cómo se comporta, qué operaciones necesita, su complejidad y qué restricciones impone el enunciado sobre estructuras permitidas (¿puedo usar `collections.deque`?). Revisa mi implementación cuando te la comparta.

#### 12. `ejecutor_red.py`

> Ayúdame a entender el rol del ejecutor de red: cómo usa la cola FIFO, cómo se relaciona con el presupuesto y con la bitácora, y si requiere hilos o es secuencial. Dame el flujo en pseudocódigo.

#### 13. `almacen_local.py`

> Explícame qué debe guardarse localmente (caché), con qué formato y cuándo se invalida. ¿Qué estructura de datos me conviene para búsquedas rápidas y por qué? Guíame sobre la lectura y escritura de archivos.

#### 14. `esqueleto.py`

> Léeme el apartado del enunciado sobre el esqueleto/estructura base y explícame qué debe contener. ¿Qué datos son obligatorios y cuáles opcionales?

#### 15. `resolutor_catalogo.py`

> Ayúdame a entender cómo se resuelven los elementos del catálogo (nombres, ids, caché) y qué debe pasar si un elemento no existe. Explícame los casos borde que debo considerar.

#### 16. `precarga_contenido.py`

> Explícame qué debe precargarse, cuándo y cómo se controla el presupuesto durante la precarga. Dame el orden de operaciones en pseudocódigo.

### C. Pruebas y mediciones

#### 17. `test_red.py`

> Ayúdame a diseñar casos de prueba para [módulo]: caminos normales, errores y casos borde. Explícame cómo simular un servidor HTTP local con unittest o pytest para no gastar el presupuesto de la API real.

#### 18. `bench_red.py`

> Explícame qué debo medir según el enunciado (tiempos, número de solicitudes) y cómo hacerlo de forma correcta en Python (`time.perf_counter`, repeticiones). ¿Cómo presento los resultados?

#### 19. `probar_api.py` (prueba contra la API real)

> Guíame para escribir un script que pruebe la API real sin agotar el presupuesto: qué consultas hacer, cómo verificar que los formatos coinciden con el enunciado y cómo contar las solicitudes usadas.

### D. Integración y revisión

#### 20. Integrar en el repositorio

> Adjunto el repositorio. Explícame cómo integrar mis módulos sin modificar archivos de otros integrantes: estructura de imports, qué archivos debo llenar y cómo ejecutar las pruebas dentro del repo.

#### 21. Verificar el alcance de mis cambios

> Compara mi versión con el repositorio original y dime qué archivos modifiqué. Indica si toqué algo que pertenece a otros integrantes. Explícame cómo hacerlo yo mismo con `git diff` o una comparación de carpetas.

#### 22. Revisión punto por punto del enunciado

> Adjunto mi código. Revisa punto por punto los apartados §3.1, §3.4, §4.2, §4.3, §4.8 y §5.1: qué cumplo, qué falta y por qué. Cita el enunciado en cada punto.

### E. Errores comunes

#### 23. Error de módulo no encontrado

> Me aparece: [pega el error, por ejemplo `ModuleNotFoundError: No module named 'requests'`]. Explícame qué significa, cómo diagnosticar la causa (entorno virtual, intérprete de VS Code) y cómo resolverlo, paso a paso.

#### 24. Interpretar la salida de una prueba

> Esta es la salida de mi prueba contra la API real: [pega la salida]. Ayúdame a interpretarla: ¿los formatos coinciden con el enunciado? ¿Cuántas solicitudes del presupuesto usé? ¿Hay algo raro?

### F. Comunicación con el equipo y documentación

#### 25. Mensaje de avance para el grupo

> Tengo esta lista de módulos terminados: [lista]. Dame una estructura (no el texto final) para un mensaje breve para WhatsApp: qué incluir por módulo, quién depende de él y qué queda pendiente. Yo lo redacto y tú me das comentarios.

#### 26. Documento de Decisiones (§8)

> Explícame qué debe contener la sección de decisiones para §4.2, §4.3 y §4.8: qué decisiones de diseño debo justificar, qué alternativas comparar y cómo argumentar. Reviso mi borrador cuando lo tengas.

#### 27. Preparación para la defensa (§9)

> Hazme preguntas como las que haría un profesor sobre [módulo], una por una, y evalúa mi respuesta explicando qué me faltó.

#### 28. Bitácora de uso de LLM (§10.3)

> Explícame qué exige el enunciado sobre la bitácora de prompts y qué formato debo seguir. Dame una plantilla con los campos (fecha, adjuntos, prompt, para qué se usó) para que yo la complete con mis prompts reales.

### Prompts generales reutilizables

> Léeme el apartado [§X] del enunciado y explícame con tus palabras qué debo implementar.

> Antes de darme código, dime las opciones de diseño y sus ventajas y desventajas.

> Este es mi código de [función]. ¿Qué falla y por qué? Dame solo una pista, no la corrección.

> Dame pseudocódigo de [funcionalidad] y yo lo implemento en Python.

> ¿Qué casos borde debería probar en [módulo]?

> Revisa si mi solución respeta las restricciones del enunciado y justifica con el apartado.

> Hazme preguntas para comprobar que entendí [concepto] antes de continuar.

---

## 2. Caché, persistencia, ordenamiento y guardado binario — Kimberly

| | |
|---|---|
| **Integrante** | Kimberly |
| **Apartados** | §4.4, §4.9, §4.10 |
| **Herramienta** | Claude (Anthropic), en todas las entradas |
| **Periodo cubierto** | Desde el inicio del proyecto hasta el 02/10/2026 |
| **Tipo de registro** | Bitácora de consultas |

Utilicé la IA como apoyo para entender los requisitos, resolver dudas y errores, tener borradores de referencia y analizar mediciones. Cada entrada indica mi consulta, el apoyo recibido y lo que hice yo para verificarlo. Los mensajes completos no se transcriben: las consultas están resumidas, y lo que va entre paréntesis resume algo que no se puede copiar (capturas, salidas de consola).

### 2.1 Comprensión de mi parte del proyecto

#### Entrada 1 — 02/10/2026

- **Consulta:** Quise entender con claridad qué tareas incluía mi parte (caché y persistencia §4.4, ordenamiento §4.9 y guardado binario §4.10) y cómo se relacionan con el enunciado. Para eso adjunté el enunciado y el documento de reparto.
- **Apoyo recibido:** Me dio una introducción general de mi parte y explicó cada tarea con un orden de trabajo sugerido.
- **Mi trabajo:** Con esa explicación armé mi plan de trabajo para los tres módulos.

#### Entrada 2 — 02/10/2026

- **Consulta:** ¿Mi parte depende del trabajo de mis compañeros o puedo empezar de inmediato?
- **Apoyo recibido:** Indicó qué componentes podía desarrollar de forma independiente (ordenamiento, tabla hash y almacenamiento) y cuáles requerirían acordar interfaces con el grupo.
- **Mi trabajo:** Empecé por los módulos independientes y dejé los puntos de integración para después.

### 2.2 Git y organización del repositorio

#### Entrada 3 — 02/10/2026

- **Consulta:** No podía crear una nueva rama en el repositorio. Adjunté capturas de GitHub Desktop y pregunté si dejarlo solo con un archivo `.txt` serviría.
- **Error:** GitHub Desktop no me dejaba crear la rama.
- **Apoyo recibido:** Explicó que la causa probable era que el repositorio estaba vacío: sin un primer commit no hay rama base de la cual partir. Confirmó que un archivo `.txt` inicial bastaba.
- **Mi trabajo:** Hice el commit inicial y creé mi rama de trabajo.

#### Entrada 4 — 02/10/2026

- **Consulta:** ¿Hay problema si trabajo sin carpetas mientras el grupo define la estructura?
- **Apoyo recibido:** Me indicó que no es un problema técnico trabajar sin carpetas, porque los archivos se pueden reorganizar después.
- **Mi trabajo:** Decidí seguir sin carpetas hasta que el grupo acordara una estructura.

### 2.3 Ordenamiento (§4.9)

#### Entrada 5 — 02/10/2026

- **Consulta:** Consulté cómo estructurar inserción, merge sort y un selector automático de algoritmo, pidiendo que cumpliera la rúbrica y que el código fuera simple y natural.
- **Apoyo recibido:** Me dio un borrador de referencia con los dos algoritmos y el selector.
- **Mi trabajo:** Ejecuté el código y verifiqué que las salidas coincidieran con lo esperado.

#### Entrada 6 — 02/10/2026

- **Consulta:** ¿Cómo mido el rendimiento de los algoritmos y qué me falta por hacer?
- **Apoyo recibido:** Propuso un script de mediciones (`bench_ordenamiento.py`) y una lista de tareas pendientes.
- **Mi trabajo:** Usé ese script para hacer mis propias mediciones.

#### Entrada 7 — 02/10/2026

- **Consulta:** Pegué la salida de `bench_ordenamiento.py` en cuatro ocasiones y pregunté si el selector automático elegía el mejor algoritmo en cada escenario.
- **Apoyo recibido:** Analizó mis resultados y sugirió ajustes al criterio del selector después de cada medición:

  | Versión | Criterio del selector | Resultado |
  |---|---|---|
  | 1 | Pares vecinos desordenados | Elegía mal en "casi ordenado" con desorden lejano (n = 5000: 95 ms contra 12 ms) |
  | 2 | Límite de tamaño | Corregía ese caso, pero perdía el caso de desorden local |
  | 3 | Medición del desorden a distancia (`SALTO = 8`) | El selector sigue a la mejor opción en los cuatro escenarios |

- **Mi trabajo:** Ejecuté el bench en mi equipo, interpreté los resultados y apliqué cada cambio hasta que el selector fue consistente.

#### Entrada 8 — 02/10/2026

- **Consulta:** Al agregar las pruebas de corrección pregunté dónde debía incluir el código nuevo y si debía reemplazar todo el archivo.
- **Error:** `NameError` al ejecutar las pruebas (pegué el mensaje de consola).
- **Apoyo recibido:** Explicó que un `NameError` de este tipo suele venir de la indentación: una función o línea queda fuera del bloque donde debía estar y el nombre no existe en ese ámbito. Indicó dónde ubicar el código y cómo alinearlo.
- **Mi trabajo:** Corregí la indentación, ejecuté las pruebas y confirmé las cuatro salidas OK (inserción, merge, selector y caso casi ordenado local).

### 2.4 Persistencia en disco (§4.4)

#### Entrada 9 — 02/10/2026

- **Consulta:** ¿Cómo guardo las fichas en disco de forma eficiente? Había una parte que no entendía y pregunté qué debía corregir.
- **Apoyo recibido:** Propuso `almacen_fichas.py`, con su test y un bench contra la alternativa de un archivo por ficha. Me explicó con más detalle la parte que no entendí y qué ajustar.
- **Mi trabajo:** Realicé y ejecuté `test_almacen_fichas.py`; las siete pruebas dieron OK.

#### Entrada 10 — 02/10/2026

- **Consulta:** ¿Puedo reutilizar `AlmacenFichas` para guardar el esqueleto y el contenido de la cripta?
- **Apoyo recibido:** Confirmó que era viable y propuso `almacen_cripta.py`, con su test y su bench.
- **Mi trabajo:** Realicé y ejecuté `test_almacen_cripta.py` y `bench_almacen_cripta.py`.

### 2.5 Guardado binario (§4.10) y revisión de diseño

#### Entrada 11

- **Consulta:** Consulté cómo implementar el guardado binario y cómo corregir los errores que aparecieron al probarlo. Como no encontraba dónde cambiar cada cosa, pedí los archivos ya corregidos.
- **Error:** `ImportError` al importar el módulo y `struct.error` al ejecutar el guardado (pegué los mensajes de consola).
- **Apoyo recibido:** Propuso `guardado_binario.py`, su test y un bench contra JSON. Sobre el `ImportError`, explicó que suele indicar que el nombre importado no coincide con el definido en el módulo, o que el archivo tiene otro nombre o está en otra carpeta.
- **Mi trabajo:** Corregí los archivos, ejecuté `test_guardado_binario.py` y las seis pruebas dieron OK.

### 2.6 Declaración

Utilicé Claude como herramienta de apoyo para comprender los requisitos, obtener borradores de referencia y diagnosticar errores. Todo el código fue revisado, ejecutado y probado por mí, con pruebas y mediciones propias, y puedo explicarlo y modificarlo. Si hubo consultas a otras herramientas, aparecen en este documento; si no aparecen, no ocurrieron.

---

## 3. Motor del juego — Mariano

| | |
|---|---|
| **Integrante** | Mariano |
| **Apartados** | §2.3–§2.12, §4.1, §4.7, §5.2, Apéndice B |
| **Herramienta** | Claude (Anthropic), en todas las entradas |
| **Periodo cubierto** | Del 27/09/2026 al 18/10/2026 (fechas aproximadas) |
| **Tipo de registro** | Banco de prompts de guía |

#### 1. Organización de módulos por integrante — 27/09/2026

> Adjunto el documento de reparto del proyecto y, como referencia, el diagrama de asignación de tareas de un proyecto anterior. Oriéntame para diseñar mi propio diagrama de módulos por integrante: qué capas y módulos incluir, cómo representar las dependencias y cuáles son los puntos de contacto entre integrantes. Aclara las responsabilidades específicas del motor del juego según el enunciado.

#### 2. Mejorar la legibilidad del diagrama — 27/09/2026

> Este es el diagrama de módulos que preparé. Evalúa su legibilidad y oriéntame para simplificarlo. Considera cómo agrupar los módulos por integrante, reducir cruces entre flechas y destacar las dependencias importantes. Señala qué información podría ser redundante y explícame por qué.

#### 3. Dependencias del motor — 27/09/2026

> Con base en el reparto del equipo y el enunciado oficial, ayúdame a identificar de qué módulos de otros integrantes depende el motor del juego. Clasifica mis tareas entre las que puedo comenzar de inmediato y las que requieren acuerdos o entregas de otras personas. Recomienda un orden de trabajo razonable y justifica cada prioridad.

#### 4. Acuerdos con la persona responsable del retroceso — 27/09/2026

> La agenda de eventos (§4.1) debe integrarse con el sistema de retroceso (§4.6), desarrollado por otro integrante. Ayúdame a preparar los acuerdos técnicos que debemos resolver antes de programar: formato de los cambios invertibles, inicio y final de las acciones del jugador, registro de los cambios de estado y tratamiento del azar. Explica las alternativas y las consecuencias de cada decisión, sin escribir la implementación.

#### 5. Diseño inicial de la agenda de eventos — 27/09/2026

> Voy a implementar en Python la agenda de eventos de §4.1 mediante un heap binario propio. Según las restricciones del proyecto, ayúdame a comprender las operaciones necesarias para agendar eventos, extraer el siguiente y cancelar eventos; analiza su complejidad y explica cómo funcionan las operaciones de subir y bajar en el heap. Incluye pseudocódigo orientativo y las decisiones de diseño que debo resolver para las clases `Evento`, `Actor` y `Sala`. Evita entregar una implementación completa.

#### 6. Organización del código al trabajar en ramas — 27/09/2026

> El equipo está trabajando en ramas de Git separadas. Compara las ventajas y desventajas de mantener temporalmente una estructura plana de archivos y organizar las capas al final, frente a definir la arquitectura desde el inicio. Explica los riesgos de integración y los pasos que puedo seguir para reducir conflictos al unir las ramas.

#### 7. Validación de la agenda de eventos — 27/09/2026

> Este es mi programa de prueba y esta es la salida obtenida: [pegar código y salida]. Ayúdame a interpretar qué demuestra la salida y qué aspectos todavía no están verificados. Propón casos de prueba para el orden temporal, los desempates por número de secuencia y la cancelación de eventos. Oriéntame para convertir esos casos en pruebas automáticas con `assert`, sin escribir todas las pruebas por mí.

#### 8. Comparación con el enunciado oficial — 03/10/2026

> Adjunto el enunciado oficial y mi código actual. Revisa los requisitos de los apartados §2.3, §2.4 y §2.9 y señala las diferencias entre mi implementación y lo solicitado. Para cada diferencia, cita el apartado correspondiente y explica su impacto. No modifiques el código; ayúdame a entender qué debo revisar y si el documento indica una fecha de entrega.

#### 9. Reprogramación por cambio de velocidad y activación de enemigos — 03/10/2026

> Explícame la fórmula de §2.3 para reprogramar una acción cuando cambia la velocidad: `restante_nuevo = max(1, (tiempo_siguiente - t) * velocidad_anterior // velocidad_nueva)`. Utiliza ejemplos numéricos para que pueda comprobar mis cálculos. Explica también por qué los enemigos que se activan en el mismo instante deben programarse por orden de id de instancia (§2.4) y cómo puedo respetar esa regla sin usar `sorted()`.

#### 10. Comportamiento de enemigos y reloj virtual — 03/10/2026

> Oriéntame para implementar por mi cuenta los comportamientos de enemigos descritos en §2.8, el desempate del rastreador de §2.9 y el bucle del reloj virtual de §2.3. Explica las responsabilidades de cada parte y presenta el flujo general en pseudocódigo. Aclara cómo calcular el costo de decisión del rastreador en proporción a las salidas de su sala, según §4.7.

#### 11. Comprender el motor, las restricciones del curso y los comentarios de revisión — 08/10/2026

> Adjunto el enunciado, el reparto del trabajo y el avance actual del repositorio. Antes de proponer cambios, explícame cómo se relacionan la agenda de eventos, el turno del jugador, los enemigos, los efectos y el retroceso.
>
> Debo limitarme a los temas vistos en el curso: listas, colas, pilas, recursividad, heaps y colas de prioridad, algoritmos de ordenamiento, formatos JSON/XML/YAML, APIs y análisis de complejidad. No se han estudiado tablas hash. Si existe más de una alternativa válida dentro de estas restricciones, compáralas y justifica cuál conviene.
>
> También necesito identificar qué información o interfaces deben quedar listas para que los demás integrantes puedan avanzar. Para la interfaz gráfica se mencionaron Pygame y Arcade; explícame qué criterios debo usar para elegir una sola biblioteca.
>
> Analiza estos comentarios de revisión y, para cada uno, explica el problema, sus consecuencias y un enfoque posible para resolverlo, sin escribir la corrección completa:
> - En `activacion.py`, el primer evento de cada enemigo no se guarda en `evento_pendiente`, por lo que `matar_enemigo` no puede cancelarlo si el enemigo muere antes de su primer turno.
> - En `agenda_eventos.py`, `reprogramar_por_cambio_velocidad` crea un evento nuevo, pero `actor.evento_pendiente` sigue apuntando al anterior.
> - La acción reutilizada conserva el tiempo anterior y calcula el siguiente turno desde un instante incorrecto después de un cambio de velocidad.
> - En `sala.py`, `OPUESTA` usa un `dict`, aunque §7 prohíbe `dict` como tabla de búsqueda; se propone una tupla paralela a `DIRECCIONES`.
> - En `activacion.py` se utiliza `sorted()`, aunque debe usarse el método de ordenamiento desarrollado por Kim.
> - `Sala` solo guarda el estado abierto/cerrado de cada salida; faltan la llave requerida y el `cierre_automatico`.
> - `Actor` no tiene `vida_max` ni `tiempo_siguiente`, necesarios para limitar la curación y gestionar los turnos.
> - El jugador no forma parte de la agenda y `correr()` no se detiene cuando llega su turno. `mover_jugador` tampoco cobra tiempo, activa enemigos ni dispara trampas; debo coordinar estos aspectos con Axel.
> - Los cambios de estado se hacen directamente, por ejemplo `enemigo.sala = ...` o `recibir_dano()`, y deberían pasar por un punto central para permitir el registro del retroceso.

#### 12. Corregir la base del motor — 08/10/2026

> Estoy trabajando en las correcciones de la revisión relacionadas con el evento pendiente, el tiempo guardado en las acciones, las restricciones sobre `dict` y `sorted()`, los datos de las salidas y los atributos de `Actor`. Oriéntame punto por punto con preguntas, pistas o pseudocódigo. Para cada ajuste, indica qué caso de prueba permitiría comprobarlo. Después compartiré mi código para revisar si lo resolví correctamente.

#### 13. Integrar el motor con la capa de datos — 10/10/2026

> Adjunto el repositorio actualizado. Según el reparto, me corresponde utilizar `resolutor.obtener(id)` para crear enemigos, objetos y trampas, y registrar mensajes en la bitácora mediante `agregar()`. Ayúdame a planificar la integración sin hacer que el modelo dependa directamente de HTTP ni de archivos (§6). Divide el trabajo en pasos pequeños e incluye el jugador en la agenda, el registro para el retroceso, los efectos de §2.10 y la detección de victoria y derrota. Prioriza el cumplimiento de la rúbrica y evita la sobreingeniería; usa pseudocódigo y explicaciones en lugar de módulos completos.

#### 14. Retomar el trabajo y determinar el siguiente paso — 10/10/2026

> Este es el avance que tengo hasta ahora: [pegar código, cambios recientes o salida de las pruebas]. Revísalo contra el enunciado, identifica los problemas que todavía están presentes y recomiéndame el siguiente paso concreto. Explica cómo puedo verificar que ese paso quedó bien antes de continuar.

#### 15. Identificar los cambios en el repositorio — 12/10/2026

> Necesito comparar mi rama con la rama principal para identificar los archivos creados, modificados y eliminados. Explícame cómo utilizar `git status`, `git diff` y `git diff --stat` para revisar los cambios, y cómo comprobar si modifiqué accidentalmente archivos que corresponden a otros integrantes. Incluye los comandos pertinentes y explica qué información aporta cada uno.

#### 16. Verificar qué falta para terminar mi parte — 12/10/2026

> Adjunto mi código actual y el enunciado oficial. Oriéntame para construir una lista de verificación de los requisitos que corresponden a mi parte (§2.3 a §2.12, §4.1, §4.7, §5.2 y el Apéndice B). Clasifica cada punto como cumplido, parcial, pendiente o no verificable con la información disponible, y cita el apartado del enunciado que respalda la evaluación. No supongas que algo está implementado si no aparece en el código.

#### 17. Determinar qué pruebas se necesitan en la entrega — 12/10/2026

> Según los apartados §5.3, §8 y §9 del enunciado, explícame qué se exige sobre pruebas y mediciones. Ayúdame a distinguir los archivos de prueba obligatorios, los que sirven de dependencia para las mediciones y los que aportan evidencia útil para la defensa. Justifica cada conclusión con el apartado correspondiente.

#### 18. Planificar el contenido del README — 15/10/2026

> Explícame qué debe incluir el README según §10.1: versión de Python, dependencias, instalación, comandos, modos `--offline`, `--replay` y `--bench`, y archivos generados. Propón una estructura de secciones y una lista de verificación para que yo redacte el documento. Después podré compartir mi borrador para revisar su cumplimiento.

#### 19. Revisar el README contra la versión actual del proyecto — 18/10/2026

> Adjunto la versión más reciente del repositorio y mi borrador del README: [pegar borrador]. Compara la documentación con el código real, incluyendo comandos, banderas, rutas, estructura de carpetas y el punto de entrada, por ejemplo `main.py`. Señala los datos incorrectos, incompletos o no comprobables sin reescribir el README completo. Basa las observaciones en los archivos disponibles.

#### 20. Comprender los requisitos de la bitácora de uso de LLM — 18/10/2026

> Explícame qué exige §10.3 sobre la bitácora de prompts, incluyendo fecha aproximada, herramienta, texto del prompt y propósito de uso. Oriéntame para crear una plantilla en Markdown que pueda completar con mis prompts reales. Revisa después mi borrador y señala qué campos faltan, sin inventar registros.


#### 21. Especificación de terreno, cazador e invalidación de rutas (Capacidad 001) — 07/11/2026

- **Integrante**: Mariano
- **Fecha**: 07/11/2026
- **Herramienta**: Google Antigravity (IDE v2.0)
- **Modelo**: Gemini 3.8 Flash / Claude Opus 4.6
- **Uso de la respuesta**: Generar la especificación formal specs/001-terreno-cazador/spec.md para la capacidad 001 de CRIPTA Parte II según el flujo de spec-kit, la constitución y las reglas del proyecto, y preparar la fase de aclaración previa a la planificación.

> Soy Mariano, responsable de la capacidad 001 de CRIPTA Parte II:
> terreno, cazador e invalidación de rutas.
> 
> Leé el enunciado oficial de la segunda parte, las reglas del proyecto
> y .specify/memory/constitution.md. Revisá las especificaciones
> existentes para usar el número 001 si continúa disponible.
> 
> Guiame mediante spec-kit para crear la especificación de esta capacidad.
> La redacción debe ser clara, propia de estudiantes de segundo año y
> centrada en comportamientos observables. Las decisiones sobre
> estructuras, clases y archivos se definirán durante la planificación.
> 
> Mi objetivo interno es terminar el 11 de noviembre de 2026.
> El 15 de noviembre es el límite de respaldo.
> 
> Incluí estos requisitos funcionales con identificadores FR estables:
> 
> 1. Cada salida admite un costo entero mayor o igual que 1. Cuando
>    se omite, el costo es 100 y es igual en ambos sentidos.
> 
> 2. El movimiento de cualquier actor tarda:
>    max(1, costo_salida * 100 // velocidad).
>    Los costos de las demás acciones conservan las reglas vigentes.
>    Errantes y rastreadores conservan su comportamiento de elección
>    de movimiento.
> 
> 3. En su turno, el cazador ataca si comparte sala con el jugador.
>    En caso contrario, determina el costo mínimo hasta la sala actual
>    del jugador utilizando únicamente salidas abiertas.
> 
> 4. Si falta una ruta o su costo mínimo supera el rango del cazador,
>    espera con costo base 100. Si el costo iguala el rango, puede avanzar.
> 
> 5. Si existe una ruta dentro del rango, avanza un paso por una ruta
>    de costo mínimo. La acción usa el costo de la salida atravesada.
> 
> 6. Cuando varias primeras vecinas permiten alcanzar el mismo costo
>    mínimo, elige la vecina de menor ID.
> 
> 7. El cazador conoce el esqueleto completo y las puertas reales.
>    La niebla del jugador y la descarga del contenido de las salas
>    no condicionan su decisión. El cazador no abre puertas.
> 
> 8. Cada decisión debe coincidir con un cálculo desde cero en ese
>    instante. Contemplar apertura y cierre de puertas, movimiento
>    del jugador, cambios de velocidad, otros actores y retroceso.
> 
> Incluí los siete escenarios obligatorios con dado, cuando y entonces:
> 
> - Cazador sin ruta abierta.
> - Ruta mínima más cara que el rango, incluyendo la prueba del límite.
> - Ruta con más pasos y menor costo frente a otra con menos pasos y
>   mayor costo.
> - Empate entre dos primeras vecinas, resuelto por menor ID.
> - Puerta de la ruta cerrada entre dos turnos.
> - Actor con velocidad alta atravesando una salida de costo 1.
> - Cambio de velocidad durante una salida costosa, aplicando la regla
>   vigente de reprogramación del tiempo restante.
> 
> Agregá escenarios para ataque al compartir sala, costo predeterminado,
> simetría del costo, una puerta que abre una ruta antes imposible y
> restauración de puertas mediante retroceso.
> 
> Definí criterios SC medibles para:
> 
> - Ciclo entre decisiones del jugador inferior a 20 ms en la cripta
>   de referencia con decenas de cazadores activos.
> - Búsqueda acotada al alcance del cazador.
> - Comparación de cálculo individual y compartido.
> - Comparación de reutilización y recálculo con puertas estables
>   e inestables.
> - Reproducción determinista con la misma cripta, semilla y acciones.
> 
> Separá los resultados esperados de las mediciones pendientes.
> 
> Después de generar la especificación, guiame por la fase de aclaración.
> Preguntá únicamente por ambigüedades que los documentos no resuelvan.
> 
> Mi primera implementación posterior será el costo de movimiento
> para todos los actores, con pruebas vinculadas a los FR.
> 
> Registrá esta solicitud de manera textual en PROMPTS_LLM.md junto
> con mi nombre, la fecha real, la herramienta, el modelo si se conoce
> y el uso de la respuesta.



#### 22. Revisión y corrección de la especificación de terreno, cazador e invalidación de rutas (Capacidad 001) — 07/11/2026

- **Integrante**: Mariano
- **Fecha**: 07/11/2026
- **Herramienta**: Google Antigravity (IDE v2.0)
- **Modelo**: Gemini 3.8 Flash / Claude Opus 4.6
- **Uso de la respuesta**: Corregir y afinar la especificación formal specs/001-terreno-cazador/spec.md según los 10 puntos de ajuste solicitados: costos exactos de acciones no de movimiento, límites y condiciones de SC-004 a SC-006, búsqueda acotada SC-002, desempate entero por ID, semántica temporal de agenda, escenario cuantitativo de reprogramación de velocidad, escenario de movimiento del jugador y clarificación de alcance por responsabilidades.

> Revisá y corregí specs/001-terreno-cazador/spec.md usando el
> enunciado oficial y la constitución. Conservá los identificadores
> FR y SC existentes y aplicá los siguientes ajustes.
> 
> 1. Corregí FR-002. El movimiento utiliza:
>    max(1, costo_salida * 100 // velocidad).
> 
>    Las demás acciones conservan sus costos vigentes de P1:
>    atacar y esperar 100, usar/equipar 50, recoger/soltar 25
>    y abrir puertas 50.
> 
>    Revisá esos valores contra el proyecto y el enunciado.
>    Agregá un escenario que compruebe que introducir costos
>    de terreno conserva los costos de las demás acciones.
> 
> 2. Corregí SC-004 para reflejar el límite de 20 ms por ciclo
>    entre decisiones del jugador, medido en el equipo local,
>    sin red ni renderizado y con decenas de cazadores activos
>    en la cripta de referencia.
> 
>    La evaluación debe permitir detectar ciclos que excedan
>    el límite. La media por sí sola es insuficiente.
>    La metodología de medición se detallará en plan.md.
> 
> 3. Reformulá SC-005 para exigir la comparación entre cálculo
>    individual y compartido con distintos números de cazadores
>    y rangos. La elección final y las condiciones donde conviene
>    cada alternativa deben justificarse mediante resultados reales.
> 
> 4. Reformulá SC-006 para exigir la comparación de reutilización
>    frente a recálculo en escenarios de puertas estables e
>    inestables, comprobando siempre equivalencia observable.
>    La mejora de rendimiento queda sujeta a medición.
> 
> 5. Reformulá SC-002 como propiedad observable de rendimiento.
>    Para un cazador de rango pequeño, el trabajo de búsqueda
>    debe depender de la región pertinente dentro de su alcance.
>    El plan definirá cómo cumplirlo y medirlo, incluyendo el
>    caso de cálculos compartidos con rangos diferentes.
> 
> 6. Eliminá la ambigüedad de “ID alfanumérico/numérico”.
>    Usá el orden de los identificadores definido por el contrato
>    de datos del proyecto. Si el contrato deja una duda real,
>    señalala para aclaración.
> 
> 7. Revisá las frases sobre “llegar al destino” o “completar el
>    movimiento”. Conservá la semántica temporal de la primera
>    parte y especificá cómo el costo determina el intervalo
>    hasta la siguiente actuación del actor.
> 
> 8. Concretá el escenario de cambio de velocidad.
>    Una acción de costo 300 iniciada en t=0 con velocidad 100
>    tiene su siguiente evento en t=300. Si en t=100 cambia a
>    velocidad 50, el tiempo restante pasa de 200 a 400 y el
>    evento queda programado para t=500.
>    Contrastá el ejemplo con la regla vigente de P1.
> 
> 9. Agregá un escenario explícito de movimiento del jugador
>    entre turnos del cazador, vinculado a FR-008.
>    La nueva decisión debe dirigirse a su posición actual y
>    coincidir con recalcular desde cero.
> 
> 10. Ajustá la aclaración de alcance.
>     Mariano es responsable de las reglas del motor para 001,
>     sus pruebas, benchmarks, integración de mediciones y
>     documentación. La presentación visual corresponde al
>     reparto acordado con Axel y Kim.
>     Expresá esto en términos de responsabilidades y dejá
>     las rutas de archivos y decisiones técnicas para el plan.
> 
> Mostrame los cambios y cualquier ambigüedad pendiente.
> Registrá este prompt textual en PROMPTS_LLM.md.



#### 23. Planificación, investigación, modelo de datos y tareas de 001-terreno-cazador — 07/11/2026

- **Integrante**: Mariano
- **Fecha**: 07/11/2026
- **Herramienta**: Google Antigravity (IDE v2.0)
- **Modelo**: Gemini 3.8 Flash / Claude Opus 4.6
- **Uso de la respuesta**: Generar los artefactos de la fase de planificación de spec-kit (plan.md, esearch.md, data-model.md, 	asks.md) y el reporte de análisis de consistencia para la capacidad 001 (terreno, cazador e invalidación de rutas), estructurados en cuatro bloques técnicos (costos de movimiento, contrato C2 de puertas, contrato C3 del cazador e invalidación/benchmarking) bajo las restricciones de la constitución.

> Continuemos con la planificación de mi capacidad
> 001-terreno-cazador.
> 
> Leé la constitución, la especificación actual, el enunciado
> oficial y el código existente del motor.
> 
> Primero aplicá tres ajustes puntuales al spec.md:
> 
> 1. En el caso borde del jugador moviéndose hacia el cazador,
>    indicá que si ambos comparten sala al comenzar el turno
>    del cazador, este ataca, independientemente del orden
>    de los movimientos anteriores.
> 
> 2. En SC-004, exigí registrar el máximo observado y la cantidad
>    de ciclos que exceden 20 ms. Los percentiles serán
>    información complementaria.
> 
> 3. Presentá las mediciones como criterios que requieren
>    validación empírica. El límite de rendimiento es un
>    requisito y la ventaja de las optimizaciones debe medirse.
> 
> Después, ejecutá las fases de planificación, tareas y análisis
> de spec-kit disponibles en esta instalación.
> 
> Prepará plan.md, research.md, data-model.md y tasks.md.
> La implementación quedará para la siguiente etapa, después
> de confirmar la especificación y el plan en Git.
> 
> Usá estas condiciones para el plan:
> 
> - Trabajaremos sobre el proyecto actual, conservando MVC
>   y las convenciones de sus pruebas.
> - Usaremos Python 3.13, arreglos y estructuras propias.
>   No usaremos tablas hash ni dependencias nuevas.
> - Inspeccioná los llamadores antes de cambiar firmas.
>   Los datos anteriores sin costo deben seguir usando 100.
> - Cada tarea debe citar sus FR y especificar cómo se verifica.
> 
> Organizá el trabajo en estos bloques:
> 
> BLOQUE 1. COSTOS DE MOVIMIENTO
> 
> Revisá sala.py, mapa.py, costos.py, partida.py,
> comportamiento.py, motor_enemigos.py y agenda_eventos.py.
> 
> Planificá:
> - Incorporar y validar costo en las salidas compartidas.
> - Mantener compatibilidad con los argumentos existentes.
> - Usar el costo de la salida para el jugador.
> - Hacer que la resolución del turno enemigo comunique el
>   costo base de la acción realmente ejecutada.
> - Programar el siguiente turno con ese costo.
> - Conservar las elecciones de errantes y rastreadores.
> - Reutilizar la fórmula de cambio de velocidad vigente.
> 
> Primero deben escribirse pruebas de FR-001 y FR-002,
> incluyendo costos predeterminados, simetría, intervalo
> mínimo, acciones sin movimiento y reprogramación a t=500.
> 
> BLOQUE 2. PUERTAS Y CONTRATO C2
> 
> Revisá apertura, cierre automático y retroceso.
> Definí un punto común de modificación y los avisos que
> requieren rutas, conocimiento e historia.
> Explicá cómo evitar avisos o registros duplicados durante
> el retroceso y qué acuerdos requieren Kim y Axel.
> 
> BLOQUE 3. CAZADOR Y CONTRATO C3
> 
> Revisá qué búsqueda de rutas está disponible.
> Kim es responsable del montículo y la búsqueda compartida.
> Documentá la interfaz necesaria y las dependencias pendientes.
> 
> Compará búsqueda individual acotada y cálculo compartido
> desde el jugador. Explicá el desempate por la primera
> vecina de menor ID y el uso de índices de sala para arreglos.
> Considerá cómo evitar reiniciar arreglos del tamaño de
> toda la cripta en cada búsqueda.
> 
> BLOQUE 4. INVALIDACIÓN Y MEDICIONES
> 
> Justificá qué cambios invalidan las distancias y cuáles
> permiten reutilizarlas. Incluí apertura de rutas antes
> inaccesibles y restauración mediante pergamino.
> 
> Planificá comparar decisiones con recálculo desde cero,
> medir puertas estables e inestables, probar distintos
> rangos y cantidades de cazadores y repetir bench_motor.
> 
> Al terminar, mostrame:
> - Los archivos que cambiará cada bloque.
> - Las tareas que puedo empezar sin depender de compañeros.
> - Los acuerdos pendientes con Kim, Jeferson y Axel.
> - Las inconsistencias encontradas por el análisis.



#### 24. Ajustes a plan y tareas, análisis spec-kit e implementación de costos (T001-T010) — 07/11/2026

- **Integrante**: Mariano
- **Fecha**: 07/11/2026
- **Herramienta**: Google Antigravity (IDE v2.0)
- **Modelo**: Gemini 3.8 Flash / Claude Opus 4.6
- **Uso de la respuesta**: Ajustar plan.md y tasks.md con 10 precisiones técnicas (validación estricta de costo, normalización con tildes, rango en enemigo, retroceso con deshacer_ultimo, rango activo vs utilizado, integración en main.py y pruebas test-first antes de implementación), ejecutar análisis de consistencia, y tras verificar el historial de Git, proceder a la implementación test-first de las tareas T001 a T010 del Bloque 1 de costos de movimiento.

> Revisá plan.md y tasks.md de 001-terreno-cazador y aplicá
> estos ajustes conservando los identificadores existentes:
> 
> 1. Quitá [P] de T001–T005 porque modifican el mismo archivo.
> 2. Definí costo como entero positivo, rechazando booleanos,
>    decimales, cadenas, cero y negativos. La omisión vale 100.
> 3. Corregí la normalización de comportamiento para contemplar
>    mayúsculas, espacios y tildes.
> 4. Agregá una tarea para incorporar rango en Enemigo y cargarlo
>    desde la ficha, coordinada con C5 y compatible con los
>    enemigos anteriores. Identificá los caminos de guardado
>    y carga que deban revisarse con Kim.
> 5. Adaptá el diseño de retroceso a deshacer_ultimo() y a los
>    inversos reales del proyecto. Documentá la coordinación
>    con conocimiento e historia y la invalidación de rutas.
> 6. Incluí el aumento del rango requerido entre las condiciones
>    de invalidación. Diferenciá rango activo y rango utilizado
>    al calcular las distancias guardadas.
> 7. Agregá la integración de --bench cazador en main.py y la
>    documentación de mi revisión de §5.6.
> 8. Colocá las pruebas de puertas e invalidación antes de sus
>    implementaciones. Agregá FR-008 a T022.
> 9. Contrastá las afirmaciones de acuerdos y commits con
>    evidencia disponible. Marcá lo pendiente como pendiente.
> 10. Distinguí mediciones sintéticas y validación posterior
>     sobre la cripta de referencia.
> 
> Ejecutá el análisis de consistencia de spec-kit.
> 
> Verificá el historial de Git antes de implementar.
> Si falta confirmar la especificación o el plan y las tareas,
> mostrame los comandos con rutas explícitas para que yo haga
> esos commits en orden y detenete en ese punto.
> 
> Si ambos hitos ya están confirmados, implementá únicamente
> T001–T010, correspondientes al bloque de costos.
> 
> Primero escribí las pruebas, ejecutalas y comprobá que los
> fallos corresponden al comportamiento pendiente. Después
> implementá los cambios mínimos necesarios.
> 
> Condiciones del bloque:
> 
> - Agregá costo al final de las firmas existentes de Salida
>   y Sala.conectar para conservar los argumentos posicionales.
> - Verificá la carga de costos mediante Mapa, además de la
>   construcción directa de salidas.
> - Asigná índices contiguos y estables desde el esqueleto.
> - El jugador usa salida.costo.
> - resolver_turno devuelve el costo de la acción ejecutada
>   en todas sus rutas de ejecución.
> - El siguiente turno enemigo usa ese costo y su velocidad.
> - Errantes y rastreadores conservan su elección de movimiento.
> - Reutilizá la reprogramación de velocidad existente.
> - Probá el costo mediante movimientos reales y la agenda.
>   Incluí al jugador y a los enemigos, además de la fórmula.
> - Verificá que las acciones restantes conservan sus costos.
> 
> Ejecutá:
> python -m tests.test_terreno_cazador
> python -m tests.test_motor_base
> python -m tests.test_partida
> 
> Al terminar, mostrámelos resultados reales, las tareas
> completadas, los archivos modificados y cualquier pendiente.
> Entregame el contenido completo de los archivos modificados
> para copiar y pegar.


#### 25. Inspección e implementación de puertas, avisos y retroceso (Bloque 2, T011-T014) — 07/11/2026

- **Integrante**: Mariano
- **Fecha**: 07/11/2026
- **Herramienta**: Google Antigravity (IDE v2.0)
- **Modelo**: Gemini 3.8 Flash / Claude Opus 4.6
- **Uso de la respuesta**: Inspeccionar los mecanismos existentes de mutación de puertas (`abrir`, `programar_cierre`), reversión con `Registro.deshacer_ultimo` y uso de pergaminos; redactar pruebas test-first para FR-008 e implementar el punto único de cambio de estado de puertas (`cambiar_estado_puerta`) con despachador desacoplado de eventos (Contrato C2 con C1 de Axel) y tratamiento reactivo de invalidación de rutas al concluir el retroceso temporal.

> Continuemos con el Bloque 2 de la capacidad 001.
> 
> Primero verificá el cierre del Bloque 1:
> 
> - Contrastá T001–T010 con el tasks.md actual y corregí cualquier
>   diferencia entre sus identificadores y el resumen de trabajo.
> - Comprobá que PROMPTS_LLM.md conserve los prompts completos,
>   incluyendo las instrucciones de commit cuando fueron enviadas.
> - Corregí la referencia a C4: corresponde a comentarios del log.
>   Para puertas y retroceso, coordinamos C2 con C1 de Axel.
> - Verificá en Git los commits de especificación, planificación
>   y Bloque 1. Si alguno sigue pendiente, mostrame los comandos
>   correspondientes y esperá a que yo los ejecute.
> 
> Con los hitos anteriores confirmados, implementá el Bloque 2
> siguiendo las tareas actuales y manteniendo sus identificadores.
> 
> Antes de programar, inspeccioná:
> - Partida.cambiar y Partida.abrir.
> - El cierre automático en efectos.py.
> - Registro.cambiar y deshacer_ultimo.
> - El uso del pergamino.
> - Los puntos de integración ya existentes de Kim y Axel.
> 
> Escribí primero pruebas vinculadas a FR-008 que comprueben:
> 
> 1. Apertura y cierre automático pasan por el mismo método.
> 2. Cada cambio efectivo emite un único aviso.
> 3. Solicitar el estado que ya tiene la puerta no genera
>    un cambio ni un aviso adicional.
> 4. El pergamino restaura la puerta y los eventos de cierre
>    conforme al comportamiento existente.
> 5. Tras el retroceso se comunica la necesidad de descartar
>    los cálculos de rutas anteriores.
> 6. La restauración no genera nuevos registros de acciones
>    ni duplica los cambios del historial.
> 
> Implementá cambiar_estado_puerta(salida, nuevo_estado)
> reutilizando el registro de cambios existente.
> 
> Definí un contrato sencillo para los avisos, compatible con
> los componentes que ya existan. Las pruebas pueden utilizar
> receptores de prueba para observarlos.
> 
> Diferenciá explícitamente:
> - Restauración del estado del juego y conocimiento.
> - Recorte o restauración de la línea de tiempo.
> - Invalidación de datos derivados de búsqueda de rutas.
> 
> Invalidar rutas al terminar el retroceso no sustituye la
> restauración del conocimiento ni el tratamiento de la historia.
> Evitá invocar atributos de una caché que todavía no exista.
> 
> Conservá las reglas de llaves, costo de apertura, cierres
> automáticos y consumo de pergaminos.
> 
> Ejecutá:
> python -m tests.test_terreno_cazador
> python -m tests.test_motor_base
> python -m tests.test_partida
> 
> Revisá además las pruebas existentes de replay y persistencia
> que ejerciten los caminos modificados.
> 
> Al finalizar, entregame los archivos completos modificados,
> los resultados reales de las pruebas, las tareas completadas
> y los acuerdos pendientes con Kim y Axel.

---

## 4. Inventario, retroceso, replay, controlador y vista — Axel

| | |
|---|---|
| **Integrante** | Axel |
| **Apartados** | Inventario (§4.5), pergaminos e historial reversible (§4.6), bitácora de partida y replay (§4.11), controlador y vista de consola (MVC, §6 y §10.2), tabla de puntajes (§2.12), y sus pruebas, benchmarks y documentación |
| **Herramienta** | Claude (Anthropic), en todas las entradas |
| **Tipo de registro** | Bitácora de prompts |

#### 1. Responsabilidades y estado de mi parte

> Estoy en el proyecto CRIPTA de Estructuras de Datos II y mi rol es Axel. Te adjunto el enunciado, el reparto y el proyecto. Dime qué me toca a mí y en qué estado está cada cosa (no iniciado, incompleto, falta probar, probado o bloqueado por el equipo). Todavía no me des código; dime de qué depende cada pendiente y cuál sería el siguiente paso.

**Uso:** Ordenar mis pendientes e identificar qué dependía de Mariano (motor y agenda) y de los demás.

#### 2. Plan de trabajo

> Con eso, ayúdame a armar un plan de pasos que pueda hacer yo: qué tengo que lograr en cada uno, qué conceptos necesito, qué archivos reviso, qué depende de mis compañeros y cómo sé que terminé. Sin código.

**Uso:** Definir el orden: inventario, historial, bitácora y replay, puntajes, controlador y, por último, benchmarks y documentación.

#### 3. Diseño del inventario (§4.5)

> Quiero diseñar el inventario yo. Tiene que recorrerse hacia adelante y hacia atrás, soltar el objeto que estoy viendo sin que el costo dependa de la posición, mandar al frente lo que se equipa, mostrar vistas ordenadas por peso, valor o nombre sin cambiar el orden real y respetar la capacidad. Compárame el arreglo, la pila y la lista doblemente enlazada con cursor según lo que cuesta cada operación real, sin usar `dict` ni `sorted()`. Dame pasos o pseudocódigo, no la implementación, y qué pruebas preparar antes de programar.

**Uso:** Comparar arreglo, pila y lista doblemente enlazada con cursor. Elegimos la lista doble con cursor porque soltar y equipar no dependen de la posición.

#### 4. Revisión del inventario

> Te paso mi inventario y la lista doble. Revísalo contra §4.5 sin reescribirlo: dime qué falla, con un ejemplo que lo reproduzca. Revisa el cursor, soltar el objeto visto, equipar sin perder ni duplicar objetos, la capacidad, la vista ordenada y los casos con inventario vacío o de un objeto.

**Uso:** Corregir casos borde del cursor al soltar el último objeto y armar las pruebas de `test_inventario`.

#### 5. Diseño del historial reversible (§4.6, §2.11)

> Tengo que hacer el historial del pergamino sin copiar todo el estado. Explícame con ejemplos pequeños qué hay que guardar para deshacer un ataque, un movimiento, recoger o soltar, un cambio de vida, una puerta o un evento de la agenda. Cómo encaja el máximo de 5 acciones, el descarte de la más vieja y que el pergamino usado no vuelva. Qué tengo que acordar con Mariano. Sin implementación todavía.

**Uso:** Definir el contrato con el motor: todo cambio pasa por un punto único que anota cómo deshacerse, y los cambios se agrupan por acción del jugador.

#### 6. Revisión del retroceso y casos límite

> Este es mi registro de inversos y la pila de 5. Revísalo contra §4.6 y §2.11 sin reemplazarlo: que incluya lo que pasa hasta la siguiente decisión del jugador, que no devuelva pergaminos, que usarlo no cuente como acción ni avance el reloj y que no toque la caché. Dame escenarios concretos que lo rompan y qué pruebas me faltan.

**Uso:** Agregar el caso de dos pergaminos seguidos, el de recoger un pergamino dentro del intervalo revertido y la restauración exacta de la posición en el inventario.

#### 7. Bitácora de partida y replay (§4.11)

> Ayúdame a planificar la bitácora y el `--replay`. Qué formato mínimo para un archivo de solo anexado, qué va en el encabezado, qué órdenes registrar y cómo reproducir sin vista. Qué hacer si la versión del log ya no está. Dime qué hace cada parte (bitácora, reproductor, controlador, modelo y adaptadores) y qué casos probar: log válido, incompleto, versión incompatible y una orden que ya no se puede ejecutar. Sin archivos completos.

**Uso:** Definir el encabezado obligatorio, el *flush* por línea y los tres caminos del reproductor: versiones iguales, copia local o "no se puede garantizar una reproducción fiel".

#### 8. Controlador y vista de consola (lógica MVC)

> Todavía no tenemos el proyecto separado en carpetas de modelo, vista y controlador, pero quiero que el controlador y la vista de consola sigan la lógica de MVC desde ya. Explícame qué le toca a cada parte, ayúdame a definir un contrato sencillo entre la vista y el controlador, y que `--replay` y `--bench` puedan correr sin la vista. Divídelo en tareas pequeñas con cómo probar cada una.

**Uso:** Separar responsabilidades aunque los archivos todavía estuvieran juntos: la vista solo lee la partida y devuelve órdenes (`Orden`), el controlador las ejecuta y el modelo no sabe de la consola. Esa separación facilitó después pasar a carpetas MVC cuando se agregó la interfaz gráfica.

#### 9. Tabla de puntajes (§2.12)

> Ayúdame a diseñar la tabla de puntajes. Qué campos pide el enunciado y cómo conectarla al final de la partida sin mezclarla con la vista ni con el modelo. Si el criterio de orden no está en el enunciado, dame alternativas para decidirlo nosotros. Qué errores manejar y qué probar: líneas dañadas, archivo vacío y derrotas.

**Uso:** Guardar una línea por partida y ordenar con nuestro `ordenar()`: primero victorias, luego menor tiempo y menos acciones (decisión del grupo, no del enunciado).

#### 10. Depuración guiada

> Esta prueba me falla: [pego la salida]. Antes de cambiar nada, dime qué demuestra el error, cuál es la causa más probable y cómo comprobarla con el cambio más chico posible. Puede venir de mi archivo o de la integración con el motor.

**Uso:** Encontrar errores de integración entre el inventario, el historial y el motor.

#### 11. Benchmarks de mi parte (§5.3)

> Ayúdame a planificar los benchmarks del inventario y del historial para `--bench`. Qué medir, con qué tamaños, cuántas repeticiones y cómo comparar con la alternativa descartada sin sacar conclusiones engañosas. No inventes resultados; después reviso contigo el que yo haga.

**Uso:** Medir la lista doble contra arreglo y pila en el inventario, y el registro de inversos contra copia completa en el historial.

#### 12. Documento de Decisiones de Diseño

> Ayúdame a redactar mis secciones del Documento de Decisiones (§4.5, §4.6 y §4.11) con los seis puntos de §8, usando mi código y mis resultados reales de `--bench`. No inventes mediciones; si falta evidencia, dime cómo conseguirla.

**Uso:** Estructurar mis secciones con los datos de `bench_inventario` y `bench_historial`.

#### 13. Revisión de integración con el equipo

> Te adjunto la versión más reciente. Revisa solo los puntos de integración de mi parte: que el inventario cumpla el contrato del jugador y del modelo, que el historial revierta cambios del motor, que el controlador siga la lógica MVC, que el replay funcione sin vista y que los puntajes se guarden al terminar. Dame un informe con errores, riesgos y acuerdos pendientes, y espera a que yo elija qué corregir.

**Uso:** Detectar diferencias de nombres e interfaces entre mis archivos y los de mis compañeros antes de integrar.

#### 14. Cierre y preparación de la defensa

> Ayúdame a comprobar si mi parte está lista: una lista de verificación para inventario, historial, replay, controlador y puntajes, marcando qué está demostrado y qué no. Después hazme preguntas de defensa una por una y espera mi respuesta antes de explicarme.

**Uso:** Practicar la defensa de mis decisiones y revisar qué faltaba demostrar.

---

## 5. Recursos visuales, sonido y repeticiones — Jeferson

| | |
|---|---|
| **Integrante** | Jeferson |
| **Alcance** | Imágenes y sprites, efectos de sonido y música, corrección de errores de la vista y menú de repeticiones |
| **Tipo de registro** | Banco de prompts de guía |

**Modo de uso**

1. Pegar primero el *prompt base* al iniciar la conversación con el LLM.
2. Adjuntar siempre el enunciado o guía del trabajo y, si aplica, el fragmento de código correspondiente.
3. Elegir el prompt de la lista según lo que se necesite y reemplazar lo que está entre `[corchetes]`.
4. Si el LLM entrega código completo, pedirle que lo reformule como pistas o pseudocódigo.

### Prompt base

> Actúa como tutor de programación. Voy a escribir yo el código. Te adjunto la guía/enunciado del trabajo. Tu papel es:
> - Explicarme qué pide el enunciado y qué conceptos necesito.
> - Proponerme un plan por pasos y ayudarme a decidir entre alternativas.
> - Darme pistas, pseudocódigo o fragmentos mínimos de ejemplo, NO la solución completa.
> - Revisar el código que yo te comparta y señalarme errores o incumplimientos del enunciado, explicando por qué.
> - Preguntarme cuando falte información en lugar de asumir.
>
> Cita siempre el apartado del enunciado en el que te basas.

### A. Imágenes, sprites y recursos visuales

#### 1. Icono del antídoto

> Necesito un icono para [objeto del juego]. Ayúdame a redactar un buen prompt para una herramienta de imágenes: ¿qué elementos (estilo, fondo, tamaño, formato) debo especificar para que encaje con el resto del juego? Explícame cómo integrarlo después en mi código.

#### 10–11. Piso y fondo de sala

> Tengo [sala/pantalla] y quiero una imagen de piso que se vea bien acomodada. Guíame sobre qué proporciones, vista (cenital o isométrica) y resolución me conviene pedir, y cómo cargarla y escalarla en [lenguaje/librería].

#### 12–13. Puertas y maqueta de sala

> Explícame cómo planificar la distribución de las puertas en la sala antes de dibujarlas: posiciones, tamaños y cómo se relacionan con el código de la vista. Ayúdame a armar el prompt de imagen con esos datos.

#### 15–16. Animación de puertas con sprites

> Quiero animar la apertura de una puerta con una tira de sprites. Explícame cómo se estructura una hoja de sprites (cuadros, tamaño, orden), qué debo pedirle al generador de imágenes y cómo recortar y reproducir los cuadros en mi código paso a paso.

#### 21–22. Cuadros que faltan en la animación de correr

> Mi personaje se ve con los pies congelados al correr sin [objeto], pero bien con [objeto]. Ayúdame a diagnosticar si faltan imágenes o si la lógica de selección de sprites está mal. Si faltan, guíame sobre qué prompt escribir y cómo recortarlas al mismo tamaño que las demás.

#### 27. Mano libre en sprites con espada

> Ayúdame a redactar un prompt de imagen para que, en los sprites con [espada] y sin [antorcha], la mano libre no parezca sostener nada. Dame los puntos clave a especificar (pose, mano abierta, consistencia con otros cuadros).

#### 28. Ataque con espada fiel al estilo

> Mi animación de ataque no coincide con el estilo de las demás. Dime qué criterios debo comparar (paleta, grosor de línea, proporciones, ángulo) y cómo estructurar el prompt para que sea consistente.

#### 29. Recortar y nombrar tiras nuevas

> Tengo una tira de sprites nueva. Explícame cómo recortarla en cuadros del mismo tamaño que los existentes, qué convención de nombres seguir y cómo reemplazarlos en la carpeta sin romper la carga en el código.

### B. Sonido y audio

#### 3. Integrar efectos de sonido

> Quiero agregar efectos de sonido a todo el juego respetando [arquitectura, por ejemplo MVC]. Explícame en qué capa debe vivir el sonido, cómo organizar un gestor de audio y en qué eventos conviene dispararlos. Respuesta corta y ordenada por pasos.

#### 17. Convertir y recortar audios

> Explícame cómo convertir audios a [formato, por ejemplo OGG] y recortarlos para que coincidan con la acción exacta (por ejemplo con ffmpeg o Audacity). Ayúdame también a definir la regla de cuándo debe sonar cada efecto (por ejemplo, la puerta solo suena si se usa una llave) y dónde ponerla en el código.

#### 18. Quitar un sonido molesto y añadir música

> Algunos sonidos se superponen y molestan. Guíame sobre cómo decidir qué efectos mantener, cómo manejar la música de fondo en menús y niveles, y cómo sincronizar la velocidad de una animación con su audio.

#### 26.1. Cambiar el sonido de muerte de un enemigo

> Un enemigo usa el mismo sonido de muerte que otro. Explícame cómo asociar sonidos por tipo de enemigo y cómo ajustar el audio para que coincida con la animación. Dime qué funciones debo revisar, sin escribirlas por mí.

### C. Corrección de errores y comportamiento

#### 2. Fondo solo en menú y selección de nivel

> Mi implementación aplicó fondo en todas las salas cuando solo debía ir en [menú de nombre] y en la selección de nivel (elegido al azar entre varias imágenes). Ayúdame a razonar qué parte de la vista decide qué fondo se dibuja y cómo separar los casos.

#### 6. Nombre con tilde en la API

> La API devuelve "guardián" con tilde y mis comparaciones fallan para elegir la imagen. Explícame cómo normalizar cadenas (tildes, mayúsculas) solo para la comparación, sin alterar el dato original del modelo.

#### 7. Mostrar enemigos como "#N" sin el id completo

> Quiero que el mensaje diga "[enemigo] te ataca..." mostrando solo "#N" y no el id completo, sin cambiar el Modelo ni el log. Guíame sobre en qué capa conviene formatear el texto y qué funciones debo modificar.

#### 19–20. Velocidad de carrera inconsistente

> Al correr hacia una puerta con llave la velocidad es distinta a la de las otras salas. Ayúdame a depurar: explícame la diferencia entre duración fija y velocidad constante, cómo calcular el tiempo según la distancia y qué parte de mi código lo controla. Te comparto el video/código para que lo analicemos.

#### 23. Ejecutar sin comando extra

> Hoy debo ejecutar un comando cada vez para correr el juego. Explícame cómo configurar el punto de entrada para que baste con el botón Run, y revisa en el enunciado si acepta ejecución por consola o gráfica.

#### 25. Lectura robusta de datos para criptas nuevas

> Mi código falla al leer [dato, por ejemplo veneno] en criptas nuevas, pero los dardos funcionan bien. Ayúdame a entender la causa del error, a redactar una explicación clara para mi equipo y a decidir cómo validar el dato sin romper lo que ya funciona.

#### 26.2. Nombre incorrecto debajo de un enemigo

> Debajo de [enemigo] aparece el nombre de otro. Explícame dónde se arma ese texto, qué relación tiene con la caché del catálogo y cómo comprobar de dónde sale el dato.

#### 26.3. Efecto de la poción de velocidad

> Pregunta corta: ¿cómo debo interpretar en el enunciado el efecto de la poción de velocidad? Indícame el apartado y qué consecuencias tiene para el código.

### D. Requisitos, revisión y entrega

#### 4. Revisar el requisito de replay

> El proyecto menciona un botón de replay. Léelo en el enunciado, dime qué exige exactamente y revisa si mi proyecto lo cumple. Explícame las opciones de diseño para cumplirlo y sus ventajas.

#### 5. Límite de repeticiones y logs

> Mis repeticiones se acumulan sin límite. Antes de darme código, explícame las opciones para limitar a las últimas [10/20] partidas y qué trade-offs tiene cada una. También ayúdame a entender por qué [enemigo] no tiene imagen.

#### 8. Menú de repeticiones

> Quiero ver la repetición al ganar/perder o desde la selección de nivel, mostrando fecha y hora de cada partida y un máximo de [20] guardadas. Guíame paso a paso: estructura de datos, cómo guardar la fecha, cómo reproducir y cómo probarlo.

#### 9. Revisión punto por punto

> Adjunto mi versión actual y el enunciado. Revisa punto por punto qué requisitos cumplo, cuáles faltan y por qué, y dime qué entregables pendientes hay (README, Documento de Decisiones, bitácora de prompts).

#### 14. Integrar un cambio en la vista

> Ya tengo [recurso]. Explícame qué partes de la vista debo modificar para integrarlo y cómo nombrar el archivo, y revisa mi código cuando lo tenga.

#### 24. Lista de verificación para probar a mano

> Extrae del enunciado todos los requisitos de funcionamiento del juego, en orden. Para cada uno: cita textual del enunciado, explicación en palabras sencillas y una forma concreta de verificarlo a mano.

### Prompts generales reutilizables

> Léeme el apartado [X] del enunciado y explícame con tus palabras qué debo implementar.

> Antes de darme código, dime las opciones de diseño y sus ventajas y desventajas.

> Este es mi código de [función]. ¿Qué falla y por qué? Dame solo una pista, no la corrección.

> Dame pseudocódigo de [funcionalidad] y yo lo implemento en [lenguaje].

> Revisa si mi solución respeta [MVC / restricciones del enunciado] y justifica con el apartado.

> Hazme preguntas para comprobar que entendí [concepto] antes de continuar.
