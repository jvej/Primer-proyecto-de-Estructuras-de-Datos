# Implementation Plan: Verificación de Resolubilidad y Extensión del Servicio Web

**Branch**: `003-resolubilidad` | **Date**: 2026-11-08 | **Spec**: [spec.md](./spec.md)  
**Input**: Requisitos de resolubilidad de CRIPTA, nuevo endpoint `GET /criptas/<id>/llaves`, costos de salidas, cazadores con rango y opciones CLI.

---

## Summary

Implementar la verificación estática de resolubilidad de criptas antes de iniciar la partida y proporcionar la herramienta de inspección en frío `--verificar <cripta>`, junto con la extensión de la capa de datos para consumir y almacenar llaves (`GET /criptas/<id>/llaves`), procesar costos de salidas (100 por defecto, entero $\ge 1$) y soportar fichas enemigas con comportamiento `"cazador"` y `"rango"` (en unidades de costo).

El núcleo algorítmico residirá en un nuevo módulo puro `modelo/juego/resolubilidad.py` que no realiza operaciones de red ni disco, respetando escrupulosamente los principios de la Constitución: no utiliza `dict` ni `set` como índices, no utiliza bibliotecas prohibidas (`heapq`, `bisect`, `collections`, `networkx`), y emplea la estructura propia `ColaFIFO` y la función `ordenar()` propia. La verificación se basa en un recorrido incremental por etapas de complejidad lineal $O(S + E + L)$ que construye el reporte de resolubilidad, frontera bloqueada y detección determinista de ciclos (DFS iterativa de 3 colores) a partir de la misma pasada de exploración.

---

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: `requests`, `pygame` (definidas en `requirements.txt`; PROHIBIDO agregar nuevas dependencias)  
**Storage**: Almacenamiento local binario estructurado `AlmacenFichas` (`.bin`) y archivos JSON offline (`.json`)  
**Testing**: Pruebas unitarias y de aceptación ejecutables con `python -m tests.<modulo>` citando los identificadores de requisito (ej. `test_FR007_...`)  
**Target Platform**: Multiplataforma (Windows, Linux, macOS) en modo consola y ventana gráfica interactiva (Pygame)  
**Project Type**: Juego de calabozo por turnos con arquitectura MVC y cliente HTTP  
**Performance Goals**:
- Verificación de resolubilidad < 200 ms en la cripta más grande publicada (`SC-001`).
- Crecimiento temporal estrictamente lineal $O(S + E + L)$ (`SC-002`).
- Reporte y ciclos generados a partir de la misma pasada de exploración (`SC-003`).
- Determinismo reproducible en empates y ciclos (`SC-004`).
**Constraints**:
- PROHIBIDO el uso de `dict` o `set` como índice o caché, `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` o cualquier biblioteca de grafos, `sorted()` y `list.sort()`.
- `list` solo como almacenamiento contiguo. Los diccionarios de `respuesta.json()` solo se leen.
- El Modelo (`modelo/`) no importa `controlador/` ni `vista/`.
- Ningún dato de una cripta concreta en el código fuente.
- Desempates: siempre por el menor identificador de texto lexicográfico. El azar proviene exclusivamente de `partida.azar`.
- Toda solicitud HTTP cuenta en `presupuesto_solicitudes`, incluidos reintentos y `/llaves`.
- Modos `--replay`, `--bench` y `--verificar` nunca inicializan ni crean la vista (consola interactiva ni Pygame).
**Scale/Scope**: Criptas de cientos de salas ($S \le 1000$), salidas ($E \le 4000$) y decenas a cientos de llaves ($L \le 200$).

---

## Constitution Check

*GATE: Evaluación previa obligatoria conforme a `.specify/memory/constitution.md`.*

| Principio | Estado | Justificación en el Plan |
|---|---|---|
| **I. Estructuras propias** | **PASS** | El algoritmo utiliza `ColaFIFO` propia y `ordenar()` propio sobre listas contiguas de Python. La indexación de salas y cerraduras usa arreglos contiguos nativos indexados por enteros sin emplear `dict` ni `set` como índices. |
| **II. Determinismo** | **PASS** | Las salidas se exploran en orden canónico fijo `N`, `S`, `E`, `O`. Los empates entre llaves de la misma etapa se resuelven por orden lexicográfico estricto. La frontera se recorre por id de sala y dirección `N`, `S`, `E`, `O`. La detección de ciclos DFS inicia en el menor ID textual y sigue vecinos ordenados. |
| **III. Separación MVC** | **PASS** | `modelo/juego/resolubilidad.py` solo opera con estructuras de datos en memoria y no sabe de HTTP, archivos ni gráficos. `--verificar` imprime en stdout y sale con código 0, 1 o 2; no importa ni crea la vista. |
| **IV. Ningún dato de cripta en código** | **PASS** | Todo el modelo y los algoritmos son independientes de IDs de salas, llaves o nombres concretos; se validan con criptas procedurales sintéticas. |
| **V. Presupuesto de solicitudes** | **PASS** | Cada llamada a `cliente_http.llaves()` descuenta 1 punto en `PresupuestoRed`, contabilizando reintentos por 429. Si hay datos locales válidos, no se consulta la red. |
| **VI. Rendimiento medido** | **PASS** | Se incorpora `bench/bench_resolubilidad.py` midiendo el algoritmo incremental frente al repetido sobre cadenas sintéticas de llaves generadas con `bench/generador_criptas.py`. |
| **VII. Especificación antes que código** | **PASS** | `spec.md` fue formalizado y clarificado en 9 puntos antes del diseño de este plan. |

---

## Project Structure

### Documentation (this feature)

```text
specs/003-resolubilidad/
├── spec.md                  # Especificación funcional y de requisitos
├── checklists/
│   └── requirements.md      # Checklist de calidad de requisitos
├── plan.md                  # Este plan de implementación
├── research.md              # Fase 0: Decisiones y comparativas técnicas
├── data-model.md            # Fase 1: Entidades y estructuras en memoria
├── quickstart.md            # Fase 1: Guía de ejecución y validación
└── contracts/               # Fase 1: Contratos de interfaz
    ├── resolubilidad-api.md # Contrato de verificar_resolubilidad
    ├── servicio-web-llaves.md # Contrato GET /llaves y persistencia
    └── cli.md               # Contrato de banderas --verificar y --forzar
```

### Source Code & Modified Layout

```text
modelo/
├── datos/
│   ├── cliente_http.py      # Agrega método llaves(id_cripta) con presupuesto
│   ├── fuente_datos.py      # Agrega firma abstracta llaves(id_cripta)
│   ├── cliente_offline.py   # Lee llaves de criptas/<id>/llaves.json
│   ├── fuente_almacen.py    # Lee llaves de AlmacenCripta
│   ├── almacen_cripta.py    # Persiste y recupera "llaves" en AlmacenFichas
│   └── esqueleto.py         # Soporta costo en salidas (100 por defecto, >= 1)
├── juego/
│   └── resolubilidad.py     # NUEVO: Verificación de resolubilidad y ciclos
controlador/
├── aplicacion.py            # Orquesta verificación previa y maneja contingencias
main.py                      # Soporta --verificar <id>, --forzar y registro de bench
bench/
├── generador_criptas.py     # NUEVO: Generador procedural determinista de criptas
└── bench_resolubilidad.py   # NUEVO: Benchmarking incremental vs repetido
tests/
├── cripta_de_prueba.py      # Helpers y criptas sintéticas con costos y llaves
├── crear_paquete_prueba.py  # Genera paquete offline con llaves.json y cazadores
└── test_resolubilidad.py    # NUEVO: Pruebas unitarias de aceptación (test_FR###_...)
```

---

## Detailed Technical Design

### 1. Algoritmo de Resolubilidad Incremental por Etapas

#### 1.1 Regla Canónica de Etapas
1. **Disponibilidad estricta**: Durante una etapa $k$, **solo se pueden cruzar** puertas abiertas o puertas cerradas cuya llave se haya obtenido en una **etapa anterior** ($0 \dots k-1$). Para la etapa 0, el conjunto de llaves disponibles es vacío.
2. **Llaves pendientes**: Las llaves encontradas en las salas visitadas durante la etapa actual quedan marcadas como **pendientes** (`llaves_pendientes`). No se consideran disponibles de inmediato.
3. **Listas de espera**: Toda puerta cerrada cuya llave no esté disponible previamente se coloca en la lista de espera asociada al identificador que pide la puerta, **incluso si su llave aparece más tarde en la misma etapa**.
4. **Cierre de etapa**: Al agotarse la cola de la etapa actual:
   - Las llaves pendientes pasan a estar disponibles (`llaves_disponibles`).
   - Se ordenan por ID de texto mediante `ordenar(llaves_etapa)`.
   - Se registran en el reporte: `etapa k: itm_...`.
   - Se activan y liberan las puertas de sus respectivas listas de espera, las cuales siembran la cola para la etapa $k+1$.
   - **Resultado**: La etapa 0 es exactamente la región alcanzable desde el inicio sin usar llaves, coincidiendo con la especificación, y el resultado es totalmente independiente del orden de exploración interno dentro de una etapa.

#### 1.2 Preprocesamiento e Indexación $O(S \log S + C \log C)$
1. **Indexación de salas**: Se recorre `esqueleto.ids` (longitud $S$). Para cada sala $i \in [0, S-1]$:
   - Se obtiene su lista de salidas hacia salas vecinas.
   - Para cada vecino, se consulta una sola vez `esqueleto.posicion(id_vecino)` (que usa `ListaOrdenada.buscar` en $O(\log S)$) y se almacena la posición entera continua $0 \le pos < S$.
   - Cada salida almacena su costo (entero $\ge 1$, por defecto 100).
   - Se almacena en un arreglo `vecinos_indexados[i]` una lista contigua de tuplas `(pos_vecino, direccion, abierta, llave_requerida)`.
2. **Indexación de cerraduras y listas de espera**:
   - Las listas de espera se indexan por el **identificador textual que pide la puerta** (`puerta["llave"]`), o por IDs de llaves.
   - Se recolectan los identificadores textuales únicos de cerraduras/llaves ($C \le L$).
   - Se ordenan con `ordenar(lista_cerraduras_unicas)` en $O(C \log C)$.
   - Se implementa una búsqueda binaria interna `_buscar_cerradura(id_texto) -> int` sobre la lista ordenada para obtener su índice $0 \le c < C$ en $O(\log C)$.
   - Se crea el arreglo contiguo de listas de espera: `listas_espera = [[] for _ in range(C)]`.

#### 1.3 Bucle Principal BFS por Etapas $O(S + E + L)$
1. **Inicialización**:
   - `visitado = [False] * S`
   - `llaves_disponibles = [False] * C`
   - `cola = ColaFIFO()`
   - `etapa = 0`
   - `reporte_orden_llaves = []`
   - `pos_inicio = esqueleto.posicion(sala_inicial)`
   - `visitado[pos_inicio] = True`
   - `cola.agregar(pos_inicio)`
2. **Ejecución de la Etapa**:
   - `salas_etapa = len(cola)`
   - `llaves_pendientes = []`
   - Para cada una de las `salas_etapa`:
     - `pos_actual = cola.sacar()`
     - **Recolección de llaves en la sala**: Si la sala actual contiene llaves (en el suelo o en la instancia de enemigo que inicia allí):
       - Para cada llave $K$ presente: si no fue recolectada previamente, registrar $K$ en `llaves_pendientes`.
     - **Exploración de salidas en orden `N`, `S`, `E`, `O`**:
       - Para cada `(pos_vecino, dir, abierta, llave_req)` de la sala actual:
         - Si `abierta` o (`llave_req is not None` y `llaves_disponibles[idx(llave_req)] == True`):
           - Si `not visitado[pos_vecino]`: marcar `visitado[pos_vecino] = True` y encolar `cola.agregar(pos_vecino)`.
         - Si `not abierta` y `llave_req is not None` y `not llaves_disponibles[idx(llave_req)]`:
           - Agregar puerta `(pos_actual, dir, pos_vecino, llave_req)` a `listas_espera[idx(llave_req)]`.
         - Si `not abierta` y `llave_req is None`:
           - Registrar puerta en `puertas_cerradas_sin_llave`.
3. **Cierre de Etapa y Siembra de la Siguiente**:
   - Si `llaves_pendientes` no está vacía:
     - Ordenar `llaves_pendientes` lexicográficamente con `ordenar()`.
     - Agregar a `reporte_orden_llaves.append((etapa, llaves_pendientes))`.
     - Para cada llave $K$ de `llaves_pendientes`:
       - Marcar disponible: `llaves_disponibles[idx(K.id)] = True`.
       - Liberar `listas_espera[idx(K.id)]`.
       - Si $K$ tiene ficha en el catálogo local y define `"abre"`, marcar `llaves_disponibles[idx(K.abre)] = True` y liberar también `listas_espera[idx(K.abre)]`.
       - Si la ficha no está en el catálogo local, se utiliza solo el `id` directo sin realizar solicitudes HTTP (límite documentado).
       - Para cada puerta liberada `(pos_origen, dir, pos_destino, _)`:
         - Si `not visitado[pos_destino]`:
           - `visitado[pos_destino] = True`
           - `cola.agregar(pos_destino)`
     - Incrementar `etapa += 1`.
   - Si no hay llaves pendientes y la cola quedó vacía: el avance concluye (punto fijo).

#### 1.4 Verificación de Victoria
- Se califica como `RESOLUBLE` si y solo si:
  1. `llave_salida` fue obtenida y está en `llaves_disponibles`.
  2. La sala de salida `pos_salida = esqueleto.posicion(sala_salida)` fue alcanzada atravesando una puerta que requiere `llave_salida`.
- En caso afirmativo: Retornar `ResultadoResolubilidad("RESOLUBLE", orden_llaves=reporte_orden_llaves)`.

---

### 2. Diagnóstico No Resoluble y Detección Determinista de Ciclos

Si la cripta no es resoluble, el reporte completo se deriva del mismo recorrido:

1. **Frontera Bloqueada**:
   - Formada por las puertas cerradas $(u \to v)$ donde la sala de origen $u$ es alcanzable (`visitado[u] == True`) y la sala de destino $v$ es inalcanzable (`visitado[v] == False`).
   - **Exclusión obligatoria**: Se excluyen expresamente puertas cuyas dos salas ya son alcanzables (`visitado[u] == True` y `visitado[v] == True`).
   - Se ordenan ascendentemente por `id_sala` de origen y luego por dirección en orden `N`, `S`, `E`, `O`.
2. **Propagación de Etiquetas hacia Salas Inalcanzadas**:
   - Se continúa el recorrido BFS desde las puertas de la frontera bloqueada hacia las regiones no visitadas.
   - La frontera se recorre en el orden determinista especificado.
   - Al atravesar una puerta de frontera que pide la llave $Y$, las salas inalcanzadas detrás de ella toman como etiqueta la llave $Y$.
   - **Regla de la puerta más cercana**: Cuando este recorrido hacia adelante encuentra otra puerta cerrada que pide la llave $Z$, las salas situadas detrás de esta segunda puerta toman como etiqueta la llave $Z$ (**la llave de esa puerta más cercana**, no la de la frontera).
   - Si en una sala etiquetada con la llave $Y$ se encuentra la llave $X$, se agrega la arista dirigida $X \to Y$ ("la llave $X$ está detrás de una puerta que pide $Y$").
   - **Demostración de linealidad**:
     - Cada sala no alcanzada se visita a lo sumo una vez durante la propagación: $O(S_{no\_alcanzadas})$.
     - Cada salida entre salas no alcanzadas se revisa a lo sumo una vez: $O(E_{no\_alcanzadas})$.
     - El grafo de dependencias de llaves resultante contiene a lo sumo $L_{no\_obtenidas} \le L$ nodos y a lo sumo $E$ aristas.
     - La construcción del grafo de dependencias es estrictamente lineal en $O(S + E)$.
3. **Detección Determinista de Ciclos (DFS Iterativa con Pila Propia)**:
   - La búsqueda en profundidad de 3 colores (Blanco: no visitado, Gris: en pila, Negro: procesado) se implementa de forma **estrictamente iterativa** utilizando una lista contigua propia como pila (`pila = []`), sin llamadas recursivas para evitar `RecursionError`.
   - Se ordenan los nodos del grafo de dependencias lexicográficamente con `ordenar()` para garantizar determinismo absoluto.
   - Se itera sobre los nodos en orden lexicográfico.
   - En la pila iterativa se gestiona el estado de cada nodo y el índice de la arista saliente que se está explorando.
   - Al encontrar una arista hacia un nodo en estado Gris, se extrae el ciclo desde la pila, se normaliza para que comience y termine en la llave del ciclo con menor ID de texto (ej. `itm_a -> itm_c -> itm_b -> itm_a`), indicando junto a cada flecha la puerta que bloquea (`[sala X (DIR)]`).
4. **Anomalías Topológicas**:
   - Si existe `llave_salida` pero ninguna puerta hacia `sala_salida` la requiere:
     `MOTIVO: no existe puerta hacia sala_salida que pida llave_salida`.

---

### 3. Procedencia de `abre` y Coincidencia de Cerraduras

- Las listas de espera se indexan por el identificador de cerradura que pide la puerta.
- Al activarse una llave $K$:
  - Se liberan las puertas de la lista de espera de `K.id`.
  - Si la ficha de la llave está disponible en el catálogo local (`AlmacenFichas`) y define `"abre"`, se liberan también las puertas de la lista de espera de `K.abre`.
  - Si la ficha no está en el catálogo local, se utiliza solo el `id` directo sin realizar solicitudes HTTP. Límite documentado: en ausencia de catálogo local, solo se reconocen llaves cuyo `id` coincida directamente con la cerradura.

---

### 4. Conteo de Solicitudes HTTP y Presupuesto

- La consulta `GET /criptas/<id>/llaves` suma exactamente **1 solicitud HTTP** al presupuesto de la expedición.
- Respuestas 429 consumen intentos adicionales contabilizados en `presupuesto_solicitudes`.
- Si los datos de llaves ya están almacenados en `AlmacenCripta` y la versión de la cripta coincide (o en `--offline`), la consulta HTTP no se ejecuta (0 solicitudes).

---

### 5. Modificaciones por Módulo

1. **`modelo/datos/fuente_datos.py`**:
   - `def llaves(self, id_cripta): raise NotImplementedError`.
2. **`modelo/datos/cliente_http.py`**:
   - `def llaves(self, id_cripta): return self._get(...)` hacia `/criptas/<id>/llaves`.
3. **`modelo/datos/cliente_offline.py`**:
   - `def llaves(self, id_cripta)` leyendo `<carpeta>/criptas/<id>/llaves.json`.
4. **`modelo/datos/fuente_almacen.py`**:
   - `def llaves(self, id_cripta)` delegando en `almacen_cripta.leer_llaves()`.
5. **`modelo/datos/almacen_cripta.py`**:
   - Métodos `tiene_llaves()`, `guardar_llaves(datos)`, `leer_llaves()`.
6. **`modelo/datos/esqueleto.py`**:
   - Interpretar `costo` en salidas como entero $\ge 1$ (`costo = max(1, int(salida.get("costo", 100)))`).
7. **`controlador/aplicacion.py`**:
   - Verificación previa antes de iniciar la partida. Si no es resoluble sin `--forzar`, no inicia.
   - En caso de contingencia (sin red/presupuesto sin copia local), emitir reporte `ESTADO: NO VERIFICADA` y no iniciar salvo `--forzar`.
8. **`main.py`**:
   - Modificador `--verificar <id>` con códigos de salida:
     - `0`: Resoluble.
     - `1`: No resoluble.
     - `2`: No verificada (falla red/presupuesto o cripta inexistente).
   - Modificador `--forzar` e incorporación de `"resolubilidad"` en `BENCHES`.
9. **`bench/generador_criptas.py`**:
   - Generador procedural determinista para calabozos sintéticos (tamaño, costos, cazadores con rango, cadenas de llaves, puertas inestables).
10. **`bench/bench_resolubilidad.py`**:
    - Comparativa incremental ($O(S + E + L)$) vs repetido ($O(L \cdot (S + E))$) sobre cadenas de llaves, más repetición de `bench_red.py`.
11. **`tests/crear_paquete_prueba.py` y `tests/cripta_de_prueba.py`**:
    - Actualizar fixtures con costos, cazadores con rango en unidades de costo, `llaves.json` con campo `"enemigo"` como ID de texto de instancia (ej. `"e-1203"`), cripta con ciclo y cripta de referencia con decenas de cazadores. Incrementar versiones de catálogo y cripta.
12. **`tests/test_resolubilidad.py`**:
    - Batería de pruebas unitarias citando cada requisito (`test_FR001_...` a `test_FR018_...`).

---

## Plan de Mediciones y Benchmarks

1. **`bench/bench_resolubilidad.py`**:
   - Criptas sintéticas encadenadas: $N$ salas en línea donde la sala $i$ contiene la llave para la puerta $i \to i+1$.
   - Mediciones con $N \in \{10, 50, 100, 200\}$.
   - Comparación del algoritmo incremental por etapas frente al repetido por llave.
2. **Repetición de `bench_red.py` (§5.6)**:
   - Medir el impacto de la consulta adicional `/llaves` en el presupuesto y tiempos de red.

---

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| **Dependencia del orden de exploración en la etapa** | Crítico | Resuelto con la regla de etapas: solo se cruzan puertas cuya llave se obtuvo en una etapa anterior; llaves de la etapa actual quedan pendientes hasta cerrarla. |
| **Desbordamiento de pila en recursión DFS** | Alto | Resuelto implementando DFS iterativa de 3 colores con pila propia (`pila = []`). |
| **Puertas internas entre salas alcanzables en la frontera** | Medio | Resuelto excluyendo de la frontera bloqueada cualquier puerta cerrada donde ambas salas (origen y destino) ya son alcanzables. |
| **Agotamiento del presupuesto de solicitudes** | Alto | Comprobación de `tiene_llaves()` en disco antes de consultar la red; código de salida 2 limpio ante error. |
