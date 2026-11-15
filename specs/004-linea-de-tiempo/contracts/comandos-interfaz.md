# Contratos de consulta y presentación

## Selectores

Consola: `historia <t>` y `historia #k`. Pygame: L abre cuadro para t o #k y Escape cierra cuadro/panel; H/F1 siguen siendo ayuda. Parser compartido produce `Orden(HISTORIA, selector)`, fuera de `ORDENES_DE_PARTIDA`; nunca se serializa con `Orden.a_texto`.

| Selector | Resultado |
|---|---|
| t entero entre 0 y reloj actual | Estado de t, respetando frontera predecisión y todos sus eventos observables |
| t negativo, decimal, texto o futuro | Mensaje de error sin mutación |
| #1 | Estado inicial vigente |
| #k entre 1 y N | Estado antes de la acción aceptada k |
| #N+1 | Estado actual, también en pantalla final |
| k fuera de 1..N+1 o inválido | Mensaje de error sin mutación |

N corresponde a historia vigente. Rechazos, historia, ayuda, inventario y mapa no cuentan; cada paso aceptado de IR_A sí. `#N+1` es notación documental: el usuario escribe el entero calculado.

Contenido: reloj, sala, vida y estadísticas, inventario en orden, efectos, enemigos locales con vida, conocimiento histórico y resultado. El reloj para consulta temporal es t; para acción es el de la frontera. `historia reloj_actual` y `historia #N+1` coinciden con el estado real, también después de reubicar persistentes y en final inmediato.

La salida usa solo proyección y bases históricas, respetando la ocultación de 002. No consulta puertas físicas ni observa/carga salas para completar el pasado. Formato común en `controlador/resumen_historia.py`, sin importar vistas.

## Efectos sobre el flujo

HISTORIA se atiende antes del bloque que cancela IR_A por otras órdenes. No abre grupo ni llama `_accion`, `_avanzar` o `_observar_puertas`, no mueve reloj/azar y no notifica observadores de órdenes/comentarios. Selector inválido se muestra por la vista sin `Partida._rechazar` ni nuevas líneas de bitácora del juego.

El cambio de Axel en controlador se limita a HISTORIA y su acceso desde la pantalla final. La lógica/emisión de comentarios de `_ejecutar_ir_a` se solicita a Kim; no se cambia por parte de Axel. Una consulta GUI se atiende entre pasos en frontera estable, sin ejecutar acciones desde vista ni cancelar el viaje por cerrar el panel.

Panel desplazable para resúmenes largos; Escape no se transforma en SALIR. Preservar modo final: `VistaPygame.pedir_orden` hoy borra `fin` y `_modal` cierra con cualquier tecla/trunca. El flujo final permite consultar sin repetir `Aplicacion.al_terminar`, puntajes o apertura del log.

## CLI y configuración

| Opción | Contrato |
|---|---|
| `--checkpoint-cada K` | Entero positivo del proceso; en ausencia usar default justificado por bench |
| `--replay partida.log --hasta t` | Reconstruir primero todas las líneas existentes, incluidas marcas IR_A/pergaminos; después consultar t sin vista |
| `--hasta` sin replay | Error de argumentos |
| t posterior a final terminal | Resumen final e indicación de que terminó antes |
| t futuro de log todavía jugando | Error de rango, sin inventar un resultado terminal |
| `--bench linea_tiempo` | Medición sin vista/red de K=10,50,200 y sin checkpoints |

K no agrega campo de log ni guardado. La misma configuración del proceso se usa en carga/replay; cambiar K reconstruye otra distribución de checkpoints con los mismos estados. No se modifica versión de ningún archivo. Propagar opciones por nombre a reproductor y al ensamblado acordado con Jeferson.

## Reporte de resolubilidad y sala

Jeferson facilita un proveedor del `app.reporte_resolubilidad` existente. Presentar `ResultadoResolubilidad.formatear_reporte()` al iniciar y ante `ErrorNoResoluble`, sin calcular desde vistas. Cumplir 003/FR-015 y 003/FR-018: ESTADO obligatorio; secciones vacías omitidas; orden de llaves, frontera, ubicaciones, ciclos y motivo canónicos. La vista no reordena el reporte; en GUI se muestra completo con desplazamiento. No resoluble bloquea inicio salvo forzar, que también muestra el reporte.

`VistaConsola._texto_salidas` y `VistaPygame._dibujar_puerta` ya muestran costos: conservar y probar con salidas distintas/destinos ocultos. Añadir `[CAZADOR]` y marca gráfica basada en comportamiento normalizado sin editar Actor ni nuevos recursos. FR-018 de esta feature sigue retirado.
