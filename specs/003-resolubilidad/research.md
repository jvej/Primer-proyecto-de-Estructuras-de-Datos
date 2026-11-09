# Research & Technical Decisions: Verificación de Resolubilidad y Extensión del Servicio Web

**Feature**: `003-resolubilidad`  
**Date**: 2026-11-08  
**Spec Reference**: `specs/003-resolubilidad/spec.md`

Este documento consolida las decisiones de diseño técnico, estructuras de datos propias y justificaciones algorítmicas requeridas por la Constitución y el enunciado del proyecto CRIPTA, evaluando el enfoque incremental propuesto frente a las alternativas descartadas.

---

## Decisión 1: Recorrido por etapas (BFS incremental estricto) frente a recorrido repetido por llave

- **Decisión**: Implementar un recorrido en anchura por etapas basado en la estructura propia `ColaFIFO` (`modelo/estructuras/cola_fifo.py`) manteniendo listas de espera para puertas bloqueadas:
  1. Durante una etapa concreta, **únicamente** se pueden cruzar puertas abiertas o puertas cerradas cuya llave fue obtenida en una **etapa anterior**.
  2. Las llaves encontradas en las salas visitadas durante la etapa actual quedan marcadas como **pendientes**; no se consideran disponibles de inmediato.
  3. Toda puerta cerrada cuya llave no esté disponible previamente va a la lista de espera de dicha cerradura, incluso si su llave aparece más adelante en la misma etapa.
  4. Al cerrarse la etapa (cuando se vacía la cola de salas a explorar de dicha etapa), las llaves pendientes pasan al conjunto de llaves disponibles, se ordenan por identificador de texto con `ordenar()` (`modelo/estructuras/ordenamiento.py`) y se liberan las listas de espera asociadas a esas llaves, las cuales siembran la cola de la etapa siguiente.
- **Justificación**:
  - Garantiza que la **etapa 0** sea exactamente la región alcanzable desde el inicio sin usar llaves, coincidiendo de forma matemática con la especificación.
  - Asegura que el resultado del recorrido por etapas y el orden de llaves sea completamente independiente del orden interno en que la cola procese las salas de una etapa.
  - Costo computacional acotado por $O(S + E + L \log L)$, lineal en la práctica ($O(S + E + L)$) con $L \ll S$, satisfaciendo `SC-001` y `SC-002`.
- **Alternativa evaluada y descartada**:
  - *Recorrido repetido por llave*: Reiniciar un recorrido completo de la cripta desde la sala inicial cada vez que se descubre una nueva llave. En una cripta con $L$ llaves encadenadas linealmente, el costo total escala a $O(L \cdot (S + E))$. Con $L = 100$ y $S = 500$, esto implica explorar decenas de miles de salas repetidamente, degradando el rendimiento en varios órdenes de magnitud. Esta alternativa se implementará en el benchmark (`bench/bench_resolubilidad.py`) con fines de comparación empírica para el informe técnico.

---

## Decisión 2: Indexación de salas y mapeo de cerraduras a listas de espera

- **Decisión**:
  1. *Indexación de salas*: Preprocesar el esqueleto al inicio para traducir una sola vez los identificadores de salas vecinas a índices enteros continuos $[0, S-1]$. El recorrido subsiguiente utiliza acceso directo por índice a listas contiguas de Python (`listas_vecinos[pos]`, `visitado[pos]`) en tiempo $O(1)$.
  2. *Listas de espera indexadas por cerradura*: Las listas de espera se indexan por el identificador textual que **pide la puerta** (`puerta["llave"]`), mapeado a un número entero $[0, C-1]$ mediante búsqueda binaria sobre un arreglo ordenado de cerraduras únicas. La inserción de una puerta en su lista de espera se ejecuta en $O(1)$ amortizado.
- **Justificación**:
  - Actualmente, `Esqueleto.vecinos_de` realiza una búsqueda en `ListaOrdenada` en $O(\log S)$ por cada consulta. Traducir a índices enteros al inicio reduce el costo de navegación de $O(E \log S)$ a $O(E)$.
  - Cumple estrictamente el Principio I de la Constitución (PROHIBIDO usar `dict` o `set` de Python como índice o caché).
  - Un arreglo indexado por identificador de cerradura con ordenamiento previo de IDs tiene menor sobrecarga en tiempo y memoria que construir una tabla hash propia con sondeo lineal.

---

## Decisión 3: Coincidencia de llaves y activación por `abre`

- **Decisión**:
  - Las listas de espera se indexan por el identificador que pide la puerta.
  - Al activarse una llave obtenida $K$:
    1. Se liberan las puertas de la lista de espera asociadas a `K.id`.
    2. Si la ficha de la llave está disponible en el catálogo local (`AlmacenFichas`) y contiene el campo `"abre"`, se liberan también las puertas de la lista de espera asociadas a `K.abre`.
    3. Si la ficha de la llave no se encuentra en el catálogo local, se utiliza únicamente su `K.id` (sin realizar solicitudes HTTP bajo ningún concepto). Este comportamiento se documenta como un límite conocido del sistema.
- **Justificación**:
  - Respeta el Principio V de la Constitución (toda solicitud HTTP debe presupuestarse). No se consumen peticiones de red para consultar atributos de fichas.
  - Replica el comportamiento de `Partida._tiene_llave()` siempre que el catálogo local disponga de las fichas precargadas, y degrada limpiamente utilizando el `id` directo si la ficha no está almacenada.

---

## Decisión 4: Diagnóstico de cripta no resoluble y detección determinista de ciclos

- **Decisión**:
  - *Frontera bloqueada*:
    - Compuesta por las puertas cerradas $(u \to v)$ donde la sala de origen $u$ es alcanzable (`visitado[u] == True`) y la sala de destino $v$ es inalcanzable (`visitado[v] == False`).
    - **Se excluyen expresamente** aquellas puertas cerradas cuyas dos salas ya son alcanzables (`visitado[u] == True` y `visitado[v] == True`), pues no constituyen una barrera hacia territorio desconocido.
  - *Propagación de etiquetas hacia salas no alcanzadas*:
    - Continuando el recorrido desde la frontera bloqueada hacia las regiones no alcanzadas (sin reiniciar el recorrido), se asignan etiquetas de llaves en orden determinista (recorriendo la frontera ordenada por `id_sala` ascendente y luego por dirección canónica `N`, `S`, `E`, `O`).
    - Cuando la exploración hacia adelante cruza otra puerta cerrada, las salas ubicadas detrás de ella toman como etiqueta la llave de **esa puerta** (la más cercana), no la de la frontera original.
    - Si en una sala etiquetada con la llave $Y$ se encuentra la llave $X$, se agrega la arista dirigida $X \to Y$ al grafo de dependencias ("la llave $X$ está detrás de una puerta que pide la llave $Y$"), guardando la sala y dirección de la puerta bloqueante más cercana.
  - *Demostración de linealidad del proceso*:
    - Cada sala no alcanzada se visita a lo sumo una vez durante la propagación desde la frontera: $O(S_{no\_alcanzadas})$.
    - Cada arista de la región no alcanzada se examina a lo sumo una vez: $O(E_{no\_alcanzadas})$.
    - El grafo de dependencias de llaves resultante contiene a lo sumo $L_{no\_obtenidas} \le L$ nodos y a lo sumo $E$ aristas.
    - La exploración completa hacia las salas no alcanzadas y la construcción del grafo de dependencias toma tiempo estrictamente lineal $O(S + E)$.
  - *Detección iterativa de ciclos con DFS de 3 colores*:
    - Para evitar desbordamientos de pila (`RecursionError`) en Python ante cadenas extensas de llaves, el recorrido DFS de 3 colores (Blanco: no visitado, Gris: en pila de exploración, Negro: procesado) se implementa de forma **estrictamente iterativa** utilizando una lista contigua propia como pila (`pila = []`).
    - Determinismo (Principio II): los nodos del grafo de dependencias se ordenan lexicográficamente por su identificador textual con `ordenar()`, y la iteración comienza en el nodo con menor ID. Las aristas salientes de cada nodo se exploran también en orden lexicográfico.
    - Al detectar una arista hacia un nodo en estado Gris, se extrae el ciclo desde la pila, se rota para que inicie y termine en la llave con menor ID de texto (ej. `itm_a -> itm_c -> itm_b -> itm_a`), y se reporta deterministamente.
- **Justificación**:
  - Garantiza robustez y estabilidad en tiempo lineal $O(S + E + L)$ sin riesgo de superar el límite de recursión de Python, cumpliendo `SC-003` y `SC-004`.
