# Contrato C3: Búsqueda de Rutas Compartida (Dijkstra Acotado y Montículo Binario)

**Identificador**: `CONTRATO-C3`  
**Participantes**: Kim (Autor / Estructuras y Niebla de guerra) y Mariano (Consumidor / Terreno y Cazador)  
**Módulos acordados**: `modelo/estructuras/monticulo_min.py` y `modelo/estructuras/dijkstra.py`  
**Estado**: Formalizado y alineado con `specs/001-terreno-cazador/plan.md` y `specs/001-terreno-cazador/research.md`

---

## 1. Propósito
Proveer una implementación determinista y compartida del algoritmo de Dijkstra acotado sobre grafos ponderados con aristas no dirigidas y costos enteros $\ge 1$, utilizando un montículo binario propio sin dependencias externas (`heapq`, `collections`, `bisect`, ni tablas hash), con eliminación perezosa, marcas de búsqueda para reinicio en tiempo constante $O(1)$ y resolución de empates por menor identificador de sala.

---

## 2. Especificación de `MonticuloMin`

### 2.1 Archivo: `modelo/estructuras/monticulo_min.py`
Clase que implementa una cola de prioridad de mínimos sobre un arreglo contiguo (`list`).

```python
class MonticuloMin:
    def __init__(self) -> None:
        """Crea un montículo binario vacío."""
        self._datos = []

    def insertar(self, elemento: tuple[int, int]) -> None:
        """
        Inserta una tupla (distancia, id_sala) en el montículo.
        Complejidad: O(log K), donde K es el número de elementos.
        """

    def extraer_min(self) -> tuple[int, int]:
        """
        Extrae y retorna la tupla con la menor distancia.
        Ante igual distancia, desempata deterministamente por menor id_sala.
        Lanza IndexError si el montículo está vacío.
        Complejidad: O(log K).
        """

    def es_vacio(self) -> bool:
        """Retorna True si no contiene elementos."""

    def __len__(self) -> int:
        """Retorna la cantidad de elementos en el montículo."""
```

### 2.2 Invariante de Eliminación Perezosa (Lazy Deletion)
Para evitar la necesidad de una tabla de símbolos inversa o índices prohibidos por la Constitución (Principio I), el montículo no implementa `decrease_key`. Cuando se relaja una arista hacia una sala ya encolada, se inserta una nueva tupla `(distancia_menor, id_sala)`. El llamador descarta tuplas con distancias obsoletas al momento de la extracción:
```python
dist, id_sala = heap.extraer_min()
if dist > dist_actual[sala.indice]:
    continue  # Entrada obsoleta descartada
```

---

## 3. Especificación de `dijkstra_acotado`

### 3.1 Firma exacta unificada con Capacidad 001
Conforme al acuerdo establecido en `specs/001-terreno-cazador/plan.md` y `research.md`:

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
```

### 3.2 Descripción de Parámetros y Retorno
- `origen`: Instancia de `Sala` desde la cual se irradian las distancias mínimas.
- `mapa`: Instancia de `Mapa`. Provee acceso a `mapa.salas_por_indice` (o lista contigua de salas por `Sala.indice`) para resolver referencias contiguas.
- `filtro_salida`: Función `(salida: Salida) -> bool`. Recibe **únicamente** la instancia de `Salida` a evaluar. Retorna `True` si la salida es transitable según los criterios del llamador. Dado que `Salida` contiene las referencias `salida.sala_a`, `salida.sala_b`, `salida.estado` y `salida.costo`, no requiere parámetros adicionales de sala.
- `cota_rango`: Entero opcional (`int | None`). Si es un entero $\ge 0$, ningún camino con costo acumulado $> \text{cota\_rango}$ es relajado (utilizado por el cazador de Mariano para acotar al rango máximo de acción). Si es `None`, se expande sin límite de costo (utilizado por "ir a" de Kim).
- `token_busqueda`: Entero positivo único que identifica la búsqueda actual (gestionado por el llamador). Por defecto 1.
- `arreglo_dist`: Lista contigua de enteros de tamaño $N$. Si se provee, la función modifica sus posiciones directamente. Al terminar, para cada sala alcanzada $v$ con `arreglo_marca[v.indice] == token_busqueda`, `arreglo_dist[v.indice]` contiene la distancia mínima exacta desde `origen` hasta $v$.
- `arreglo_marca`: Lista contigua de enteros de tamaño $N$. Almacena el identificador de la búsqueda actual. Un nodo $v$ no alcanzado en la búsqueda actual tiene `arreglo_marca[v.indice] != token_busqueda`.
- **Retorno**: Tupla `(arreglo_dist, arreglo_marca)`.

### 3.3 Garantía de Función Sin Estado (Stateless)
La función `dijkstra_acotado` **no almacena ningún estado global ni a nivel de módulo**. Toda la memoria de trabajo temporal es provista por el llamador o vive en variables locales durante la ejecución del algoritmo.

---

## 4. Política de Propiedad y Administración de Arreglos

### 4.1 Propiedad de Arreglos por Llamador
Cada subsistema cliente es dueño exclusivo de sus estructuras de memoria:
1. **Mariano (Motor de Cazadores)**:
   - Administra `self._dist_cazador: list[int]` y `self._marca_cazador: list[int]` de tamaño $N$.
   - Administra `self._token_cazador: int` (inicializado en 0).
2. **Kim (Viaje Automático "ir a")**:
   - Administra `self._dist_navegacion: list[int]` y `self._marca_navegacion: list[int]` de tamaño $N$.
   - Administra `self._token_navegacion: int` (inicializado en 0).

### 4.2 Prevención de Colisiones e Interferencia en el Mismo Ciclo
- **Justificación**: En un mismo pulso del reloj de juego, Mariano invoca el cálculo de rutas de cazadores y conserva su campo de distancias en caché a lo largo de turnos futuros (SC-006). Si el jugador ejecuta "ir a", la navegación de Kim utiliza exclusivamente `self._dist_navegacion` y `self._marca_navegacion`, sin alterar jamás los arreglos del cazador.
- **Resultado**: Cero riesgo de que dos búsquedas se pisen, cero recálculos forzados en la caché de Mariano y cero asignaciones dinámicas $O(N)$ en cada paso.

---

## 5. Ejemplos de Integración

### 5.1 Llamada de Mariano (Cazador)
```python
# Mariano ejecuta desde la posición del jugador acotado a su rango
self._token_cazador += 1
filtro_cazador = lambda salida: salida.esta_abierta()

dijkstra_acotado(
    origen=partida.jugador.sala,
    mapa=partida.mapa,
    filtro_salida=filtro_cazador,
    cota_rango=rango_maximo,
    token_busqueda=self._token_cazador,
    arreglo_dist=self._dist_cazador,
    arreglo_marca=self._marca_cazador
)
```

### 5.2 Llamada de Kim ("ir a")
```python
# Kim ejecuta búsqueda inversa desde el destino hacia el jugador
self._token_navegacion += 1
filtro_jugador = lambda salida: (
    partida.conocimiento.es_explorada(salida.sala_a) and
    partida.conocimiento.es_explorada(salida.sala_b) and
    partida.conocimiento.puerta_recordada_abierta(salida)
)

dijkstra_acotado(
    origen=sala_destino,
    mapa=partida.mapa,
    filtro_salida=filtro_jugador,
    cota_rango=None,
    token_busqueda=self._token_navegacion,
    arreglo_dist=self._dist_navegacion,
    arreglo_marca=self._marca_navegacion
)
```
