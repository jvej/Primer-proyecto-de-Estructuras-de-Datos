# Documento de Decisiones de Diseño — CRIPTA

Una sección por cada problema de §4 resuelto, más las decisiones de rendimiento (§5.1, §5.2) y algunas reglas del juego con decisiones de estructura (§2.6, §2.10, §2.12). Cada sección sigue los seis puntos de §8: problema, alternativas consideradas, decisión, análisis de complejidad, evidencia empírica y límites conocidos.

**Sobre las mediciones.** Salen de los archivos `bench_*.py`, que se ejecutan con `python main.py --bench`. Las secciones de Kim (9 a 11) se midieron en su equipo, en Windows y con el repositorio dentro de OneDrive. Las demás (1, 2, 5, 7, 12 y 13) se midieron en una laptop con Intel Core i5-10310U (4 núcleos) y 15.6 GB de memoria, con Windows 11, Python 3.14.5 y fuera de OneDrive. Las de inventario (12) e historial (13) se tomaron con otros benchmarks corriendo en paralelo, así que sus tiempos pueden estar algo inflados. Los tiempos varían entre corridas y equipos, así que se cita la tendencia; los conteos (comparaciones, solicitudes de red) son exactos y repetibles.

**Entorno documentado por sección.** La atribución a Python 3.14.5 del párrafo anterior se limita a las secciones enumeradas; Python 3.13 en un plan indica la versión prevista del proyecto, no acredita la versión de una medición histórica. Se conservan todos los valores originales:

| Sección / medición | Python | Sistema operativo documentado |
|---|---|---|
| 1, 2 (corrida principal), 5, 7, 12 y 13 (corrida principal) | 3.14.5 | Windows 11 |
| 2, corrida anterior citada en 2.5 | 3.10.12 | Máquina virtual Linux de dos núcleos |
| 13, comparación anterior citada en 13.6 | 3.10; versión exacta POR CONFIRMAR | POR CONFIRMAR; no se identifica el SO de esa corrida |
| 4b | 3.13; versión exacta POR CONFIRMAR | Windows 11 |
| 4c | POR CONFIRMAR; 4c.4 no indica versión | Windows 11 |
| 8b | POR CONFIRMAR; 8b.5 no indica versión | POR CONFIRMAR; sin entorno propio declarado |
| 8c | 3.13.18 del venv | Windows; edición/versión POR CONFIRMAR |
| 8d | POR CONFIRMAR; sin entorno propio declarado | POR CONFIRMAR; no se hereda el entorno de 8c |
| 9, 10 y 11 | POR CONFIRMAR | Windows, repositorio en OneDrive; edición/versión POR CONFIRMAR |
| 16, mediciones de Parte II, incluidas las repeticiones de historial e inventario | 3.13.9 del venv | Windows 11 Pro de 64 bits, compilación 26300 |
| 17, benchmark sintético inicial, verificación posterior y mapa dibujado de 17.7 | 3.13.18 | Windows 11; compilación 26200 en la verificación posterior y en 17.7 |

Las secciones 3, 4, 6, 8, 14 y 15 no declaran un entorno independiente de medición; no se les asigna uno por proximidad. La comparación con los planes que sigue usa sus primeras versiones disponibles en Git (001: `43b8ce1`; 003: `8ddfd70`; 002: `db75930`; 004: `a7a764f`), además de los `plan.md` actuales y el código real. Las correcciones funcionales se distinguen de cambios motivados por mediciones.

## Índice

- **Mariano** (motor del juego)
  - [1. §4.1 Qué ocurre a continuación (agenda de eventos)](#1-41-qué-ocurre-a-continuación-agenda-de-eventos)
  - [2. §5.2 Ciclo completo entre dos decisiones del jugador](#2-52-ciclo-completo-entre-dos-decisiones-del-jugador)
  - [3. §4.7 El rastro del jugador](#3-47-el-rastro-del-jugador)
  - [4. Efectos temporales y combate determinista (§2.6, §2.10)](#4-efectos-temporales-y-combate-determinista-26-210)
  - [4b. Revisión de §5.6: Motor con cazadores, costos de terreno y eventos empatados](#4b-revisión-de-56-motor-con-cazadores-costos-de-terreno-y-eventos-empatados)
  - [4c. Capacidad 001: Terreno, Cazador e Invalidación Reactiva de Rutas (§5.1, §5.2, SC-004..SC-006)](#4c-capacidad-001-terreno-cazador-e-invalidación-reactiva-de-rutas-51-52-sc-004sc-006)
- **Jeferson** (red, precarga, catálogo y bitácora en pantalla)
  - [5. §4.2 Traer el contenido antes de que haga falta](#5-42-traer-el-contenido-antes-de-que-haga-falta)
  - [6. §4.3 Resolución de referencias del catálogo](#6-43-resolución-de-referencias-del-catálogo)
  - [7. §4.8 Bitácora en pantalla](#7-48-bitácora-en-pantalla)
  - [8. §5.1 Presupuesto de red](#8-51-presupuesto-de-red)
  - [8b. Parte II — Servicio web, datos nuevos y contrato C5 (003)](#8b-parte-ii--servicio-web-datos-nuevos-y-contrato-c5-003-fr-001fr-008)
  - [8c. Parte II — §5.4 Verificación de resolubilidad (003)](#8c-parte-ii--54-verificación-de-resolubilidad-003-fr-009fr-018-sc-001sc-005)
  - [8d. Parte II — §5.6 Revisión de la red con los datos nuevos](#8d-parte-ii--56-revisión-de-la-red-con-los-datos-nuevos)
- **Kim** (caché persistente, ordenamiento, guardado y capacidad 002)
  - [9. §4.4 Reutilización y caché persistente](#9-44-reutilización-y-caché-persistente)
  - [10. §4.9 Ordenamiento](#10-49-ordenamiento)
  - [11. §4.10 Guardado binario de la partida](#11-410-guardado-binario-de-la-partida)
  - [17. Niebla de guerra e IR_A (002, Parte II)](#17-niebla-de-guerra-e-ir_a-002-parte-ii)
- **Axel** (inventario, retroceso, replay y puntajes)
  - [12. §4.5 Inventario](#12-45-inventario)
  - [13. §4.6 Pergaminos de retroceso e historial reversible](#13-46-pergaminos-de-retroceso-e-historial-reversible)
  - [14. §4.11 Bitácora de partida y reproducción](#14-411-bitácora-de-partida-y-reproducción)
  - [15. Tabla de puntajes (§2.12)](#15-tabla-de-puntajes-212)
  - [16. Línea de tiempo (004, Parte II)](#16-línea-de-tiempo-004-parte-ii)

---

# Parte de Mariano — Motor del juego

## 1. §4.1 Qué ocurre a continuación (agenda de eventos)

### 1.1 Problema

El juego no tiene rondas: avanza con un reloj virtual y una agenda de eventos (turnos del jugador y de los enemigos, pulsos de veneno, regeneración, fin de efectos de velocidad, apagado de antorcha, rearme de trampas, cierre de puertas). En cada paso del bucle hay que:

1. Sacar el evento pendiente con menor `tiempo_siguiente` y, si empatan, menor número de secuencia. Es la operación más frecuente: decenas de miles de veces por partida, con cientos de eventos pendientes.
2. Agendar el siguiente evento del actor que acaba de actuar. Ocurre casi siempre junto con la anterior.
3. Cancelar eventos: cuando un actor muere, cuando un antídoto corta el veneno o cuando una puerta ya no debe cerrarse.
4. Reprogramar una acción ya agendada cuando cambia la velocidad (§2.3), con número de secuencia nuevo.
5. Mantener un orden total y determinista aun con cancelaciones, reprogramaciones y empates.

Además, la agenda tiene que poder deshacerse con el pergamino (§4.6).

### 1.2 Alternativas consideradas

- **Lista sin orden.** Agendar es O(1), pero sacar el mínimo obliga a recorrer todo: O(n). §4.1 lo prohíbe ("no puede requerir examinar todos los eventos"). Se midió.
- **Lista ordenada** (de mayor a menor, el mínimo sale por el final). Sacar es O(1), pero agendar es O(n) por el desplazamiento. Se midió.
- **Heap binario (montículo de mínimos).** Es el elegido.

**Para cancelar**

- **Buscar el evento en la agenda y sacarlo.** O(n) por cada cancelación, y en un heap además hay que reacomodar.
- **Cancelación perezosa:** marcar el evento como inválido y descartarlo cuando llegue a la cima. Es la elegida.

### 1.3 Decisión

- `AgendaEventos` (`agenda_eventos.py`): un **heap binario propio** sobre una `list` (sin `heapq`, que es una implementación de biblioteca). `_subir` y `_bajar` mantienen la propiedad del heap.
- **Orden:** `Evento.__lt__` compara primero `tiempo_siguiente` y después `secuencia`. `nueva_secuencia()` entrega números que solo crecen y nunca se reutilizan, así que el orden es total y no depende de la hora del sistema ni del orden de llegada de la red.
- **Cancelación perezosa:** `cancelar(evento)` pone `valido = False` en O(1). `siguiente()` saca de la cima y descarta los inválidos hasta encontrar uno válido.
- **Sin recorrer la agenda:** cada actor guarda referencias a sus eventos pendientes (`evento_pendiente`, `evento_veneno`, `evento_regeneracion`). Al morir, `_morir` cancela exactamente esos, sin buscarlos.
- **Cambio de velocidad:** `reprogramar_por_cambio_velocidad` calcula `restante_nuevo = max(1, restante × vel_anterior // vel_nueva)`, cancela el evento viejo y agenda uno nuevo con secuencia nueva, y actualiza la referencia del actor para que una muerte posterior lo alcance.
- **Retroceso:** agendar anota "invalidarlo"; cancelar anota "volver a validarlo"; sacar anota "volver a meterlo". Así el pergamino restaura la agenda sin copiarla.

### 1.4 Análisis de complejidad

Con n eventos en el heap (incluidos los cancelados que aún no salieron):

| Operación | Costo | Frecuencia |
|---|---|---|
| Sacar el siguiente | O(log n) | La más frecuente |
| Agendar | O(log n) | Casi siempre junto con sacar |
| Cancelar | O(1) | Muertes, antídotos, cambios de velocidad |
| Reprogramar por velocidad | O(log n) (cancelar + agendar) | Al empezar y terminar un efecto de velocidad |
| Descartar un cancelado | O(log n), una sola vez | Cuando llega a la cima |
| Alternativa lista sin orden: sacar | O(n) | — |
| Alternativa lista ordenada: agendar | O(n) | — |

### 1.5 Evidencia empírica

`bench_motor.py`. Carga que imita al juego: cada actor tiene un evento pendiente y, al ejecutarlo, agenda el siguiente entre 50 y 150 unidades después. 20 000 pasos de "sacar el siguiente y agendar su sucesor", en milisegundos totales:

| Pendientes | Heap (elegido) | Lista ordenada | Lista sin orden |
|---|---|---|---|
| 100 | 155.4 | **70.5** | 616.3 |
| 300 | 169.6 | **72.6** | 2277.9 |
| 1000 | 665.1 | **395.4** | 12206.7 |
| 3000 | **325.4** | 388.7 | 21350.3 |
| 10000 | 304.0 | **211.1** | — |
| 30000 | **311.2** | 333.2 | — |

(La lista sin orden no se midió por encima de 3000 porque tardaba demasiado.)

Lectura de los resultados:

- **Lista sin orden:** descartada. Crece de forma lineal con los pendientes: con 300 ya es 13 veces más lenta que el heap y con 3000, 66 veces. Es la que prohíbe §4.1.
- **Heap:** crece poco. De 100 a 30 000 pendientes el tiempo pasa de 155 a 311 ms (×2 con 300 veces más eventos), como se espera de O(log n). La fila de 1000 tuvo ruido en esta corrida (665 ms, más que con 3000 o 10 000 pendientes).
- **Lista ordenada:** es más rápida que el heap hasta unos 10 000 pendientes (en esta corrida la fila de 3000 salió al revés, también por ruido). La causa es que su inserción es O(n), pero el desplazamiento lo hace `list.insert` en C sobre memoria contigua, mientras que nuestro heap hace sus O(log n) comparaciones en Python. A partir de unas decenas de miles de eventos la lista ordenada empieza a perder (333 contra 311 ms con 30 000) y su costo sigue creciendo.
- **Decisión a pesar de la medición:** con los tamaños del juego las dos opciones cumplen de sobra. Se eligió el heap porque su costo no depende del tamaño de la agenda y el enunciado advierte que la cripta de la revisión puede tener más actores y efectos simultáneos (§9). El punto de cruce queda anotado como límite conocido.
- **Pruebas:** `test_motor_base.py` (orden con empates y cancelaciones, fórmula de cambio de velocidad, reprogramar da secuencia nueva y actualiza al actor, deshacer la agenda con el registro) y `test_partida.py` (ejemplo de la sección 2.13 del enunciado, cancelación al morir, activación en orden de id).

### 1.6 Límites conocidos

- Hasta unas 10 000 entradas una lista ordenada sería más rápida en Python; la ventaja del heap es de escala, no de velocidad absoluta con cargas pequeñas.
- Los eventos cancelados quedan dentro del heap hasta llegar a la cima: ocupan memoria y hacen el heap más alto. Con muchas cancelaciones seguidas (muchas muertes o cambios de velocidad) n incluye esos eventos muertos. No se compacta el heap.
- Los eventos guardan funciones (lambdas), por eso la agenda no se puede escribir en un archivo: el guardado reconstruye la partida re-ejecutando las órdenes (§4.10).

---

## 2. §5.2 Ciclo completo entre dos decisiones del jugador

### 2.1 Problema

Con la cripta cargada, y sin contar red ni dibujo, resolver todo lo que pasa entre dos decisiones del jugador debe tomar menos de 20 ms.

### 2.2 Alternativas consideradas

- **Recorrer todos los actores de la cripta en cada ciclo** (estilo "por rondas"). El costo crecería con el tamaño de la cripta aunque casi nadie actúe.
- **Avanzar solo por los eventos de la agenda.** Es la elegida: el trabajo depende de cuántos eventos ocurren antes de la siguiente decisión, no de cuántos actores existen.

### 2.3 Decisión

`Partida._avanzar` saca eventos de la agenda y los ejecuta hasta que vuelve a ser el turno del jugador. Los enemigos dormidos no tienen eventos (se activan al entrar el jugador a su sala, §2.4), así que no cuestan nada. El rastreador solo mira sus salidas (§4.7).

### 2.4 Análisis de complejidad

Con e eventos ejecutados en el ciclo y n pendientes: O(e · log n), más el trabajo de cada evento (un ataque, un movimiento, un pulso), que es O(1) o O(salidas).

### 2.5 Evidencia empírica

`bench_motor.py`, 50 ciclos de "esperar", en milisegundos:

| Carga | Medio | Máximo |
|---|---|---|
| 300 eventos pendientes, ~15 actúan por ciclo | 0.35 | 10.00 |
| 300 enemigos en la misma sala atacando en cada ciclo (peor caso) | 4.79 | 14.61 |

- El caso típico queda muy por debajo de 20 ms: 0.35 ms de promedio y 10.00 ms en el peor ciclo.
- El peor caso sintético (300 enemigos atacando a la vez en cada ciclo) tiene un promedio de 4.79 ms y su ciclo más lento llegó a 14.61 ms, también por debajo del límite. Ese máximo incluye picos del sistema (recolector de basura, planificador), por eso el promedio es mucho menor. En una corrida anterior en una laptop más lenta (Intel Core i7-8665U dentro de una máquina virtual Linux de 2 núcleos, con Python 3.10.12) el mismo caso dio 8.63 ms de promedio y 25.11 ms de máximo, y **superó los 20 ms**.

### 2.6 Límites conocidos

- El costo por ciclo crece con la cantidad de actores que **actúan**, no con el tamaño de la cripta. Una sala con cientos de enemigos rápidos atacando en el mismo ciclo puede pasarse del límite en algunos ciclos en un equipo lento: con 300 enemigos atacando a la vez, el ciclo más lento tardó 14.6 ms en la laptop de prueba, pero 25 ms en la máquina virtual de la corrida anterior.
- En el peor caso, cada ataque también registra sus inversos para el retroceso (§4.6), lo que suma costo.
- Hay que repetir la medición en el equipo de la revisión.

---

## 3. §4.7 El rastro del jugador

### 3.1 Problema

Cada sala registra el último instante en que el jugador estuvo allí. Un rastreador, en su turno, mira solo las salas vecinas por salidas abiertas y va a la de rastro más fresco, si tiene menos de 400 unidades de antigüedad; en empate, a la de menor id (§2.9). La decisión debe costar según las salidas de su sala, no según el tamaño de la cripta ni lo largo del recorrido. Hay que decidir si los rastros viejos se borran activamente o se detecta su caducidad al consultarlos.

### 3.2 Alternativas consideradas

**Qué guardar**

- **El recorrido completo del jugador** (lista de salas visitadas con su tiempo). Para decidir, el rastreador tendría que buscar en esa lista, que crece durante toda la partida.
- **Un solo número por sala** (`ultimo_instante_jugador`). Es la elegida.

**Rastros viejos**

- **Borrarlos activamente** con un evento "caducar rastro" 400 unidades después de cada visita. Agrega un evento por cada movimiento del jugador, que además habría que registrar para el retroceso.
- **Detectar la caducidad al consultar.** Es la elegida.

### 3.3 Decisión

- `Sala.ultimo_instante_jugador` (`sala.py`) se actualiza con `partida.cambiar` (así lo revierte el pergamino) en cada movimiento y, según el Apéndice B, en cada acción del jugador en la sala actual. La sala inicial recibe rastro en el instante 0.
- `rastro_fresco(ahora)` devuelve `ahora − ultimo_instante < 400`.
- `_rastreador` (`comportamiento.py`) recorre solo las salidas abiertas de su sala, se queda con la vecina de rastro más reciente y, en empate exacto, con la de menor id. Si ninguna tiene rastro fresco, espera.

### 3.4 Análisis de complejidad

| Operación | Costo | Frecuencia |
|---|---|---|
| Marcar el rastro | O(1) | Cada acción del jugador |
| Consultar si es fresco | O(1) | Por cada vecina examinada |
| Decisión de un rastreador | O(salidas) ≤ 4 | Cada turno de un rastreador |
| R rastreadores actuando en un ciclo | O(R) | — |
| Alternativa con recorrido completo | O(largo del recorrido) por decisión | — |

### 3.5 Evidencia empírica

No hay un bench específico del rastro: la decisión es de costo constante por construcción (un número por sala y a lo sumo 4 vecinas). El costo de los rastreadores está incluido en el bench de ciclo de la sección 2.5.

- `test_motor_base.py`: `probar_rastro_caduca_a_las_400`.
- `test_partida.py`: `probar_rastreador_persigue_el_rastro`.
- Prueba manual: en el paquete `--offline`, la rata (rastreadora) sigue al jugador si pasa cerca y deja de seguirlo tras esperar más de 400 unidades lejos.

### 3.6 Límites conocidos

- El rastreador no conoce el mapa: si el rastro fresco está a dos salas, no lo encuentra (así lo pide §2.9).
- El rastro no se borra nunca; cada sala guarda un número aunque esté vencido. Es memoria constante por sala.
- No se midió el costo por separado; si se quisiera evidencia directa, habría que agregar un bench con muchos rastreadores.

---

## 4. Efectos temporales y combate determinista (§2.6, §2.10)

### 4.1 Problema

Los efectos (veneno, velocidad temporal, antorcha, regeneración, rearme de trampas, cierre de puertas) ocurren en el tiempo y algunos se pueden cancelar antes. El combate usa azar, y dos ejecuciones con la misma semilla y las mismas órdenes deben dar la misma partida, incluida la misma secuencia de llamadas al generador.

### 4.2 Alternativas consideradas

- **Revisar en cada ciclo todos los efectos activos** para ver si les toca. El costo crece con los efectos activos aunque ninguno ocurra.
- **Cada efecto es un evento en la misma agenda.** Es la elegida.

**Azar**

- **Usar `random` global.** Prohibido (§2.6) y no reproducible si otra parte del programa lo usa.
- **Una instancia propia `random.Random(semilla)` envuelta en `AzarReversible`.** Es la elegida.

### 4.3 Decisión

- `efectos.py`: cada efecto programa su próximo pulso o su fin en la agenda. El veneno guarda su evento en el actor para que el antídoto lo cancele en O(1); la regeneración se reprograma cada 200 unidades sin pasar de `vida_max`; la trampa programa su rearme (300 o el de su ficha); abrir una puerta con cierre automático programa el cierre.
- Todo cambio pasa por `partida.cambiar`/`programar`, así queda registrado para el retroceso.
- `combate.calcular_dano`: `max(1, ataque + azar.randint(0, 4) − defensa)`, con el azar de la partida.
- `AzarReversible` (`azar.py`) envuelve el generador y guarda su estado la primera vez que se usa en una acción, para que el pergamino restaure también las tiradas.

### 4.4 Análisis de complejidad

Un efecto activo cuesta O(log n) solo cuando le toca (sacar y reagendar su evento); cancelarlo es O(1). Un ataque es O(1).

### 4.5 Evidencia empírica

- `test_partida.py`: veneno, antídoto y regeneración; velocidad temporal; trampa y rearme; puerta con llave y cierre automático; combate, botín y cancelación al morir; **mismo resultado con la misma semilla**.
- `test_replay_puntajes.py`: el pergamino restaura también el azar; el replay reproduce exactamente la partida.
- Prueba manual con el paquete `--offline`: veneno de la aguja y antídoto, regeneración del troll, poción de velocidad y puerta que se cierra sola.

### 4.6 Límites conocidos

- Las fichas del catálogo real no traen veneno en las trampas publicadas; el nombre exacto del campo no está confirmado. La lectura (`leer_veneno`) acepta varios formatos para no fallar con una cripta nueva.
- Los comportamientos se comparan en minúscula y sin tildes solo para la imagen; en el Modelo se espera exactamente "errante" y "rastreador".
- No hay bench de efectos por separado; su costo está dentro del ciclo de la sección 2.5.


---

## 4b. Revisión de §5.6: Motor con cazadores, costos de terreno y eventos empatados

**Coincidencia con plan.md original:** Parcial. El plan 001 original (`43b8ce1`, bloques 1 y 4) ya proponía costos de terreno, conservar el heap y repetir `bench_motor` con cazadores; el código de `motor_enemigos.py` y `Partida._avanzar` conserva esas decisiones. El cierre de eventos empatados mediante `AgendaEventos.proximo_en_tiempo` y el segundo bucle de `_avanzar` amplía ese plan y figura en su bloque 5 actual. Lo motivó la coherencia funcional de historia `<t>` descrita en 4b.2, no una medición de velocidad documentada; la tabla 4b.4 evalúa el resultado y no demuestra el motivo del cambio.

### 4b.1 Problema y contexto de la Parte II
En la Parte II se introducen costos variables por salida (FR-001, FR-002), el enemigo cazador con búsqueda acotada por Dijkstra (FR-003..FR-007) y la garantía estricta de cierre del instante $t$ requerida para la integración con historia `<t>` (Axel). El objetivo es comprobar si el motor continúa resolviendo el ciclo completo entre dos decisiones del jugador en menos de 20 ms (§5.2) ante estas nuevas cargas dinámicas y empates de tiempo.

### 4b.2 Alternativas y decisiones de diseño
1. **Cierre del instante $t$**:
   - *Alternativa rechazada*: Detener el bucle en cuanto `self.esperando = True`, dejando eventos empatados pendientes en la agenda. Esto provocaba que eventos con el mismo tiempo $t$ pero secuencia mayor al turno del jugador se ejecutaran tras aceptar la siguiente acción, rompiendo la coherencia de historia `<t>`.
   - *Decisión adoptada*: Se incorporó `AgendaEventos.proximo_en_tiempo(tiempo)` y un segundo bucle en `Partida._avanzar()`: mientras la partida continúe en `"jugando"` y esperando al jugador, se extraen y ejecutan todos los eventos válidos con `tiempo_siguiente == self.reloj.tiempo_actual`. Si la raíz del heap tiene un tiempo estrictamente mayor, la función retorna `None` en $O(1)$ sin extraer eventos futuros ni alterar el determinismo.
2. **Costos variables de terreno**:
   - La duración de cada movimiento se calcula como `costo_accion(salida.costo, actor.velocidad) = max(1, salida.costo * 100 // velocidad)`. Los enemigos agendan sus turnos con este costo exacto, manteniendo la invariante de avance temporal no nulo.

### 4b.3 Análisis de complejidad
- Con $k$ eventos empatados en el instante $t$: la extracción y ejecución toma $O(k \log n)$, donde $n$ es la cantidad de eventos en la agenda.
- Si no hay eventos empatados tras el turno del jugador: la verificación en `AgendaEventos.proximo_en_tiempo` inspecciona la raíz `self._heap[0]` en $O(1)$ y concluye inmediatamente.

### 4b.4 Evidencia empírica (`bench_motor.py`)
Medición repetida con 50 ciclos de esperar en Windows 11 con Python 3.13 (`python main.py --bench agenda`):

| Carga | Tiempo Medio | Tiempo Máximo | Cumple < 20 ms |
|---|---|---|---|
| 300 eventos pendientes, ~15 actúan por ciclo | 0.51 ms | 13.51 ms | SÍ |
| 300 enemigos en sala atacando a la vez (peor caso) | 19.24 ms | 121.79 ms | NO (caso extremo saturado) |
| **50 cazadores activos en esqueleto de costos variables (§5.6 Parte II)** | **2.03 ms** | **7.31 ms** | **SÍ (cumple con holgura)** |

### 4b.5 Límites conocidos
- Si se satura artificialmente una sala con 300 enemigos atacando en el mismo ciclo, el registro masivo de operaciones inversas para el historial puede provocar picos que superen los 20 ms en equipos con fluctuaciones de CPU. Sin embargo, en escenarios tácticos reales con 50 cazadores y costos variables, el tiempo máximo es de 7.31 ms, garantizando fluidez.

---

## 4c. Capacidad 001: Terreno, Cazador e Invalidación Reactiva de Rutas (§5.1, §5.2, SC-004..SC-006)

Especificación: [`specs/001-terreno-cazador/spec.md`](specs/001-terreno-cazador/spec.md) · Plan: [`specs/001-terreno-cazador/plan.md`](specs/001-terreno-cazador/plan.md)

**Coincidencia con plan.md original:** Sí en la decisión algorítmica: el plan 001 original (`43b8ce1`, bloques 3 y 4), el plan actual y `PlanificadorCazador` en `modelo/juego/cazador.py` usan Dijkstra compartido desde el jugador, rango máximo activo, arreglos con tokens, desempate por menor id e invalidación selectiva por puertas y global tras pergamino. Las precisiones posteriores sobre rango utilizado y `deshacer_ultimo()` concretan ese diseño. Las mediciones SC-005 y SC-006 de 4c.4 respaldan la elección original; no documentan una sustitución del algoritmo previsto.

### 4c.1 Problema
El enemigo cazador conoce la topología del esqueleto y persigue al jugador por el camino de costo mínimo acumulado de terreno, respetando las puertas abiertas y acotado por su campo de visión/rango ($d \le rango$). Calcular Dijkstra individualmente para cada cazador desde su posición hacia el jugador en cada decisión de juego tiene un costo prohibitivo $O(K \cdot (E' \log V'))$ que incumple el presupuesto de 20 ms con decenas de cazadores (`SC-004`, `SC-005`). Además, ante cambios de puertas o desplazamientos, el cálculo debe invalidarse reactivamente manteniendo equivalencia observable estricta (`SC-006`).

### 4c.2 Alternativas consideradas
1. **Dijkstra individual por cada cazador en cada paso**: Cada cazador ejecuta Dijkstra acotado hacia el jugador. Costo $O(K \cdot \text{Dijkstra})$. Descartado por no escalar con múltiples cazadores.
2. **Cálculo compartido invertido desde el jugador**: Dado que el grafo de terreno es no dirigido y simétrico (`costo(u,v) = costo(v,u)`), un único Dijkstra acotado desde la sala del jugador calcula simultáneamente la distancia mínima hacia todas las salas dentro del rango máximo de interés.
3. **Reinicio de marcas**:
   - *Reiniciar arreglos contiguos en cada búsqueda*: $O(N)$ por búsqueda. Descartado.
   - *Token de búsqueda persistente*: Arreglos de tamaño $N$ indexados por `Sala.indice`. Se incrementa `token_busqueda += 1`. Una sala está alcanzada si y solo si `marca[i] == token_busqueda`. El reinicio lógico es $O(1)$.
4. **Reutilización selectiva e invalidación reactiva**:
   - Se distinguen dos variables:
     - $R_{\text{activo}}$: El rango del cazador específico que consulta su movimiento.
     - $R_{\text{utilizado}}$: La cota de rango empleada en la última ejecución de Dijkstra acotado.
   - El campo se conserva y reutiliza mientras:
     1. El jugador permanezca en la misma sala (`_sala_jugador_id == partida.jugador.sala.id`).
     2. Ningún cazador requiera un rango mayor que el calculado ($R_{\text{requerido}} \le R_{\text{utilizado}}$). Si $R_{\text{activo}} \le R_{\text{utilizado}}$, el campo se conserva.
     3. Ninguna puerta con al menos un extremo a distancia $\le R_{\text{utilizado}}$ haya cambiado de estado (Contrato C2 con Axel y Kim).
   - *Puertas lejanas*: Si una puerta cambia pero ambos extremos están a distancia $> R_{\text{utilizado}}$ (o no alcanzados con la marca vigente), no se invalida la caché.
   - *Retroceso con pergamino*: Invalida incondicionalmente el campo derivado y revierte las mutaciones vía `deshacer_ultimo()`, suprimiendo avisos duplicados mediante verificación en `_notificar_invalidacion_rutas`.
   - *Independencia cognitiva*: El cazador consulta el estado físico real (`salida.esta_abierta()`), mientras que la memoria de observación del jugador reside en `ConocimientoMapa`, garantizando total desacoplamiento.

### 4c.3 Análisis de complejidad
1. **Cálculo compartido**: Una ejecución de `dijkstra_acotado` desde el jugador explora el subgrafo $G' = (V', E')$ donde las distancias son $\le R_{\text{utilizado}}$. Costo: $O(E' \log V')$ usando el montículo binario propio de Kim (Contrato C3).
2. **Reinicio lógico de marcas**: $O(1)$ mediante incremento del token entero `_token_busqueda`. (Nota: el reinicio lógico es $O(1)$, la búsqueda explora las aristas acotadas).
3. **Consulta de cada cazador**:
   - Obtener el rango máximo entre cazadores activos requiere recorrer la lista de enemigos de la partida: $O(E_{nemigos})$.
   - Elegir la primera vecina: examina a lo sumo 4 salidas abiertas en $O(1)$, consultando `dist[vecino.indice]`.
   - Desempate determinista por menor `vecino.id` entero: $O(1)$.
4. **Costo total para $K$ cazadores**:
   - Con recálculo necesario: $O(E' \log V' + K \cdot \text{salidas})$.
   - Con reutilización selectiva válida: $O(K \cdot \text{salidas}) = O(K)$, sin tocar Dijkstra.
5. **Espacio**: $O(N)$ arreglos fijos de distancias y marcas contiguas de tamaño $N = |Salas|$, reutilizados persistentemente sin alocaciones dinámicas.

### 4c.4 Evidencia empírica (`bench/bench_cazador.py`)
Medido en Windows 11 con `python main.py --bench cazador`:

#### 1. SC-004: Medición de ciclos individuales entre decisiones del jugador
- Configuración: 100 salas sintéticas, 30 cazadores activos simultáneos, rango = 600, 50 ciclos consecutivos de juego.
- **Tiempo máximo por ciclo**: **0.075 ms**.
- **Tiempo medio por ciclo**: **0.013 ms** (p50: 0.010 ms, p95: 0.021 ms, p99: 0.075 ms).
- **Ciclos que exceden 20 ms**: **0 de 50 (0%)**. Cumple estrictamente con el requisito de $< 20\text{ ms}$.

#### 2. SC-005: Comparación sistemática Individual vs. Compartido
Tiempo en milisegundos para resolver las decisiones de todos los cazadores activos en un turno:

| Cazadores Activos | Rango | Individual | Compartido | Aceleración (Speedup) |
|---|---|---|---|---|
| 1 cazador | Pequeño (250) | 0.00 ms | 0.00 ms | ~1x |
| 10 cazadores | Pequeño (250) | 0.00 ms | 0.00 ms | ~1x |
| 30 cazadores | Pequeño (250) | 0.41 ms | 0.12 ms | **3.4x** |
| 100 cazadores | Pequeño (250) | 1.18 ms | 0.10 ms | **11.3x** |
| 30 cazadores | Grande (1500) | 5.23 ms | 1.15 ms | **4.6x** |
| 100 cazadores | Grande (1500) | 10.97 ms | 0.42 ms | **26.3x** |

*Conclusión SC-005*: Con 100 cazadores y rango amplio, el cálculo compartido es **26.3 veces más rápido** que el individual.

#### 3. SC-006: Reutilización con Invalidación vs. Recálculo Continuo
Medido a lo largo de 30 pasos con 20 cazadores activos en 100 salas sintéticas:

| Escenario | Recálculo Continuo | Reutilización con Inv. | Speedup | Cálculos | Reutilizaciones | Equivalencia Observable |
|---|---|---|---|---|---|---|
| **Puertas Estables** | 16.35 ms | 1.83 ms | **8.91x** | 1 | 209 | **100% IDÉNTICAS** |
| **Puertas Inestables** (mutación c/5 pasos) | 13.35 ms | 1.74 ms | **7.67x** | 6 | 204 | **100% IDÉNTICAS** |

*Conclusión SC-006*: La reutilización selectiva logra una mejora de casi **9x**, manteniendo idénticas las decisiones de movimiento en cada ciclo.

### 4c.5 Límites conocidos
- La optimización de campo compartido asume simetría de costos de arista (`costo(u,v) == costo(v,u)`), lo cual se cumple por diseño en `Salida` (FR-001).
- El escaneo lineal de `partida.mapa.enemigos` para determinar el rango máximo requerido toma $O(K)$ en cada consulta. Con cientos de enemigos, este escaneo toma menos de 0.05 ms, pero sigue siendo un costo lineal en la cantidad de enemigos.
- Las mediciones fueron realizadas sobre topologías sintéticas deterministas y quedará abierta la validación sobre la cripta oficial definitiva que publique la cátedra para la defensa final (§9).

---

# Parte de Jeferson — Red, precarga, catálogo y bitácora en pantalla

## 5. §4.2 Traer el contenido antes de que haga falta

### 5.1 Problema

Antes de confirmar un movimiento, el contenido de la sala destino tiene que estar en memoria, y el jugador nunca puede quedar en una sala sin contenido. Cada solicitud tarda unos 400 ms (dato del enunciado) y acepta hasta 10 salas, con casi el mismo costo que una. El esqueleto completo se conoce desde el inicio. Una sala pedida no se vuelve a pedir, y las respuestas que lleguen en otro orden no deben cambiar la partida.

Operación real: en cada entrada a una sala, decidir qué salas pedir por adelantado; y antes de cada movimiento, garantizar la sala destino.

### 5.2 Alternativas consideradas

- **Pedir la sala al entrar** (una sala por solicitud). Es lo más simple, pero cada puerta cuesta una espera de ~400 ms y una solicitud del presupuesto.
- **Descargar todo el contenido al inicio.** Elimina las esperas, pero en una cripta grande gasta muchas solicitudes en salas que el jugador quizá no visite.
- **Precarga por cercanía en lotes de 10, en segundo plano.** Es la elegida.

### 5.3 Decisión

- `PrecargaContenido` (`precarga_contenido.py`). Al entrar a una sala hace una **búsqueda en anchura** sobre el esqueleto (`Esqueleto.cercanas`, con `ColaFIFO`) y arma un lote con las **10 salas más cercanas que no se hayan pedido**, hasta una profundidad de 2.
- Si alguna de esas salas ya está guardada en disco (misma versión de cripta), se lee de ahí y no se pide.
- El lote se envía a un `EjecutorRed`: un hilo que hace las solicitudes en segundo plano, una tras otra, mientras el jugador decide.
- `asegurar(destino)` se llama antes de confirmar el movimiento: si la sala ya llegó, sigue; si está en camino, espera esa solicitud (tiempo real, el reloj virtual no se mueve); si no se pidió, la pide en ese momento. Si no se puede obtener, el movimiento se rechaza y el jugador no se mueve.
- Las salas pedidas se marcan en una `ListaOrdenada` para no repetirlas.
- **Orden determinista:** las respuestas se incorporan en el **orden en que se enviaron**, aunque lleguen en otro orden.
- **Reserva:** la precarga especulativa deja 2 solicitudes del presupuesto libres para los movimientos que sí o sí hay que atender.

### 5.4 Análisis de complejidad

Con S salas en la cripta y d salidas por sala (como máximo 4):

| Operación | Costo | Frecuencia |
|---|---|---|
| Elegir el lote (BFS hasta encontrar 10 salas no pedidas) | O(salas visitadas por la BFS) | Al entrar a una sala |
| ¿Ya se pidió esta sala? | O(log S) | Por cada sala candidata |
| `asegurar` cuando la sala ya llegó | O(log S) | Antes de cada movimiento |
| `asegurar` cuando hay que esperar | Una espera de red (~400 ms reales) | Raro con la precarga |
| Solicitudes para recorrer la cripta | ≈ S / 10 | Durante toda la partida |

### 5.5 Evidencia empírica

`bench_red.py`, cripta lineal sintética recorrida de punta a punta (se cuentan solicitudes, que son exactas):

| Salas | Lotes de 10: solicitudes (esperas) | Una por solicitud: solicitudes (esperas) |
|---|---|---|
| 20 | **5** (2) | 33 (20) |
| 60 | **9** (6) | 73 (60) |
| 200 | **23** (20) | 213 (200) |

- Con lotes se hacen unas 9 veces menos solicitudes y muchas menos esperas. Con una sala por solicitud, **cada** movimiento espera (20 esperas en 20 salas, es decir ~8 s de espera solo por la red).
- En una partida real con caché caliente el reporte final dio "esperas bloqueantes = 1" (solo la sala inicial) y "salas leídas de disco = 20".
- Pruebas: `test_red.py` (nunca en una sala sin contenido y lotes, el orden de incorporación es el de solicitud, lote máximo de 10).

### 5.6 Límites conocidos

- En la cripta lineal del bench quedan esperas, porque el jugador avanza más rápido de lo que alcanza la profundidad 2. En criptas con más ramas el lote cubre mejor las salidas posibles.
- La precarga puede pedir salas que el jugador nunca visita; con presupuestos muy ajustados conviene bajar la profundidad.
- Un solo hilo de red hace las solicitudes una tras otra; varios hilos no ayudarían porque el límite de frecuencia del servicio produce 429.
- El costo de la BFS crece con las salas ya pedidas alrededor del jugador; con criptas de miles de salas muy conectadas convendría limitarla más.

---

## 6. §4.3 Resolución de referencias del catálogo

### 6.1 Problema

Cada enemigo, objeto y trampa trae solo un id de tipo, que hay que convertir en su ficha antes de mostrarlo o simularlo. Los ids aparecen en orden no controlado, se repiten entre salas y entre criptas. Un id vigente no se debe pedir dos veces si ya está en memoria o en disco.

### 6.2 Alternativas consideradas

- **Pedir cada id por separado** cuando aparece. Una solicitud por tipo.
- **Juntar los ids nuevos y pedirlos en lotes de hasta 10.** Es la elegida.

### 6.3 Decisión

- `ResolutorCatalogo` (`resolutor_catalogo.py`). Cuando llega el contenido de una sala, `ids_de_contenido` saca los ids sin repetir. `pedir` descarta los que ya están en la caché o en el disco (`AlmacenLocalCache`, de Kim) y los que ya están pendientes o en camino (marcados en una `ListaOrdenada`).
- `lanzar` envía lotes de 10 al `EjecutorRed`; con `forzar` envía también un lote incompleto cuando hace falta ya.
- Al llegar un lote, cada ficha se guarda en la caché y en el disco. Si un enemigo tiene objetos en `suelta`, esos ids también se piden.
- Los lotes se incorporan en el orden en que se enviaron.
- `asegurar` (§4.2) no deja entrar a una sala hasta que todas las fichas de su contenido estén listas.

### 6.4 Análisis de complejidad

Con F fichas conocidas:

| Operación | Costo | Frecuencia |
|---|---|---|
| ¿Ya la tengo? (caché o disco) | O(log F) | Por cada id que aparece |
| ¿Ya está pendiente o en camino? | O(log F) | Por cada id nuevo |
| Solicitudes por T tipos nuevos | ⌈T / 10⌉ | Al descubrir tipos |

### 6.5 Evidencia empírica

- La tabla de la sección 5.5 cuenta solicitudes de contenido **y** de catálogo juntas: con lotes de 10 contra uno por solicitud, 23 contra 213 en 200 salas.
- En una partida real con caché caliente: **3 solicitudes de 23** de presupuesto, 13 aciertos y 11 fallos de caché.
- Pruebas: `test_red.py` (lotes sin repetir ids, lo que `suelta` un enemigo también se resuelve).

### 6.6 Límites conocidos

- Un lote incompleto se fuerza cuando una sala cercana lo necesita, aunque no tenga 10 ids; en criptas con pocos tipos casi todos los lotes salen incompletos.
- Si el servicio no devuelve una ficha pedida, se informa como error de red.

---

## 7. §4.8 Bitácora en pantalla

### 7.1 Problema

La interfaz muestra solo los últimos 20 mensajes; la memoria debe ser constante durante toda la partida, y agregar un mensaje no debe desplazar físicamente los 19 anteriores.

### 7.2 Alternativas consideradas

- **Lista con `append` y `pop(0)`.** Es la más simple, pero `pop(0)` desplaza todos los mensajes.
- **Arreglo circular.** Es la elegida.

### 7.3 Decisión

`BitacoraPantalla` (`bitacora_pantalla.py`): un arreglo de 20 casillas creado una vez, un índice al mensaje más antiguo y una cantidad. Al llenarse, el mensaje nuevo sobrescribe la casilla del más antiguo y solo avanza el índice. `ultimos()` devuelve los mensajes del más antiguo al más reciente. Guarda además el total histórico de mensajes, que la vista usa para saber cuáles son nuevos.

### 7.4 Análisis de complejidad

| Operación | Costo |
|---|---|
| Agregar | O(1), sin desplazar |
| `ultimos()` | O(20) |
| Memoria | Constante: 20 casillas |

### 7.5 Evidencia empírica

`bench_red.py`, microsegundos por mensaje con la bitácora llena:

| Capacidad | Circular | `pop(0)` |
|---|---|---|
| 20 | 0.197 | **0.176** |
| 1000 | **0.209** | 0.252 |
| 20000 | **0.222** | 3.587 |
| 200000 | **0.227** | 228.575 |

- El circular se mantiene constante (≈0.2 µs) en todas las capacidades. `pop(0)` crece con la capacidad, porque desplaza: con 200 000 mensajes es unas 1000 veces más lento.
- Con la capacidad real (20), `pop(0)` es un poco más rápido: el desplazamiento de unas pocas referencias lo hace C. Con 1000 ya gana el circular. El requisito, sin embargo, es no desplazar y tener memoria constante, y solo el circular lo cumple.

### 7.6 Límites conocidos

- Con capacidad 20, la ventaja del circular es de forma, no de velocidad.
- Los mensajes más antiguos se pierden; el historial completo de la partida está en el log de replay (órdenes), no en la bitácora.

---

## 8. §5.1 Presupuesto de red

### 8.1 Problema

Cada cripta declara `presupuesto_solicitudes`, el máximo de solicitudes HTTP de la partida. Cuentan todas (lista de criptas, datos, páginas, contenido, catálogo, versiones y reintentos tras 429). Lo leído de disco o en `--offline` no cuenta. Al terminar se reportan solicitudes, presupuesto, aciertos y fallos de caché.

### 8.2 Alternativas consideradas

- **Contar después de hacer la solicitud.** Es simple, pero permite pasarse del límite.
- **Contar antes de cada intento y reservar para la precarga.** Es la elegida.

### 8.3 Decisión

- `PresupuestoRed` (`presupuesto_red.py`). El límite se fija con el valor de la cripta; no hay constantes ni fórmulas en el código.
- `ClienteHTTP._get` llama a `registrar()` **antes de cada intento**, incluidos los reintentos tras 429; si ya se llegó al límite lanza `ErrorPresupuesto` sin hacer la solicitud, y la acción se rechaza con un mensaje.
- La precarga **reserva** antes de planificar y deja libres 2 solicitudes para los movimientos obligatorios.
- El contador se reinicia antes de listar las criptas, para que esa solicitud cuente en la partida que sigue.
- `ClienteOffline` usa el presupuesto desactivado.

### 8.4 Análisis de complejidad

Registrar y reservar son O(1) con un cerrojo, porque el hilo de red y el principal comparten el contador.

### 8.5 Evidencia empírica

- Partida real con caché caliente: **3 solicitudes de 23**, con 20 salas leídas de disco.
- `test_partida.py` (`probar_sin_presupuesto_no_se_cae`): con el presupuesto agotado, el jugador se detiene en la última sala cargada, el reloj solo avanza por los movimientos confirmados y el juego sigue.
- `test_red.py`: los reintentos tras 429 cuentan (`test_cabecera_429_y_conteo`, `test_flujo_completo_con_429`), el presupuesto se respeta y, agotado, lanza el error en vez de hacer la solicitud.

### 8.6 Límites conocidos

- Las consultas de versión de cripta y de catálogo, necesarias para validar la caché, gastan presupuesto en cada partida.
- Con un presupuesto muy pequeño la reserva de 2 puede no alcanzar en criptas con muchas puertas seguidas.
- No se midió una corrida en frío contra una con caché caliente en la misma cripta; conviene agregarlo (borrar `datos_cripta/`, jugar, y jugar de nuevo).

---

## 8b. Parte II — Servicio web, datos nuevos y contrato C5 (003, FR-001..FR-008)

Especificación: [`specs/003-resolubilidad/spec.md`](specs/003-resolubilidad/spec.md) · Plan: [`specs/003-resolubilidad/plan.md`](specs/003-resolubilidad/plan.md) · Contratos: [`specs/003-resolubilidad/contracts/`](specs/003-resolubilidad/contracts/)

**Coincidencia con plan.md original:** Parcial. Se conservan `/llaves`, presupuesto y copia por versión previstos en el plan 003 original (`8ddfd70`), comprobables en `ClienteHTTP.llaves`, `AlmacenCripta` y `Aplicacion._verificar_cripta`. `Esqueleto.agregar_pagina` rechaza costos inválidos con `ErrorRed`, mientras el plan original proponía `max(1, int(...))`; el plan actual ya recoge el rechazo. El generador incorpora cuadrícula y rangos por intervalo. Son correcciones de validación y cobertura de escenarios documentadas en 8b.2 y al final de esta sección, sin medición motivadora registrada. Además, la verificación final usa solo `id`/`abre` de `/llaves` en `resolubilidad.py`, como exige el plan actual; la alternativa de fichas locales conservada en la tabla 8b.2 describe una decisión anterior, sustituida por la revisión de determinismo de 8c. No se atribuyen estos cambios a los tiempos de 8b.5.

### 8b.1 Problema

La Parte II agrega datos al servicio web: cada salida puede traer `costo` (100 si falta), las fichas de enemigo pueden ser `cazador` con `rango` (en unidades de costo) y hay una consulta nueva, `GET /criptas/<id>/llaves`, que dice dónde está cada llave (en el suelo o en la `suelta` de un enemigo). Todo debe respetar `presupuesto_solicitudes`, la validación por versión y el modo `--offline`. Además, el equipo necesitaba criptas sintéticas reproducibles para medir (contrato C5).

### 8b.2 Alternativas consideradas

| Tema | Alternativas | Elegida y motivo |
|---|---|---|
| Costo inválido (`0`, negativo, texto) | Corregirlo en silencio a 1 · Rechazarlo como respuesta mal formada | **Rechazar con `ErrorRed`** indicando sala, dirección y valor. Igual que el resto de validaciones de la Parte I; esconder un dato roto del servidor no se puede defender. Solo si **falta** se usa 100. |
| `/llaves` en cada partida | Consultar siempre · Guardar junto a la cripta y reutilizar mientras coincida la versión | **Guardar en `AlmacenCripta`**, ligado a la versión: con copia vigente se gastan 0 solicitudes. |
| Campo `abre` de las llaves | Pedir las fichas al catálogo (gasta presupuesto) · Usar solo fichas ya disponibles localmente | **Solo fichas locales**. Si no hay ficha, la llave abre únicamente la cerradura igual a su id (límite documentado). |
| Topología del generador | Solo línea · Línea y cuadrícula | **Ambas.** La línea es el peor caso de la cadena de llaves; la cuadrícula da caminos alternativos con costos distintos (necesaria para Dijkstra, cazador e IR_A). |
| Rango de los cazadores generados | Un valor para todos · Intervalo sorteado | **Entero o intervalo** `(min, max)` sorteado con la semilla, para tener distintos rangos. |

### 8b.3 Decisión

- `llaves(id_cripta)` en `FuenteDatos`, `ClienteHTTP` (`GET /criptas/<id>/llaves`, cuenta en el presupuesto, incluidos los reintentos 429), `ClienteOffline` (`criptas/<id>/llaves.json`) y `FuenteAlmacen`. `AlmacenCripta` guarda y descarta las llaves con la versión de la cripta (sin borrar archivos a mano).
- `Esqueleto` conserva `costo` en cada salida; no modifica la respuesta original.
- `bench/generador_criptas.py → generar_cripta(...)`: determinista por semilla (un `random.Random` local que no toca el azar de ninguna partida), mismo formato que la API (`general`, `paginas`, `contenido`, `catalogo`, `llaves`, `version_catalogo`), parámetros validados con `ValueError` y sin ajustes silenciosos.
- Paquete offline (`tests/crear_paquete_prueba.py`): costos, `llaves.json`, una cripta no resoluble con ciclo y una con 32 cazadores.

### 8b.4 Análisis de complejidad

| Operación | Costo |
|---|---|
| `llaves()` con red | 1 solicitud (+1 por cada 429) y O(L) para leer la respuesta |
| `llaves()` con copia de la misma versión | 0 solicitudes, O(L) |
| Costo de una salida al armar el esqueleto | O(1) por salida |
| `generar_cripta` | O(S + L + C) (salas, llaves, cazadores) |

### 8b.5 Evidencia empírica

`bench_red.py`, sección `/llaves` (sesión simulada, sin red real ni espera de reintento):

| Caso | Solicitudes gastadas | Tiempo (ms) |
|---|---|---|
| Sin copia local (200) | **1** | 0.075 |
| Copia local de la misma versión | **0** | 0.065 |
| Sin copia local (429 → 200) | **2** | 0.136 |

Pruebas: `test_esqueleto` (4, FR-007: costo por defecto, costos válidos, rechazo de inválidos, payload sin mutar), `test_generador_criptas` (9, FR-008: determinismo, línea y cuadrícula, rangos, validación), `test_red` (`test_FR003_bench_llaves_cuenta_consulta_copia_y_reintento_sin_red`), `test_almacen_cripta` (versión distinta descarta) y `test_resolubilidad` (`test_FR003_endpoint_llaves_cuenta_en_presupuesto_solicitudes`).

### 8b.6 Límites conocidos

- Si una llave abre una puerta necesaria para resolver la cripta solo por el `abre` de su ficha de catálogo, la verificación la reporta `NO RESOLUBLE`; en ese caso se juega con `--forzar`.
- El generador cierra con `cierre_automatico` solo las puertas de la cadena de llaves; no genera trampas.
- Las mediciones son con sesión simulada y criptas sintéticas, no con la cripta oficial.

**Plan frente a lo final.** La primera implementación corregía en silencio los costos inválidos a 1; en la revisión se cambió a rechazo con `ErrorRed`. La cuadrícula y los rangos por intervalo se agregaron al revisar el generador, porque la línea no servía para los bench de Dijkstra y cazador. Commits: `2a0432e`.

---

## 8c. Parte II — §5.4 Verificación de resolubilidad (003, FR-009..FR-018, SC-001..SC-005)

Especificación: [`specs/003-resolubilidad/spec.md`](specs/003-resolubilidad/spec.md) · Plan: [`specs/003-resolubilidad/plan.md`](specs/003-resolubilidad/plan.md) · Investigación: [`specs/003-resolubilidad/research.md`](specs/003-resolubilidad/research.md) · Modelo de datos: [`specs/003-resolubilidad/data-model.md`](specs/003-resolubilidad/data-model.md)

**Coincidencia con plan.md original:** Parcial. Se conserva el recorrido incremental por etapas con cola y listas de espera del plan 003 original (`8ddfd70`). `resolubilidad.py` usa `ordenar_merge()` en lugar de `ordenar()`: lo motivó la medición de 8c.5, donde 200 llaves dieron 19.503 ms antes y 4.732 ms después; el plan actual ya incorpora el cambio. `_menor_nodo_ciclico` añade Kosaraju antes del DFS de tres colores de `_detectar_ciclo`, aunque el plan actual aún describe solo ese DFS. El código justifica la adición por elegir el menor id cíclico sin enumerar ciclos; **POR CONFIRMAR:** no se encontró una medición comparativa que motivara ese cambio. El uso exclusivo del `abre` de `/llaves`, frente al catálogo local original, y `MOTIVO` obligatorio son correcciones funcionales documentadas al final de esta sección, ya recogidas en el plan actual, sin medición motivadora registrada.

### 8c.1 Problema

Antes de iniciar una partida hay que decidir si la cripta se puede ganar: obtener `llave_salida` y entrar a `sala_salida` por una puerta que la pide, con los supuestos de §3.5 (las llaves no se gastan, todo enemigo se vence, una llave en la `suelta` se obtiene en la sala donde empieza el enemigo, trampas y cierres no bloquean). Si no se puede, el reporte debe decir qué llaves faltan, la frontera bloqueada, dónde está cada llave y el ciclo si existe. Debe tardar menos de 200 ms y crecer de forma lineal, sin repetir el recorrido por cada llave.

### 8c.2 Alternativas consideradas

| Tema | Alternativas | Elegida y motivo |
|---|---|---|
| Recorrido | Repetir un recorrido completo desde la sala inicial cada vez que se obtiene una llave, O(L·(S+E)) · Un solo recorrido incremental con listas de espera por cerradura | **Incremental.** Cada sala y cada puerta se procesan una vez. La alternativa se implementó en el bench para medir. |
| Orden de las llaves | Orden en que se descubren · Por distancia · Por etapas y, dentro de cada etapa, por id de texto | **Por etapas.** La etapa 0 es todo lo alcanzable sin llaves; en una etapa solo se usan llaves de etapas anteriores. El resultado no depende del orden interno del recorrido ni del orden en que llegan los datos. |
| Índice id → número | `dict` (prohibido) · Tabla hash propia · Lista ordenada con búsqueda binaria propia | **Lista ordenada + búsqueda binaria** (el equipo acordó no usar tablas hash). |
| Ordenamiento para los índices | `ordenar()` (elige inserción o mergesort) · `ordenar_merge()` | **`ordenar_merge()`**, por la medición del punto 8c.5. |
| Coincidencia de llaves con puertas | Usar también el `abre` de la ficha del catálogo local · Pedir siempre las fichas de las llaves (gasta presupuesto) · Solo el `id` o el `abre` del registro de `/llaves` | **Solo el `id` o el `abre` del registro de `/llaves`.** Con la primera alternativa, la misma cripta daba `NO RESOLUBLE` o `RESOLUBLE` según el caché de cada equipo (lo detectó la revisión cruzada de Axel); la segunda gasta solicitudes y se aleja de §3.5, que pide usar solo el esqueleto y la ubicación de las llaves. |
| Ciclos | DFS desde cada llave · Componentes fuertemente conexas (Kosaraju) y luego un DFS para el testigo | **Kosaraju**, ambos recorridos iterativos: elige siempre el ciclo que contiene el menor id, en tiempo lineal. |
| Reporte de no resoluble | Segundo recorrido · Lo que quedó en las listas de espera más una continuación desde la frontera | **Mismo recorrido**: la frontera son las listas de espera que quedaron; para los ciclos se continúa desde la frontera etiquetando cada sala con la llave de la puerta cerrada más cercana (X → Y si X está detrás de una puerta que pide Y). |

### 8c.3 Decisión

`modelo/juego/resolubilidad.py` es puro (sin red, archivos, controlador ni vista): `verificar_resolubilidad(esqueleto, ubicaciones, sala_inicial, sala_salida, llave_salida)` devuelve `ResultadoResolubilidad` (`RESOLUBLE`, `NO RESOLUBLE` o `NO VERIFICADA`) con `formatear_reporte()` según la plantilla FR-018.

- Recorrido por etapas con la `ColaFIFO` propia, salidas en orden N, S, E, O.
- Listas de espera indexadas por lo que pide la puerta; al activar una llave se liberan las de su `id` y las de su `abre` del registro de `/llaves`, si lo contiene, nunca por fichas del catálogo.
- Puerta cerrada sin llave: infranqueable; si es adyacente a la región alcanzable, aparece en la frontera "sin llave asociada".
- Todo `NO RESOLUBLE` lleva `MOTIVO` con el primero que aplique, en este orden: "no existe puerta hacia sala_salida que pida llave_salida", "llave_salida no puede obtenerse" y "ninguna puerta hacia sala_salida que pide llave_salida es alcanzable".
- Integración (`controlador/aplicacion.py`, `main.py`): solo en partidas nuevas (no en replay, reconstrucción ni carga de guardado) se obtienen las llaves (copia local primero), se verifica y se guarda `app.reporte_resolubilidad`. Si no es `RESOLUBLE` y no hay `--forzar`, se lanza `ErrorNoResoluble` (subclase de `ErrorCripta`) y no se crea la partida; el controlador muestra el reporte y vuelve a la selección. Sin red o sin presupuesto y sin copia local: `NO VERIFICADA`, misma regla. `--verificar CRIPTA` no crea vista, imprime solo el reporte y sale con 0 / 1 / 2.

### 8c.4 Análisis de complejidad

S = salas, E = salidas, L = llaves y cerraduras distintas.

| Fase | Costo |
|---|---|
| Preparación: ordenar ids de salas y de llaves/cerraduras, traducir vecinos a posiciones | O(S log S + E log S + L log L) (búsquedas binarias propias y `ordenar_merge`) |
| Recorrido por etapas | **O(S + E + L)**: cada sala entra una vez a la cola y cada lista de espera se libera una vez |
| Ordenar las llaves dentro de cada etapa | O(L log L) en total |
| Frontera, ubicaciones y continuación para ciclos | O(S + E + L) |
| Ciclos (Kosaraju + testigo) | O(L + aristas del grafo de dependencias), con aristas ≤ L |
| Alternativa descartada (recorrido repetido) | O(L · (S + E)) |

Pruebas: `test_resolubilidad` (7 de aceptación: ciclo de la llave de salida, llave en la `suelta` de un errante, mismo orden en ejecuciones repetidas, no inicia sin `--forzar`, `/llaves` en el presupuesto, códigos 0/1/2 de `--verificar`, plantilla exacta), `test_resolubilidad_unitaria` (17: ciclo de tres llaves, coincidencia por `abre` del registro de `/llaves`, independencia del catálogo, `MOTIVO` obligatorio, etapa 0 sin llaves de la misma etapa, entre otras), `test_resolubilidad_integracion` (14: replay y carga no verifican, contingencia de red y presupuesto, `--forzar`, offline real sin vista), `test_bench_resolubilidad` (9, incluida la igualdad de resultados antes y después del cambio de ordenamiento). Ahora hay pruebas con nombre de requisito para FR-001, FR-006, FR-007 y SC-001 a SC-004.

### 8c.5 Evidencia empírica

`python main.py --bench resolubilidad`. Criptas sintéticas de `generar_cripta` (semilla 7), mediana de 7 repeticiones con `time.perf_counter`, preprocesamiento incluido en ambas versiones. Ambas versiones dieron siempre el mismo estado y el mismo orden de llaves. Equipo: laptop de Jeferson, Windows, Python 3.13.18 del venv, repositorio fuera de OneDrive.

**Antes (commit `809f398`, índices con `ordenar()`):**

| Topología | Salas | Llaves | Por etapas (ms) | Repetido (ms) |
|---|---|---|---|---|
| línea | 51 | 50 | 0.759 | 1.280 |
| línea | 101 | 100 | 1.577 | 3.687 |
| línea | 201 | 200 | **19.503** | 29.284 |
| cuadrícula | 1000 | 50 | 10.783 | 24.100 |

Con 200 llaves el tiempo se multiplicó por 12 al duplicar el tamaño. Causa: `ordenar()` elige inserción cuando el desorden "lejano" es ≤ 2 %, y la lista de ids (llave de salida + cerraduras de las puertas + ids de las ubicaciones) son dos tramos ordenados pegados, que el detector toma como "casi ordenada" (≈1,5 % de desorden con 200 llaves; ≈3 % con 100, donde sí elige mergesort). Así la preparación pagaba O(n²).

**Después (commit `d5bc68a`, `ordenar_merge()`):**

| Topología | Salas | Salidas | Llaves | Por etapas (ms) | Repetido (ms) | Aceleración |
|---|---|---|---|---|---|---|
| línea | 11 | 20 | 10 | 0.153 | 0.179 | 1.17× |
| línea | 51 | 100 | 50 | 0.899 | 1.509 | 1.68× |
| línea | 101 | 200 | 100 | 2.663 | 5.776 | 2.17× |
| línea | 201 | 400 | 200 | **4.732** | 15.950 | 3.37× |
| línea | 401 | 800 | 400 | **10.586** | 63.248 | **5.97×** |
| cuadrícula | 1000 | 3872 | 50 | 13.319 | 27.342 | 2.05× |

- **Por etapas crece lineal:** al duplicar las llaves el tiempo se multiplica por 1.78 (100 → 200) y 2.24 (200 → 400). El 2.96 de 50 → 100 es ruido de mediciones de menos de 3 ms.
- **El repetido crece cuadrático:** ×2.8 y ×4.0 en los mismos pasos. La ventaja de la versión por etapas aumenta con el tamaño.
- Con 100 llaves, `ordenar_merge` es algo más lento que la inserción (2.66 frente a 1.58 ms): es el costo fijo de mergesort en listas chicas, que se acepta a cambio de no caer nunca en O(n²).
- **SC-001:** 13.3 ms en la cuadrícula de 1000 salas, muy por debajo de 200 ms (referencia sintética).

Pruebas nuevas: **SC-001 provisional**, en sustitución de la cripta publicada, en la cuadrícula sintética de 1000 salas, semilla 7, mediana de 7 verificaciones completas: **14.7 ms**; **SC-002**: al duplicar salas y llaves, las salidas examinadas pasaron de **1406 a 2818 (×2.0)**.

### 8c.6 Límites conocidos

- **SC-001 no está validado con la cripta oficial publicada**; los números son de criptas sintéticas.
- La preparación agrega un factor logarítmico (búsquedas binarias y ordenamiento); el recorrido en sí es lineal. Con tamaños chicos la aceleración es modesta porque ambas versiones incluyen esa preparación.
- Se reporta un solo ciclo (el que contiene el menor id), no todos.
- Si una llave abre una puerta necesaria para resolver la cripta solo por el `abre` de su ficha de catálogo, la verificación la reporta `NO RESOLUBLE`; en ese caso se juega con `--forzar`.
- Lección para el equipo: `ordenar()` puede caer en O(n²) con listas formadas por tramos ordenados concatenados; donde eso pueda ocurrir, usar `ordenar_merge()` o medir.

**Plan frente a lo final.**
1. El plan usaba `ordenar()`; la medición obligó a cambiar a `ordenar_merge()` (en el mismo commit se actualizaron primero `plan.md` y `research.md` y después el código).
2. El plan proponía un DFS de tres colores; la versión final agrega Kosaraju para elegir siempre el mismo ciclo sin enumerarlos todos.
3. La primera versión del plan dejaba usar en una etapa las llaves encontradas en esa misma etapa, lo que hacía depender el orden del recorrido; se corrigió en el plan antes de programar.
4. El reporte se guarda en `app.reporte_resolubilidad` y lo muestra la vista activa; el controlador no imprime (MVC).
5. El plan liberaba también por el `abre` de la ficha local; tras la revisión cruzada se quitó por determinismo, corrigiendo primero `spec.md`, `plan.md`, `research.md` y `data-model.md` (`6b60532`) y después el código (`dd98792`).
6. El reporte sin puerta alcanzable hacia la salida salía sin explicación; ahora `MOTIVO` es obligatorio en todo `NO RESOLUBLE`.

Commits: `ff0ace9` (spec), `8ddfd70` y `9dab2b6` (plan, tareas y análisis), `809a7b6` (pruebas de aceptación), `b3a2a01` (algoritmo), `dc5f4e8` (integración, `--verificar`, `--forzar`), `809f398` (bench), `d5bc68a` (corrección del ordenamiento), `6b60532` (corrección de la spec), `dd98792` (corrección del código).

---

## 8d. Parte II — §5.6 Revisión de la red con los datos nuevos

### 8d.1 Problema

§5.6 pide repetir las mediciones de la Parte I con los datos de la Parte II y decir si las decisiones siguen valiendo. En red, lo nuevo es `/llaves` (una solicitud más antes de jugar) y que las salidas traen costo.

### 8d.2 Evidencia (`python main.py --bench red`)

**Recorrido de la cripta (lotes de 10 frente a una sala por solicitud):**

| Salas | Lotes de 10: solicitudes (esperas) | Una por solicitud: solicitudes (esperas) |
|---|---|---|
| 20 | **5** (2) | 33 (20) |
| 60 | **9** (6) | 73 (60) |
| 200 | **23** (20) | 213 (200) |

Estas solicitudes incluyen también las del catálogo, así que la revisión de §5.6 cubre las decisiones de las secciones 5 y 6.

Iguales a la Parte I (sección 5.5): el costo de las salidas no cambia cuántas páginas ni cuántos lotes se piden.

**Bitácora en pantalla (µs por mensaje):**

| Capacidad | Circular | `pop(0)` |
|---|---|---|
| 20 | 0.146 | **0.113** |
| 1000 | **0.156** | 0.216 |
| 20000 | **0.162** | 46.305 |
| 200000 | **0.147** | 136.538 |

Misma conclusión que la sección 7.5: el circular se mantiene constante y `pop(0)` crece con la capacidad.

**`/llaves`:** 1 solicitud por partida nueva sin copia local, 0 con copia de la misma versión, 2 si hay un 429. En replay, reconstrucción y carga de guardado no se consulta (no se verifica).

### 8d.3 Conclusión

Las decisiones de la Parte I (lotes de 10, prioridad por cercanía, bitácora circular, presupuesto con reserva) siguen siendo correctas con los datos nuevos. El único costo nuevo es una solicitud por partida nueva, que desaparece cuando la cripta ya se jugó con esa versión.

### 8d.4 Límites conocidos

- Con un presupuesto muy chico, la solicitud de `/llaves` compite con la reserva de la precarga; si no alcanza y no hay copia local, la verificación queda `NO VERIFICADA` y la partida no inicia sin `--forzar` (el programa no se cae).
- No se midió contra el servidor real con la cripta oficial.

---

# Parte de Kim — Caché persistente, ordenamiento, guardado y capacidad 002

## 9. §4.4 Reutilización y caché persistente

### 9.1 Problema

Las fichas del catálogo se usan todo el tiempo (cada enemigo, objeto y trampa remite a una). Cada solicitud de red tarda cerca de 400 ms y gasta presupuesto, así que una ficha ya descargada no se debe volver a pedir. Hay tres necesidades:

1. Saber si una ficha está en memoria, que es de las operaciones más frecuentes.
2. Mantener un máximo de fichas en memoria (`--cache-size`, 25 por defecto) y decidir cuál liberar, sin liberar nunca una ficha en uso.
3. Que lo descargado sobreviva al cierre del programa y se valide con la versión de catálogo y de cripta, sin descargar todo otra vez.

### 9.2 Alternativas consideradas

**Para la búsqueda ("¿tengo esta ficha?")**

- Búsqueda lineal en una lista. Es la más simple, pero crece con n.
- Lista ordenada con búsqueda binaria. Es la elegida.

**Para qué ficha liberar**

- FIFO (liberar la más antigua en entrar). Es más simple, pero no mira si la ficha se sigue usando.
- LRU (liberar la menos recientemente usada). Es la elegida.

**Para el disco**

- Un archivo por ficha.
- Un solo archivo de datos con un índice en memoria. Es el elegido.
- Volver a descargar siempre. Se descartó porque no cabe en el presupuesto de solicitudes.

### 9.3 Decisión

- **Búsqueda:** `ListaOrdenada` (`lista_ordenada.py`). Son dos listas paralelas, claves y valores, siempre ordenadas por clave. La búsqueda es binaria. Tiene `insertar_muchos`, que junta todo, ordena una sola vez con nuestro `ordenar` y descarta duplicados (gana la última).
- **Memoria:** `Cache` (`cache.py`). Una lista doblemente enlazada guarda el orden de uso (la más reciente al frente) y la `ListaOrdenada` guarda `id -> nodo`. Al consultar una ficha, su nodo pasa al frente. Para liberar se mira desde el final y se libera la primera ficha que no esté en uso. La caché recibe una función `en_uso(id)`, que en el juego es `Partida.ficha_en_uso`. Si todas las fichas están en uso, no se libera nada y la caché se pasa del tope.
- **Disco:** `AlmacenFichas` (`almacen_fichas.py`). Es un archivo con encabezado (marca y versión de catálogo) y registros `[largo del id][id][largo del JSON][JSON]`. El índice en memoria es una `ListaOrdenada` con `id -> [posición, largo]`. Leer una ficha es una búsqueda en el índice, un `seek` y una lectura. Si la versión guardada no coincide con la actual, se descarta todo y se empieza un archivo nuevo. Una ficha que se guarda otra vez se añade al final y el índice apunta a la nueva copia.
- **Cripta:** `AlmacenCripta` (`almacen_cripta.py`) reutiliza `AlmacenFichas` con la versión de cripta en el encabezado. Guarda los datos generales, cada página del esqueleto y el contenido sala por sala (`general`, `pagina_n`, `sala_n`). Una sala vacía también se guarda, porque "ya la pedí y está vacía" no es lo mismo que "nunca la pedí".
- **Unión:** `AlmacenLocalCache` (`almacen_local_cache.py`) implementa la interfaz `AlmacenLocal` del cliente de red. Consulta primero la caché, luego el disco, y deja la red al resolutor. El estado de la caché no se registra en el historial de retroceso, porque es infraestructura y no estado del juego (§2.11).

### 9.4 Análisis de complejidad

Con n fichas:

| Operación | Costo | Frecuencia |
|---|---|---|
| Buscar o `contiene` | O(log n) | La más frecuente |
| Mover un nodo al frente (LRU) | O(1) | En cada acierto |
| Liberar una ficha | O(1) en el caso normal; recorre más solo si las últimas están en uso | Al llenarse |
| Insertar o eliminar en la lista ordenada | O(n), por el desplazamiento | Pocas veces: al llegar un lote o al liberar |
| Cargar muchas fichas de golpe (`insertar_muchos`) | O(n log n) | Al arrancar |
| Leer una ficha de disco | O(log n) en el índice, más un `seek` y una lectura | Al recuperar una ficha liberada |
| Reconstruir el índice al arrancar | O(n) recorriendo el archivo, más O(n log n) del ordenamiento | Una vez por ejecución |

El costo O(n) de insertar es aceptable porque la caché en memoria tiene como máximo `--cache-size` fichas (25 por defecto).

### 9.5 Evidencia empírica

**Búsqueda: lista ordenada contra lineal** (`bench_lista_ordenada.py`, microsegundos por búsqueda):

| n | ordenada | lineal | lineal / ordenada |
|---|---|---|---|
| 25 | 0.602 | **0.438** | 0.7 |
| 100 | **0.715** | 1.526 | 2.1 |
| 1000 | **0.942** | 9.308 | 9.9 |
| 10000 | **1.333** | 91.200 | 68.4 |

La búsqueda ordenada casi no crece con n y la lineal sí. Con 25 fichas gana la lineal, y la diferencia es de décimas de microsegundo. El punto de cruce está entre 25 y 100.

**Inserción** (milisegundos para cargar n elementos que llegan en desorden):

| n | uno a uno | `insertar_muchos` |
|---|---|---|
| 25 | **0.033** | 0.043 |
| 100 | 0.268 | **0.173** |
| 1000 | 21.9 | **3.1** |
| 5000 | 515 | **10.7** |
| 10000 | 2015 | **23.3** |

Insertar uno a uno crece de forma cuadrática. Por eso `AlmacenFichas._reconstruir_indice` junta los registros y llama a `insertar_muchos` una sola vez. Este cambio sale de la medición.

**Eliminar y reinsertar una clave** (µs): 3.4 con n=25, 8.6 con n=100, 88 con n=1000 y 1135 con n=10000. Crece de forma lineal, como se espera, y con 25 fichas es despreciable.

**LRU contra FIFO** (`bench_cache.py`, porcentaje de aciertos con 20 000 accesos sintéticos, 80 % a 10 ids calientes que van rotando y 20 % al azar):

| tope | LRU | FIFO |
|---|---|---|
| 5 | 32.1 | 31.1 |
| 10 | 60.4 | 54.1 |
| 15 | 76.3 | 66.3 |
| **25** | **83.8** | **76.9** |
| 50 | 89.2 | 87.2 |

LRU gana en todos los topes. Con el tope por defecto (25) obtiene unos 7 puntos más de aciertos. Con tope 5 casi empatan, porque no caben ni los ids calientes, y con tope 50 se acercan, porque casi todo cabe.

**Disco: índice con `seek` contra un archivo por ficha** (`python -m bench.bench_almacen_fichas`, con `ListaOrdenada`, microsegundos por lectura):

| n | índice + seek | un archivo por ficha | por ficha / índice |
|---|---|---|---|
| 25 | 39.1 | 205.6 | 5.3 |
| 100 | 42.2 | 578.1 | 13.7 |
| 1000 | 64.4 | 5388.4 | 83.7 |
| 5000 | 73.2 | 11645.7 | 159.0 |

El índice con `seek` gana en todos los tamaños y su tiempo casi no crece con n. Un archivo por ficha se degrada mucho al crecer n. No medí la causa; puede influir el sistema de archivos, OneDrive y el antivirus.

**Guardar una ficha** (µs): 315 con n=25, 493 con 100, 866 con 1000 y 956 con 5000. Crece con n porque `guardar` inserta en la lista ordenada (O(n)) y además abre y cierra el archivo en cada llamada. Solo ocurre cuando llega un lote de red, así que es despreciable frente a una solicitud de unos 400 ms.

**Memoria contra disco:** un acierto de caché cuesta entre 1 y 2 µs y una lectura de disco entre 39 y 73 µs según la tabla de arriba, es decir, del mismo orden. La caché en memoria sirve sobre todo para no abrir el archivo ni decodificar el JSON cada vez que se usa una ficha. Según el enunciado, una solicitud de red tarda cerca de 400 ms (es un dato del enunciado, no una medición mía). Por eso conviene tener la caché en memoria y el disco como respaldo.

**Tiempos de la caché con la lista ordenada** (`python -m bench.bench_cache`, microsegundos por operación):

| tope | obtener acierto | obtener fallo | poner con desalojo |
|---|---|---|---|
| 25 | 1.725 | 1.064 | 8.9 |
| 1000 | 1.870 | 1.253 | 108.3 |
| 10000 | 2.138 | 1.701 | 1710.8 |

Acierto y fallo casi no crecen con el tope (O(log n)). `poner` con desalojo sí crece de forma lineal, porque liberar e insertar desplaza elementos en las listas paralelas. Los porcentajes de aciertos de LRU y FIFO salieron idénticos en las dos corridas, como se esperaba, porque no dependen de la estructura de búsqueda.

**Arranque (reconstruir el índice)**, en milisegundos, mediana de 7 repeticiones: 0.27 con n=25, 0.44 con 100, 8.2 con 1000 y **336.7 con 5000**. De 1000 a 5000 fichas el tiempo se multiplica por unas 41 con solo 5 veces más datos, o sea que crece más que de forma lineal. La segunda corrida dio el mismo orden (332 ms), así que no es ruido. `_reconstruir_indice` recorre el archivo una vez y llama a `insertar_muchos` una sola vez, por lo que el recorrido no debería explicarlo.

No se llegó a encontrar la causa con una prueba. Una explicación posible es que `insertar_muchos` usa el selector `ordenar`: los ids del bench son `id_0, id_1, ...`, y como texto quedan desordenados a larga distancia, pero el selector mide el desorden a distancia 8 y podría haber elegido inserción (O(n²)). Es solo una idea que no se comprobó. Se anota como limitación: con miles de fichas el arranque tarda cientos de milisegundos, y con las cantidades que usa el juego (decenas o cientos de fichas) tarda menos de 10 ms.

**Prueba con una partida completa (`python main.py --replay LOG`).** Al reproducir un registro hubo 4 solicitudes de red de 23, 3 aciertos de caché, 10 fallos, 0 lotes de contenido y 20 salas leídas de disco. Es un solo dato, no una comparación: no se midió una corrida en frío contra una con la caché caliente, porque la carpeta `datos_cripta` ya tenía archivos de corridas anteriores. Por eso la ventaja de la caché persistente se sustenta en las tablas de lectura de disco y de red de arriba, y no en esta prueba.

### 9.6 Límites conocidos

- La lista ordenada deja de ser adecuada si `--cache-size` o el catálogo crecen a decenas de miles y se insertan de a uno, porque insertar es O(n) y cuadrático en total. `insertar_muchos` mitiga la carga inicial.
- Con la lista ordenada, `poner` con desalojo es O(n) y crece de forma lineal con el tope: 8.9 µs con tope 25, 108 µs con 1000 y 1.7 ms con 10000. Con el tope por defecto no importa, porque solo ocurre cuando llega una ficha nueva y las fichas llegan en lotes de a lo sumo 10 por solicitud. Con topes de miles de fichas convendría otra estructura de búsqueda. Es el costo de usar listas ordenadas.
- La ventaja de LRU se midió con un patrón de accesos sintético con localidad. Con accesos que nunca se repiten, LRU y FIFO se comportarían casi igual. Conviene repetir la comparación con los accesos reales de una partida.
- Si todas las fichas están en uso, la caché supera el tope (está cubierto por `test_cache.py`).
- `AlmacenFichas` abre y cierra el archivo en cada `leer` y `guardar`. Las fichas re-guardadas dejan basura y no hay compactación. Reconstruir el índice recorre todo el archivo y el arranque crece con las fichas guardadas; con 5000 fichas tardó unos 330 ms, más de lo esperado (ver la hipótesis de la sección 9.5).
- Solo hay una consulta de versión de catálogo y una de cripta por ejecución, y las dos cuentan contra el presupuesto de solicitudes. Un catálogo con cientos de miles de fichas exigiría guardar el índice en un archivo aparte.
- Las mediciones se hicieron en Windows sobre OneDrive.

---

## 10. §4.9 Ordenamiento

### 10.1 Problema

El programa ordena en varios contextos: vistas del inventario por peso, valor o nombre, tabla de puntajes, el índice del guardado binario y la carga ordenada de la lista de la caché. No se permite `list.sort()` ni `sorted()`. Los datos pueden ser pequeños (un inventario de pocas decenas), casi ordenados o grandes, y la comparación puede ser cara.

### 10.2 Alternativas consideradas

- **Solo inserción.** Es excelente con datos pequeños o casi ordenados, pero es O(n²) con datos grandes desordenados.
- **Solo merge sort.** Es siempre O(n log n) y estable, pero tiene más costo fijo con listas pequeñas y usa memoria extra.
- **`sorted()` de Python.** Se midió solo como referencia, porque está prohibido en el programa.
- **Selector automático** entre inserción y merge. Es el elegido.

### 10.3 Decisión

`ordenamiento.py` implementa `ordenar_insercion` y `ordenar_merge`, ambos estables, y un selector `ordenar(datos, clave, descendente, comparacion_costosa)` que devuelve una lista nueva sin modificar la original (el inventario necesita una vista sin alterar su orden real). La clave se calcula una sola vez por elemento.

El selector elige inserción en estos casos:

1. `n` no supera `UMBRAL_PEQUENO` (32), o `UMBRAL_COSTOSO` (8) si la comparación es costosa.
2. Hay poco desorden a distancia: se compara cada elemento con el que está `SALTO` (8) posiciones adelante, y si la fracción fuera de orden es de 0.02 o menos, se usa inserción.

En cualquier otro caso usa merge.

**Cómo llegamos a esta regla.** El selector pasó por tres versiones, todas medidas:

1. Medía los pares vecinos fuera de orden. Eligió mal en "casi ordenado" con desorden lejano (n=5000: 95 ms con inserción contra 12 ms con merge).
2. Se añadió un límite de tamaño. Arregló ese caso, pero perdió el desorden local, donde inserción gana (n=5000: 1.3 ms contra 10.8 ms).
3. La versión final mide el desorden a distancia 8. Con ella `auto` sigue a la mejor opción en los cuatro escenarios.

### 10.4 Análisis de complejidad

| Algoritmo | Mejor caso | Caso medio y peor | Memoria extra |
|---|---|---|---|
| Inserción | O(n), casi ordenado | O(n²) | O(1) |
| Merge | O(n log n) | O(n log n) | O(n) |
| Medida de desorden del selector | O(n), una pasada | O(n) | O(1) |

### 10.5 Evidencia empírica

`bench_ordenamiento.py`, milisegundos. Se muestran las filas de n = 1000 y n = 5000 de la última corrida, y la tendencia en n pequeños.

| Escenario | n | Inserción | Merge | `auto` |
|---|---|---|---|---|
| Aleatorio | 1000 | 50.4 | 2.8 | 2.9 |
| Aleatorio | 5000 | 767.7 | 11.3 | 13.2 |
| Casi ordenado (desorden lejano) | 5000 | 93.2 | 10.2 | 13.2 |
| Casi ordenado local | 1000 | 0.218 | 1.442 | 0.644 |
| Casi ordenado local | 5000 | 1.308 | 10.809 | 1.670 |
| Inverso | 5000 | 1456.8 | 8.7 | 9.3 |

- Con n pequeño (10 a 20) inserción gana o empata, y el cruce con merge está entre 20 y 50 elementos.
- Con comparaciones costosas merge gana siempre. Con n=1000 tardó unos 20 ms y inserción unos 574 ms. También hace muchas menos comparaciones: con n=5000 aleatorio, 55 131 contra 6 230 815.
- `sorted()` fue unas 25 veces más rápido que nuestro merge con n=1000 (0.078 ms), porque está escrito en C. Esto es esperado y no afecta a los tamaños reales del juego.
- Las pruebas de corrección están en `test_ordenamiento.py` (casos básicos, duplicados, descendente, estabilidad y el caso casi ordenado local con n grande).

### 10.6 Límites conocidos

- Con claves baratas y n pequeño, el costo de medir el desorden domina. Por ejemplo, con n=100 aleatorio `auto` tardó 0.65 ms contra 0.40 de merge puro, aunque otras corridas dieron valores cercanos, así que parte es ruido.
- Con desorden lejano moderado el selector elige merge, aunque en casos intermedios inserción podría ganar.
- Los umbrales (32, 8, `SALTO` = 8, 0.02) salen de estas mediciones y habría que recalibrarlos en otro equipo.
- Los tiempos varían entre corridas; las comparaciones contadas son exactas y repetibles.
- Nuestro ordenamiento es mucho más lento que `sorted()`. Es aceptable para inventarios de decenas de objetos y tablas de puntajes pequeñas.

---

## 11. §4.10 Guardado binario de la partida

### 11.1 Problema

El estado se guarda en un archivo binario de formato propio. Al cargar debe poder recuperarse una sala específica sin leer todo el archivo, debe detectarse una versión de formato incompatible y hay que comparar tamaño y tiempo de carga contra JSON.

### 11.2 Alternativas consideradas

- **JSON.** Es simple y `json.load` está escrito en C, pero para una sola sala obliga a cargar todo el archivo. Se midió como alternativa.
- **Binario sin índice.** Hay que leer de forma secuencial hasta la sala que se busca, que es O(n) como JSON. Se descartó por razonamiento; no se midió.
- **Binario con índice ordenado de entradas de tamaño fijo y búsqueda binaria con `seek`.** Es el elegido.

### 11.3 Decisión

`guardado_binario.py`. El archivo tiene esta forma:

```
[ encabezado ]  marca "CRPT", versión del formato, n_salas, posición y largo del bloque general
[ índice ]      una entrada por sala (id, posición, largo), de 16 bytes cada una, ordenada por id
[ bloques de salas ]
[ bloque general ]  reloj, semilla, vida, sala actual, inventario
```

- Las entradas del índice son de tamaño fijo, así que la sala i está en una posición calculable. `leer_sala` hace una búsqueda binaria directamente en el archivo con `seek`, y luego un `seek` al bloque de la sala.
- El índice se ordena con nuestro `ordenar` al guardar (es el uso de §4.9 en el "índice del guardado").
- Los textos se guardan con su largo (2 bytes) delante, y se usa `struct` para los números.
- Si la marca o la versión de formato no coinciden, se lanza `ErrorFormato` y no se lee nada más.

**Estado actual:** la estructura (`PartidaGuardada` y `SalaGuardada`) es de prueba. Guarda reloj, semilla, vida, sala actual, inventario, y por sala el rastro, enemigos, objetos y puertas. Limitación conocida: no está adaptada a todos los campos reales del modelo (`partida.py`, `sala.py`, `actor.py`, `objetos.py`, agenda y efectos activos). El formato, la búsqueda de una sala y la verificación de versión son los que se miden y se prueban; para guardar una partida real habría que escribir la conversión entre `Partida` y `PartidaGuardada`.

### 11.4 Análisis de complejidad

| Operación | Costo |
|---|---|
| Guardar | O(n log n) por ordenar el índice, más escribir O(n) |
| Leer una sala | O(log n) pasos de 16 bytes, más una lectura |
| Cargar los datos generales | O(1) en el número de salas |
| Carga completa | O(n) |

### 11.5 Evidencia empírica

`bench_guardado_binario.py` (mediana de 7 repeticiones). Los JSON se guardaron como listas, sin nombres de campos, por lo que ya es compacto.

| Salas | Binario (KB) | JSON (KB) | Cargar bin (ms) | Cargar JSON (ms) | 1 sala bin (ms) | 1 sala JSON (ms) |
|---|---|---|---|---|---|---|
| 20 | 1.1 | 1.2 | 0.172 | 0.076 | 0.0535 | 0.054 |
| 200 | 10.0 | 11.9 | 0.597 | 0.154 | 0.0432 | 0.150 |
| 1000 | 49.9 | 60.1 | 1.635 | 0.695 | 0.0402 | 0.657 |
| 5000 | 250.4 | 311.4 | 9.775 | 4.448 | 0.0323 | 3.877 |

- **Tamaño:** el binario pesa entre un 8 y un 20 % menos. La mejora es real pero modesta.
- **Carga completa:** gana JSON, unas 2 a 2.5 veces. `json.load` está escrito en C y nuestro desempaquetado corre en Python.
- **Una sola sala:** el binario tarda entre 0.03 y 0.05 ms y no crece con n. JSON obliga a cargar todo y pasa de 0.054 a 3.877 ms. Con 5000 salas el binario es unas 120 veces más rápido. Con 20 salas empatan.
- Las pruebas de corrección están en `test_guardado_binario.py`: datos generales, lectura de cada sala, carga completa, partida vacía, versión incompatible y marca incorrecta.

### 11.6 Límites conocidos

- La carga completa es más lenta que JSON. El formato conviene cuando se necesitan salas sueltas.
- Los números tienen tamaño fijo (por ejemplo, vida y tiempos en 4 bytes). Si el modelo usa valores mayores, hay que cambiar los tipos de `struct`.
- El historial de retroceso no se guarda: son funciones, no datos. Al cargar una partida, el historial empieza vacío.
- La estructura guardada es de prueba y debe ajustarse a los campos reales del modelo.
- Las mediciones se hicieron en Windows sobre OneDrive.

---

## 17. Niebla de guerra e IR_A (002, Parte II)

**Coincidencia con plan.md original:** Parcial. El plan 002 original (`db75930`), el actual y el código conservan arreglos indexados en `ConocimientoMapa`, Dijkstra inverso con memoria de puertas en `controlador/planificador_rutas.py`, IR_A compuesto y guardado v4. Frente al comentario inicial único del plan original, `Controlador._ejecutar_ir_a` emite una marca antes de cada observación exterior, después de la cancelación; `Registro` protege las observaciones permanentes con generaciones. Son ajustes funcionales de reconstrucción y retroceso descritos en 17.3, no cambios motivados por tiempos documentados. La ampliación US5 de 17.7 agrega el mapa dibujado y un AVL de ocupación: con 5000 conocidas midió 123,594 ms frente a 759,674 ms de ListaOrdenada, con picos de 4444,2 frente a 3872,0 KiB. Esa comparación respalda el AVL; restaurar la lista simple y el barrido O(N) obedeció a la instrucción expresa del usuario, no a esa medición, que excluye la foto. El plan actual recoge esos ajustes. `Orden` pasó del controlador al modelo por MVC durante la integración con 004, sin medición motivadora registrada.

Responsable: Kimberly. Base funcional publicada:
`617f6665455e81a0ffe7311a4e60006aef1e8a2f`.
[Especificación](specs/002-niebla-ir-a/spec.md),
[plan](specs/002-niebla-ir-a/plan.md) y
[matriz y mediciones](specs/002-niebla-ir-a/DECISIONES.md).
Los seis apartados siguen la estructura documental del equipo. La evidencia
funcional se contrasta con el extracto oficial disponible de Parte II. La
verificación académica del registro de IA requiere cotejar el texto completo
de P1 §10.3 y recuperar las consultas originales que aún no están disponibles.

### 17.1 Problema

Separar el conocimiento del jugador del mapa precargado, mantener memoria de
puertas y exploración por antorcha, y navegar sin revelar información privada.
Cada paso de IR_A debe conservar eventos, tiempo, registro y retroceso propios.
El conocimiento debe sobrevivir al guardado y reconstruirse en la historia.

### 17.2 Alternativas consideradas

Son alternativas documentadas en research.md de 002, no experimentos adicionales:

| Tema | Decisión frente a alternativa documentada |
|---|---|
| Conocimiento | Arreglos por Sala.indice frente a atributos en Sala, árboles o recorridos de listas; separan mundo real y conocimiento con acceso directo. |
| Montículo | Eliminación perezosa frente a decrease_key con índice inverso; evita un índice auxiliar prohibido. |
| Búsqueda | Dijkstra compartido frente a duplicar algoritmos, con arreglos y tokens independientes para cada consumidor. |
| Navegación | Búsqueda inversa desde el destino y elección del primer vecino frente a reconstruir una ruta completa desde el jugador. |
| Medición | Benchmark independiente conservado e integrado mediante adaptador en --bench. |

No se atribuyen alternativas evaluadas sin fuente a las generaciones FR-010
ni a T046: son correcciones de integración verificadas por pruebas.


**Correspondencia entre plan e implementación final.** Se mantiene la arquitectura
central de [plan.md](specs/002-niebla-ir-a/plan.md): conocimiento indexado,
Dijkstra compartido, búsqueda inversa, movimientos ordinarios y separación MVC.
El cierre incorporó ajustes de integración respecto del diseño inicial:

| Diseño inicial / punto a precisar | Implementación final y justificación verificable |
|---|---|
| Inversos de celda sin barrera para escrituras posteriores | Generaciones solo en memoria_puertas: el fallo FR-010 mostraba que un inverso antiguo borraba una observación permanente. 2d42a8a y 12 pruebas específicas; integrado con captura C1 en 3c20c98. |
| Comentario de viaje tratado como marca inicial | Una marca antes de cada observación exterior efectiva, después de cancelar: 69dbc30 y test_comentarios_ir_a_002 cubren bloqueos sin movimiento y cancelación previa. |
| Reconstrucción limitada a órdenes e import de Orden desde controlador | T045/T046 aplica líneas intercaladas dentro del contexto de la candidata e importa Orden del modelo. Casos FR014 de test_historia_persistencia y test_carga_v4_002 verifican rollback, MVC y pergaminos posteriores. |
| Integración gráfica y atención entre pasos desarrolladas por etapas | Observador opcional y pergamino diferido ligado a Partida; QUIT prevalece. test_ir_a_grafico_002 verifica ausencia de órdenes desde el callback, cancelación y descarte de pendientes. |
| Benchmark inicialmente independiente | Adaptador --bench mapa_conocido en 75cc63e; cuatro pruebas de despacho y mediciones reproducibles. No se alteró Dijkstra para ajustar artificialmente tiempos. |

El plan vigente ya recoge varios de estos ajustes en sus notas finales; la tabla
los identifica como evolución histórica, no como incumplimientos funcionales
actuales. Se conserva el límite de 5 ms de SC-001; su aceptación oficial sigue
pendiente. Ninguna medición justificó reemplazar las estructuras elegidas.

### 17.3 Decisión adoptada

- **C1 de 002:** cambios indexados mediante Partida.cambiar y Registro.
  No confundir con C1 de 004: captura histórica, que ocurre antes de escribir.
- **Conocimiento:** N estados de sala y 4N memorias de puertas, contadores
  mantenidos y referencias al mapa conservadas. Salas: 0 desconocida, 1 avistada,
  2 explorada. Puertas: 0 desconocida, 1 abierta, 2 cerrada.
- **C2:** observar sincroniza ambos extremos sin explorar la vecina. Un cambio
  físico remoto no actualiza la memoria. Se conservan los consumidores de
  conocimiento y la invalidación selectiva del cazador de Mariano.
- **Antorcha y privacidad:** revela vecinas al entrar sin activar contenido
  remoto ni observar puertas remotas. mapa_conocido y salidas_visibles filtran
  identificadores, nombres y contenido no permitido. Las salidas tienen costo
  y destino None si no está explorado. MAPA no consume tiempo.
- **C3:** montículo binario propio y dijkstra_acotado sin estado global, con
  filtro, cota inclusiva y marcas/tokens por consumidor. Sin heapq, bisect,
  collections ni bibliotecas de rutas.
- **C4:** solo salas exploradas y puertas recordadas abiertas; minimiza costos
  y desempata por menor ID del primer vecino. IR_A no es orden ordinaria:
  recalcula antes de cada movimiento, nunca abre puertas y se interrumpe por
  llegada, enemigos vivos, daño, ausencia de ruta o final de partida.
- **Marcas:** tras callbacks y comprobaciones de cancelación, emite # ir a X
  inmediatamente antes de cada observación exterior efectiva, incluso sin
  movimiento. Se preservan el orden y las repeticiones legítimas.
- **Pygame:** V solicita destino; Escape cancela sin SALIR; R deja un único
  pergamino pendiente ligado a la partida y ejecutado fuera del callback.
  QUIT prevalece y descarta ese pendiente.
- **FR-010 de 004:** generaciones exclusivamente en memoria_puertas. El inverso
  restaura si su generación sigue vigente. Una observación permanente incrementa
  la generación incluso con el mismo valor. No protege otras listas ni contadores.
  Es distinto del FR-010 de privacidad de 002.
- **Persistencia v4 y T046:** foto_de copia conocimiento y guardar utiliza
  lineas_para_reconstruir(). Cargar aplica cada cadena con el callback de
  preparar_reconstruccion y valida dentro del contexto antes de publicar.
  Un error conserva la sesión anterior; no sustituye Registro ni sus arreglos.
  Orden se importa desde modelo.juego.orden, respetando MVC.
- **Formato:** N uint16, N estados, P uint16 y P entradas <HBB>. P cuenta
  posiciones de memoria, incluidos ambos extremos; ceros omitidos. Bloque de
  enemigos conservado; rango recuperado del catálogo. Rechazo explícito de v3.
  Validación estructural y comparación con replay; no hay CRC.
- **003:** cargar no vuelve a verificar resolubilidad; se conserva la condición
  `partida_nueva and ordenes_previas is None and exigir_versiones is None`.

### 17.4 Análisis de complejidad

| Operación | Complejidad y memoria |
|---|---|
| Consultar estado/puerta por índice y resumen | O(1); almacenamiento persistente O(N). |
| Consulta por ID | O(log N), búsqueda binaria propia. |
| Explorar | Proporcional a salas y salidas directamente reveladas; sin recorrido global. |
| Mostrar mapa completo | O(N), distinto de consultar una celda. |
| Registrar o invertir celda | O(1); pergamino O(cambios del grupo). |
| Dijkstra con eliminación perezosa | O((V' + E') log(V' + E')); en el grafo de grado acotado, O((V' + E') log V'). |
| Espacio del planificador | Arreglos persistentes O(N), más montículo temporal dependiente de las relajaciones. |
| Cargar | Replay de las líneas más validación y recuento O(N); mantiene identidad de arreglos. |

V' y E' son el subgrafo alcanzable permitido por el filtro. El costo de cada
paso puede depender de ese componente completo, no solo de la longitud de ruta.

### 17.5 Evidencia empírica y funcional

Resultados de ejecuciones anteriores sobre el contenido de 617f666; esta
edición documental no vuelve a ejecutar pruebas ni benchmarks:

- Cierre de integración: **42/42 módulos** por separado y **229/229 pruebas
  unittest** conjuntas. No son cantidades sumables ni cobertura porcentual.
- Validación posterior: **15/15 módulos** aprobados; arranque CLI offline real,
  mapa, movimiento, turno enemigo, historia, guardar y cargar. Ventana Pygame
  real de 1280 x 720 dibujada. No se realizó partida gráfica completa manual
  ni validación del servicio web real.
- Suites específicas: test_conocimiento, test_conocimiento_partida,
  test_niebla_ir_a, test_planificador_rutas, test_ir_a_compuesto,
  test_comentarios_ir_a_002, test_ir_a_grafico_002,
  test_fr010_generaciones_002 (12), test_guardado_v4_002 (15),
  test_carga_v4_002 (11), test_historia_persistencia y test_linea_tiempo.
- FR-010 cubre permanente antes/después de reversible, mismo valor, dos extremos,
  varios grupos/pergaminos, otras listas y ausencia de tiempo/grupos adicionales.
  T046 cubre marcas repetidas, observaciones sin movimiento, rechazo, rollback,
  import MVC y pergaminos posteriores a cargar.

Benchmark **sintético**, Windows 11, Python 3.13.18, semilla 20261110,
7 x 20 ejecuciones de rutas; preparación y calentamiento fuera del tiempo.
Comando: `python main.py --bench mapa_conocido`.

| Salas / conexiones | Planificar: media / máximo (ms) |
|---|---|
| 10 / 13 | 0,074946 / 0,478600 |
| 100 / 180 | 0,972790 / 1,944900 |
| 1000 / 1936 | 11,755245 / 15,624900 |

La media histórica aproximada de 8,548 ms corresponde a otra medición, no a
una línea base equivalente. Las métricas completas de consultas, exploración,
registro/inversión, pergamino y los cuatro benchmarks de regresión están en
DECISIONES.md de 002; no se atribuyen a una ejecución nueva de esta edición.


**Verificación posterior sobre 18b9364 (fuente: salida de la sesión de validación).**
Se repitieron dos veces, secuencialmente, mapa_conocido y los cuatro benchmarks
de T030, desde un temporal externo, con Python 3.13.18, Windows 11 compilación
26200, Intel Core i7-1255U y 34029162496 bytes de RAM. No se controlaron frecuencia
de CPU, temperatura, carga externa ni plan de energía. Los tiempos no son una
línea base controlada. Esta edición documental no ejecuta nuevamente los bancos.

Comando por subsistema, con el ejecutable del venv:
`<python-del-venv> -B -X utf8 <worktree>/main.py --bench <subsistema>`.
mapa_conocido: semilla 20261110, 7 x 20 muestras por operación de rutas,
7 lotes de un millón de consultas; viaje en línea con semilla 17 y 7 x 8 pasos.
Preparación y calentamiento excluidos del tiempo de mapa_conocido. Cache y
ordenamiento usan semilla 42; lista ordenada usa datos deterministas; guardado
usa la mediana de siete lecturas y un mapa sintético explícito.

| Salas / conexiones | Planificar corrida 1 media / máx. ms | Corrida 2 media / máx. ms |
|---|---|---|
| 10 / 13 | 0,138314 / 0,197400 | 0,077156 / 0,109100 |
| 100 / 180 | 1,119990 / 3,491500 | 1,030026 / 1,435200 |
| 1000 / 1936 | 13,312969 / 39,571500 | 8,024614 / 16,473800 |

Las huellas de mapa coinciden en ambas corridas: 1153647197, 1573915151 y
334788457. La diferencia de tiempos muestra variabilidad del entorno; en las
dos corridas los máximos de 1000 salas superan 5 ms. Esto caracteriza un riesgo
sintético, sin sustituir la cripta oficial de SC-001. El recálculo en línea de
1000 salas dio 6,057354 / 23,720400 y 4,857848 / 6,564100 ms (media / máximo);
solo mide planificación entre pasos, no el viaje completo.

**T030: contraste documentado Parte I / Parte II.** Los valores históricos se
conservan en 9.5, 10.5 y 11.5; no se sustituyen por estas cifras. Los tiempos
actuales proceden de las dos corridas anteriores. Diferencias porcentuales
redondeadas calculadas como (actual / anterior - 1) x 100; son descriptivas,
no una prueba causal de aceleración o ausencia de regresión.

| Operación y carga | Parte I | Parte II: corrida 1 / 2 | Diferencia y comparabilidad |
|---|---|---|---|
| Cache, tope 25, acierto (µs) | 1,725 | 0,728 / 0,623 | -57,8 % / -63,9 %. Misma operación y tamaño; entorno histórico no controlado. |
| Cache, tope 25, desalojo (µs) | 8,9 | 2,868 / 2,828 | -67,8 % / -68,2 %. Misma metodología de 20000 operaciones en el script disponible. |
| LRU / FIFO, tope 25, 20000 accesos | 83,8 % / 76,9 % | 83,8 % / 76,9 % en ambas | Mismo conteo y patrón documentado, 80 % de accesos calientes; respalda la política LRU en esta carga. |
| Lista ordenada, N=10000, búsqueda (µs) | 1,333 | 1,103 / 1,089 | -17,3 % / -18,3 %. Mismo tamaño y operación; lineal actual 118,066 / 106,214 µs. |
| Lista ordenada, N=10000, inserción masiva (ms) | 23,3 | 21,518 / 22,757 | -7,6 % / -2,3 %. Inserción individual actual 1879,409 / 1844,719 ms; ventaja masiva conservada. |
| Merge, N=5000 aleatorio (ms) | 11,3 | 8,604 / 8,040 | -23,9 % / -28,8 %. Algoritmo y escenario nominal equivalentes; comparación temporal no controlada. |
| Selector, N=5000 aleatorio (ms) | 13,2 | 10,437 / 8,578 | -20,9 % / -35,0 %. Mismas 55131 comparaciones merge y 6230815 inserción. |
| Guardado, N=5000, binario / JSON (KB) | 250,4 / 311,4 | 404,2 / 563,0 | Cargas diferentes: v4 agrega conocimiento y la estructura sintética evolucionó. No atribuir el crecimiento a regresión del codec. |
| Guardado, N=5000, cargar binario (ms) | 9,775 | 18,463 / 25,005 | NO equivalente entre versiones; se informa sin porcentaje de regresión. |
| Guardado, N=5000, una sala binaria (ms) | 0,0323 | 0,0451 / 0,1028 | En v4 sigue evitando cargar todo JSON: 5,302 / 7,032 ms actuales. No es carga histórica idéntica. |

Duraciones de cada proceso, corridas 1 / 2: mapa_conocido 17,964 / 12,230 s;
cache 17,718 / 16,450 s; lista_ordenada 8,223 / 7,299 s; ordenamiento
16,784 / 15,489 s; guardado 1,513 / 1,406 s. Todos terminaron con código 0.

Contra 69dbc30, Git no muestra cambios en los scripts de cache, lista_ordenada
u ordenamiento ni en sus tres estructuras. Esto respalda la equivalencia de
código con esa base disponible, pero no identifica por sí solo el entorno o el
commit exactos de las mediciones antiguas de Parte I. Guardado sí cambia:
el fixture añade N, estados y 4N memorias, también a la alternativa JSON.

**Conclusión técnica:** LRU mantiene sus aciertos, la búsqueda ordenada evita
recorridos lineales, la inserción masiva evita el costo cuadrático repetido y
merge conserva la ventaja para cargas grandes. El binario mantiene el acceso
por sala; la carga completa JSON sigue siendo más rápida en las mediciones v4.
Las estructuras siguen justificadas para esos usos, con sus costos conocidos.
T030 permanece pendiente porque su criterio vigente pide una línea base
equivalente para concluir ausencia de regresiones, no solo un contraste nominal.

**Pruebas de la misma verificación sobre 18b9364:** 42/42 módulos aprobados,
0 fallidos; ejecución conjunta 229/229 unittest, 0 fallos y 0 errores,
140,442 s. Comandos: `<python-del-venv> -B -X utf8 -m tests.<modulo>` para
cada tests.test_* y `-m unittest discover -s <worktree>/tests -t <worktree>`.
Son formas de ejecución distintas y no se suman como pruebas independientes.
No aparecieron archivos nuevos/eliminados dentro del repositorio.

### 17.6 Límites conocidos y cierre pendiente

- **SC-001:** falta identificar la cripta oficial y medir el cálculo/recálculo
  completo frente a 5 ms. Las 1000 salas sintéticas no son esa referencia.
- **T030:** benchmarks ejecutados; falta comparación con línea base equivalente.
- **T031:** pendiente cierre integral FR/SC y las evidencias anteriores. Los
  13 fallos históricos ya están corregidos; las menciones 35/39 en documentos
  de 002 describen su revisión anterior, no el estado funcional actual.
- N y P tienen límites uint16; v3 se rechaza. Logs antiguos con observaciones
  ausentes no permiten inventar marcas. No hay CRC implementado.
- Se conserva el cierre T050/T065 de Axel en 16.6 y sus mediciones originales.
- La bitácora de IA documenta las fuentes disponibles y distingue extractos
  auténticos de resúmenes retrospectivos. Para completar su evaluación académica
  falta cotejar P1 §10.3 y recuperar las invocaciones históricas identificadas
  como pendientes en PROMPTS_LLM.md, sección 8.4.

---

### 17.7 Mapa dibujado US5: disposición sin información oculta (2026-11-17)

**Ajuste visual:** niebla radial texturada cacheada por apertura/zoom, avistadas con capas alfa y «?» tenue, conexiones que se desvanecen y exploradas nítidas; no se dibujan formas en lo desconocido porque revelarían posiciones de salas (FR-026, FR-030, FR-031).

**Trazabilidad:** [especificación FR-025..FR-038, SC-006..SC-008](specs/002-niebla-ir-a/spec.md),
[plan de la ampliación US5](specs/002-niebla-ir-a/plan.md#ampliacion-us5-mapa-dibujado-fr-025fr-038-sc-006sc-008)
y [tareas T032..T042](specs/002-niebla-ir-a/tasks.md).

**Problema.** El mapa anterior presentaba un listado de exploradas; las avistadas
solo aparecían como destinos desconocidos. Había que dibujar ambas sin consultar
topología desconocida, actualizar observaciones de puertas ni alterar la partida.
La privacidad incluye posiciones y orden: cambiar ids ocultos de avistadas no
puede modificar el dibujo ni los textos.

**Alternativas.** Usar la disposición de la cripta completa violaría FR-031.
Filtrar la lista de estados en cada apertura cuesta O(N), aunque haya pocas
conocidas; se elige ese barrido para no modificar el almacenamiento compartido
del conocimiento. Solo después de filtrar se accede a los objetos explorados.
Reservar una matriz rectangular para la ocupación
puede requerir espacio cuadrático en K. Una ListaOrdenada propia evita tablas
hash pero desplaza O(K) elementos al insertar. Se comparó esta última con un
índice AVL propio sobre arreglos contiguos, para el mismo layout y la misma entrada.
No se añadieron dependencias ni estructuras prohibidas.

**Decisión revisada.** Por instrucción expresa del usuario se restaura
`modelo/juego/conocimiento.py` byte por byte desde f600fdd. `estado_salas` vuelve
a ser una lista simple: se retiran la subclase, sus enlaces y el directorio de
exploradas. Así el mapa no añade comportamiento a las escrituras, segmentos o
inversos del conocimiento ni memoria persistente adicional. No cambian el formato
v4, el log, las acciones, las puertas ni el retroceso. La foto recorre la lista
de estados una vez por apertura; solo cuando una celda vale EXPLORADA accede
al objeto correspondiente. Nunca consulta ids, nombres, topología o contenido
de objetos desconocidos para filtrar o posicionar casillas. ListaOrdenada
se construye en bloque para deduplicar extremos por índice. Esos índices solo
identifican extremos; no deciden el orden público. Las avistadas salen con id y
nombre None y sin salidas propias.

El cálculo puro recibe esa foto y la posición del jugador. La BFS usa N,S,E,O y
exploradas por menor id dentro de cada nivel. La asignación de casillas prioriza
exploradas por menor id, luego avistadas por su primera salida reveladora al recorrer
exploradas por id y direcciones N,S,E,O. Las avistadas se proponen desde la posición
final de la explorada que las revela. Los anillos Manhattan prueban primero
N,S,E,O y después, para a=1..r-1, (a,-(r-a)), (a,r-a), (-a,r-a), (-a,-(r-a)).
El índice AVL almacena ocupación por (x,y); el orden nunca usa ids ocultos.
Las conexiones desplazadas conservan dirección, costo y memoria. La consulta
histórica y el contrato anterior de mapa conocido se conservan.

Consola representa ASCII por bloques y tabla; la ventana usa primitivas y encuadre
local para desplazamiento, zoom y recentrado, sin recalcular posiciones por cuadro.
Se conserva M y el botón existentes. Una protección en la selección de sprites
permite que la vista parcial usada por la regresión histórica funcione sin catálogo.

**Cambio ajeno al mapa: guarda de sprites.** El test
`tests/test_historia_interfaces.py:189` llama `_dibujar_enemigos` con una vista
fabricada mediante `object.__new__` por `tests/test_gui.py:188`, sin ejecutar
el constructor ni crear `sprites`. La selección original de sprites en
`f600fdd:vista/vista_pygame.py:1735` evaluaba
`if por_nombre != "" and self.sprites.tiene(por_nombre):` y lanzaba AttributeError.
Se reprodujo el mismo test sustituyendo solo ese método por el de f600fdd cargado
en memoria, sin editar archivos: un error por atributo `sprites` inexistente.
Con la guarda actual, el mismo test pasa. Ambos archivos de pruebas tienen diff
vacío contra f600fdd; `git blame` sitúa la línea causante en ese commit previo.
Por tanto, se conserva la guarda como corrección de un fallo anterior del repositorio,
expresamente ajena al mapa; no se atribuye el fallo al nuevo dibujante.

**Complejidad.** K = exploradas + avistadas, E = salidas conocidas y C = posiciones
candidatas examinadas; N es la longitud de la lista de estados de conocimiento.
Filtrar esa lista cuesta O(N) una vez por apertura. La foto compacta y el layout
solo contienen K casillas y E salidas conocidas. La BFS sin ordenar es O(K+E);
el layout puro cuesta O((K+E+C) log K) y la apertura completa cuesta
O(N + (K+E+C) log K), con O(K+E) espacio temporal adicional.
No se afirma independencia temporal de N para la apertura ni linealidad estricta
del layout completo. C puede crecer con las
colisiones. La alternativa ListaOrdenada agrega hasta O(K²) por desplazamientos.
Se eliminan los dos arreglos persistentes de enlaces por índice. El barrido no
reserva otro arreglo de tamaño N ni se repite por fotograma. Mostrar ASCII depende
además del área dibujada y sus bloques; repintar la GUI recorre las casillas y enlaces
conocidos, sin reconstruir su disposición.

**Evidencia de medición.** Comando:
`venv\Scripts\python.exe main.py --bench mapa_conocido`, salida 0, 35,5 s en la
corrida posterior a restaurar la lista simple. Python 3.13.18, Windows 11
(10.0.26200). Entrada sintética determinista:
cuadrícula de K exploradas, ancho floor(sqrt(K)), sala actual primera, costos
generados de 1 a 7; E cuenta salidas dirigidas. Calentamiento y construcción de
entrada excluidos. Mediana de cinco muestras con GC normal y sin trazador; pico
de memoria de una llamada separada con tracemalloc, excluyendo la entrada.
Cada alternativa se valida contra el mismo resultado antes de medir.

| K | E | AVL, ms | ListaOrdenada, ms | AVL, pico KiB | ListaOrdenada, pico KiB | C |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 26 | 0,089 | 0,225 | 8,4 | 7,6 | 10 |
| 100 | 360 | 1,264 | 1,097 | 78,5 | 70,5 | 100 |
| 1000 | 3872 | 22,125 | 46,742 | 865,1 | 758,6 | 1000 |
| 5000 | 19716 | 123,594 | 759,674 | 4444,2 | 3872,0 | 5000 |

En 5000 conocidas, AVL fue aproximadamente 6,15 veces más rápido y usó un pico
aproximadamente 14,8 % mayor. En tamaños pequeños no hay ventaja consistente.
Esta evidencia respalda el intercambio entre tiempo y memoria, no una mejora
universal. El benchmark previo de rutas continúa ejecutándose antes del layout;
sus mediciones sintéticas no certifican SC-001 oficial.
El layout puro no se modificó en esta revisión: estas diferencias respecto de la
corrida anterior son nuevas mediciones, no una mejora o regresión atribuible al
barrido de estados. El benchmark excluye la preparación de la foto y, por tanto,
no mide el costo O(N) incorporado a la apertura.

Se repitieron las 43 suites mediante el mismo script de auditoría: cada módulo
se ejecutó con `venv\Scripts\python.exe -m tests.<modulo>` desde una carpeta
temporal externa, SDL_VIDEODRIVER=dummy y bytecode deshabilitado. Las 43 salieron
con código 0, con 168,937 s acumulados. La tabla completa está en tasks.md,
revisión posterior del almacenamiento. Las 21 pruebas del mapa siguen pasando
sin modificar el archivo de pruebas para aceptar la restauración.

**Correspondencia con el plan y límites.** Revisa la ampliación US5 de fase B:
se conserva foto compacta, BFS, prioridades, anillos, AVL y comparación con
ListaOrdenada, pero se retira el directorio de exploradas para conservar intacto
el almacenamiento original. Esta decisión y el costo O(N) del barrido solicitado
están reflejados en plan.md y T034/T043/T044. Amplía el plan
original de 002, que mostraba un listado O(N). La spec no se modifica; el barrido
autorizado no permite acreditar independencia temporal de N para preparar la foto.
La medición anterior es del layout puro; excluye la foto, la impresión y el dibujo
gráfico. No es una prueba de estrés del peor caso de colisiones: aquí C=K. Las
pruebas de aceptación cubren colisiones y cambios de ids ocultos e índices,
desconocidas adicionales y ausencia de iteración de objetos de salas desconocidas.
La validación gráfica se hace con SDL dummy; los pasos para una revisión humana
de la ventana están en README.md. No se declara realizada esa revisión manual.
Los pendientes anteriores SC-001, T030 y T031 no se cierran por esta ampliación.

---

# Parte de Axel — Inventario, retroceso, replay y puntajes

## 12. §4.5 Inventario

### 12.1 Problema

El inventario cambia en casi todas las acciones del jugador. Las operaciones que el juego hace de verdad son:

1. Recorrer hacia adelante y hacia atrás desde el objeto que se está viendo (teclas W/S).
2. Soltar, usar o equipar el objeto que se está viendo, que puede estar en cualquier posición. El costo no debe depender de esa posición.
3. Equipar mueve el objeto al frente del orden real.
4. Mostrar una vista ordenada por peso, valor o nombre sin cambiar el orden real.
5. Rechazar recoger cuando se llega a `inventario_max`.
6. Para el pergamino: devolver un objeto quitado exactamente a su posición anterior, aunque mientras tanto se hayan quitado o movido otros.

El tamaño es pequeño (`inventario_max` es una decena en las criptas publicadas), pero el requisito es sobre la forma del costo, no sobre el tamaño.

### 12.2 Alternativas consideradas

- **Arreglo (`list` con `del` e `insert`).** Es la más simple y recorre rápido, pero quitar o insertar en medio desplaza los elementos siguientes: el costo depende de la posición.
- **Pila (`list` usada solo por su tope).** Equipar al frente es barato si el frente es el tope, pero para llegar a un objeto del medio hay que sacar y volver a meter todo lo que está encima. No se puede recorrer sin vaciarla.
- **Lista doblemente enlazada con cursor.** Es la elegida.

### 12.3 Decisión

- **Estructura:** `ListaDoble` (`lista_doble.py`), con nodos centinela al inicio y al final, y un **cursor** que apunta al nodo que se está viendo. `Inventario` (`inventario.py`) la envuelve con la capacidad y la vista ordenada.
- **Recorrer:** el cursor sigue los enlaces `siguiente` y `anterior`.
- **Soltar el objeto visto:** se desengancha el nodo del cursor; no se busca.
- **Equipar:** se quita el nodo y se engancha después del centinela de inicio.
- **Vista ordenada:** se copian las referencias a una lista nueva y se ordena con nuestro `ordenar` (§4.9). La lista enlazada no se toca.
- **Volver a su sitio (retroceso):** cada nodo recibe al crearse una **etiqueta de orden** fija y única (1, 2, 3… al final; 0, −1, −2… al frente). `quitar` devuelve el nodo y su vecino anterior como pista; `restaurar` lo reinserta junto a la pista si sigue siendo válida y, si no, busca su lugar por la etiqueta. Recordar solo "quién iba delante" no alcanza: con dos pergaminos seguidos ese vecino también pudo haberse quitado.
- **Capacidad:** `recoger` consulta `lleno()` antes de actuar y rechaza sin gastar tiempo (Apéndice B).

### 12.4 Análisis de complejidad

Con n objetos:

| Operación | Costo | Frecuencia |
|---|---|---|
| Avanzar o retroceder el cursor | O(1) | Cada tecla W/S |
| Soltar, usar o equipar el objeto visto | O(1) | Cada acción sobre un objeto |
| Mover al frente (equipar) | O(1) | Cada equipar |
| Recoger (agregar al final) | O(1) | Cada recoger |
| Quitar un objeto que no es el visto | O(n), lo busca | Solo al reconstruir desde un log |
| Restaurar con pista válida | O(1) | Cada retroceso que toque el inventario |
| Restaurar sin pista válida | O(n), por la etiqueta | Raro: varios retrocesos seguidos |
| Vista ordenada | O(n) copiar más el costo de `ordenar` | Cuando el jugador la pide |
| Recorrer todo | O(n) | Al dibujar la lista |

### 12.5 Evidencia empírica

`bench_inventario.py`, microsegundos por operación (mejor de 5 corridas).

**Soltar el objeto visto y deshacer:**

| n | posición | lista (cursor) | lista (sin cursor) | arreglo | pila |
|---|---|---|---|---|---|
| 10 | medio | 1.17 | 1.63 | **0.14** | 1.80 |
| 100 | último | 1.08 | 6.86 | **0.13** | 26.01 |
| 1000 | medio | 1.16 | 30.68 | **0.54** | 107.61 |
| 10000 | primero | 1.11 | 1.27 | 7.97 | **0.56** |
| 10000 | medio | **1.22** | 310.27 | 4.12 | 1062.96 |
| 10000 | último | 1.18 | 612.22 | **0.14** | 2331.25 |

**Equipar (al frente) y deshacer:** la lista con cursor se mantiene entre 2.34 y 3.08 µs en todos los tamaños y posiciones. La pila llega a 2167 µs con n=10000 en la última posición.

**Recorrer todo el inventario:** lista 1.16 µs con n=10 y 693 µs con n=10000; arreglo 0.18 µs y 82 µs. Recorrer es O(n) en las dos, y el arreglo es entre 6 y 9 veces más rápido.

Lectura de los resultados:

- La lista con cursor es la única con un tiempo plano en cualquier tamaño y posición (≈1.1 µs al soltar y ≈2.5 µs al equipar). Es lo que pide §4.5.
- Sin cursor, la lista tiene que buscar el objeto y crece con la posición: así se comportaría si no se guardara el objeto que se está viendo.
- El arreglo es más rápido en números absolutos con n pequeño, porque el desplazamiento lo hace C sobre memoria contigua. Pero su costo depende de la posición: con n=10000, quitar del primero cuesta 7.97 µs y del último 0.14 µs. Con un inventario de decenas de objetos esa diferencia no se nota, pero no cumple la forma de costo que exige el enunciado.
- La pila es la peor para llegar a un objeto en medio o al fondo; solo gana cuando el objeto está en el tope (primera posición).
- Pruebas de corrección: `test_inventario.py` (capacidad, recorrer, inventario vacío, soltar en cada posición, equipar y deshacer, restaurar con el vecino ya quitado, dos pergaminos seguidos, vista ordenada estable y una prueba aleatoria de deshacer intervalos) y `test_inventario_partida.py`.

### 12.6 Límites conocidos

- Con los tamaños reales el arreglo sería más rápido; la lista se eligió por la garantía de costo independiente de la posición, no por velocidad absoluta.
- Recorrer la lista es entre 6 y 9 veces más lento que recorrer un arreglo. Ocurre al dibujar el inventario y con decenas de objetos tarda microsegundos.
- Quitar un objeto que no es el del cursor es O(n). La interfaz siempre actúa sobre el objeto visto; la búsqueda solo ocurre al reconstruir una partida desde un log.
- Cada nodo ocupa más memoria que una casilla de arreglo (valor, dos enlaces, etiqueta y bandera). Con decenas de objetos es despreciable.
- Si `inventario_max` llegara a miles, la vista ordenada y el recorrido para dibujar crecerían linealmente.

---

## 13. §4.6 Pergaminos de retroceso e historial reversible

### 13.1 Problema

El pergamino deshace la última acción del jugador y **todo lo que pasó después hasta su siguiente decisión**: turnos de enemigos, veneno, rearmes, reloj, agenda, rastro, vida, inventario, suelo, puertas y trampas (§2.11). Hasta 5 acciones hacia atrás, descartando la más antigua. No se puede copiar el estado completo. Los pergaminos quedan fuera: el usado no vuelve y recoger o soltar uno tampoco se deshace. La caché tampoco se revierte porque es infraestructura.

Operaciones reales: registrar un cambio ocurre muchas veces por ciclo (cada golpe, cada evento agendado, cada movimiento); deshacer ocurre pocas veces (solo al usar un pergamino).

### 13.2 Alternativas consideradas

- **Copia completa del estado antes de cada acción** (`copy.deepcopy` de mapa, jugador, inventario, agenda, reloj y azar). Es la más fácil de programar y nunca olvida un dato. Está prohibida por §4.6, pero se midió para justificar el descarte.
- **Instantánea solo de lo que puede cambiar** (vidas, posiciones, inventario…). Hay que saber de antemano qué cambia, y la agenda contiene funciones que no se pueden copiar como datos. Se descartó por razonamiento.
- **Registro de inversos.** Es la elegida.

### 13.3 Decisión

- **Registro de inversos** (`registro.py`). Cada cambio de estado pasa por un punto único de `Partida` (`cambiar`, `programar`, `cancelar`, `_lista_agregar`, `_lista_quitar`, `_inv_*`), que antes de cambiar el dato anota en el registro **una función que lo deshace** (por ejemplo, "volver a poner vida = 20").
- **Grupos por acción:** `_accion` abre un grupo con la acción del jugador y lo cierra cuando vuelve a ser su turno; todo lo que ocurre en medio queda en el mismo grupo. Deshacer ejecuta los inversos del grupo **en orden inverso**.
- **Límite de 5:** los grupos se guardan en una `PilaAcotada`, un **arreglo circular de 5 casillas**. Apilar con la pila llena sobrescribe el grupo más antiguo en O(1), sin desplazar nada.
- **Agenda:** agendar un evento anota "invalidarlo"; cancelarlo anota "volver a validarlo"; sacar un evento anota "volver a meterlo".
- **Azar:** `AzarReversible` guarda el estado del generador la primera vez que se usa en un grupo, así repetir una acción después de retroceder da el mismo resultado.
- **Pergaminos:** sus movimientos de inventario y suelo no registran inverso. El pergamino usado se quita sin registrar justo antes de deshacer. Usarlo no llama a `_accion`: no consume tiempo ni cuenta como acción, por eso dos pergaminos seguidos deshacen dos acciones distintas.
- **Coordinación con el motor (Mariano):** el contrato es que el motor no cambia estado directamente, sino por esos puntos únicos.

### 13.4 Análisis de complejidad

Con c = cambios ocurridos en el ciclo (acción del jugador más lo que actúa hasta su siguiente decisión):

| Operación | Costo | Frecuencia |
|---|---|---|
| Registrar un cambio | O(1) | Muchas por ciclo |
| Cerrar un grupo y apilarlo | O(1), descarta el más antiguo sin desplazar | Una por acción |
| Deshacer una acción | O(c) | Solo al usar un pergamino |
| Memoria del historial | O(suma de c de las 5 últimas acciones) | — |
| Alternativa: copia completa | O(tamaño de todo el estado) **en cada acción** | — |

El costo del registro sigue a **lo que cambió**, no al tamaño de la cripta.

### 13.5 Evidencia empírica

`bench_historial.py`. A = registro de inversos (elegido); B = copia completa (descartada, medida directamente).

| Caso | Salas | Activos | Eventos | A ciclo (ms) | A deshacer (ms) | A historial (KB) | B 1 copia (ms) | B 1 copia (KB) | B 5 copias (KB) |
|---|---|---|---|---|---|---|---|---|---|
| Típico | 20 | 10 | 18 | 0.100 | 0.063 | 83.4 | 1.53 | 51.5 | 257.3 |
| Típico | 200 | 10 | 18 | 0.098 | 0.066 | 83.4 | 10.42 | 402.6 | 2012.9 |
| Típico | 1000 | 10 | 18 | 0.079 | 0.050 | 81.0 | 52.65 | 1971.4 | 9857.0 |
| Peor caso | 200 | 200 | 398 | 4.127 | 3.379 | 1700.7 | 14.18 | 473.5 | 2367.4 |
| Peor caso | 1000 | 1000 | 1998 | 26.161 | 12.544 | 9557.4 | 87.20 | 2342.6 | 11713.2 |

- En el caso típico, el costo de A es el mismo con 20 que con 1000 salas (≈0.1 ms por ciclo, ≈80 KB de historial). B crece con la cripta: de 1.5 a 52.7 ms **por acción** y unos 9.9 MB para 5 copias.
- En el peor caso (todos los enemigos actuando a la vez) A crece porque cambia mucho, pero sigue por debajo de B en tiempo (26 contra 87 ms con 1000 activos).
- Pruebas: `test_partida.py` (retroceso no toca los pergaminos, recoger pergamino dentro del intervalo) y `test_replay_puntajes.py` (pila acotada descarta lo más antiguo, el pergamino restaura también el azar). También se verificó jugando: dos pergaminos seguidos vuelven de la sala 3 (tiempo 200) a la 1 (tiempo 0).

### 13.6 Límites conocidos

- Si muchos actores cambian en el mismo ciclo, el historial guarda muchos inversos: en el peor caso de 1000 activos ocupa 9.6 MB. En la laptop de prueba (Python 3.14) eso es apenas un 18 % menos que 5 copias completas (11.7 MB); en una corrida anterior con Python 3.10 en otra laptop las 5 copias ocupaban 21.3 MB y el historial 9.2 MB: el tamaño de las copias depende de la versión de Python. Cada inverso es una función de Python, que pesa más que el dato que restaura.
- Funciona solo si **todo** cambio pasa por los puntos únicos. Un cambio hecho directamente sobre un atributo no se revertiría; las pruebas aleatorias de deshacer ayudan a detectarlo.
- El historial no se guarda en disco (son funciones, no datos): al cargar una partida empieza vacío.

### 13.7 Revisión §5.6 (Parte II)

Medición del 2026-11-17 con `venv\Scripts\python.exe -B -X utf8 -u main.py --bench historial`, salida 0, 45.0 s. Línea de entorno impresa por el bench:

```text
Entorno: Python 3.13.18 | Windows-11-10.0.26200-SP0
```

**Antes y después en el mismo entorno.** La referencia «I original» repite las 30 esperas del escenario original, con trolls guardianes y regeneración, costo uniforme 100 y sin captura C1. Es la carga de Parte I ejecutada sobre el motor actual, no una ejecución del código histórico. La carga «II» reemplaza los trolls por cazadores, asigna costos simétricos variables entre 40 y 180 usando exclusivamente `partida.azar`, enciende una antorcha mediante una acción ordinaria y realiza 10 movimientos directos y 19 pasos reales de `ir a` hacia vecinas ya exploradas. Hubo 16 entradas mientras la antorcha seguía encendida; su apagado conserva la duración ordinaria. El viaje observa puertas y recalcula por el controlador real; se detiene ante enemigos según sus reglas, sin omitir el paso ya ejecutado.

Ambas cargas usan **semilla 3**, el mismo corredor y número de salas, n−1 enemigos incorporados y **9 activos inicialmente**. La preparación carga todo el contenido y amplía la vida del jugador para sostener la carga sin curaciones durante la medición; agrega antorcha y pergamino al inventario mediante el punto único. Esa preparación queda fuera del tiempo. «II sin C1» ejecuta exactamente las mismas acciones que «II con C1», pero sin conectar la historia; permite observar el sobrecosto integrado de captura, deltas, proyección y checkpoints, conservando los inversos del pergamino. Con C1 se usa el K vigente, **10**, sin cambiar la decisión de 004.

Una pasada de calentamiento precede a tres repeticiones independientes: **90 muestras de acciones y 3 retrocesos por fila**, con `perf_counter_ns` y sin `tracemalloc`. Cada muestra completa una sola acción aceptada; el tiempo incluye su ciclo de eventos y, cuando corresponde, planificación/observación de IR_A, captura C1 y creación de checkpoint. Los retrocesos usan `Partida.usar_pergamino`, no el deshacer directo del registro de la tabla histórica. Se comparan trazas por valor de todas las acciones y del retroceso entre repeticiones; con C1 también se comparan los deltas y se exige que la historia actual coincida con la partida. Las variantes II con/sin C1 deben dar el mismo estado final. La pasada de memoria debe producir el mismo estado que la cronometrada. No hay HTTP real ni vista.

**Memoria:** otra partida y otra pasada, con recolección antes de empezar el trazador y al terminar las acciones. Se excluye la preparación del mapa, contenido e inventario; se incluye la inicialización C1 y su checkpoint cero cuando corresponde. Los KiB retenidos/pico abarcan **todas las asignaciones de la carga**: inversos de las últimas cinco acciones, agenda, bitácora y auxiliares, y con C1 además normalizador, proyección, deltas y checkpoints desde el inicio. No son la memoria exclusiva del historial de cinco acciones de 13.5 ni la memoria total del proceso. El pico incluye asignaciones temporales y la recolección final.

| Salas | Carga | Acción media (ms) | Acción máxima (ms) | Pergamino medio (ms) | Pergamino máximo (ms) | Retenida (KiB) | Pico (KiB) |
|---:|---|---:|---:|---:|---:|---:|---:|
| 20 | I original (antes) | 0.0728 | 0.3861 | 0.0452 | 0.0530 | 110.0 | 125.8 |
| 20 | II sin C1 (control) | 0.3154 | 0.6915 | 0.0402 | 0.0416 | 209.0 | 236.4 |
| 20 | II con C1 (después) | 0.6652 | 1.1679 | 0.3989 | 0.4849 | 484.8 | 512.1 |
| 200 | I original (antes) | 0.1196 | 2.0819 | 0.0608 | 0.0757 | 110.0 | 125.8 |
| 200 | II sin C1 (control) | 1.2934 | 3.0340 | 0.0584 | 0.0901 | 209.1 | 236.4 |
| 200 | II con C1 (después) | 1.3679 | 3.3707 | 0.2657 | 0.2842 | 1003.3 | 1018.2 |
| 1000 | I original (antes) | 0.0715 | 0.0983 | 0.0490 | 0.0558 | 110.0 | 125.8 |
| 1000 | II sin C1 (control) | 5.1033 | 6.2970 | 0.0430 | 0.0449 | 209.1 | 236.4 |
| 1000 | II con C1 (después) | 5.5215 | 7.2751 | 0.3234 | 0.3323 | 3340.6 | 3355.5 |

Conteos al completar las 30 acciones de la pasada de memoria, antes de usar el pergamino; fueron iguales en los tres tamaños:

| Carga | Inversos en los últimos 5 grupos | Deltas desde el inicio | Deltas de conocimiento | Checkpoints | Pasos IR_A / entradas iluminadas |
|---|---:|---:|---:|---:|---:|
| I original | 246 | 0 | 0 | 0 | 0 / 0 |
| II sin C1 | 343 | 0 | 0 | 0 | 19 / 16 |
| II con C1 | 343 | 980 | 144 | 4 | 19 / 16 |

Los deltas de conocimiento cuentan escrituras de `estado_salas`, `memoria_puertas` y contadores de exploradas/avistadas; no son 144 salas distintas. Los cuatro checkpoints son el inicial y los de las acciones 10, 20 y 30. El bench exige costos distintos, cantidad de activos prevista y cálculos reales del planificador cazador; no basta con añadir enemigos dormidos a la entrada.

**Conclusión sobre la decisión.** El registro de inversos sigue siendo adecuado para esta carga: conserva los cinco grupos del pergamino, con **343 inversos** tanto con C1 como sin C1, y el retroceso integrado con 1000 salas dio **0.3234 ms de media y 0.3323 ms de máximo**. No se sustituyó por copias completas ni se modificó ninguna estructura del juego. El trabajo nuevo sí tiene costo: en 1000 salas la acción pasa de **0.0715 a 5.5215 ms de media**, y la memoria incremental retenida de **110.0 a 3340.6 KiB**. La comparación controlada dentro de II da **0.4182 ms adicionales de media** al activar C1 (5.5215 frente a 5.1033), con máximos de 7.2751 frente a 6.2970 ms. Todos los máximos de acciones de esta comparación estuvieron por debajo de 20 ms.

Ese aumento no se atribuye íntegramente al registro de inversos: la carga II incorpora búsqueda y observación de rutas, y C1 conserva la historia completa y copias periódicas de proyección. El código del cazador recorre los enemigos incorporados para obtener el rango activo; los checkpoints copian la proyección cuyo tamaño también crece con el mapa. Esta medición no separa sus tiempos por función. Que los conteos de inversos y deltas sean iguales al crecer n no implica tiempo ni memoria constantes para el conjunto de Parte II.

**Comparabilidad y límites.** Se mantienen intactas las cifras históricas de 13.5, medidas con otro Python y con una extracción distinta de memoria. La primera tabla del bench sigue ofreciendo la alternativa B descartada, pero se retiró su `dict` de memoización y se usa el AVL propio mediante `MemoCopias`; sus tiempos incluyen ese índice y **no equivalen a los de B históricos**, ni se usan aquí para atribuir una aceleración al registro. La copia de referencia conserva el mismo límite de objetos compartidos; no constituye una implementación de retroceso ni una nueva decisión del juego. La comparación §5.6 anterior no utiliza esa referencia B. Las trazas y conteos son reproducibles por semilla; los tiempos y picos varían con GC y carga del sistema. Son 30 acciones sintéticas con 9 activos, no una certificación con miles de acciones, todos los enemigos activos, la cripta oficial o consultas históricas de menos de 50 ms.

---

## 14. §4.11 Bitácora de partida y reproducción

### 14.1 Problema

Cada acción del jugador debe quedar en un archivo de texto de solo anexado, con un encabezado que tenga id y versión de cripta, versión de catálogo y semilla. `--replay` debe reproducir la partida completa sin interacción y sin vista. Si la versión del log ya no está disponible y no hay copia local, hay que informarlo en vez de reproducir contra datos distintos. Es el mecanismo principal para reportar errores en la evaluación.

Operaciones reales: anotar una orden por cada acción del jugador (decenas a cientos por partida) y, pocas veces, leer el log completo para reproducirlo.

### 14.2 Alternativas consideradas

**Qué registrar**

- **El estado después de cada acción.** Permitiría saltar a cualquier punto, pero repite el problema de copiar el estado y el archivo crece mucho.
- **Las órdenes del jugador más la semilla.** Es la elegida: como el juego es determinista (§2.6), la misma semilla, la misma versión y las mismas órdenes producen la misma partida.

**Cuándo escribir**

- **Guardar las órdenes en memoria y escribirlas al terminar.** Si el programa se cae, se pierde el log justo cuando más se necesita.
- **Anexar cada orden y vaciar el búfer (`flush`) de inmediato.** Es la elegida.

### 14.3 Decisión

- **Formato** (`bitacora_partida.py`): primera línea con una marca y versión del formato (`CRIPTA-LOG 1`); luego `clave=valor` para `id_cripta`, `version_cripta`, `version_catalogo`, `semilla`, `jugador` y `fecha`; una línea `---`, y después una orden por línea. Los cuatro primeros campos son obligatorios: si falta alguno, el log se rechaza.
- **Escritura:** el archivo se abre en modo `"a"` y cada orden se escribe y se vacía al disco en el momento.
- **Qué se anota:** solo las órdenes aceptadas que cambian la partida. Mirar el inventario, la ayuda o los puntajes no se anota.
- **Reproducción** (`reproductor.py`): sin vista; usa el `Controlador` con `vista=None` y le entrega las órdenes del log desde una `ColaFIFO`. Antes de reproducir decide qué datos usar:
  1. Si las versiones actuales coinciden con las del log, se usa la fuente actual.
  2. Si no, pero hay una copia local de esa versión en `datos_cripta`, se usa la copia (`FuenteAlmacen`).
  3. Si no, informa **"no se puede garantizar una reproducción fiel"** y no reproduce.
  Si una orden del log se rechaza al reconstruir, también lo informa en vez de seguir.
- **Últimas 20 partidas:** al crear un log nuevo se borran los más antiguos (`podar_logs`), y la lista de repeticiones ordena por fecha con nuestro `ordenar`.

### 14.4 Análisis de complejidad

Con k órdenes en la partida:

| Operación | Costo | Frecuencia |
|---|---|---|
| Anotar una orden | O(1) más una escritura y un `flush` | Cada acción del jugador |
| Leer y validar el log | O(k) | Al reproducir |
| Reproducir | O(k × costo de un ciclo) | Al reproducir |
| Podar logs | O(L log L) para ordenar L logs por fecha | Al crear un log nuevo |

### 14.5 Evidencia empírica

No hay un bench de §4.11 en `--bench`; la evidencia es de corrección:

- `test_replay_puntajes.py`: el log tiene el encabezado y solo las órdenes aceptadas; el replay reproduce **exactamente** la partida (misma foto final); con una versión nueva usa la copia local o se niega; detecta divergencias y logs dañados; `--replay` y `--bench` no crean la vista.
- Prueba manual: al reproducir un log real, el resultado (acciones, derrotados y tiempo) coincidió con la línea de la tabla de puntajes de esa partida.
- Prueba manual de versión incompatible: al cambiar `version_cripta` en una copia del log, el programa mostró el mensaje y no reprodujo.

### 14.6 Límites conocidos

- El `flush` en cada orden es más lento que escribir al final; se acepta porque ocurre una vez por acción del jugador, a escala humana. No se midió.
- Reproducir cuesta lo mismo que jugar la partida de nuevo: no se puede saltar a la mitad sin reproducir todo lo anterior.
- La reproducción fiel depende de que la versión del log esté publicada o guardada en `datos_cripta`. Si se borra esa carpeta y la versión cambió en el servicio, el log ya no se puede reproducir (y el programa lo informa).
- Solo se conservan los últimos 20 logs.
- Falta un bench propio para cuantificar el costo de anotar y de reproducir.

---

## 15. Tabla de puntajes (§2.12)

### 15.1 Problema

Al terminar una partida (victoria o derrota) hay que registrar nombre, id y versión de la cripta, acciones, enemigos derrotados y tiempo final, y poder mostrar la tabla.

### 15.2 Alternativas consideradas

- **Mantener el archivo siempre ordenado** (insertar cada registro en su lugar). Cada partida obliga a reescribir el archivo.
- **Anexar una línea por partida y ordenar al mostrar.** Es la elegida.

### 15.3 Decisión

`puntajes.py`: `TablaPuntajes.registrar` anexa una línea separada por tabulaciones (nombre, cripta, versión, resultado, acciones, derrotados, tiempo y fecha). `listar` lee el archivo, ignora las líneas dañadas y ordena con `ordenar` (§4.9). El criterio de orden **no lo fija el enunciado**; lo decidió el grupo: primero victorias, luego menor tiempo y luego menos acciones.

### 15.4 Análisis de complejidad

Registrar es O(1) (una línea al final). Mostrar es O(m) para leer más el costo de `ordenar` con m registros; como la tabla crece de una en una y es pequeña, el selector suele elegir inserción.

### 15.5 Evidencia empírica

`test_replay_puntajes.py` (los puntajes se registran y se ordenan; ganar registra el puntaje y cierra el log). En una prueba manual con el paquete offline se registraron una victoria y una derrota con todos los campos.

### 15.6 Límites conocidos

- Con miles de partidas, ordenar en cada consulta sería más costoso que mantener el archivo ordenado.
- El nombre del jugador no puede contener tabulaciones.

---

## 16. Línea de tiempo (004, Parte II)

**Responsable:** Axel. **Referencias:** [especificación](specs/004-linea-de-tiempo/spec.md) y [plan](specs/004-linea-de-tiempo/plan.md). Decisiones de FR-001..014, FR-019/020 y evidencia de SC-001..005; T064.

**Coincidencia con plan.md original:** Parcial: se conservan captura C1, deltas, proyección aislada, checkpoints periódicos, índices y recorte del plan 004 original (`a7a764f`), visibles en `Registro` y `LineaTiempo`. El plan proponía K=50 solo como candidato y exigía medir: el código fija `K_DEFECTO = 10`. Con D=1000, las dos corridas de 16.5 dieron máximos de 45.1258/36.0871 ms para K=10, 343.3691/355.1113 ms para K=50 y 242.3210/223.2240 ms para K=200; se eligió K=10 para cumplir los 50 ms en esos casos medidos, con el costo de memoria ya indicado en 16.3. Es la selección empírica prevista por el plan, no un cambio de estructura. La otra diferencia es sustituir el parser inyectado original por `modelo/juego/orden.py` y su reexportación desde `controlador/orden.py`; el plan actual lo recoge como corrección de MVC y compatibilidad, sin medición motivadora registrada.

### 16.1 Problema

Consultar el estado desde el inicio por tiempo (`historia <t>`) o antes de una acción (`historia #k`), sin cambiar la partida ni gastar el pergamino, que conserva su límite de cinco acciones. La historia debe representar la rama vigente tras retroceder, incluidos los cambios no reversibles. SC-001 exige una consulta máxima menor de 50 ms con al menos 5000 acciones.

### 16.2 Alternativas consideradas

| Decisión elegida | Alternativa descartada | Motivo |
|---|---|---|
| **C1:** capturar deltas en `Registro.cambiar`, `_lista_*` y `_inv_*`, leyendo el reloj al anotar | Copiar el estado completo en cada acción o comparar todo el mundo para descubrir cambios | El trabajo sigue a los cambios reales y conserva anterior/nuevo, instante y reversibilidad; copiar todo cuesta según el tamaño del mundo aun cuando cambia poco |
| Checkpoint de proyección cada K acciones; selección O(1) por `#k` y binaria propia por t | Reconstruir siempre desde cero sin checkpoints o hacia atrás desde una copia actual | Ambas alternativas recorren un tramo que crece con la historia; los checkpoints limitan la aplicación a un máximo de K acciones |
| Proyección copiada por valor, con bases inmutables compartidas, sin agenda, funciones ni azar | Copiar `Partida` o conservar referencias a sus datos dinámicos vivos | Las referencias modificarían el pasado; copiar el motor arrastraría infraestructura y funciones innecesarias. Consultar solo reconstruye datos, sin ejecutar eventos ni consumir azar |
| Recortar el sufijo al usar el pergamino y reubicar sus no reversibles al reloj restaurado | Borrar todo el sufijo, registrar el retroceso como otra acción o reconstruir recorriendo el prefijo | Borrar todo perdería consumo y observaciones persistentes; conservar la rama revertida mostraría acciones inexistentes. El recorte solo toca el sufijo y libera sus checkpoints |
| Reconstruir mediante órdenes y marcas existentes `# ir a X` | Nuevo formato de log/binario, persistir deltas o volver a ejecutar el viaje IR_A | Cada marca reproduce una observación exterior sin tiempo ni grupo; se conserva la secuencia real sin rediseñar formatos ni adivinar viajes/cancelaciones |
| `Orden` en `modelo/juego/orden.py`, con reexportación desde `controlador/orden.py` | Mantener el import de controlador desde datos o exigir un parser inyectado a cada lector | Cumple MVC conservando la misma clase por ambas rutas y las llamadas ordinarias `leer_log(ruta)` y `listar_logs`, sin romper sus consumidores |
| HISTORIA fuera del log, de la bitácora y del grupo; tecla L | Tratarla como acción o asignarle H/F1 | Es una consulta sin efectos ni cancelación de IR_A; H y F1 ya abren ayuda |

### 16.3 Decisión

El checkpoint 0 se toma después de iniciar la partida y antes de reconstruir órdenes. Después se copia la proyección exactamente cada K acciones aceptadas. `#k` selecciona el bloque con `(k-1)//K`; t usa búsqueda binaria propia y el corte anterior a la decisión de ese instante. La consulta copia ese checkpoint, aplica los deltas necesarios y genera el resumen con datos históricos.

Al retroceder se eliminan reversibles y checkpoints del sufijo. Los cambios no reversibles posteriores al reloj restaurado pasan a ese instante, después de sus eventos y antes de la siguiente decisión; los anteriores o simultáneos conservan su tiempo. Esta operación solo reconstruye la proyección: no reaplica persistentes sobre el motor ni cambia los inversos del pergamino.

Replay reconstruye todas las órdenes, marcas y pergaminos antes de resolver `--hasta`, para no consultar una rama eliminada después. K es configuración del proceso (`--checkpoint-cada`), no un campo persistido. La fidelidad de carga v4 depende de las entregas indicadas en 16.6.

**K elegido = 10**, fijado en T063 (`7a7c435`). Es el único de los tres valores que cumple el máximo estricto de 50 ms tanto en la carga de 5000 acciones como en los peores casos medidos, en las dos corridas históricas. Con D=1000 retiene 180557.5 KiB frente a 172607.7 KiB con K=50: aproximadamente un **5 % más de memoria** (4.6 %). Se acepta ese costo para reducir el tramo reconstruido. El tiempo de consulta crece con **K × deltas por acción**, además de copiar la proyección y construir la salida; las pausas del proceso pueden alterar los máximos.

### 16.4 Análisis de complejidad

A = acciones vigentes; D = deltas totales; S = tamaño de proyección; B = `1+floor(A/K)` checkpoints; E_K = deltas de hasta K acciones; U = deltas exteriores; L = operaciones sobre secuencias/inventario; R = tamaño del resumen.

| Operación | Costo |
|---|---|
| Captura C1 | O(1) amortizado más normalización/ubicación real; memoria según el cambio |
| Crear checkpoint | O(S), una vez cada K acciones |
| Consultar por `#k` | O(S + E_K + U + L + R); selección de checkpoint O(1) |
| Consultar por t | O(log B + S + E_K + U + L + R) |
| Historia retenida | O(D + A + B·S), incluida la capacidad reservada |
| Sin checkpoints / desde actual | O(S + deltas hasta el destino / posteriores al destino + L + R) |
| Foto por acción (referencia) | O(S + R) por consulta; fotos O(A·S) |
| Recorte | Proporcional a los deltas/persistentes del sufijo y al tamaño de las fotos liberadas; sin recorrer el prefijo |

K limita acciones, no la cantidad de eventos/deltas de cada acción ni el tamaño del resumen. Los arreglos conservan capacidad reservada al recortar y limpian las referencias retiradas.

### 16.5 Evidencia empírica

**Equipo:** Intel Core i7-8665U a 1.90 GHz (4 núcleos, 8 hilos), 31.78 GiB de RAM, Windows 11 Pro de 64 bits (compilación 26300), Python 3.13.9 del entorno virtual. **Semilla de línea de tiempo:** 20261113. Estas mediciones de Parte II tienen su propio equipo y no sustituyen las de las secciones anteriores.

Comandos desde la raíz: `venv\Scripts\python.exe main.py --bench linea_tiempo` y `venv\Scripts\python.exe main.py --bench historial inventario`. Sin HTTP ni vista; no se modificaron los benches. Se excluye preparación y se valida equivalencia antes de medir. Los tiempos de consulta incluyen copia, aplicación y construcción del resumen; las fases instrumentadas se miden en otra pasada. `tracemalloc` se usa para memoria, fuera del cronometraje; incluye bases compartidas, deltas, directorios y reserva real.

**5000 acciones, ejecución adicional durante T064 (2026-11-14).** Carga mixta de 16 salas: 21884 deltas, 5000 exteriores y 18 bases; recoger/soltar, movimientos, esperas, evento interior y cambios exteriores. Tres repeticiones sobre 17 objetivos, alternando `#k` y t: 51 muestras por alternativa. La carga segura adicional tiene 5000 acciones y 10000 deltas, con las seis variantes equivalentes antes de medir.

| Variante | Máximo (ms) | Mediana (ms) | Retenida (KiB) | Checkpoints |
|---|---:|---:|---:|---:|
| K=10 | 0.0677 | 0.0271 | 8462.2 | 501 |
| K=50 | 0.1960 | 0.0276 | 7075.6 | 101 |
| K=200 | 0.5791 | 0.0678 | 6815.4 | 26 |
| Sin checkpoints periódicos | 18.2527 | 0.2076 | 6728.7 | 1 |
| Desde la copia actual | 315.4758 | 134.0021 | 6728.7 | 1 |
| Foto por acción | 0.0244 | 0.0191 | 23485.6 | 1 + 5001 fotos |

El conteo del bench incluye el checkpoint 0; la referencia por acción conserva además 5001 fotos y la traza común. La memoria incluye la proyección actual de trabajo. Los máximos de K=10/50/200 en la carga de 5000 de la corrida 1 de T063 fueron 0.0617/0.2157/0.6686 ms. Ambas ejecuciones quedan muy por debajo de 50 ms en esta carga; la densidad de deltas decide entre los K.

**Peor caso real, N=600.** Dos salas con D−2 cazadores activos en la inicial y vida ampliada antes del checkpoint 0 para sostener las esperas; D exacto se comprueba por C1 en todas las acciones. Se consultan ambas APIs en cada objetivo, incluidos los finales de bloque con K−1 acciones por reconstruir. Corrida 1: salida de T063 suministrada por Axel; corrida 2: repetición manual suministrada por Axel. No se sustituyen por la ejecución adicional de T064.

| D por acción | K | Corrida 1 máx/mediana (ms) | Corrida 2 máx/mediana (ms) | Retenida/pico, corrida 1 (KiB) | Máx. grupos/deltas | Checkpoints |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 10 | 3.5785 / 1.2071 | 1.1959 / 0.9223 | 17872.2 / 17905.6 | 9 / 900 | 61 |
| 100 | 50 | 19.7613 / 2.6252 | 7.0223 / 1.9460 | 17044.4 / 17077.8 | 49 / 4900 | 13 |
| 100 | 200 | 105.8679 / 10.9830 | 16.9835 / 6.2279 | 16889.2 / 17035.5 | 199 / 19900 | 4 |
| 1000 | 10 | 45.1258 / 24.3986 | 36.0871 / 24.8103 | 180557.5 / 180872.1 | 9 / 9000 | 61 |
| 1000 | 50 | 343.3691 / 36.8403 | 355.1113 / 36.3436 | 172607.7 / 172922.4 | 49 / 49000 | 13 |
| 1000 | 200 | 242.3210 / 87.1505 | 223.2240 / 85.6998 | 171117.1 / 171431.8 | 199 / 199000 | 4 |

**Recorte de 1 a 5 grupos (T064).** K=50, siete muestras por caso y mismo sufijo con prefijos crecientes. Cada celda temporal muestra máximo/mediana en ms. Los conteos incluyen persistentes reubicados y liberación de un checkpoint por caso.

| Grupos | N=200 | N=2000 | N=5000 | Visitas al sufijo/prefijo | Persistentes | Bytes liberados |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.0672 / 0.0506 | 0.0732 / 0.0647 | 0.0805 / 0.0744 | 7 / 0 | 1 | 3400 |
| 2 | 0.1104 / 0.0949 | 0.1814 / 0.1212 | 0.2235 / 0.1406 | 17 / 0 | 2 | 3344 |
| 3 | 0.1657 / 0.1523 | 0.1991 / 0.1803 | 0.1996 / 0.1907 | 30 / 0 | 3 | 3288 |
| 4 | 0.2887 / 0.2427 | 0.3001 / 0.2777 | 0.2984 / 0.2882 | 54 / 0 | 4 | 3232 |
| 5 | 0.4267 / 0.3331 | 0.4794 / 0.3583 | 0.3986 / 0.3730 | 75 / 0 | 5 | 3176 |

Siempre hubo **0 visitas al prefijo**. La reserva antes/después permaneció en 1544/1544, 20544/20544 y 49280/49280 casillas para N=200, 2000 y 5000 respectivamente: liberar las fotos no copia ni reduce los directorios.

**Sobrecosto C1 integrado (T064).** Mediana de cinco repeticiones de 100 ciclos con `_inv_al_frente`, `_inv_quitar` y `_inv_agregar` dentro de `_accion`; incluye normalización y fronteras, excluye inicio y checkpoints periódicos. Cada caso produjo 500 deltas y se comprobó igualdad del resultado vivo e inventario histórico.

| Objetos | Sin C1 (µs/ciclo) | Con C1 (µs/ciclo) | Extra (µs) | Extra (%) |
|---:|---:|---:|---:|---:|
| 10 | 16.854 | 67.979 | 51.125 | 303.3 |
| 100 | 21.629 | 79.591 | 57.962 | 268.0 |
| 1000 | 76.604 | 228.435 | 151.831 | 198.2 |

**Repetición de historial (§5.6, T064).** A = inversos; B = copia completa. Tiempos en ms y memoria en KiB (el bench la rotula KB y divide entre 1024). Se conservaron las cargas y el procedimiento del bench existente.

| Caso | Salas | Activos | Eventos | A ciclo | A deshacer | A historial (inversos) | B 1 copia | B 1 copia (KiB) | B 5 copias (KiB) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Típico | 20 | 10 | 18 | 0.095 | 0.056 | 83.7 (265) | 1.96 | 53.6 | 268.0 |
| Típico | 200 | 10 | 18 | 0.101 | 0.059 | 83.7 (265) | 14.07 | 442.7 | 2213.7 |
| Típico | 1000 | 10 | 18 | 0.110 | 0.059 | 81.5 (265) | 77.50 | 1991.5 | 9957.3 |
| Peor caso | 200 | 200 | 398 | 3.441 | 1.756 | 1657.1 (5205) | 19.73 | 512.0 | 2560.2 |
| Peor caso | 1000 | 1000 | 1998 | 20.937 | 10.810 | 9160.7 (26005) | 91.12 | 2362.6 | 11813.1 |

Con diez activos, A mantiene aproximadamente 0.1 ms por ciclo al crecer de 20 a 1000 salas; B pasa de 1.96 a 77.50 ms por copia. Con 1000 activos A también crece, hasta 20.937 ms por ciclo. Este bench deshace directamente `Registro` y el de inventario usa la estructura sin `Partida`: **ninguno mide el sobrecosto C1**, que corresponde a la tabla integrada anterior.

**Repetición de inventario (§5.6, T064).** `main.py --bench historial inventario` ejecuta primero inventario según el orden del despachador. Mejor de cinco corridas, µs por operación; mismas alternativas del bench existente, sin instrumentación añadida.

| Soltar el objeto visto y deshacer | Lista con cursor | Lista sin cursor | Arreglo | Pila |
|---|---:|---:|---:|---:|
| n=10, medio | 1.19 | 1.67 | 0.13 | 1.77 |
| n=100, último | 1.19 | 7.37 | 0.12 | 24.91 |
| n=1000, medio | 1.19 | 35.49 | 0.65 | 100.42 |
| n=10000, primero | 1.16 | 1.26 | 10.59 | 0.53 |
| n=10000, medio | 1.17 | 343.69 | 5.35 | 961.41 |
| n=10000, último | 1.19 | 688.22 | 0.12 | 1908.42 |

Equipar y deshacer con cursor quedó entre 2.61 y 3.11 µs en todos los tamaños/posiciones. Recorrer n=10/100/1000/10000 tomó 1.11/7.21/67.55/677.33 µs con lista y 0.18/0.99/9.14/90.26 µs con arreglo. Se repite la tendencia de costo independiente de la posición con cursor, a cambio de un recorrido más lento.

### 16.6 Límites conocidos y entregas externas

Con D=1000 se repitió la anomalía: el máximo de K=50 fue **343.3691 y 355.1113 ms**, peor que K=200 (**242.3210 y 223.2240 ms**), aunque las medianas sí siguen el orden esperado. Los máximos observados no son una cota universal; la elección de K se apoya en ambas corridas y no solo en medianas.

**Diagnóstico desde consola, sin crear archivos ni modificar el bench.** Se importaron sus funciones con `venv\Scripts\python.exe -B -` y se registraron pausas mediante `gc.callbacks`, con D=1000, N=600, los tres K y equivalencia validada. Es una exploración adicional: se agregó una consulta cronometrada antes de `medir_consulta`, por lo que cambió la presión de asignaciones y no reproduce exactamente la secuencia del bench original.

| K | Consulta del máximo diagnóstico | Repetición | Total (ms) | GC dentro de la consulta |
|---:|---|---:|---:|---|
| 10 | `historia #420` (419 acciones completadas) | 1 | 48.9791 | Generación 0: 0.5533 ms |
| 50 | `historia 21900` (219 acciones completadas) | 3 | 303.8953 | Generación 2: 271.0896 ms |
| 200 | `historia #290` (289 acciones completadas) | 1 | 346.5908 | Generación 2: 277.5270 ms |

Se confirmó que una recolección de generación 2 explica la mayor parte de esos dos picos diagnósticos. No se reprodujo el orden K=50 peor que K=200 en esta exploración, ni se instrumentaron las corridas históricas: **la causa y el objetivo exactos de sus máximos de 343/355 ms siguen sin confirmar**. La recolección de basura dependiente de la secuencia de asignaciones sigue siendo una explicación posible para la anomalía repetida, no una conclusión probada sobre aquellas dos corridas.

| Entrega | Estado de verificación | Prueba que lo demuestra |
|---|---|---|
| T025, Mariano: eventos simultáneos | Verificado en 617f666 | `tests.test_linea_tiempo`: `test_FR002_eventos_simultaneos_y_predecision` |
| T043, Kim: marcas `# ir a` | Entregado en `69dbc30`; verificado en 617f666 | `tests.test_historia_persistencia`: `test_FR010_comentario_ir_a_observa_sin_accion`, `test_FR014_ir_a_bloqueo_posterior_sin_paso` y `test_FR014_cancelacion_sin_observacion_fantasma`; `tests.test_ir_a_compuesto` completo |
| T046, Kim: carga v4 e import de `persistencia_partida.py` | Verificado en 617f666 | `tests.test_historia_persistencia`: `test_FR014_guardar_cargar_historia_completa`, `test_FR014_cargar_con_K_distinta`, `test_FR014_ir_a_bloqueo_posterior_sin_paso`, `test_FR014_fallo_carga_conserva_sesion` y `test_FR014_modelo_datos_sin_imports_controlador`; `tests.test_guardado_binario` completo |
| FR-010: inverso y persistente sobre destino compartido | Corrección con generaciones integrada; verificado en 617f666 | `tests.test_linea_tiempo`: `test_FR010_destino_compartido_inverso_y_persistente` y `test_FR010_no_reversibles_reubicados_y_estado_actual` |

Las cuatro entregas quedan verificadas en 617f666 mediante el cierre T050/T065: los 14 módulos solicitados pasan con `venv\Scripts\python.exe -m tests.<modulo>`, incluidas las regresiones de resolubilidad, integración, replay, guardado y GUI. La revisión de solo lectura confirma la condición original de `_armar`, los contratos de resolubilidad y CLI, el inverso manual del reloj y la ausencia de cambios de Axel en `_avanzar`, así como las restricciones de estructuras y MVC. Archivos antiguos con marcas incompletas no permiten inventar las observaciones faltantes. K=10 cumple los casos medidos, pero K no limita los deltas por acción ni elimina pausas del sistema.

---

# Cómo reproducir las mediciones

Desde la raíz del repositorio:

```
python main.py --bench                      (todas)
python main.py --bench agenda red cache     (solo las indicadas)
```

Cada medición también se puede correr por separado:

```
python -m bench.bench_motor            agenda de eventos y ciclo (§4.1, §5.2)
python -m bench.bench_red              precarga, catálogo y bitácora en pantalla (§4.2, §4.3, §4.8)
python -m bench.bench_cache            caché LRU contra FIFO (§4.4)
python -m bench.bench_almacen_fichas   fichas en disco (§4.4)
python -m bench.bench_almacen_cripta   esqueleto y contenido en disco (§4.4)
python -m bench.bench_lista_ordenada   lista ordenada contra búsqueda lineal (§4.4)
python -m bench.bench_inventario       inventario (§4.5)
python -m bench.bench_historial        historial reversible (§4.6)
python -m bench.bench_ordenamiento     ordenamiento (§4.9)
python -m bench.bench_guardado_binario guardado binario contra JSON (§4.10)
```

Las pruebas de corrección son los archivos `tests/test_*.py` (por ejemplo `python -m tests.test_partida`).
