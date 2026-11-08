# Research & Architectural Decisions: Terreno, cazador e invalidación de rutas

**Feature**: `001-terreno-cazador`  
**Author**: Mariano (Motor del juego)  
**Date**: 2026-11-07  
**Constitution Authority**: `.specify/memory/constitution.md` (Version 1.0.0)

---

## 1. Bloque 1: Costos de terreno y movimiento ponderado

### 1.1 Contexto y análisis de llamadores
En la primera parte (P1 §2.3), el costo base de moverse era una constante fija `COSTO_MOVER = 100`. En la segunda parte (P2 §3.1), cada salida puede declarar un entero `costo >= 1`, con valor predeterminado 100 si se omite, idéntico en ambos sentidos.

Revisión exhaustiva de llamadores actuales:
- `modelo/juego/sala.py`:
  - `Salida.__init__(self, sala_a, sala_b, estado="abierta", llave=None, cierre_automatico=None)`: Se agrega parámetro opcional `costo: int = 100` con validación `assert isinstance(costo, int) and costo >= 1`.
  - `Sala.conectar(self, direccion, otra, estado="abierta", llave=None, cierre_automatico=None)`: Se agrega parámetro opcional `costo: int = 100`. Se pasa directamente al constructor de `Salida`. Al ser compartida, la instancia única de `Salida` almacena `self.costo`, garantizando simetría matemática estricta ($A \to B$ y $B \to A$ comparten exactamente el mismo objeto `Salida`).
  - `Sala.__init__(self, id, nombre="")`: Se agrega `self.indice = None` para indexación contigua $O(1)$.
- `modelo/juego/mapa.py`:
  - `Mapa.__init__`: Lee `datos.get("costo", 100)` y asigna `sala.indice = p` (posición contigua en `esqueleto.ids`).
  - `Mapa.incorporar`: Normaliza `comportamiento = ficha.get("comportamiento", "guardian").lower().strip()` para aceptar "cazador", "guardian", "errante", "rastreador" sin fallas por mayúsculas o tildes.
- `modelo/juego/partida.py`:
  - `mover(self, direccion)`: Obtiene `salida = self.jugador.sala.salidas[DIRECCIONES.index(direccion)]` y ejecuta `self._accion(salida.costo, lambda: self._entrar(destino))`.
- `modelo/juego/costos.py`:
  - Conserva `COSTO_MOVER = 100` como valor de respaldo.
  - Conserva inalterados: `COSTO_ATACAR = 100`, `COSTO_ESPERAR = 100`, `COSTO_USAR_EQUIPAR = 50`, `COSTO_RECOGER_SOLTAR = 25`, `COSTO_ABRIR_PUERTA = 50`, `COSTO_TURNO_ENEMIGO = 100`.
  - Función `costo_accion(costo_base, velocidad)`: `max(1, costo_base * 100 // velocidad)`.
- `modelo/juego/comportamiento.py` y `motor_enemigos.py`:
  - `resolver_turno(partida, enemigo, ahora) -> int`: Ahora retorna el costo base consumido por la acción ejecutada:
    - Atacar: retorna `COSTO_ATACAR` (100).
    - Esperar (sin salidas o sin rastro): retorna `COSTO_ESPERAR` (100).
    - Desplazamiento de errante o rastreador: retorna `salida.costo`.
    - Cazador (ataque, espera o movimiento de costo mínimo): retorna el costo correspondiente.
  - `agendar_turno`: Recibe el valor retornado por `resolver_turno`, agenda el siguiente evento en `ahora + costo_accion(costo_real, enemigo.velocidad)`.

### 1.2 Reprogramación de velocidad (P1 §2.3)
La función existente en `agenda_eventos.py`:
```python
restante = evento.tiempo_siguiente - tiempo_actual
restante_nuevo = max(1, restante * velocidad_anterior // velocidad_nueva)
```
Demostración de corrección con el escenario de aceptación:
- Salida costo 300, velocidad 100 iniciada en $t = 0$: $tiempo\_siguiente = 0 + (300 \times 100 // 100) = 300$.
- En $t = 100$, velocidad pasa a 50: $restante = 300 - 100 = 200$.
- $restante\_nuevo = \max(1, 200 \times 100 // 50) = 400$.
- Evento reprogramado a: $tiempo\_actual + restante\_nuevo = 100 + 400 = 500$.
La fórmula de P1 es 100% compatible y no requiere modificación matemática, solo verificación de pruebas vinculadas a `FR-002`.

---

## 2. Bloque 2: Puertas y Contrato C2

### 2.1 Centralización del cambio de puertas
En el diseño actual, el estado de las puertas se modifica en:
1. `partida.abrir(direccion)`: `self.cambiar(salida, "estado", "abierta")`
2. `efectos.programar_cierre`: `partida.cambiar(salida, "estado", "cerrada")`
3. `partida.usar_pergamino`: revierte mutaciones registradas en `registro.py`.

### 2.2 Diseño del Contrato C2
Se establece en `Partida` un punto único de cambio de puertas:
```python
def cambiar_estado_puerta(self, salida, nuevo_estado):
    if salida.estado == nuevo_estado:
        return
    estado_anterior = salida.estado
    self.cambiar(salida, "estado", nuevo_estado)
    self._notificar_cambio_puerta(salida, estado_anterior, nuevo_estado)
```
Subscriptores desacoplados mediante lista de callbacks:
- `cache_rutas`: invalida el cálculo si la puerta afecta la región dentro del rango.
- `conocimiento` (Kim): actualiza memoria de puertas si el jugador observa la sala.
- `linea_tiempo` (Axel): registra el evento de puerta si corresponde.

### 2.3 Tratamiento del retroceso (evitar avisos o registros duplicados)
Cuando se usa el pergamino de retroceso, el mecanismo de `Registro` en `registro.py` invoca lambdas inversos (por ejemplo `setattr(salida, "estado", "cerrada")`).
Para que la caché de rutas se entere del retroceso sin que Axel duplique registros de deltas en la línea de tiempo:
- Durante la ejecución de `registro.deshacer()`, `Partida` activa una bandera temporal `self._en_retroceso = True`.
- Al finalizar el bloque de reversión, `Partida` emite una invalidación global de rutas (`cache_rutas.invalidar_todo()`).
- Esto evita notificaciones individuales redundantes durante la marcha atrás y garantiza que el siguiente cálculo del cazador refleje el estado restaurado.

---

## 3. Bloque 3: Cazador y Contrato C3

### 3.1 Búsqueda de rutas disponible y dependencias
Actualmente, el repositorio **no contiene** ningún algoritmo de Dijkstra ni montículo de mínimos (prohibido `heapq` según Constitución Principio I).
- **Responsable de C3**: Kim implementa `modelo/estructuras/monticulo_min.py` (montículo binario propio) y la función genérica `dijkstra_acotado`.
- **Compromiso del equipo**: Entrega pactada para el sábado 7 de noviembre.

### 3.2 Interfaz requerida para el Contrato C3
```python
def dijkstra_acotado(origen, mapa, filtro_salida, cota_rango=None, token_busqueda=1, arreglo_dist=None, arreglo_marca=None):
    """
    origen: Sala
    mapa: Mapa
    filtro_salida: Callable[[Salida], bool] -> True si es transitable
    cota_rango: int | None -> distancia máxima a expandir
    token_busqueda: int -> identificador de la búsqueda actual
    arreglo_dist: list[int]
    arreglo_marca: list[int]
    
    Retorna: (arreglo_dist, arreglo_marca)
    """
```

### 3.3 Cálculo Compartido vs. Búsqueda Individual
- **Búsqueda Individual**: Cada cazador corre un Dijkstra desde su propia sala hacia la del jugador acotado a su `rango`. Con $K$ cazadores, se realizan $K$ búsquedas independientes por ciclo.
- **Cálculo Compartido**: Como las salidas son simétricas ($costo(u, v) = costo(v, u)$), la distancia mínima desde cualquier sala $u$ hasta la sala del jugador $P$ es idéntica a la distancia desde $P$ hasta $u$.
  - Se ejecuta **un solo Dijkstra** desde la sala actual del jugador $P$, acotado a $R_{\max} = \max(\{c.rango \text{ para } c \text{ cazador activo}\})$.
  - Al terminar, cada cazador en sala $u$ solo tiene que revisar sus salidas abiertas locales ($O(\text{salidas})$):
    $$d_u = \min_{v \in vecinos\_abiertos(u)} (costo(u, v) + dist[v.indice])$$
    Si $d_u \le rango$, elige el vecino $v$ que minimiza $d_u$, desempatando por el menor `v.id` entero.
  - Con 30 cazadores, se realiza **1 búsqueda por ciclo en lugar de 30**.

### 3.4 Arreglos de tamaño fijo con Marca de Búsqueda (Token)
Para evitar el costo $O(N)$ de crear o reiniciar arreglos `dist = [INF] * N` en cada ciclo (donde $N$ es la cantidad de salas de la cripta):
- Se pre-asignan dos arreglos de tamaño $N$: `self._dist = [0] * N` y `self._marca = [0] * N`.
- Se mantiene un contador entero `self._token_busqueda = 0`.
- Al iniciar una búsqueda, `self._token_busqueda += 1`.
- Una sala con índice $i$ se considera no visitada si `self._marca[i] != self._token_busqueda` (en tal caso, su distancia lógica es $\infty$).
- Cuando se actualiza la distancia de $i$: `self._dist[i] = nueva_dist` y `self._marca[i] = self._token_busqueda`.
- **Costo de reinicialización**: $O(1)$. El trabajo depende únicamente de las salas expandidas dentro de $R_{\max}$.

---

## 4. Bloque 4: Invalidación de rutas y Benchmarking

### 4.1 Teorema de Validez del Cálculo Compartido
El cálculo compartido almacenado en `CampoDistancias` (que contiene las distancias desde la sala actual del jugador $P$ a todas las salas dentro de $R_{\max}$) **sigue siendo matemáticamente exacto y reutilizable** entre turnos sucesivos si y solo si:
1. El jugador permanece en la misma sala $P$.
2. Ningún cazador con rango estrictamente mayor a $R_{\max}$ se ha activado.
3. Ninguna puerta que tenga al menos un extremo a distancia $\le R_{\max}$ ha cambiado de estado (abierta/cerrada).

**Demostración del punto 3**:
Sea una puerta $e = (A, B)$ que cambia de estado (se abre o se cierra). Si tanto $\text{dist}(P, A) > R_{\max}$ como $\text{dist}(P, B) > R_{\max}$, cualquier camino que utilice la arista $e$ tendrá un costo estrictamente mayor que $R_{\max} + costo(e) > R_{\max}$. Por lo tanto, dicha arista no puede formar parte de ningún camino de costo $\le R_{\max}$ hacia ninguna sala en la región de interés. Las distancias hacia todas las salas dentro del rango permanecen idénticas a las que daría un recálculo desde cero.

### 4.2 Eventos que NO invalidan las rutas
- El desplazamiento de otros enemigos (errantes, rastreadores u otros cazadores).
- La muerte o daño de otros actores.
- Los cambios de velocidad o tiempo restante de otros actores.
- La apertura o cierre de puertas lejanas (ambos extremos con distancia $> R_{\max}$).

### 4.3 Diseño del Benchmark (`bench/bench_cazador.py`)
Para responder a los criterios `SC-004`, `SC-005` y `SC-006`:
1. **Instrumentación de SC-004**:
   - Medir el tiempo de cada ciclo individual entre dos decisiones del jugador.
   - Registrar: `tiempo_maximo_ms`, `ciclos_exceden_20ms` y percentiles (p50, p95, p99).
   - Condición de éxito: `ciclos_exceden_20ms == 0` y `tiempo_maximo_ms < 20.0`.
2. **Comparación SC-005 (Individual vs. Compartido)**:
   - Probar con 1, 10, 30 y 100 cazadores en cripta sintética con semilla determinista.
   - Variar rango: pequeño ($R = 250$) vs. grande ($R = 1500$).
   - Medir tiempo total de resolución por turno de cazadores y determinar el punto de cruce donde el cálculo compartido supera al individual.
3. **Comparación SC-006 (Reutilización vs. Recálculo continuo)**:
   - Escenario A: Puertas estables (sin puertas con cierre automático ni llaves).
   - Escenario B: Puertas inestables (múltiples puertas con cierre automático cada 200 pulsos).
   - Validar en cada paso que la decisión tomada por el cazador con caché sea idéntica a la calculada desde cero (`assert decision_reutilizada == decision_desde_cero`).
4. **Repetición de `bench_motor.py` (§5.6)**:
   - Ejecutar la agenda de eventos y el bucle de eventos incorporando cazadores activos y costos variables para contrastar contra los tiempos de la primera parte.
