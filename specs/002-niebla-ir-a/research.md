# Research & Architectural Decisions: Niebla de guerra, mapa conocido y viaje automático "ir a"

**Feature**: `002-niebla-ir-a`  
**Author**: Kim (Estructuras de Datos y Mapa Conocido)  
**Date**: 2026-11-08  
**Constitution Authority**: `.specify/memory/constitution.md` (Version 1.0.0)

---

## 1. Bloque 1: Representación del conocimiento del jugador y niebla de guerra

### 1.1 Contexto y análisis del problema
En la primera parte del juego (P1), la visualización de la sala actual y sus salidas dependía del esqueleto completo de la cripta precargado. En la segunda parte (P2 §3.3 y §3.4), el jugador no posee omnisciencia sobre la cripta:
- Una sala puede estar en uno de tres estados: **Desconocida** (0), **Avistada** (1) o **Explorada** (2).
- De una sala **Avistada**, el jugador solo conoce la existencia de una salida hacia ella y su costo de cruce, pero **nunca** su identificador numérico ni su nombre o contenido.
- De una sala **Explorada**, el jugador conoce su nombre, identificador, todas sus salidas con sus costos y el estado recordado de cada puerta según la última observación.
- La memoria de cada puerta debe actualizarse cada vez que el jugador realiza una acción o turno en cualquiera de las dos salas conectadas por la salida.

### 1.2 Estructura de datos elegida para el conocimiento
- **Restricción constitucional**: Prohibición estricta de `dict` o `set` como índice o caché, y sin tablas hash (Principio I).
- **Decisión**: Dos arreglos contiguos (`list` de Python utilizada únicamente como bloque de memoria contigua indexada por enteros), preasignados con tamaño fijo al inicializar el mapa:
  1. `estado_salas: list[int]` de longitud $N$ (donde $N$ es el total de salas de la cripta, obtenido de `len(esqueleto.ids)`). Cada posición $p$ almacena el estado de conocimiento de la sala con `sala.indice == p`.
     - `0`: Desconocida (`ESTADO_DESCONOCIDA`)
     - `1`: Avistada (`ESTADO_AVISTADA`)
     - `2`: Explorada (`ESTADO_EXPLORADA`)
  2. `memoria_puertas: list[int]` de longitud $4N$, indexada por la fórmula de acceso plano:
     $$\text{posicion} = \text{sala.indice} \times 4 + \text{dir\_idx}$$
     donde $\text{dir\_idx} \in \{0: \text{N}, 1: \text{S}, 2: \text{E}, 3: \text{O}\}$.
     - `0`: No observada / desconocida (`PUERTA_DESCONOCIDA`)
     - `1`: Recordada abierta (`PUERTA_ABIERTA`)
     - `2`: Recordada cerrada (`PUERTA_CERRADA`)
- **Complejidad**:
  - Consulta del estado de una sala: $O(1)$.
  - Consulta de puerta recordada: $O(1)$.
  - Espacio total: $N + 4N = 5N$ enteros contiguos (para $N = 1000$ salas, $< 40\text{ KB}$ de memoria).
- **Alternativas consideradas**:
  - *Atributos directos en cada objeto `Sala` (`sala.estado_conocimiento`)*: Aunque es $O(1)$, mezcla el estado de simulación física del mundo con la percepción epistemológica del jugador. Además, complica la serialización compacta y la comparación limpia entre el mapa real y el mapa conocido.
  - *Árbol binario de búsqueda propio*: Daría consultas en $O(\log N)$, innecesariamente lento comparado con la indexación directa por `sala.indice` que ya existe en el modelo.
  - *Listas enlazadas*: Consultas $O(N)$, inaceptable para consultas frecuentes de renderizado y ruteo.

### 1.3 Mutaciones reversibles (C1) y Contadores $O(1)$ para la Línea de Tiempo (C6)
- **Principio central (C1)**: Todo cambio de estado del juego debe pasar por los métodos únicos de `Partida` (`cambiar`, `_lista_*`, `_inv_*`, y el método único de puertas), para que el pergamino lo revierta y la línea de tiempo lo registre.
- **Mecanismo de reversión**:
  - `Registro.cambiar` originalmente operaba sobre atributos de objetos mediante `getattr`/`setattr`.
  - Se extiende `Registro.cambiar(objeto, campo, valor)` para admitir la mutación indexada de arreglos contiguos cuando `objeto` es una `list` y `campo` es un entero `int` (índice):
    ```python
    if isinstance(objeto, list) and isinstance(campo, int):
        anterior = objeto[campo]
        objeto[campo] = valor
        if self._abierto is not None:
            self._abierto.append(lambda: objeto.__setitem__(campo, anterior))
        return
    ```
  - De esta forma, cualquier mutación de conocimiento:
    ```python
    partida.cambiar(self.conocimiento.estado_salas, sala.indice, ESTADO_EXPLORADA)
    partida.cambiar(self.conocimiento.memoria_puertas, pos_puerta, PUERTA_ABIERTA)
    ```
    queda automáticamente integrada en el grupo de reversión activo de `Registro`.
  - Al utilizar un pergamino de retroceso (`partida.usar_pergamino()`), `registro.deshacer_ultimo()` re-ejecuta `objeto.__setitem__(campo, anterior)` restaurando el estado previo de las salas y puertas en $O(1)$ por cambio sin reinicializaciones globales.
- **Contadores de Conocimiento $O(1)$ para la Línea de Tiempo de Axel (C6)**:
  - Para evitar que la línea de tiempo de Axel (Capacidad 004) deba recorrer los $N$ elementos de `estado_salas` en cada turno para generar su resumen de estado, `ConocimientoMapa` mantiene dos contadores enteros:
    - `num_exploradas: int` (inicia en 1 al instanciar la sala de inicio).
    - `num_avistadas: int` (inicia en la cantidad de vecinas directas de la sala inicial).
  - **Prevención estricta de conteo duplicado**:
    - Al explorar una nueva sala $u$: si $u$ estaba previamente en `ESTADO_AVISTADA`, se decrementa `num_avistadas` en 1; en todos los casos se incrementa `num_exploradas` en 1.
    - Por cada vecina directa $w$ de $u$: se consulta su estado actual. **Solo si $estado\_salas[w.indice] == ESTADO\_DESCONOCIDA$** se actualiza su estado a `ESTADO_AVISTADA` y se incrementa `num_avistadas` en 1. Si $w$ ya era vecina de otra sala explorada y ya figuraba como avistada o explorada, su contador **no se incrementa**.
  - Ambas mutaciones se ejecutan pasando por `partida.cambiar(self.conocimiento, "num_exploradas", nuevo_valor)`, permitiendo que el pergamino restaure el resumen en $O(1)$.
  - Método `resumen() -> tuple[int, int]`: retorna `(self.num_exploradas, self.num_avistadas)` en tiempo constante $O(1)$.

---

## 2. Bloque 2: Búsqueda de rutas compartida y Contrato C3 con Mariano

### 2.1 Especificación del Contrato C3
El contrato C3 establece la provisión de una estructura de montículo binario propio (`MonticuloMin`) y una función genérica de caminos mínimos (`dijkstra_acotado`) en `modelo/estructuras/monticulo_min.py` y `modelo/estructuras/dijkstra.py`, utilizada conjuntamente por el cazador de Mariano (Capacidad 001) y por el viaje automático "ir a" de Kim (Capacidad 002).

### 2.2 Diseño de `MonticuloMin` con Eliminación Perezosa
- **Restricción constitucional**: Prohibido `heapq`, `bisect`, `collections` y algoritmos de ordenamiento evaluados en librerías externas.
- **Implementación**:
  - Lista contigua de tuplas `(distancia, id_sala)`.
  - Operaciones estándar de árbol binario implícito sobre arreglo 0-indexado: hijo izquierdo $2i + 1$, hijo derecho $2i + 2$, padre $(i - 1) // 2$.
  - `insertar(elemento)`: Inserta al final y ejecuta `_flotar(pos)` en $O(\log K)$.
  - `extraer_min()`: Intercambia la raíz con el último elemento, extrae el último y ejecuta `_hundir(0)` en $O(\log K)$.
- **Eliminación Perezosa (Lazy Deletion)**:
  - En Dijkstra clásico, cuando se descubre una distancia menor hacia un nodo ya presente en la cola de prioridad, se requiere una operación `decrease_key`.
  - Implementar `decrease_key` en un montículo binario requiere un mapa o índice inverso (nodo $\to$ posición en el montículo), lo cual tentaría a usar una tabla hash prohibida o un arreglo inverso costoso.
  - **Solución con eliminación perezosa**: Simplemente se inserta una nueva tupla `(nueva_distancia, id_sala)` al montículo. Al extraer un elemento `(dist, id_sala)` del montículo, se consulta el arreglo contiguo de distancias vigente. Si `dist > dist[sala.indice]`, la entrada es obsoleta y se descarta inmediatamente.
  - Esto mantiene la pureza de estructuras propias sin índices auxiliares, garantizando $O((V + E) \log V)$ en tiempo.
- **Desempate determinista por menor ID**:
  - Al comparar tuplas `(distancia, id_sala)`, Python compara primero el elemento 0 (`distancia`). Ante igualdad numérica exacta de distancia, compara el elemento 1 (`id_sala`).
  - Como `id_sala` es un entero único de la sala, los empates en la cola de prioridad se resuelven de forma matemáticamente determinista a favor de la sala con menor `id` (Principio II).

### 2.3 Firma unificada de `dijkstra_acotado` (Alineada con 001)
En estricta conformidad con `specs/001-terreno-cazador/plan.md` y `specs/001-terreno-cazador/research.md`:
```python
def dijkstra_acotado(
    origen: Sala,
    mapa: Mapa,
    filtro_salida: Callable[[Salida], bool],
    cota_rango: Optional[int] = None,
    token_busqueda: int = 1,
    arreglo_dist: Optional[List[int]] = None,
    arreglo_marca: Optional[List[int]] = None
) -> tuple[List[int], List[int]]:
    """
    Calcula distancias de costo mínimo desde 'origen' sobre el grafo transitado.
    
    Parámetros:
      origen: Sala desde la cual se irradian las distancias mínimas.
      mapa: Instancia de Mapa con acceso a las salas de la cripta por indice.
      filtro_salida: Callable[[Salida], bool] -> True si la salida es transitable.
                     Recibe ÚNICAMENTE la instancia de Salida (que ya contiene
                     referencias a sala_a, sala_b, estado y costo).
      cota_rango: Entero máximo de costo a expandir, o None para sin límite.
      token_busqueda: Entero identificador único de la búsqueda actual.
      arreglo_dist: Arreglo preasignado de enteros de tamaño N.
      arreglo_marca: Arreglo preasignado de enteros de tamaño N.
      
    Retorna:
      (arreglo_dist, arreglo_marca)
    """
```

### 2.4 Administración de arreglos y prevención de colisiones en el mismo ciclo
- **Propuesta evaluada**: Cada llamador (Mariano para cazadores, Kim para "ir a") crea y mantiene su **propio juego independiente de arreglos** `dist` y `marca`, junto con su propio contador de secuencia `token_busqueda`. La función `dijkstra_acotado` es estrictamente **sin estado (stateless)**.
- **Justificación técnica**:
  1. **Independencia de subsistemas**: En un mismo turno o ciclo del reloj virtual, Mariano necesita consultar o actualizar su campo de distancias de cazadores hacia el jugador. En ese mismo ciclo, el jugador puede ejecutar un comando "ir a" o una consulta de mapa. Si ambos compartieran un único arreglo `dist` global en el módulo, la búsqueda de "ir a" sobreescribiría los valores del cazador.
  2. **Validez de la caché de cazador (SC-006 de Mariano)**: El diseño de Mariano se basa en conservar el `CampoDistancias` calculado durante múltiples turnos siempre que el jugador no se mueva y las puertas cercanas no cambien. Si "ir a" utilizara el mismo arreglo, invalidaría y corrompería la caché de Mariano en cada paso de planificación.
  3. **Seguridad contra re-entrancia**: Aunque Python sea monohilo en este entorno, tener llamadores con arreglos propietarios desacoplados previene efectos secundarios ocultos o dependencias de orden de ejecución entre el motor de enemigos y el controlador.
  4. **Costo de memoria insignificante**: Para $N = 1000$ salas, un juego de arreglos `dist` y `marca` consume menos de $16\text{ KB}$. Mantener dos juegos separados consume $\approx 32\text{ KB}$, lo cual es despreciable y garantiza aislamiento absoluto.
  5. **Reinicio $O(1)$ sin reinicialización**: Cada llamador incrementa su propio `token_busqueda += 1`. Un nodo $u$ se considera no visitado si `marca[u.indice] != token_busqueda`. No se requiere ningún bucle de limpieza $O(N)$ al iniciar una búsqueda.

### 2.5 Ejemplos mínimos de uso

#### Ejemplo 1: Llamador del cazador (Mariano)
```python
# Mariano calcula distancias desde la sala del jugador hacia los cazadores
self._token_cazador += 1
filtro_cazador = lambda salida: salida.esta_abierta()

dist, marca = dijkstra_acotado(
    origen=partida.jugador.sala,
    mapa=partida.mapa,
    filtro_salida=filtro_cazador,
    cota_rango=rango_maximo_activo,
    token_busqueda=self._token_cazador,
    arreglo_dist=self._dist_cazador,
    arreglo_marca=self._marca_cazador
)

# Cada cazador en sala_u consulta sus vecinas:
mejor_vecino = None
menor_costo = float("inf")
for i, salida in enumerate(sala_u.salidas):
    if salida is not None and salida.esta_abierta():
        v = salida.otro_lado(sala_u)
        if marca[v.indice] == self._token_cazador:
            costo_total = salida.costo + dist[v.indice]
            if costo_total < menor_costo or (costo_total == menor_costo and (mejor_vecino is None or v.id < mejor_vecino.id)):
                menor_costo = costo_total
                mejor_vecino = v
```

#### Ejemplo 2: Llamador del viaje automático "ir a" (Kim)
```python
# Kim calcula distancias desde la sala destino hacia la posición actual
self._token_navegacion += 1

filtro_jugador = lambda salida: (
    partida.conocimiento.es_explorada(salida.sala_a) and
    partida.conocimiento.es_explorada(salida.sala_b) and
    partida.conocimiento.puerta_recordada_abierta(salida)
)

dist, marca = dijkstra_acotado(
    origen=sala_destino,
    mapa=partida.mapa,
    filtro_salida=filtro_jugador,
    cota_rango=None,
    token_busqueda=self._token_navegacion,
    arreglo_dist=self._dist_navegacion,
    arreglo_marca=self._marca_navegacion
)

# El jugador en sala_actual evalúa sus vecinas inmediatas:
vecina_elegida = None
direccion_elegida = None
menor_costo = float("inf")
for dir_idx, salida in enumerate(sala_actual.salidas):
    if salida is not None and filtro_jugador(salida):
        v = salida.otro_lado(sala_actual)
        if marca[v.indice] == self._token_navegacion:
            costo_total = salida.costo + dist[v.indice]
            if costo_total < menor_costo or (costo_total == menor_costo and (vecina_elegida is None or v.id < vecina_elegida.id)):
                menor_costo = costo_total
                vecina_elegida = v
                direccion_elegida = DIRECCIONES[dir_idx]
```

---

## 3. Bloque 3: Viaje automático "ir a", búsqueda inversa y desempate

### 3.1 Búsqueda inversa desde el destino hacia el jugador
- **Problema de ruteo y desempate**: El requisito `FR-016` exige que, ante rutas de igual costo mínimo total hacia el destino, el primer paso del jugador seleccione deterministamente la sala vecina con el menor identificador (`v.id`).
- **Análisis matemático**:
  - El grafo de la cripta es no dirigido y las salidas tienen costos simétricos ($costo(A, B) = costo(B, A)$).
  - Si calculamos Dijkstra partiendo desde `sala_destino` hacia todas las salas:
    - $dist[u]$ representa la distancia mínima exacta desde la sala $u$ hasta `sala_destino`.
    - La sala actual del jugador $P$ tiene un costo de llegada a $destino$ igual a $dist[P]$.
    - Para dar el primer paso, el jugador solo necesita examinar sus vecinos directos transitables $v \in vecinos(P)$:
      $$C(v) = costo(P, v) + dist[v]$$
    - El costo mínimo factible es $C^* = \min_{v} C(v)$.
    - Los vecinos que logran $C^*$ son los candidatos óptimos.
    - El desempate se reduce a seleccionar $\arg\min_{v \in candidatos} v.id$.
  - Si por el contrario se hiciera una búsqueda hacia adelante desde el jugador hacia el destino:
    - Se requeriría mantener punteros de procedencia o etiquetas del primer vecino expandido a lo largo de todo el árbol de relajación de Dijkstra para resolver empates en el destino. Esto añadiría complejidad innecesaria y espacio adicional.
  - Por lo tanto, **la búsqueda inversa desde el destino hacia el jugador es la solución más simple, elegante y matemáticamente directa**.

### 3.2 ¿Conviene compartir o separar la implementación de Dijkstra?
- **Evaluación**:
  - *Argumento para compartir*:
    1. El núcleo del algoritmo (relajación de aristas, cola de prioridad con `MonticuloMin`, marcas de visita $O(1)$) es 100% idéntico.
    2. La única diferencia entre el cazador y el jugador es la regla de transitabilidad de las aristas (mundo físico real vs. mapa recordado) y la cota de rango.
    3. Al parametrizar la condición de paso mediante `filtro_salida` y el límite mediante `cota_rango`, una sola función cubre todas las necesidades del proyecto.
    4. Reduce la superficie de código, facilita el mantenimiento, unifica las pruebas de rendimiento y cumple con el Contrato C3.
  - *Argumento para separar*:
    - Si las firmas requirieran estructuras de datos drásticamente distintas. Sin embargo, ambos subsistemas operan sobre el mismo esqueleto de salas con `Sala.indice`.
  - **Veredicto y Justificación**: **Conviene compartir la implementación en `modelo/estructuras/`**. Se implementa una única función `dijkstra_acotado` genérica y stateless. Cada llamador mantiene sus propios arreglos preasignados para garantizar total independencia de ejecución.

---

## 4. Bloque 4: Controlador, órdenes individuales y bitácora (C4)

### 4.1 Descomposición de "ir a" en el Controlador y Clasificación (C4)
- **Requisito FR-017, FR-022 y Contrato C4**:
  - La orden `IR_A` es una **orden compuesta del controlador y NO pertenece a `ORDENES_DE_PARTIDA`**.
  - `ORDENES_DE_PARTIDA` se mantiene restringida a las acciones atómicas del juego: `(MOVER, ABRIR, ATACAR, ESPERAR, RECOGER, USAR, EQUIPAR, SOLTAR, PERGAMINO)`.
  - En `partida.log`, la orden "ir a" debe figurar exclusivamente como un comentario descriptivo (`# ir a <destino>`) y cada paso como un `mover <dir>` ordinario.
- **Flujo de ejecución en `Controlador`**:
  1. El usuario ingresa `ir a <id_sala>`. La vista genera `Orden(IR_A, id_sala)`.
  2. Validación preliminar ($O(1)$):
     - Si la sala no está en estado Explorada o no existe en la cripta: rechazo inmediato con mensaje claro, 0 turnos consumidos.
     - Si el jugador ya se encuentra en la sala destino: mensaje informativo ("Ya estás en esa sala"), 0 turnos consumidos.
  3. Comprobación de ruta inicial: se ejecuta Dijkstra inverso. Si no hay ruta alcanzable por caminos explorados y puertas recordadas abiertas: rechazo inmediato ("No hay ruta conocida"), 0 turnos consumidos.
  4. Si la ruta es viable:
     - Se registra el comentario en la bitácora: la aplicación asienta `# ir a <id_sala>` a través de `log.anotar_comentario(...)`.
     - Se inicia el bucle de pasos paso a paso:
       - En cada iteración:
         - Se recalculan distancias desde `destino` con el conocimiento vigente (FR-018).
         - Si el jugador llegó al destino: fin exitoso (FR-019).
         - Se evalúan las salidas transitables y se elige la dirección $D$ con menor costo total, desempatando por menor ID de vecino.
         - Se guarda la vida actual del jugador: `vida_previa = partida.jugador.vida`.
         - Se ejecuta la acción ordinaria: `aceptada = self._ejecutar_de_partida(Orden(MOVER, D))`.
           - Esto invoca `partida.mover(D)`, avanza el reloj, ejecuta turnos de enemigos, veneno y trampas, notifica a observadores y anota `mover <D>` en el log.
         - Se evalúan condiciones de interrupción inmediata (FR-019):
           1. ¿Partida terminada (victoria o derrota)? $\to$ detener.
           2. ¿Vida reducida (`jugador.vida < vida_previa`) por trampa o veneno? $\to$ detener con aviso de daño recibido.
           3. ¿Enemigos vivos en la sala actual (incluyendo dormidos que acaban de activarse)? $\to$ detener con aviso de presencia de enemigos.
           4. ¿Ruta bloqueada (la puerta observada estaba cerrada o no hay paso)? $\to$ detener con aviso de bloqueo.
       - Si se detiene por cualquier causa antes del destino, se notifica el motivo exacto mediante `self._avisar(motivo)` (FR-020).

### 4.2 Soporte de comentarios en `bitacora_partida.py` y Replay
- En `BitacoraPartida` (`modelo/datos/bitacora_partida.py`):
  - Actualmente el archivo dispone de `anotar(self, orden)`, `cerrar(self)` y `_escribir(self, linea)`.
  - Se añade el método público específico:
    ```python
    def anotar_comentario(self, texto: str) -> None:
        if self._archivo is None:
            return
        self._escribir("# " + _limpio(texto))
    ```
- En `leer_log(ruta)`: al parsear las órdenes del archivo de registro, cualquier línea que inicie con `#` o esté en blanco es descartada antes de procesar `Orden.desde_texto`.
- **Resultado en repeticiones (`--replay`)**: La repetición reproduce fielmente los movimientos individuales `mover <dir>` registrados paso a paso, garantizando determinismo exacto sin tener que reejecutar la lógica de búsqueda de rutas durante el replay.

---

## 5. Bloque 5: Separación de información y no filtración en la Vista

### 5.1 Fuga de información en el código existente
En el código actual:
- `vista/vista_consola.py`:
  ```python
  def _texto_salidas(self, partida):
      ...
      textos.append("%s -> sala %s (%s)" % (direccion, id_vecino, detalle))
  ```
- `vista/vista_pygame.py`:
  ```python
  def _dibujar_puerta(self, direccion, estado, id_vecino, llave):
      ...
      texto = "%s: sala %s" % (direccion, id_vecino)
  ```
Ambas vistas exponen directamente el `id_vecino` de todas las salidas, incluso si la sala de destino solo ha sido avistada y no explorada. Esto viola directamente el requisito `FR-004` y `FR-010`.

### 5.2 Corrección arquitectónica
- **Responsabilidad del Modelo**: `partida.salidas_visibles()` entrega la información ya tamizada según el conocimiento del jugador:
  `(direccion, estado_recordado, id_vecino if explorada else None, llave if observada else None, costo)`
- **Comportamiento en las vistas**:
  - En consola:
    - Si el vecino está explorado: `"N -> sala 4 (abierta, costo 100)"`
    - Si el vecino solo está avistado: `"N -> desconocida (abierta, costo 100)"`
  - En Pygame (`_dibujar_puerta`):
    - Si el vecino está explorado: etiqueta `"N: sala 4"`
    - Si el vecino solo está avistado: etiqueta `"N: desconocida"`
  - En ambas vistas, nunca se imprimen identificadores ni nombres de salas que no tengan `estado == ESTADO_EXPLORADA`.

---

## 6. Bloque 6: Formato de guardado binario v4, rechazo v3 y Coordinación C7

### 6.1 Estructura del formato de guardado versión 4
- En `modelo/datos/guardado_binario.py`:
  - Se incrementa `VERSION_FORMATO = 4`.
  - El encabezado general se mantiene con su firma mágica `CRPT` y versión `4`.
  - Se extiende `_empaquetar_general` y `_desempaquetar_general` para almacenar la información de niebla de guerra:
    1. Cantidad total de salas $N$ (`<H`).
    2. Arreglo de estados de salas: $N$ bytes (1 byte por sala, con valores 0, 1 o 2).
    3. Cantidad de puertas observadas registradas $P$ (`<H`).
    4. Por cada puerta observada: índice de sala (`<H`), dirección (`<B`), estado recordado (`<B>`).
- **Coordinación C7 con Mariano (Enemigo.rango)**:
  - El campo `rango: int` del cazador es un atributo estático propio de la ficha del catálogo (`ficha.get("rango", 0)`), no un estado mutable en partida.
  - **Acuerdo C7**: El campo `rango` **no se persiste en el bloque binario de enemigos** de `SalaGuardada`. La estructura de enemigos permanece idéntica (`[instancia, tipo, vida, tiempo]`). Al cargar la partida, `mapa.incorporar` recupera la ficha desde el catálogo local, asignando `enemigo.rango = ficha.get("rango", 0)` sin tocar la estructura binaria de salas.
- **Manejo de versiones previas (FR-024)**:
  - En `_leer_encabezado`:
    ```python
    if version != VERSION_FORMATO:
        if version == 3:
            raise ErrorFormato("versión de formato 3 incompatible (se esperaba 4): formato previo sin soporte de niebla de guerra")
        raise ErrorFormato(f"versión de formato {version} incompatible (se esperaba {VERSION_FORMATO})")
    ```
  - Al capturar `ErrorFormato` en `persistencia_partida.py`, se emite un `ErrorCarga` descriptivo que el controlador muestra al usuario sin alterar la sesión en curso ni corromper datos.

---

## 7. Bloque 7: Plan de mediciones de rendimiento (`--bench`)

### 7.1 Nuevo benchmark: `bench/bench_mapa_conocido.py`
Se integrará en `main.py` bajo el nombre `mapa_conocido` para verificar los criterios de éxito:
1. **SC-001 (Tiempo de cálculo "ir a")**:
   - Generación de criptas sintéticas con $N = 50, 200, 500, 1000$ salas.
   - Medición del tiempo de ejecución de `dijkstra_acotado` con todas las salas exploradas.
   - Meta medible: $< 5.0\text{ ms}$ en la cripta de referencia de 1000 salas.
2. **SC-002 (Consulta $O(1)$ de sala y puerta recordada)**:
   - Medición de $10^6$ consultas indexadas a `estado_salas` y `memoria_puertas` en criptas de distintos tamaños ($N=10, 100, 1000$).
   - Demostración de tiempo medio constante e independiente de $N$.
3. **SC-003 (Costo de exploración proporcional a salidas)**:
   - Medición del tiempo de revelar una sala y actualizar sus vecinas (con y sin antorcha).
   - Constancia frente al tamaño total acumulado del mapa conocido.
4. **SC-004 (Costo de registrar y revertir conocimiento)**:
   - Medición de 10,000 operaciones de `cambiar` y `deshacer_ultimo` sobre arreglos de conocimiento.
   - Verificación de tiempo constante $O(1)$.

### 7.2 Repetición de benchmarks de regresión
Para asegurar que los cambios en `guardado_binario.py`, `sala.py` y `partida.py` no degradan los subsistemas existentes:
- `python main.py --bench cache`
- `python main.py --bench lista_ordenada`
- `python main.py --bench ordenamiento`
- `python main.py --bench guardado`
- `python main.py --bench mapa_conocido`
