# Investigación: alcance reducido de la línea de tiempo

Fecha: 2026-11-13. Investigación sobre código real; ninguna medición de la capacidad se ha ejecutado. Esta revisión reemplaza las propuestas de cambiar el reloj y crear formatos nuevos.

## R1. Captura sin cambiar el motor

**Decisión:** mantener `Registro.PilaAcotada(5)` y los inversos actuales. `Registro.cambiar` ya acepta atributo o posición de lista; capturar anterior/nuevo normalizados. `_lista_*` y `_inv_*` emiten operación, instancia y posición porque sus lambdas no describen datos recuperables. Una mutación es reversible si efectivamente se agregó inverso; no basta `registrar=True` sin grupo abierto.

**Motivo:** los mismos puntos únicos permiten agregar un consumidor histórico sin modificar los efectos de juego. `Partida.cambiar_estado_puerta` pasa por C1 antes de avisar a C2, así que no se necesita otro observador que duplique el delta.

**Alternativas:** comparar la partida completa por acción agrega trabajo/memoria por tamaño de estado; inspeccionar lambdas no obtiene valores nuevos; observar solo puertas pierde el resto del resumen.

## R2. Tiempo leído y checkpoint después del inicio

**Decisión:** cada delta lee `partida.reloj.tiempo_actual` al anotarse. `_avanzar` conserva su escritura directa y `_accion` conserva el inverso manual del reloj. Guardar relojes de fronteras pre/postacción; no hace falta una cadena de deltas de reloj. Para una consulta temporal el reloj del resultado es t; para #k se usa el reloj de su frontera.

**Evidencia:** `Partida._avanzar` mueve el reloj y ejecuta eventos; `Partida._accion` abre grupo, registra el inverso de reloj, incrementa acciones, ejecuta efecto y avanza; `Partida.iniciar` hace `jugador.mover_a` y `sala.marcar_visita_jugador` antes de aceptar acciones.

**Motivo:** tomar checkpoint 0 después de `iniciar()` absorbe posición, rastro, sala inicial y efectos de inicialización sin editar esos métodos. Se pide a Jeferson conectar `inicializar_historia(partida, K)` inmediatamente después de iniciar y antes del bucle de reconstrucción.

**Alternativas descartadas:** reloj mediante `cambiar`, retirar su inverso manual o canalizar escrituras iniciales por otras clases. Se eliminan del plan.

## R3. Proyección y adopción desde archivos propios

**Decisión:** proyección de jugador, inventario ordenado, efectos, conocimiento, resultado y estados necesarios de actores incorporados. No copiar Partida, agenda, funciones ni random. `Partida.efectos_activos` ya retorna su lista actual: reutilizar su criterio sobre campos históricos, no invocar estado actual para completar una consulta.

**Evidencia:** `ConocimientoMapa.resumen` da contadores pero no qué salas eran conocidas; hacen falta `estado_salas` y `memoria_puertas`. Copiar solo enemigos de la sala del checkpoint es insuficiente al consultar una sala diferente. `Objeto.id` es id de ficha, no identidad de instancia. `Inventario.quitar/restaurar` usa nodos vivos que no pertenecen a una foto aislada.

**Motivo:** adoptar entidad en foto inicial o al primer encuentro en C1, capturando sus datos anteriores al primer cambio. `resumen_historico.py` puede asignar tokens auxiliares a los objetos existentes sin editar sus clases y conservar bases inmutables por referencia. La consulta no carga contenido ni observa puertas. Si la captura descubre una carencia real posterior al inicio, se pide al dueño el mínimo necesario; no se cambia Mapa por prevención.

**Alternativas:** un barrido completo del mundo por acción desperdicia tiempo; copiar fichas mutables hace cambiar el pasado; usar id de ficha confunde dos objetos iguales.

## R4. Fronteras y pergamino sin alterar su comportamiento

**Decisión:** distinguir por secuencia la frontera predecisión de los efectos de una acción iniciada al mismo tiempo entero. `_accion` registra las fronteras, no ejecuta eventos adicionales. Pedir a Mariano confirmar el caso de toda la cohorte automática simultánea; no se propone editar agenda ni `_avanzar` desde esta capacidad.

`Partida.usar_pergamino` consume el pergamino sin inverso, activa `_en_retroceso`, llama `Registro.deshacer_ultimo` y avisa invalidación de rutas. Mantener ese flujo y sus mutaciones. La instrumentación identifica el grupo retirado, lee el reloj restaurado y cambia exclusivamente la historia: elimina reversibles, conserva persistentes y reubica a r los que eran posteriores a r; anteriores/simultáneos mantienen instante.

**Motivo:** el usuario mantiene explícitamente el pergamino actual. Los deltas persistentes se aplican sobre copias históricas; no se vuelven a ejecutar sobre el motor para reconciliar campos. Comprobar `historia reloj_actual == historia #(N+1) == resumen vivo`. Si un inverso existente pisa un persistente del mismo destino, documentar el caso y coordinarlo; no esconder la divergencia cambiando el juego.

**Alternativas descartadas:** borrar todo el sufijo pierde persistentes; registrar los inversos como acciones mantiene acciones eliminadas; reaplicar persistentes en la partida modifica el comportamiento fuera del alcance aprobado.

## R5. FR-014 y replay con comentarios existentes

**Decisión:** reutilizar exactamente `# ir a X`. El reconstructor interpreta la marca como una llamada de observación exterior a `Partida._observar_puertas`, con grupo cerrado, sin tiempo ni acción; no vuelve a ejecutar IR_A. Se conservan órdenes atómicas de movimiento, comentarios y pergaminos en su posición. No nuevos formatos, versiones, campos de K, batches externos ni huellas persistidas.

**Evidencia real:** `Controlador._ejecutar_ir_a` escribe actualmente un comentario al comienzo, después ejecuta callbacks y antes de cada intento observa puertas; puede bloquearse sin paso. `BitacoraPartida.anotar_comentario` ya escribe `# ...`, pero `leer_log` lo omite. `Aplicacion.registrar_comentario` no conserva la marca en `app.ordenes`; `persistencia_partida.foto_de` convierte únicamente órdenes a texto y `cargar` intenta `Orden.desde_texto` por cada línea. La capacidad de guardado v4 pertenece a Kim.

**Pedido mínimo:** Kim debe situar el mismo comentario justo antes de cada observación exterior efectiva, después de callbacks que puedan cancelar, incluido un bloqueo posterior sin movimiento. Jeferson conserva su intercalación en memoria; Kim conserva esas mismas cadenas en el campo de líneas ya existente de v4 y usa el aplicador al cargar. Esta revisión no cambia el formato de ese campo.

**Por qué importa la frecuencia:** con una única marca inicial, una observación al bloquearse después de varios pasos no tiene marca propia; al repetir solo los movimientos su observación acabaría dentro del grupo y sería reversible, mientras originalmente era exterior. Una marca emitida antes de una cancelación también provocaría una observación que no ocurrió. No afirmar equivalencia universal de los comentarios actuales sin este ajuste del dueño.

**Suficiencia condicionada:** mismo inicio/versiones/semilla; cada orden reproduce el mismo grupo; cada marca exterior llama el mismo método en la misma posición, por lo que genera el mismo conocimiento sin grupo; cada pergamino recorta y reubica del mismo modo. Por inducción se conservan estados históricos si se entregan marcas completas y carga intercalada. Las pruebas deben demostrarlo, no solo comparar reloj/vida finales.

**Firmas propias ofrecidas:** `iterar_lineas_reconstruccion(lineas)` y `aplicar_linea_reconstruccion(controlador, linea) -> bool`; `reproducir_observacion_ir_a(partida, destino: int) -> None`. Se implementan en `controlador/reproductor.py`; datos recibe callbacks inyectados, no importa controlador.

**K:** se configura en el proceso con `--checkpoint-cada K` o default medido, sin persistirlo. Reconstruir con otra K cambia checkpoints/costos pero conserva estados y línea lógica, que es lo exigido por FR-014.

**Alternativas descartadas:** nuevo log v2, nuevo esquema binario de registros, `@externo`, base64 y módulo adicional en datos; volver a planificar IR_A; prometer reconstruir comentarios que el archivo no contiene. Un archivo antiguo con marcas incompletas conserva una limitación verificable; no se lo convierte inventando historia.

## R6. Lectura y MVC con cambios mínimos

`modelo/datos/bitacora_partida.py` solo retira la dependencia de Orden mediante un parser/fábrica inyectado, preservando su formato y función ordinaria. La interpretación de comentarios se hace en el lector de reproductor sobre las líneas originales; no se amplía la bitácora con nuevas clases/registros.

El lector de reproductor conserva el orden de comentarios y órdenes, reutiliza validación de encabezado existente y ofrece el aplicador a Kim/Jeferson. Mantener API/llamadores ordinarios de lectura con el callback acordado y probar esa compatibilidad; no registrar HISTORIA ni cambiar los contadores de acciones por comentarios.

`--hasta` reconstruye primero todo el flujo y luego consulta t: detenerse al primer reloj superior puede mostrar una acción eliminada por un pergamino posterior. Ambas rutas de `preparar_reproduccion` (datos actuales y FuenteAlmacen) reciben la misma K. Un t posterior a un final terminal muestra estado final y aviso; log interrumpido jugando no debe presentarse como derrota/victoria.

## R7. Interfaz y alcance compartido

HISTORIA es orden de interfaz, previa a la cancelación de IR_A por otra orden. `controlador/controlador.py` solo incorpora HISTORIA y su uso desde pantalla final; el tramo de IR_A lo cambia Kim si acepta el pedido. `VistaPygame.pedir_orden` borra `fin`, por lo que hace falta preservar modo final; `_modal` cierra con cualquier tecla/trunca, así que requiere adaptación para Escape y resumen extenso.

L abre historia; H/F1 siguen ayuda. `VistaConsola._texto_salidas` y `VistaPygame._dibujar_puerta` ya muestran costos: conservarlos/probarlos. Cazador requiere marca textual/gráfica. `app.reporte_resolubilidad` y `ResultadoResolubilidad.formatear_reporte` ya existen; Jeferson solo facilita el proveedor, respetando 003/FR-015/018.

## R8. Complejidad, alternativas y medición

A acciones vigentes, D datos de cambios, S proyección, B=1+floor(A/K), E_K deltas de hasta K acciones, U exteriores, L operaciones de secuencia, R salida.

| Alternativa | Consulta | Memoria | Evaluación |
|---|---|---|---|
| Checkpoints y deltas adelante | O(log B + S + E_K + U + L + R); #k selecciona bloque O(1) | O(D+A+B·S) | Elegida, <=K acciones |
| Desde 0 sin checkpoints | O(S+D_hasta_t+L+R) | O(D+A+S) | Baseline, no satisface K en general |
| Desde actual hacia atrás | O(S+D_despues_t+L+R) | O(D+A+S) | Baseline sobre copia, nunca usa pergamino real |
| Foto por acción | O(S+R) más ubicación | O(A·S) | Solo referencia descartada |

Captura O(1) amortizado más normalización/posición real, que puede costar O(I) para inventario. Checkpoint O(S) cada K. Recorte proporcional a deltas/persistentes/destinos afectados y tamaños de checkpoints liberados, sin recorrer prefijo. Liberar una foto propietaria no es O(1). K limita acciones, no deltas ni mapa impreso.

Medir capacidad reservada y bases por referencias, no solo longitud lógica. Los directorios no redimensionan prefijo al recortar; con cinco inversos su reserva sigue ligada a A+5 en la misma sesión. Cambiar/cargar sesión reemplaza esos directorios.

`bench_linea_tiempo.py` usa `generar_cripta(numero_salas, semilla, rango_costos, cantidad_cazadores, rango_cazadores, cadena_llaves, cierre_automatico, salas_por_pagina, topologia)` y su catálogo real, sin la fuente de pruebas con catálogo fijo. Semilla sintética 20261113 y >=5000 acciones aceptadas; casos seguros y casos con cambios/efectos/conocimiento. Comparar K=10,50,200, sin checkpoints, adelante/atrás y foto por acción como referencia; verificar equivalencia antes de cronometrar. Medir memoria retenida/pico, máximo/mediana de consulta total, fases y costo de recorte 1–5 con prefijo creciente.

Repetir `historial` e `inventario` sin modificar sus archivos. El primero usa `Registro.deshacer_ultimo` directamente y el segundo llama Inventario sin Partida: agregar en el bench nuevo la variante integrada C1 para medir su sobrecosto. K=50 es candidato; seleccionar default solo con resultados <50 ms y memoria comparada. No se ejecutaron medidas durante esta revisión documental.
