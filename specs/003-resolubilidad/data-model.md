# Data Model: Verificación de Resolubilidad y Extensión del Servicio Web

**Feature**: `003-resolubilidad`  
**Date**: 2026-11-08  
**Spec Reference**: `specs/003-resolubilidad/spec.md`

Este documento describe las entidades de datos, campos, invariantes y estructuras internas en memoria utilizadas para el análisis de resolubilidad y las extensiones de la API de CRIPTA.

---

## 1. Entidades del Dominio y Contratos de Datos

### 1.1 Salida / Puerta (`Esqueleto`)
Representa una conexión orientada entre la sala actual y una sala adyacente dentro del esqueleto topológico de la cripta.

- **Campos**:
  - `sala` (*int*): Identificador numérico de la sala de destino.
  - `direccion` (*str*): Dirección cardinal de salida, restringida a `"N"`, `"S"`, `"E"`, `"O"`.
  - `estado` (*str*): `"abierta"` o `"cerrada"`.
  - `costo` (*int*): Costo de desplazamiento por la salida. Entero mayor o igual a 1 (`costo >= 1`). Si no viene especificado en la respuesta JSON del servicio web, toma obligatoriamente el valor por defecto `100`.
  - `llave` (*str | None*): Identificador textual de la llave requerida para abrir la salida si está cerrada. Puede ser `None` si la puerta está cerrada sin llave asociada o si está abierta.
- **Invariantes**:
  - `costo >= 1`.
  - Si `estado == "abierta"`, la puerta es transitable de inmediato en la verificación.
  - Si `estado == "cerrada"` y `llave is None`, la puerta es permanentemente infranqueable durante la verificación y forma parte de la frontera bloqueada si conecta una sala alcanzable con una no alcanzable.

---

### 1.2 Ficha de Catálogo de Enemigo
Representa una plantilla de entidad del catálogo (`catalogo`) con soporte para los nuevos atributos de IA y percepción.

- **Campos**:
  - `id` (*str*): Identificador textual único de la ficha (ej. `"ent_cazador_cripta"`).
  - `clase` (*str*): `"enemigo"`.
  - `nombre` (*str*): Nombre legible del enemigo.
  - `comportamiento` (*str*): Estrategia de IA. Admite `"errante"`, `"guardian"`, `"rastreador"` y el nuevo valor `"cazador"`.
  - `rango` (*int*): Radio de percepción medido en **unidades de costo** de desplazamiento (no en número de salas) para enemigos cazadores.
  - `suelta` (*list[str]*): Lista de identificadores de objetos o llaves que el enemigo porta y deja caer al ser derrotado.
- **Invariantes**:
  - El modelo de juego y el catálogo preservan `"cazador"` y `"rango"` intactos desde la fuente de datos hasta la creación de instancias de `Actor`/`Enemigo`.

---

### 1.3 Ubicación de Llave
Información devuelta por la consulta `GET /criptas/<id>/llaves` y procesada para la verificación de alcanzabilidad.

- **Campos**:
  - `id` (*str*): Identificador textual de la llave (ej. `"itm_llave_bronce"`).
  - `sala` (*int*): Sala donde se encuentra la llave en el suelo o sala inicial donde inicia el enemigo que la porta.
  - `enemigo` (*str | None*): Identificador de texto de la instancia de enemigo que la porta (por ejemplo `"e-1203"`), o `None` si la llave está en el suelo. En este caso, la llave reside en el campo `suelta` de dicha instancia de enemigo.
  - `abre` (*str | None*): Identificador de la cerradura o puerta que esta llave desbloquea según su ficha del catálogo local (si existe en el catálogo local).
- **Invariantes**:
  - En la verificación de resolubilidad, una llave se considera disponible para el jugador en el momento en que se alcanza la sala correspondiente a su `sala`.

---

### 1.4 Reporte de Resolubilidad
Resultado estructurado emitido tras el análisis topológico de la cripta.

- **Campos**:
  - `estado` (*str*): `"RESOLUBLE"`, `"NO RESOLUBLE"` o `"NO VERIFICADA"`.
  - `orden_llaves` (*list[tuple[int, list[str]]]*): Lista de tuplas `(numero_etapa, lista_llaves_ordenadas)`. Solo presente si `estado == "RESOLUBLE"`.
  - `llaves_no_obtenibles` (*list[str]*): Lista ordenada lexicográficamente de llaves que no pudieron alcanzarse.
  - `frontera_bloqueada` (*list[tuple[int, str, int, str | None]]*): Lista de puertas cerradas adyacentes a la región explorada `(id_sala_origen, dir, id_sala_destino, llave_pedida)`. **Excluye estrictamente** puertas cuyas dos salas (origen y destino) ya son alcanzables.
  - `ubicacion_llaves` (*list[tuple[str, str]]*): Lista de pares `(id_llave, descripcion_ubicacion)` para las llaves requeridas por la frontera bloqueada o faltantes.
  - `ciclos` (*list[str]*): Lista de cadenas representativas de dependencias circulares detectadas (ej. `"itm_a -> itm_b [sala 3 (S)] -> itm_a [sala 8 (O)]"`).
  - `motivo` (*str | None*): Mensaje explicativo cuando la verificación no se completa o se detecta una anomalía de diseño.

---

## 2. Estructuras de Datos Internas en Memoria (Algoritmo)

Conforme a la Constitución (Principio I), está prohibido el uso de `dict` y `set` como índices, `heapq`, `bisect`, `collections` y `sorted()`. El algoritmo de resolubilidad implementa almacenamiento contiguo mediante listas nativas indexadas (`list`):

```text
[0 .. S-1] Salas del Esqueleto
  │
  ├── visitado: list[bool]                  # Marca de alcanzabilidad O(1)
  ├── vecinos_indexados: list[list[tuple]]  # Aristas traducidas a índices [0..S-1]
  └── etiqueta_llave: list[int]             # Llave de la puerta más cercana que protege la sala
```

1. **Tabla de correspondencia de Salas (`id_sala -> indice_entero`)**:
   - Resuelta una única vez al inicio mediante el ordenamiento existente en `Esqueleto` (`ListaOrdenada.buscar`).
   - Genera una lista contigua de tamaño $S$ donde cada entrada contiene las 4 posibles salidas con sus destinos ya convertidos a índices $[0, S-1]$.

2. **Tabla de Cerraduras/Llaves (`identificador_cerradura -> indice_cerradura`)**:
   - Arreglo ordenado contiguo de IDs textuales que las puertas pueden pedir como llave, de tamaño $C \le L$.
   - Búsqueda binaria propia implementada para resolver `id -> indice` en $O(\log C)$.

3. **Listas de Espera (`listas_espera`)**:
   - Lista contigua de tamaño $C$ indexada por el identificador que pide la puerta, donde `listas_espera[idx_cerradura]` es una lista contigua de puertas `[(pos_origen, dir, pos_destino), ...]`.
   - Inserción en $O(1)$ amortizado al encontrar una puerta cerrada cuya llave no ha sido obtenida en una etapa previa.
   - Al activarse una llave, se liberan las listas de espera asociadas a su `id` y, si su ficha está disponible en el catálogo local, también la lista de espera asociada a su atributo `abre`. Si la ficha no está en el catálogo local, se usa únicamente su `id` (sin realizar solicitudes HTTP).

4. **Frontera Bloqueada**:
   - Compuesta por las puertas cerradas $(u \to v)$ donde `visitado[u] == True` y `visitado[v] == False`.
   - Las puertas que conectan dos salas ya alcanzadas (`visitado[u] == True` y `visitado[v] == True`) quedan expresamente excluidas de la frontera bloqueada.

5. **Grafo de Dependencias de Llaves (`grafo_dependencias`) y Detección de Ciclos**:
   - Al continuar el recorrido más allá de la frontera bloqueada, cuando se cruza otra puerta cerrada, las salas detrás de ella toman como etiqueta la llave de **esa puerta** (la más cercana), no la de la frontera.
   - Las etiquetas se asignan en orden determinista (recorriendo la frontera ordenada por `id_sala` y dirección `N`, `S`, `E`, `O`).
   - El grafo de dependencias almacena aristas $X \to Y$ (la llave $X$ está detrás de una puerta que pide $Y$).
   - La detección de ciclos se ejecuta mediante un algoritmo DFS de 3 colores **estrictamente iterativo con pila propia** (`pila = []`), evitando la recursión de Python para prevenir desbordamientos de pila (`RecursionError`).
