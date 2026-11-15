# Decisiones técnicas de 002: niebla del mapa e IR_A

Revisión documental: 2026-11-10. Base de código: commit `f3741c8`.
Este documento pertenece exclusivamente a 002; no sustituye ni modifica el
[registro global del equipo](../../DECISIONES.md).

Se distingue implementación existente de diseño previsto. «Implementada» se
refiere al alcance de cada decisión, no a la finalización de toda la capacidad.
Las pruebas citadas son evidencia automatizada disponible en el repositorio;
no se han vuelto a ejecutar para esta modificación exclusivamente documental.
Las alternativas indicadas proceden de `research.md`; no implican comparaciones
experimentales. Donde no consta una evaluación, se indica expresamente.

Fuentes de diseño: [spec](spec.md), [plan](plan.md), [modelo de datos](data-model.md),
[tareas](tasks.md), [investigación](research.md) y
[constitución](../../.specify/memory/constitution.md).
El extracto oficial aportado en la sesión contiene §3.3, §3.4, §5.3, §6 y
Apéndice B; no equivale a disponer del PDF íntegro versionado en este documento.

## D01. Conocimiento en arreglos indexados por sala

- **Problema:** consultar frecuentemente el conocimiento sin índices hash ni
  recorridos de todas las salas.
- **Alternativas documentadas:** atributos en `Sala`, árbol binario propio y
  listas enlazadas (`research.md`, §1.2).
- **Decisión:** `ConocimientoMapa(n, salas_por_indice, mapa)` conserva las
  referencias recibidas; almacena `N` estados y `4N` memorias de puertas en
  arreglos contiguos. La posición de puerta es `sala.indice * 4 + direccion`.
- **Justificación:** consultas por índice O(1); por ID, búsqueda binaria del
  mapa O(log N). `resumen()` devuelve contadores mantenidos, en O(1).
  Espacio O(N), sin atribuir un número de bytes no medido a objetos Python.
- **Archivos:** [conocimiento.py](../../modelo/juego/conocimiento.py),
  [mapa.py](../../modelo/juego/mapa.py), `data-model.md` (C6).
- **Estado:** implementada.
- **Evidencia:** [test_conocimiento.py](../../tests/test_conocimiento.py),
  pruebas de referencias, índices inválidos, consulta por ID y resumen sin
  recorrer los arreglos (FR-001, SC-002).

## D02. Tres estados y memoria independiente de puertas

- **Problema:** diferenciar existencia, exploración y última observación sin
  revelar información que el jugador todavía desconoce.
- **Alternativas:** no consta una evaluación adicional; los estados vienen
  fijados por FR-001..FR-006 y el [contrato C2](contracts/contrato_c2_puertas.md).
- **Decisión:** salas desconocidas=0, avistadas=1, exploradas=2; puertas
  desconocidas=0, recordadas abiertas=1, recordadas cerradas=2. Observar una
  puerta sincroniza las posiciones de ambos extremos, sin explorar la vecina.
  La consulta de apertura recordada exige ambos extremos recordados abiertos;
  una discrepancia o memoria desconocida no habilita el paso.
- **Justificación:** la puerta es compartida, pero conocerla no identifica su
  sala vecina. Un cambio remoto físico no actualiza la memoria del jugador.
- **Archivos:** `modelo/juego/conocimiento.py`,
  [partida.py](../../modelo/juego/partida.py), contrato C2.
- **Estado:** implementada.
- **Evidencia:** pruebas FR-004/FR-005 en `test_conocimiento.py` y FR-006 en
  [test_conocimiento_partida.py](../../tests/test_conocimiento_partida.py),
  incluyendo cambios remotos y actualización al regresar.

## D03. Cambios reversibles y contadores coherentes

- **Problema:** restaurar estados, puertas y resumen al usar un pergamino,
  sin recalcular todo el conocimiento.
- **Alternativas:** no consta comparación adicional; C1 exige el punto único
  de cambios y C6 exige un resumen barato.
- **Decisión:** extender `Registro.cambiar` para posiciones de arreglos además
  de atributos; las actualizaciones de conocimiento y contadores pasan por
  `Partida.cambiar`. Cada acción ordinaria conserva su propio grupo de inversos.
- **Justificación:** restauración O(1) por cambio, O(cambios) por grupo; no se
  duplican contadores por revisitas o por vecinos compartidos.
  Solo se registran inversos cuando hay un grupo abierto: la inicialización
  en t=0 no constituye una acción reversible. La observación local previa al
  recálculo de IR_A tampoco crea por sí misma un nuevo grupo de acción.
- **Archivos:** [registro.py](../../modelo/juego/registro.py), `partida.py`,
  `conocimiento.py`, `data-model.md` (C1/C6).
- **Estado:** implementada para los grupos de acciones; esto no declara
  implementada la línea de tiempo ni su reconstrucción histórica (FR-013).
- **Evidencia:** FR-012 en `test_conocimiento.py` y
  `test_conocimiento_partida.py`: reversión de memoria, estados y contadores,
  apertura/autocierre y exploración con/sin antorcha.

## D04. Antorcha y separación entre percepción y mundo real

- **Problema:** revelar topología por iluminación sin activar contenido remoto
  ni adquirir observaciones de puertas que no se han presenciado.
- **Alternativas:** no consta evaluación adicional; FR-007/FR-008 fijan la regla.
- **Decisión:** `Partida` inicializa el conocimiento y aplica exploración y
  observaciones; `ConocimientoMapa` almacena y consulta. Al entrar con antorcha
  se exploran las vecinas directas, incluso tras salidas cerradas; no se propaga
  recursivamente la antorcha ni se activan contenidos de esas vecinas.
  Las puertas se observan físicamente desde la sala actual, no desde todas las
  salas reveladas por la antorcha.
- **Justificación:** precarga del esqueleto y exploración son conceptos
  distintos. Las actualizaciones recorren salidas de las salas afectadas,
  con grado máximo cuatro, y mantienen contadores mediante cambios reversibles.
- **Archivos:** `partida.py` (`iniciar`, `_entrar`, `_explorar_sala`,
  `_observar_puertas`, `_observar_cambio_puerta`), `conocimiento.py`.
- **Estado:** implementada.
- **Evidencia:** pruebas FR-002, FR-007/FR-008 y FR-012 de
  `test_conocimiento_partida.py`: inicio, vecinos tras puerta cerrada,
  ausencia de activación remota y restauración por pergamino.

## D05. Dijkstra genérico con montículo propio

- **Problema:** calcular distancias ponderadas deterministas sin estructuras
  prohibidas y ofrecer un núcleo común a distintos consumidores.
- **Alternativas documentadas:** `decrease_key` frente a entradas duplicadas
  descartadas al extraer; implementación compartida frente a separada
  (`research.md`, §2.2 y §3.2).
- **Decisión:** montículo binario sobre arreglo, eliminación perezosa y
  `dijkstra_acotado` sin estado global, con filtro, cota inclusiva opcional,
  arreglos de distancias/marcas y token propiedad del llamador.
  El heap usado por Dijkstra lleva `(distancia, id, indice)`; el índice permite
  acceso directo y conserva el desempate por distancia e ID de C3.
- **Justificación:** no usa `dict`/`set` como índices, `heapq`, `bisect`,
  `collections` ni bibliotecas de rutas. Reutilizar marcas evita limpiar O(N)
  posiciones entre búsquedas. Tiempo O((V_r+E_r) log(E_r+1)) con entradas
  perezosas; en este grafo de grado acotado, O(V_r log V_r).
- **Archivos:** [monticulo_min.py](../../modelo/estructuras/monticulo_min.py),
  [dijkstra.py](../../modelo/estructuras/dijkstra.py),
  [contrato C3](contracts/contrato_c3_dijkstra.md).
- **Estado:** implementada como proveedor C3; no acredita por sí sola la
  integración del consumidor cazador en otra capacidad.
- **Evidencia:** [test_niebla_ir_a.py](../../tests/test_niebla_ir_a.py):
  montículo, costos mínimos, cota, filtro, determinismo y arreglos independientes.

## D06. IR_A planifica exclusivamente sobre conocimiento

- **Problema:** hallar el siguiente paso mínimo sin consultar puertas físicas
  ni atravesar salas que el jugador no haya explorado.
- **Alternativas documentadas:** Dijkstra desde el jugador con etiquetas de
  primer vecino frente a búsqueda inversa desde el destino (`research.md`, §3.1).
- **Decisión:** `PlanificadorRutas` valida destino explorado; ejecuta Dijkstra
  inverso con `cota_rango=None`, filtro de ambos extremos explorados y puerta
  recordada abierta. Selecciona la vecina por costo total y después menor ID.
  No ejecuta acciones. Tiene sus propios arreglos y token.
- **Justificación:** sobre salidas no dirigidas y costos simétricos,
  `costo(salida)+dist[vecina]` permite resolver el primer paso y su desempate.
  El costo depende del componente conocido alcanzable, no solo de la longitud
  final de la ruta: actualmente se expande completo, sin parada en el origen.
- **Archivos:** [planificador_rutas.py](../../controlador/planificador_rutas.py),
  `conocimiento.py`, `dijkstra.py`, [contrato IR_A/C4](contracts/contrato_ir_a.md).
- **Estado:** implementada; no se ha optimizado tras los benchmarks.
- **Evidencia:** [test_planificador_rutas.py](../../tests/test_planificador_rutas.py):
  ruta ponderada, empate, destinos inválidos, intermedias desconocidas,
  discrepancia entre memoria y puerta física, independencia y consulta sin tiempo.

## D07. Viaje compuesto de movimientos ordinarios

- **Problema:** conservar tiempo, eventos, replay y retroceso por cada paso
  sin convertir todo el viaje en una sola acción del motor.
- **Alternativas:** no consta comparación adicional; §3.4 y C4 exigen pasos ordinarios.
- **Decisión:** `IR_A` queda fuera de `ORDENES_DE_PARTIDA`; el controlador
  observa localmente y recalcula antes de cada movimiento `MOVER` ordinario.
  Se detiene por llegada, enemigos vivos, daño, fin de partida o falta de ruta;
  nunca abre puertas automáticamente. Cambiar la partida recrea el planificador.
  Para detectar daño seguido de curación, un adaptador temporal de `cambiar`
  delega al método original y se retira incluso ante excepciones.
- **Justificación:** cada paso mantiene su grupo reversible y notificación de
  orden aceptada. El pergamino revierte el último paso y no reanuda el viaje.
  La intención se emite a observadores de comentarios; `leer_log` ignora `#`.
- **Archivos:** [controlador.py](../../controlador/controlador.py),
  [orden.py](../../controlador/orden.py),
  [bitacora_partida.py](../../modelo/datos/bitacora_partida.py), contrato C4.
- **Estado:** parcial: viaje y soporte de comentarios implementados; falta
  conectar los comentarios al log activo desde Aplicacion/main.
- **Evidencia:** [test_ir_a_compuesto.py](../../tests/test_ir_a_compuesto.py):
  FR-017..FR-023, costos, eventos, daño incluso curado, puertas, desvíos,
  pergamino, sustitución y replay con comentarios conectados por la prueba.
  Esa conexión de prueba no demuestra la conexión de producción pendiente.

## D08. Cancelación mediante observador opcional

- **Problema:** ofrecer un punto seguro para atender eventos entre pasos,
  sin hilos ni movimientos adicionales tras cancelar.
- **Alternativas:** no consta evaluación comparativa; se adoptó el callback
  opcional autorizado para no imponer cambios a las vistas compartidas.
- **Decisión:** `agregar_observador_viaje(funcion)` registra callbacks
  `funcion(partida_actual) -> bool`. Tras la validación inicial y antes de
  observar puertas, recalcular y mover en cada iteración: `False` cancela,
  `True` continúa; se exige `bool` y se comprueban token e identidad después
  de cada callback. Excepciones se propagan y finalizan el viaje.
- **Justificación:** cancelación sin tiempo extra ni deshacer pasos anteriores;
  sin observadores se conserva el viaje existente. El callback debe limitarse
  a eventos/presentación y no ejecutar acciones de juego.
- **Archivos:** `controlador.py`, `test_ir_a_compuesto.py`.
- **Estado:** implementada en controlador; conexión gráfica pendiente.
- **Evidencia:** pruebas C4 de cancelación inicial y tras varios pasos, reloj,
  log individual, retroceso, cambio de partida, token, ausencia de observadores,
  retorno estricto y propagación de excepciones.

## D09. Datos filtrados para consola y Pygame

- **Problema:** impedir que la interfaz confunda la precarga real con el mapa
  conocido o presente identificadores de salas solamente avistadas.
- **Alternativas:** no consta comparación adicional; el filtrado en el modelo
  está documentado en `research.md`, §5.2, y en T012–T014.
- **Decisión:** `mapa_conocido()` entrega únicamente salas exploradas y salidas
  filtradas. `salidas_visibles()` entrega cinco campos: dirección, estado
  recordado, ID vecino o `None`, llave permitida y costo. Usa conocimiento para
  visibilidad/memoria y referencias estáticas para nombres, topología y costos;
  no lee el estado físico de puertas para presentar la memoria.
  Las vistas muestran destinos anónimos sin imprimir «sala None».
- **Justificación:** el modelo controla privacidad; consola y Pygame consumen
  los mismos datos filtrados. MAPA no es acción ordinaria, no muta ni avanza
  tiempo. Construir la consulta completa sí recorre las salas O(N), a diferencia
  de las consultas individuales y `resumen()` O(1).
- **Archivos:** `partida.py`, `orden.py`, `controlador.py`,
  [vista_base.py](../../vista/vista_base.py),
  [vista_consola.py](../../vista/vista_consola.py),
  [vista_pygame.py](../../vista/vista_pygame.py),
  [controles_gui.py](../../vista/controles_gui.py).
- **Estado:** parcial: MAPA funciona en ambas vistas y consola acepta IR_A;
  Pygame tiene mapa con M, cierre/desplazamiento y diálogo privado preparado,
  pero el diálogo no inicia viajes ni está conectado a una tecla de ejecución.
  Falta atender eventos y cancelar durante el recorrido gráfico.
- **Evidencia:** [test_mapa_consola.py](../../tests/test_mapa_consola.py) y
  [test_gui.py](../../tests/test_gui.py): privacidad, memoria frente a estado
  real, costos, consulta sin tiempo, `ir a 4`, `ir n`, controles y diálogo sin viaje.

## D10. Benchmarks independientes y reproducibles

- **Problema:** medir operaciones reales sin modificar módulos compartidos,
  abrir Pygame, depender de red ni confundir medidas locales con certificación.
- **Alternativas:** `research.md`, §7, propone integración mediante `main.py
  --bench`; el alcance autorizado adoptó primero un módulo independiente.
- **Decisión:** [bench_niebla_ir_a.py](../../tests/bench_niebla_ir_a.py), ejecutable
  con `venv/Scripts/python.exe -B -m tests.bench_niebla_ir_a`, usa
  `perf_counter_ns()`, cuadrículas de 10/100/1000 salas, semilla 20261110 y viajes
  sobre líneas con semilla 17. Preparación, calentamiento y comprobaciones se
  excluyen de las muestras. No escribe resultados ni archivos del proyecto.
- **Justificación:** mide consultas, resumen, actualización/reversión mediante
  helpers reales, Dijkstra acotado/completo, planificación y recálculo dentro
  de viajes ordinarios. Reporta tamaños, ejecuciones, media y máximo; para
  consultas el máximo es de lote y el valor por operación es amortizado.
  El recálculo cronometrado excluye movimiento, eventos y validación preliminar;
  no representa la latencia completa de un paso ni de la interfaz.
- **Estado:** parcial: módulo independiente implementado; integración `--bench`,
  referencia oficial y medición del ciclo con cazadores pendientes.
- **Evidencia de código:** comprobaciones de huella determinista, distancias,
  restauración de arreglos, reloj y cantidad de pasos en el propio benchmark.
- **Medición histórica comunicada en la sesión:** planificación de 1000 salas,
  cuadrícula de 1936 aristas, semilla 20261110, 7 × 20 = 140 muestras:
  **media aproximada 8,548 ms** (8,547739 ms), máximo 12,153700 ms.
  Entorno reportado: Python 3.13.18, Windows. Es un resultado previo de consola,
  no una ejecución nueva de esta revisión ni un informe de resultados versionado.
  El extracto §6.1 establece 5 ms en la cripta de referencia; no identifica esa
  referencia como esta cuadrícula de 1000 salas. Esta medición no acredita
  cumplimiento oficial. Tampoco se ha medido aquí el ciclo de 20 ms con cazadores.

## Inconsistencias documentales y coordinación pendiente

- `spec.md` mantiene estado Draft y `tasks.md` conserva casillas sin actualizar;
  las casillas no constituyen evidencia de implementación ni se modifican aquí.
- `research.md`, §1.3, describe contadores iniciales ya explorados; el constructor
  real empieza con cero y `Partida.iniciar()` aplica FR-002 en t=0, conforme a
  la aclaración de `data-model.md`.
- Las cifras de memoria en KB de `research.md` son estimaciones de diseño sin
  medición del tamaño real de los objetos Python; no se certifican aquí.
- `research.md`, §7, asocia 1000 salas a una referencia de rendimiento; el
  benchmark distingue expresamente ese escenario interno de la referencia oficial.
- Guardado v4 sigue siendo un contrato previsto:
  [contrato_guardado_v4.md](contracts/contrato_guardado_v4.md).
  `modelo/datos/guardado_binario.py` conserva `VERSION_FORMATO = 3`.
  No se declara implementada serialización explícita de niebla ni historia.
- Coordinar con Axel la conexión gráfica del observador, el log de comentarios
  activo y la compatibilidad futura del adaptador temporal C1 con historia;
  con Jeferson, los puntos compartidos de Aplicacion/main y sustitución de partida;
  con Mariano, consumo C3 y evolución de puertas/costos. Esto identifica puntos
  de contacto, sin atribuir trabajo pendiente como ya realizado por otra persona.
- Próximo orden sugerido: coordinar conexiones gráficas y de comentarios;
  verificar integración con pruebas; acordar persistencia/historia; obtener
  referencia de rendimiento y evaluar optimizaciones con mediciones comparables.
