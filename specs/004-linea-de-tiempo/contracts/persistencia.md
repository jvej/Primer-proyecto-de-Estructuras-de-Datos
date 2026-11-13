# Contrato mínimo de reconstrucción con comentarios existentes

Este contrato reutiliza `partida.log`, el comentario `# ir a X` y las líneas ya disponibles del guardado v4 de Kim. No crea formato, versión, bloque/campo binario, metadatos persistidos de K, registros externos ni módulo en datos.

## Evidencia y pedido a Kim

`Controlador._ejecutar_ir_a` actualmente escribe la marca al comienzo del viaje y observa antes de cada paso, después de callbacks de cancelación. `BitacoraPartida.anotar_comentario` escribe la marca, `leer_log` la ignora y `Aplicacion.registrar_comentario` no la conserva entre las órdenes en memoria. `foto_de/cargar` trabajan con textos de órdenes, no preservan/aplican esas observaciones.

Pedido a Kim: mantener el contenido `# ir a X` y emitirlo justo antes de cada observación exterior efectiva, incluidos bloqueos sin paso después de movimientos previos, después del callback que puede cancelar. No repetir el viaje durante replay. Con la única marca inicial actual no se demuestra fidelidad de una observación exterior posterior; con una marca previa a cancelación se podría reconstruir una observación que nunca ocurrió.

En v4, conservar esas cadenas intercaladas en el campo existente de líneas/órdenes, sin cambiar su representación binaria. No introducir bloques de deltas. Jeferson conserva la intercalación en aplicación y facilita las líneas; Kim integra la carga y mantiene validación anterior al reemplazo de partida. Si la versión v4 todavía no admite estas cadenas, es una dependencia que la dueña debe confirmar/resolver, no autorización para que Axel rediseñe el formato.

## Firmas mínimas ofrecidas por Axel

En `controlador/reproductor.py`:

- `iterar_lineas_reconstruccion(lineas: iterable[str]) -> iterable[str]`: conserva órdenes y comentarios IR_A en orden; ignora blancos y otros comentarios según la política actual.
- `reproducir_observacion_ir_a(partida, destino: int) -> None`: valida la marca y llama una vez a `partida._observar_puertas()` con grupo cerrado. Destino sirve para reconocer/validar la intención; no planifica ni mueve.
- `aplicar_linea_reconstruccion(controlador, linea: str) -> bool`: reutiliza un controlador ya creado para órdenes atómicas y el adaptador anterior para comentarios, sin crear un controlador por línea.

Al modelo/datos se inyecta un callback `reproducir_linea(linea: str) -> bool` que cierra sobre el controlador, no se importa `controlador.reproductor` desde persistencia. En `aplicacion.py`, Jeferson puede reutilizar el `Controlador(partida)` que ya crea `_armar`.

Pedidos complementarios a Jeferson:

- `lineas_para_reconstruir() -> iterable[str]`: proporciona la misma secuencia de órdenes y comentarios que el log, para foto/carga/continuación.
- Conectar `inicializar_historia(partida, checkpoint_cada)` después de iniciar y antes de esas líneas.

## Lector de replay y alcance de bitácora

El lector en reproductor inspecciona las líneas originales conservando comentarios y valida el encabezado actual. `modelo/datos/bitacora_partida.py` solo retira import de Orden mediante parser/fábrica inyectado como adaptación mínima; no agrega soporte de comentarios al retorno de su lector ordinario ni cambia encabezados/escritura/versiones. Mantener sus llamadores de lectura ordinaria mediante el parser acordado y pruebas de compatibilidad.

Cada orden se interpreta con `Orden.desde_texto` desde controlador. Cada `# ir a X` invoca observación sin tiempo, sin acción ni grupo. HISTORIA nunca genera comentario ni línea. Los comentarios no aumentan contadores de acciones o solicitudes y no deben etiquetarse como acciones en el mensaje de carga.

## Garantía de reconstrucción

Bajo versiones/semilla iguales y marcas completas en las posiciones reales: mismo inicio produce la misma proyección; cada orden produce el mismo grupo; cada marca exterior produce el mismo cambio no reversible; cada pergamino produce el mismo recorte/reubicación. Así se reconstruyen las fronteras y estados interiores. Las pruebas comparan historia y estado completo, no solo reloj/vida/sala finales.

La prueba depende de la entrega de Kim/Jeferson. Una marca al inicio no representa automáticamente las observaciones de todos los intentos posteriores. No volver a ejecutar el viaje para adivinarlas, porque cancelación y bloqueo pueden diferir. No prometer fidelidad histórica de un archivo que no conserva la secuencia necesaria ni migrarlo inventando observaciones.

K se obtiene de CLI/configuración del proceso o default medido. No se guarda. Cargar con otra K modifica distribución de checkpoints pero no estados consultables, lo que preserva FR-014.

## Hasta t

Reproducir todo el flujo, incluidas marcas/pergaminos, y después consultar la historia vigente. Detenerse al primer reloj >t puede mostrar una rama eliminada después. Si el estado terminal acabó antes de t, imprimir resumen final y aviso; para log interrumpido aún jugando, t futuro es error de rango. Sin vista, log nuevo ni puntajes.
