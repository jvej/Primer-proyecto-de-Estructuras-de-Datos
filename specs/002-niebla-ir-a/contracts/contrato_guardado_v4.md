# Contrato de Persistencia Binaria: Guardado Versión 4 y Coordinación C7

**Identificador**: `CONTRATO-GUARDADO-V4` (C7)  
**Participantes**: Kim (Persistencia y Formato Binario) y Mariano (Compatibilidad de Motor y Cazador)  
**Módulos acordados**: `modelo/datos/guardado_binario.py`, `modelo/datos/persistencia_partida.py`, `modelo/juego/actor.py`  
**Estado**: Codec v4 y carga T045/T046 implementados y probados; base 75cc63e.

---

## 1. Versión del Formato Binario

Se actualiza la constante en `modelo/datos/guardado_binario.py`:
```python
VERSION_FORMATO = 4
```

---

## 2. Incompatibilidad Explícita con Versión 3 (FR-024)

### 2.1 Regla de Rechazo
Un archivo binario generado con la versión 3 de la primera parte (P1) no almacena la información de niebla de guerra ni la memoria de puertas. Intentar cargarlo en la versión 4 provocaría estados inconsistentes o salas artificialmente descubiertas.

### 2.2 Implementación en `_leer_encabezado(f)`
```python
if version != VERSION_FORMATO:
    if version == 3:
        raise ErrorFormato("versión de formato 3 incompatible (se esperaba 4): formato previo sin soporte de niebla de guerra")
    raise ErrorFormato("versión de formato " + str(version) + " incompatible (se esperaba " + str(VERSION_FORMATO) + ")")
```

### 2.3 Tratamiento en `persistencia_partida.py`
La excepción `ErrorFormato` es capturada y convertida en `ErrorCarga`. El método `cargar()` reporta el error directamente al controlador, el cual muestra el aviso al jugador sin alterar la partida en curso, sin fallos silenciosos y sin corromper datos.

---

## 3. Coordinación C7 con Mariano: Persistencia de Cazadores y `rango`

### 3.1 Decisión Técnica sobre `Enemigo.rango`
En respuesta a la coordinación solicitada en `specs/001-terreno-cazador/plan.md` (Bloque 3, ítem 1):
- El campo `rango: int` del cazador es un atributo estático propio de la ficha del catálogo (`ficha.get("rango", 0)`), al igual que su velocidad o ataque base. No es un estado mutable del reloj de juego ni sufre alteraciones dinámicas en partida.
- **Acuerdo formal C7**: **El campo `rango` NO se persiste en el bloque binario de enemigos**.
- La estructura binaria de serialización de enemigos en `SalaGuardada` se mantiene estrictamente intacta en formato v4:
  `[instancia: str, tipo: str, vida: int, tiempo_siguiente: int]`.
- Al cargar una partida guardada en v4:
  - `app.preparar_reconstruccion(...)` entrega una candidata y aplicar_linea para reconstruir el estado antes de publicarlo.
  - Al incorporar cada sala, `mapa.incorporar(sala, contenido, resolutor)` recupera la ficha desde el catálogo local (`AlmacenFichas`), asignando `enemigo.rango = ficha.get("rango", 0)`.
- **Ventajas**:
  - Cero modificaciones a la estructura binaria de salas y actores.
  - Cero riesgo de desincronización entre el catálogo y el guardado.
  - Total compatibilidad con el motor de cazadores de Mariano.

---

## 4. Estructura de Datos Binaria en Versión 4

El bloque de datos generales (`_empaquetar_general` y `_desempaquetar_general`) se amplía exclusivamente para el conocimiento:

1. **Datos generales existentes**:
   - `reloj` (`<q`), `semilla` (`<q`), `vida` (`<i`), `sala_actual` (`<i`).
   - Inventario, `id_cripta`, `version_cripta`, `version_catalogo`, `nombre`, `ordenes`, `solicitudes`.
2. **Datos de Niebla de Guerra y Mapa Conocido (Añadidos en v4)**:
   - `n_salas_conocidas`: `uint16` (`<H`). Cantidad de salas en la cripta ($N$).
   - `estados_salas`: $N$ bytes contiguos (`<B` repetido $N$ veces).
     - Cada byte corresponde al estado de la sala con `sala.indice == i` ($0$: Desconocida, $1$: Avistada, $2$: Explorada).
   - `n_puertas_recordadas`: `uint16` (`<H`). Cantidad de entradas de memoria de puertas observadas ($P$).
   - Por cada una de las $P$ entradas:
     - `indice_sala`: `uint16` (`<H`).
     - `direccion`: `uint8` (`<B`) ($0..3$ para N, S, E, O).
     - `estado_recordado`: `uint8` (`<B`) ($1$: abierta, $2$: cerrada).

### 4.1 Invariante de Reconstrucción
Al cargar una partida guardada en v4:
- El codec decodifica estados y memoria en PartidaGuardada; no escribe en una Partida viva.
- Guardar obtiene app.lineas_para_reconstruir(), conserva orden y duplicados en el campo de ordenes existente y copia los arreglos de conocimiento.
- Cargar aplica cada linea mediante el callback de T045 y valida dentro del contexto. Los contadores se mantienen por replay; un recuento O(N) comprueba su coherencia.
- Se comparan exactamente los arreglos guardados y reconstruidos, sin reemplazar ConocimientoMapa, listas ni Registro. Discrepancias lanzan ErrorCarga y conservan la sesion anterior.
- N coincide con el mapa; estados y direcciones son validos; memoria no desconocida exige salida existente y coherencia de extremos; sala actual explorada.
- La carga mantiene partida_nueva=False, ordenes previas de reconstruccion y versiones exigidas mediante T045; no activa resolubilidad 003.
- La sala actual del jugador queda validada contra `sala_actual`.
- No se filtran datos no explorados al restaurar la sesión.

## Validacion binaria y limites

N y P son uint16; P cuenta posiciones de memoria, no puertas fisicas unicas.
Las entradas con valor 0 se omiten y se reconstruyen a cero. Se rechazan valores
invalidos, duplicados, indices fuera de N, truncamientos, longitudes/offsets
invalidos y datos sobrantes. El encabezado sigue `<4sHIQI>` con marca CRPT.
No hay CRC implementado ni se encontro exigencia contractual de CRC: la
integridad se comprueba estructuralmente y comparando la fotografia con replay.
El bloque de enemigos conserva instancia, tipo, vida y tiempo_siguiente.
Evidencia: tests.test_guardado_v4_002 (15), tests.test_carga_v4_002 (11),
tests.test_guardado_binario y casos FR014 de tests.test_historia_persistencia.
