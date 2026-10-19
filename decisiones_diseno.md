# Documento de Decisiones de Diseño:

Secciones: §4.4 (caché y persistencia), §4.9 (ordenamiento) y §4.10 (guardado binario).
Las mediciones salen de los archivos `bench_*.py`, ejecutados en Windows con el repositorio dentro de OneDrive. Los tiempos varían entre corridas, así que se cita la tendencia y las comparaciones de operaciones, que sí son exactas.

## 1. §4.4 Reutilización y caché persistente

### 1.1 Problema

Las fichas del catálogo se usan todo el tiempo (cada enemigo, objeto y trampa remite a una). Cada solicitud de red tarda cerca de 400 ms y gasta presupuesto, así que una ficha ya descargada no se debe volver a pedir. Hay tres necesidades:

1. Saber si una ficha está en memoria, que es de las operaciones más frecuentes.
2. Mantener un máximo de fichas en memoria (`--cache-size`, 25 por defecto) y decidir cuál liberar, sin liberar nunca una ficha en uso.
3. Que lo descargado sobreviva al cierre del programa y se valide con la versión de catálogo y de cripta, sin descargar todo otra vez.

### 1.2 Alternativas consideradas

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

### 1.3 Decisión

- **Búsqueda:** `ListaOrdenada` (`lista_ordenada.py`). Son dos listas paralelas, claves y valores, siempre ordenadas por clave. La búsqueda es binaria. Tiene `insertar_muchos`, que junta todo, ordena una sola vez con nuestro `ordenar` y descarta duplicados (gana la última).
- **Memoria:** `Cache` (`cache.py`). Una lista doblemente enlazada guarda el orden de uso (la más reciente al frente) y la `ListaOrdenada` guarda `id -> nodo`. Al consultar una ficha, su nodo pasa al frente. Para liberar se mira desde el final y se libera la primera ficha que no esté en uso. La caché recibe una función `en_uso(id)`, que en el juego es `Partida.ficha_en_uso`. Si todas las fichas están en uso, no se libera nada y la caché se pasa del tope.
- **Disco:** `AlmacenFichas` (`almacen_fichas.py`). Es un archivo con encabezado (marca y versión de catálogo) y registros `[largo del id][id][largo del JSON][JSON]`. El índice en memoria es una `ListaOrdenada` con `id -> [posición, largo]`. Leer una ficha es una búsqueda en el índice, un `seek` y una lectura. Si la versión guardada no coincide con la actual, se descarta todo y se empieza un archivo nuevo. Una ficha que se guarda otra vez se añade al final y el índice apunta a la nueva copia.
- **Cripta:** `AlmacenCripta` (`almacen_cripta.py`) reutiliza `AlmacenFichas` con la versión de cripta en el encabezado. Guarda los datos generales, cada página del esqueleto y el contenido sala por sala (`general`, `pagina_n`, `sala_n`). Una sala vacía también se guarda, porque "ya la pedí y está vacía" no es lo mismo que "nunca la pedí".
- **Unión:** `AlmacenLocalCache` (`almacen_local_cache.py`) implementa la interfaz `AlmacenLocal` del cliente de red. Consulta primero la caché, luego el disco, y deja la red al resolutor. El estado de la caché no se registra en el historial de retroceso, porque es infraestructura y no estado del juego (§2.11).

### 1.4 Análisis de complejidad

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

### 1.5 Evidencia empírica

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

### 1.6 Límites conocidos

- La lista ordenada deja de ser adecuada si `--cache-size` o el catálogo crecen a decenas de miles y se insertan de a uno, porque insertar es O(n) y cuadrático en total. `insertar_muchos` mitiga la carga inicial.
- Con la lista ordenada, `poner` con desalojo es O(n) y crece de forma lineal con el tope: 8.9 µs con tope 25, 108 µs con 1000 y 1.7 ms con 10000. Con el tope por defecto no importa, porque solo ocurre cuando llega una ficha nueva y las fichas llegan en lotes de a lo sumo 10 por solicitud. Con topes de miles de fichas convendría otra estructura de búsqueda. Es el costo de usar listas ordenadas.
- La ventaja de LRU se midió con un patrón de accesos sintético con localidad. Con accesos que nunca se repiten, LRU y FIFO se comportarían casi igual. Conviene repetir la comparación con los accesos reales de una partida.
- Si todas las fichas están en uso, la caché supera el tope (está cubierto por `test_cache.py`).
- `AlmacenFichas` abre y cierra el archivo en cada `leer` y `guardar`. Las fichas re-guardadas dejan basura y no hay compactación. Reconstruir el índice recorre todo el archivo y el arranque crece con las fichas guardadas; con 5000 fichas tardó unos 330 ms, más de lo esperado (ver la hipótesis de la sección 1.5).
- Solo hay una consulta de versión de catálogo y una de cripta por ejecución, y las dos cuentan contra el presupuesto de solicitudes. Un catálogo con cientos de miles de fichas exigiría guardar el índice en un archivo aparte.
- Las mediciones se hicieron en Windows sobre OneDrive.

---

## 2. §4.9 Ordenamiento

### 2.1 Problema

El programa ordena en varios contextos: vistas del inventario por peso, valor o nombre, tabla de puntajes, el índice del guardado binario y la carga ordenada de la lista de la caché. No se permite `list.sort()` ni `sorted()`. Los datos pueden ser pequeños (un inventario de pocas decenas), casi ordenados o grandes, y la comparación puede ser cara.

### 2.2 Alternativas consideradas

- **Solo inserción.** Es excelente con datos pequeños o casi ordenados, pero es O(n²) con datos grandes desordenados.
- **Solo merge sort.** Es siempre O(n log n) y estable, pero tiene más costo fijo con listas pequeñas y usa memoria extra.
- **`sorted()` de Python.** Se midió solo como referencia, porque está prohibido en el programa.
- **Selector automático** entre inserción y merge. Es el elegido.

### 2.3 Decisión

`ordenamiento.py` implementa `ordenar_insercion` y `ordenar_merge`, ambos estables, y un selector `ordenar(datos, clave, descendente, comparacion_costosa)` que devuelve una lista nueva sin modificar la original (el inventario necesita una vista sin alterar su orden real). La clave se calcula una sola vez por elemento.

El selector elige inserción en estos casos:

1. `n` no supera `UMBRAL_PEQUENO` (32), o `UMBRAL_COSTOSO` (8) si la comparación es costosa.
2. Hay poco desorden a distancia: se compara cada elemento con el que está `SALTO` (8) posiciones adelante, y si la fracción fuera de orden es de 0.02 o menos, se usa inserción.

En cualquier otro caso usa merge.

**Cómo llegamos a esta regla.** El selector pasó por tres versiones, todas medidas:

1. Medía los pares vecinos fuera de orden. Eligió mal en "casi ordenado" con desorden lejano (n=5000: 95 ms con inserción contra 12 ms con merge).
2. Se añadió un límite de tamaño. Arregló ese caso, pero perdió el desorden local, donde inserción gana (n=5000: 1.3 ms contra 10.8 ms).
3. La versión final mide el desorden a distancia 8. Con ella `auto` sigue a la mejor opción en los cuatro escenarios.

### 2.4 Análisis de complejidad

| Algoritmo | Mejor caso | Caso medio y peor | Memoria extra |
|---|---|---|---|
| Inserción | O(n), casi ordenado | O(n²) | O(1) |
| Merge | O(n log n) | O(n log n) | O(n) |
| Medida de desorden del selector | O(n), una pasada | O(n) | O(1) |

### 2.5 Evidencia empírica

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

### 2.6 Límites conocidos

- Con claves baratas y n pequeño, el costo de medir el desorden domina. Por ejemplo, con n=100 aleatorio `auto` tardó 0.65 ms contra 0.40 de merge puro, aunque otras corridas dieron valores cercanos, así que parte es ruido.
- Con desorden lejano moderado el selector elige merge, aunque en casos intermedios inserción podría ganar.
- Los umbrales (32, 8, `SALTO` = 8, 0.02) salen de estas mediciones y habría que recalibrarlos en otro equipo.
- Los tiempos varían entre corridas; las comparaciones contadas son exactas y repetibles.
- Nuestro ordenamiento es mucho más lento que `sorted()`. Es aceptable para inventarios de decenas de objetos y tablas de puntajes pequeñas.

---

## 3. §4.10 Guardado binario de la partida

### 3.1 Problema

El estado se guarda en un archivo binario de formato propio. Al cargar debe poder recuperarse una sala específica sin leer todo el archivo, debe detectarse una versión de formato incompatible y hay que comparar tamaño y tiempo de carga contra JSON.

### 3.2 Alternativas consideradas

- **JSON.** Es simple y `json.load` está escrito en C, pero para una sola sala obliga a cargar todo el archivo. Se midió como alternativa.
- **Binario sin índice.** Hay que leer de forma secuencial hasta la sala que se busca, que es O(n) como JSON. Se descartó por razonamiento; no se midió.
- **Binario con índice ordenado de entradas de tamaño fijo y búsqueda binaria con `seek`.** Es el elegido.

### 3.3 Decisión

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

### 3.4 Análisis de complejidad

| Operación | Costo |
|---|---|
| Guardar | O(n log n) por ordenar el índice, más escribir O(n) |
| Leer una sala | O(log n) pasos de 16 bytes, más una lectura |
| Cargar los datos generales | O(1) en el número de salas |
| Carga completa | O(n) |

### 3.5 Evidencia empírica

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

### 3.6 Límites conocidos

- La carga completa es más lenta que JSON. El formato conviene cuando se necesitan salas sueltas.
- Los números tienen tamaño fijo (por ejemplo, vida y tiempos en 4 bytes). Si el modelo usa valores mayores, hay que cambiar los tipos de `struct`.
- El historial de retroceso no se guarda: son funciones, no datos. Al cargar una partida, el historial empieza vacío.
- La estructura guardada es de prueba y debe ajustarse a los campos reales del modelo.
- Las mediciones se hicieron en Windows sobre OneDrive.

---

## 4. Cómo reproducir las mediciones

Desde la raíz del repositorio:

```
python -m bench.bench_ordenamiento
python -m bench.bench_lista_ordenada
python -m bench.bench_cache
python -m bench.bench_almacen_fichas
python -m bench.bench_almacen_cripta
python -m bench.bench_guardado_binario
python main.py --bench
```

Las pruebas de corrección son los archivos `test_*.py` (por ejemplo `python test_ordenamiento.py`). Se ejecutaron en Windows con el repositorio dentro de OneDrive.

---

## 5. Uso de herramientas de apoyo

El uso de un LLM para estas secciones está registrado en `PROMPTS_LLM.md`.