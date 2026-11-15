# Quickstart de 002: uso y validacion actual

Base: `75cc63eae09b3c7c85d388f44457086ba443da8a` (2026-11-13).
Usar Python 3.13 del venv. Si este worktree no tiene venv, usar el ejecutable
absoluto del entorno del proyecto original con directorio actual del worktree.

## Pruebas

```powershell
.\venv\Scripts\python.exe -B -m tests.test_conocimiento
.\venv\Scripts\python.exe -B -m tests.test_conocimiento_partida
.\venv\Scripts\python.exe -B -m tests.test_niebla_ir_a
.\venv\Scripts\python.exe -B -m tests.test_planificador_rutas
.\venv\Scripts\python.exe -B -m tests.test_ir_a_compuesto
.\venv\Scripts\python.exe -B -m tests.test_comentarios_ir_a_002
.\venv\Scripts\python.exe -B -m tests.test_ir_a_grafico_002
.\venv\Scripts\python.exe -B -m tests.test_fr010_generaciones_002
.\venv\Scripts\python.exe -B -m tests.test_guardado_v4_002
.\venv\Scripts\python.exe -B -m tests.test_carga_v4_002
.\venv\Scripts\python.exe -B -m tests.test_bench_mapa_conocido_002
```

Completar con test_mapa_consola, test_integracion_comentarios_002, motor,
Partida, terreno/cazador, resolubilidad y replay/puntajes. No basta C3 para toda
002. Ejecutar cada tests.test_* como modulo: unittest discover por si solo no
ejecuta las pruebas del proyecto basadas en funciones.
Verificación posterior sobre 18b9364: 42/42 módulos y 229/229 unittest conjuntos
aprobados. Los 13 fallos de la auditoría histórica fueron corregidos. La
aceptación de SC-001 y la comparación equivalente T030 siguen pendientes.
Matriz y resultados reales en DECISIONES.md.

## Interfaz

Consola: mapa, ir a <id>, ir n. Pygame: M mapa; V dialogo IR_A; Escape cancela
viaje sin SALIR; R cancela y deja un unico pergamino para pedir_orden, fuera del
callback. Otra Partida o QUIT descarta pendientes. MAPA no consume tiempo.
Destinos no explorados anonimos; puertas presentan memoria, no estado remoto.

## Benchmark sintetico

```powershell
.\venv\Scripts\python.exe -B main.py --bench mapa_conocido
.\venv\Scripts\python.exe -B -m tests.bench_niebla_ir_a --tamanos 10 100 1000
```

Adaptador main([]) aisla argumentos externos. Salida: entorno, semilla, N/E,
muestras, media/maximo. Consultas por lotes: maximo de lote y media amortizada.
Preparacion/calentamiento excluidos. Helpers sin/con antorcha no equivalen a
accion completa; pergamino real se mide tambien. SC-004 es O(1) por cambio,
O(cambios) por grupo. SC-001 de menos de 5 ms sigue pendiente de cripta oficial;
1000 salas sinteticas no certifican cumplimiento. Ciclo con cazadores no medido.

## T030

Cache/lista_ordenada/ordenamiento no escriben archivos. Guardado crea y elimina
bench_partida.bin/json relativos al directorio actual. Ejecutar desde temporal
externo, con raiz del proyecto en sys.path, como en la auditoria; no usar una
carpeta que contenga archivos que deban conservarse con esos nombres.
Los cuatro benchmarks terminaron codigo 0; no hay linea base equivalente para
certificar ausencia de regresiones. Resultados en DECISIONES.md.

## Replay y v4

Usar un log real, no una ruta de ejemplo inexistente:
`<python-del-venv> main.py --replay <ruta-real.log> --detalle`.
Movimientos atomicos y marcas IR_A se reconstruyen sin planificar otro viaje:
las marcas solo observan, otros comentarios se ignoran. Guardar conserva orden
y repeticiones; T045/T046 valida candidata antes de publicarla, sin reemplazar
arreglos. Error conserva sesion; v3 se rechaza explicitamente. No hay CRC:
validaciones estructurales y comparacion con replay. --verificar requiere ID
y no sustituye las pruebas de carga ni activa resolubilidad al reconstruir.
