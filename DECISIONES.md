# Documento de Decisiones de Diseño — CRIPTA

Una sección por cada problema de §4 resuelto, más las decisiones de rendimiento (§5.1, §5.2) y algunas reglas del juego con decisiones de estructura (§2.6, §2.10, §2.12). Cada sección sigue los seis puntos de §8: problema, alternativas consideradas, decisión, análisis de complejidad, evidencia empírica y límites conocidos.

**Sobre las mediciones.** Salen de los archivos `bench_*.py`, que se ejecutan con `python main.py --bench`. Las secciones de Kim (9 a 11) se midieron en su equipo, en Windows y con el repositorio dentro de OneDrive. Las demás (1, 2, 5, 7, 12 y 13) se midieron en una laptop con Intel Core i5-10310U (4 núcleos) y 15.6 GB de memoria, con Windows 11, Python 3.14.5 y fuera de OneDrive. Las de inventario (12) e historial (13) se tomaron con otros benchmarks corriendo en paralelo, así que sus tiempos pueden estar algo inflados. Los tiempos varían entre corridas y equipos, así que se cita la tendencia; los conteos (comparaciones, solicitudes de red) son exactos y repetibles.

## Índice

- **Mariano** (motor del juego)
  - [1. §4.1 Qué ocurre a continuación (agenda de eventos)](#1-41-qué-ocurre-a-continuación-agenda-de-eventos)
  - [2. §5.2 Ciclo completo entre dos decisiones del jugador](#2-52-ciclo-completo-entre-dos-decisiones-del-jugador)
  - [3. §4.7 El rastro del jugador](#3-47-el-rastro-del-jugador)
  - [4. Efectos temporales y combate determinista (§2.6, §2.10)](#4-efectos-temporales-y-combate-determinista-26-210)
- **Jeferson** (red, precarga, catálogo y bitácora en pantalla)
  - [5. §4.2 Traer el contenido antes de que haga falta](#5-42-traer-el-contenido-antes-de-que-haga-falta)
  - [6. §4.3 Resolución de referencias del catálogo](#6-43-resolución-de-referencias-del-catálogo)
  - [7. §4.8 Bitácora en pantalla](#7-48-bitácora-en-pantalla)
  - [8. §5.1 Presupuesto de red](#8-51-presupuesto-de-red)
- **Kim** (caché persistente, ordenamiento y guardado binario)
  - [9. §4.4 Reutilización y caché persistente](#9-44-reutilización-y-caché-persistente)
  - [10. §4.9 Ordenamiento](#10-49-ordenamiento)
  - [11. §4.10 Guardado binario de la partida](#11-410-guardado-binario-de-la-partida)
- **Axel** (inventario, retroceso, replay y puntajes)
  - [12. §4.5 Inventario](#12-45-inventario)
  - [13. §4.6 Pergaminos de retroceso e historial reversible](#13-46-pergaminos-de-retroceso-e-historial-reversible)
  - [14. §4.11 Bitácora de partida y reproducción](#14-411-bitácora-de-partida-y-reproducción)
  - [15. Tabla de puntajes (§2.12)](#15-tabla-de-puntajes-212)

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

# Parte de Kim — Caché persistente, ordenamiento y guardado binario

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
