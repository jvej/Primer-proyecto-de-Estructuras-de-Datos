# Contrato C2: Puertas, Observación y Actualización de Memoria

**Identificador**: `CONTRATO-C2`  
**Participantes**: Kim (Conocimiento / Mapa conocido), Mariano (Motor / C2 Despachador de puertas), Axel (Línea de tiempo)  
**Módulos acordados**: `modelo/juego/partida.py`, `modelo/juego/efectos.py`, `modelo/juego/conocimiento.py`  
**Estado**: Activo en el código existente (`partida.py`, commit `af4ebda`); alineado con la implementación real

---

## 1. Punto Central de Mutación de Puertas
Todo cambio de estado físico de una puerta en la cripta se efectúa exclusivamente a través del método centralizado de `Partida`:

```python
def cambiar_estado_puerta(self, salida, nuevo_estado: str) -> bool:
    """
    Punto único de mutación de puertas (FR-008, Contrato C2).
    Retorna True si hubo un cambio efectivo, False si ya tenía ese estado o si salida es None.
    """
    if salida is None or salida.estado == nuevo_estado:
        return False
    estado_anterior = salida.estado
    self.cambiar(salida, "estado", nuevo_estado)
    if not self._en_retroceso:
        for obs in self._observadores_puertas:
            obs(salida, estado_anterior, nuevo_estado)
    return True
```

Cualquier invocación en `partida.abrir(dir)` y en `efectos.programar_cierre(salida)` delega en este método.

---

## 2. Suscripción y Despacho Directo de Notificaciones
`Partida` mantiene la lista `self._observadores_puertas = []`. Los componentes interesados se registran con `suscribir_cambio_puerta(observador)` y se dan de baja con `desuscribir_cambio_puerta(observador)`.

### 2.1 Despacho de Notificaciones
- Las notificaciones **se despachan directamente dentro de `cambiar_estado_puerta`** iterando sobre `self._observadores_puertas`.
- **Firma del Callback**:
  ```python
  def observador_puerta(salida: Salida, estado_anterior: str, nuevo_estado: str) -> None:
  ```

### 2.2 Receptores y Comportamiento
1. **Conocimiento del Mapa (`ConocimientoMapa` de Kim)**:
   - Si el jugador se encuentra físicamente en `salida.sala_a` o en `salida.sala_b`, actualiza la memoria recordada de la puerta al nuevo estado.
   - Si el jugador no se encuentra en ninguna de las dos salas conectadas, la memoria recordada **no se altera**.
2. **Consumidor de rutas de cazador (`PlanificadorCazador`)**:
   - En `modelo/juego/cazador.py`, posee arreglos y token propios, usa Dijkstra con filtro de puertas fisicas abiertas y recalcula el campo en `decidir_movimiento`. `invalidar_todo()` incrementa su token. No se afirma una clase CampoDistancias ni una invalidacion selectiva por rango suscrita a este callback sin evidencia. El despacho C2 conserva la posibilidad de registrar observadores; al retroceder se mantiene la invalidacion general de rutas.
3. **Línea de Tiempo (Axel)**:
   - Registra el evento de cambio de estado de puerta si corresponde.

### 2.3 Tratamiento del Retroceso Temporal
- Durante la ejecución de `usar_pergamino()`, `Partida` establece `self._en_retroceso = True` mientras ejecuta `self.registro.deshacer_ultimo()`.
- Por consiguiente, `cambiar_estado_puerta` **silencia las notificaciones a `_observadores_puertas`** durante el retroceso, evitando eventos duplicados o deltas espurios.
- Al concluir la reversión, `Partida` ejecuta `self._notificar_invalidacion_rutas()` para alertar a los cálculos de rutas derivados.

---

## 3. Actualización de Memoria en Acciones Locales (FR-006)
- **Regla**: Cada vez que el jugador ejecuta una acción voluntaria (moverse, esperar, atacar, usar objeto, etc.) o se resuelve un turno del jugador en una sala:
  - El sistema itera sobre las salidas de la sala actual del jugador.
  - Para cada salida que posea una puerta, se sincroniza la memoria recordada de dicha puerta con el estado físico real (`PUERTA_ABIERTA` o `PUERTA_CERRADA`).
- **Reversión con Pergamino**:
  - Toda actualización de la memoria de puertas se registra pasando por `partida.cambiar(self.conocimiento.memoria_puertas, pos, nuevo_estado)`.
  - Al utilizar un pergamino de retroceso, el inverso restaura la memoria previa si no hubo una observacion permanente posterior de esa celda; en ese caso FR-010 de 004 exige conservar esa observacion mediante generaciones.

## Integracion verificada con FR-010 de 004

Partida vincula conocimiento.memoria_puertas a Registro. Solo ese arreglo
recibe generaciones por posicion O(1). Captura historica C1 precede al inverso
condicionado o al incremento permanente y a la escritura. Fuera de grupo,
_recordar_puerta registra ambos extremos incluso si se observa el mismo valor.
No se explora la sala vecina al recordar su puerta. Evidencia:
`tests.test_fr010_generaciones_002` (12 pruebas) y
`test_FR010_destino_compartido_inverso_y_persistente` de test_linea_tiempo.
