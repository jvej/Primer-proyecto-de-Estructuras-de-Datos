# Guía de validación del alcance reducido

Se ejecuta después de implementar. Los tests nuevos y `bench_linea_tiempo.py` aún no existen; esta revisión documental no ejecutó pruebas/mediciones. No instala paquetes ni modifica código.

## Preparación

Desde raíz, entorno virtual existente Python 3.13. Usar un paquete/log de prueba compatible para interfaz; el bench utiliza el generador local sin red.

```powershell
.\venv\Scripts\python.exe --version
.\venv\Scripts\python.exe -m tests.test_linea_tiempo
.\venv\Scripts\python.exe -m tests.test_historia_interfaces
.\venv\Scripts\python.exe -m tests.test_historia_persistencia
.\venv\Scripts\python.exe -m tests.test_bench_linea_tiempo
```

[Captura](contracts/c1-captura.md), [interfaz](contracts/comandos-interfaz.md), [reconstrucción con comentarios](contracts/persistencia.md) y [datos](data-model.md).

## Captura y consultas

1. Confirmar checkpoint 0 después de iniciar y antes de órdenes previas. No canalizar mover_a/visita iniciales.
2. Comparar ejecución con y sin instrumentación: mismo reloj, acciones, agenda, azar y comportamiento de pergamino. `_avanzar` y el inverso manual de `_accion` permanecen intactos.
3. Probar historia 0, #1, acciones intermedias, #N+1 y tiempos interiores/simultáneos. El resumen contiene todos los campos requeridos sin leer datos actuales para completar el pasado.
4. t negativo/decimal/futuro y k fuera de rango: mensaje sin tiempo, acción, grupo, cambios de estado ni línea en log.
5. Checkpoint exactamente cada K acciones aceptadas, consulta aplicando como máximo K acciones; externos contados aparte.
6. Revertir entrada con antorcha: desaparecen sus revelaciones. Conservar/reubicar persistentes históricos y comprobar igualdad con el estado real, incluido inventario completo; no reaplicar nada sobre el motor desde historia.
7. Si falla un caso de simultáneos o inverso/persistente, guardar caso mínimo para el pedido al dueño; no resolverlo ampliando archivos propios.

## Reconstrucción con el formato existente

1. Comentario IR_A al inicio con observación sin paso: replay invoca una observación exterior, sin ejecutar viaje.
2. Viaje de varios pasos y bloqueo posterior: el comentario emitido justo antes de esa observación, pedido a Kim, conserva que sea no reversible.
3. Cancelación en callback previa al siguiente intento: no debe haber marca que haga observar algo que nunca ocurrió.
4. Guardar/cargar con marcas intercaladas conservadas en v4 y aplicación, según pedidos a Kim/Jeferson. Comparar conocimiento, inventario, efectos, enemigos, resultado y consultas históricas; no basta reloj/vida/sala.
5. Guardar después de pergamino, reconstruir marcas/órdenes/pergaminos completos y comprobar reubicación. No truncar el log original al recortar historia.
6. Reconstruir con K distinta: mismos estados históricos, checkpoints distribuidos de otra forma. No nuevos campos, versiones, registros externos o huellas persistidas.
7. Log con marca inicial antigua pero sin marcas de observaciones posteriores: documentar límite de fidelidad; no afirmar que el código actual ya preserva FR-014 para ese caso.

```powershell
.\venv\Scripts\python.exe main.py --offline <paquete> --replay <partida.log> --hasta <t> --checkpoint-cada 10
```

Sustituir marcadores por rutas/entero reales. Replay reconstruye todas las líneas antes de consultar t; una rama luego revertida no aparece. Para t posterior a final, resumen final y aviso; para log interrumpido jugando, error de rango. Sin vista, log nuevo ni puntajes. Probar datos actuales y camino FuenteAlmacen.

## Interfaz

L abre historia, Enter envía t/#k y Escape cierra sin cambiar partida; H/F1 continúan ayuda. Panel largo desplazable y disponible en final sin borrar resultado ni duplicar al_terminar/puntajes. Consola usa ambos comandos. Consultar durante un viaje no cancela ni agrega comentarios.

Reporte desde app, plantilla 003/FR-018 y bloqueo 003/FR-015 salvo forzar. Costos existentes se conservan y cazador tiene marca visible. No se modifica etiqueta de salas ni Actor.

## Mediciones y §5.6

```powershell
.\venv\Scripts\python.exe main.py --bench linea_tiempo
.\venv\Scripts\python.exe main.py --bench historial inventario
```

K=10,50,200 y sin checkpoints; adelante/atrás y foto por acción como referencia. Semilla fija, >=5000 acciones aceptadas en la misma carga; verificar equivalencia antes de medir. Registrar equipo/Python, tamaños/densidad de cambios, memoria real retenida/pico, máximo/mediana de consulta completa, fases y grupos aplicados.

Recorte 1–5 con prefijo creciente/sufijo fijo, incluyendo liberar checkpoints; medir capacidad reservada. Repetir benches existentes sin editarlos y agregar al nuevo casos integrados C1 con captura activada/desactivada. Seleccionar K por evidencia <50 ms y comparación de memoria, sin inventar resultados.

## Regresiones sin modificar sus archivos

```powershell
.\venv\Scripts\python.exe -m tests.test_partida
.\venv\Scripts\python.exe -m tests.test_motor_base
.\venv\Scripts\python.exe -m tests.test_conocimiento_partida
.\venv\Scripts\python.exe -m tests.test_inventario_partida
.\venv\Scripts\python.exe -m tests.test_ir_a_compuesto
.\venv\Scripts\python.exe -m tests.test_replay_puntajes
.\venv\Scripts\python.exe -m tests.test_guardado_binario
.\venv\Scripts\python.exe -m tests.test_controlador
.\venv\Scripts\python.exe -m tests.test_gui
```

Registrar fallos reales y pedidos de integración sin cambiar expectativas para ocultarlos. En particular, comprobar compatibilidad de lectura ordinaria de bitácora tras inyectar su parser y que las marcas no se cuentan como acciones.
