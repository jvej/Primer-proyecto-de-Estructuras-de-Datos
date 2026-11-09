# Contrato de Viaje Automático "ir a": Controlador, Bitácora y Replay

**Identificador**: `CONTRATO-IR-A` (C4)  
**Participantes**: Kim (Controlador / Navegación "ir a") y Axel (Registro / Replay / Bitácora)  
**Módulos acordados**: `controlador/orden.py`, `controlador/controlador.py`, `modelo/datos/bitacora_partida.py`, `controlador/aplicacion.py`  
**Estado**: Especificado para implementación conforme a FR-014..FR-023

---

## 1. Definición de la Orden en el Controlador

### 1.1 Orden Compuesta de Interfaz: `IR_A`
En `controlador/orden.py`:
```python
IR_A = "ir_a"
```

- **Regla fundamental de clasificación (C4)**:
  `IR_A` es una **orden compuesta del controlador** y **NO pertenece a `ORDENES_DE_PARTIDA`**.
  - `ORDENES_DE_PARTIDA` permanece restringida a las acciones atómicas del juego:
    `(MOVER, ABRIR, ATACAR, ESPERAR, RECOGER, USAR, EQUIPAR, SOLTAR, PERGAMINO)`.
  - `Orden(IR_A, id_destino).es_de_partida()` retorna `False`.
  - No se invoca `a_texto()` sobre `IR_A`, impidiendo que se asiente directamente como acción ordinaria en el archivo de repetición.
- **Sintaxis de entrada**: `ir a <id_sala>` (ej. `ir a 4`).

---

## 2. Registro de Comentarios en Bitácora (C4)

### 2.1 Anotación de Comentarios en `BitacoraPartida`
En el código base actual, `BitacoraPartida` solo dispone del método `anotar(self, orden)` para órdenes que implementan `a_texto()`. Para satisfacer el requisito `FR-022` y el contrato C4:
- Se incorpora en `modelo/datos/bitacora_partida.py` el método específico:
  ```python
  def anotar_comentario(self, texto: str) -> None:
      """Escribe una línea de comentario prefijada con '#' en el archivo de log."""
      if self._archivo is None:
          return
      self._escribir("# " + _limpio(texto))
  ```
- En `Aplicacion` (`controlador/aplicacion.py`):
  ```python
  def registrar_comentario(self, texto: str) -> None:
      if self.log is not None:
          self.log.anotar_comentario(texto)
  ```
- El controlador notifica el inicio de la orden mediante un observador de comentarios o invocando el despachador de la aplicación.

### 2.2 Descarte de Comentarios en Replay
En `modelo/datos/bitacora_partida.py`:
- Al leer el archivo de repetición con `leer_log(ruta)`, toda línea cuyo contenido inicie con `#` (tras `strip()`) se descarta como comentario explicativo y no se envía a `Orden.desde_texto`.
- **Garantía**: El reproductor (`--replay`) únicamente procesa los movimientos atómicos `mover <dir>` ejecutados paso a paso durante la partida original, garantizando determinismo de 100% sin recalcular rutas en tiempo de repetición.

---

## 3. Protocolo de Ejecución en `Controlador`

El controlador gestiona `IR_A` dentro de `_ejecutar_de_interfaz` o mediante `_ejecutar_ir_a(orden)` siguiendo este protocolo determinista:

1. **Validación Previa sin Costo de Tiempo** (FR-014, Edge Cases):
   - Si `id_destino` no existe en la cripta o `partida.conocimiento.estado_por_id(id_destino) != ESTADO_EXPLORADA`:
     - Rechazar con mensaje informativo: `"La sala destino no está explorada o no existe."`
     - Retorna `False` sin consumir tiempo del reloj virtual ni turnos.
   - Si `id_destino == partida.jugador.sala.id`:
     - Mensaje informativo: `"Ya te encuentras en esa sala."`
     - Retorna `True` sin consumir tiempo.
   - Comprobación preliminar de ruta: si no existe camino alcanzable usando salas exploradas y puertas recordadas abiertas:
     - Rechazar con mensaje: `"No hay ruta conocida disponible hacia el destino."`
     - Retorna `False` sin consumir tiempo.

2. **Registro de la Intención**:
   - Se escribe el comentario en la bitácora: `# ir a <id_destino>`.

3. **Ejecución Paso a Paso como Acciones Ordinarias** (FR-017, FR-018):
   - Se itera paso a paso:
     a. Recalcular distancias desde `id_destino` hacia todas las salas con el conocimiento vigente.
     b. Si el jugador ya se encuentra en `id_destino`: terminar con éxito (`"Has llegado a tu destino."`).
     c. Evaluar las salidas transitables de la sala actual y seleccionar la vecina con menor costo acumulado total, desempatando por menor ID numérico entero (`FR-016`).
     d. Determinar la dirección `dir_paso` hacia dicha vecina.
     e. Registrar la vida antes del paso: `vida_antes = partida.jugador.vida`.
     f. Despachar el paso individual como orden de partida estándar:
        ```python
        aceptada = self._ejecutar_de_partida(Orden(MOVER, dir_paso))
        ```
        Esto garantiza que:
        - Se invoque `partida.mover(dir_paso)` cobrando el costo de terreno de la salida.
        - Se registre `mover <dir_paso>` como orden regular en `partida.log`.
        - Transcurran los turnos y eventos de la agenda (enemigos, trampas, veneno).
     g. Evaluar condiciones de parada reactiva inmediata (FR-019, FR-020):
        - **Muerte o fin de juego**: Si `partida.estado != "jugando"`, detener el viaje.
        - **Daño recibido**: Si `partida.jugador.vida < vida_antes`, detener con mensaje:
          `"Viaje automático interrumpido: has recibido daño."`
        - **Enemigos presentes**: Si `len(partida.enemigos_en_sala()) > 0` (enemigos vivos, incluyendo dormidos que despertaron al entrar):
          `"Viaje automático interrumpido: presencia de enemigos en la sala."`
        - **Bloqueo o camino interrumpido**: Si `not aceptada` o el recálculo indica ausencia de ruta abierta viable:
          `"Viaje automático interrumpido: ruta bloqueada por puerta cerrada o camino intransitable."`

---

## 4. Reversión con Pergamino (FR-023)
- Debido a que cada paso de movimiento se ejecutó mediante `_ejecutar_de_partida(Orden(MOVER, dir))` abriendo y cerrando su propio grupo en `Registro`, el uso de un pergamino de retroceso (`partida.usar_pergamino()`) invoca `registro.deshacer_ultimo()`, revirtiendo **única y exclusivamente el último paso individual de movimiento** y cancelando cualquier continuación automática del viaje.
