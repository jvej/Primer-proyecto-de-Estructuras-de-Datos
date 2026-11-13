# Implementation Plan: Línea de tiempo de CRIPTA

**Branch**: `004-linea-de-tiempo` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Responsable**: Axel. Revisión de alcance: instrumentar los puntos existentes, reutilizar comentarios de IR_A e incorporar la integración limitada en `controlador/aplicacion.py`, **autorizado por Jeferson**. Esta revisión solo modifica `plan.md` y `tasks.md`; no implementa código ni modifica `spec.md` o contratos. T001–T009 ya están hechas y confirmadas.

## Summary

C1 alimenta una línea de tiempo de deltas, independiente de `Registro.PilaAcotada(5)`. Cada delta toma su instante leyendo `partida.reloj.tiempo_actual` al anotarse. Se conservan `_avanzar`, el inverso manual del reloj en `_accion` y el comportamiento actual del pergamino. La historia usa un checkpoint después de `iniciar()` y uno exactamente cada K acciones, índices contiguos por acción y búsqueda binaria propia por tiempo.

Tras un pergamino se eliminan los deltas reversibles del grupo retirado; los persistentes posteriores al reloj restaurado se reubican allí, sin ejecutar sus operaciones sobre la partida viva. La consulta reconstruye una proyección aislada, sin agenda, funciones ni azar. Pygame usa L y Escape; H/F1 siguen siendo ayuda.

Para FR-014 y replay se reutiliza `# ir a X`: su interpretación llama al mismo método de observación que IR_A sin ejecutar el viaje ni consumir tiempo. No se crea formato nuevo de log/guardado, metadatos persistidos de K, registros externos, huellas persistidas ni módulo de reconstrucción en datos. Kim debe conservar los comentarios y su intercalación dentro de las líneas ya guardadas por v4, y asegurar que representan cada observación exterior efectiva.

## Technical Context

- **Language/Version**: Python 3.13; comandos con `venv\Scripts\python.exe`.
- **Dependencies**: solo requests y pygame existentes; biblioteca estándar para medir tiempo/memoria. Sin instalaciones.
- **Storage**: deltas por grupo/frontera, checkpoints de proyección y bases inmutables. Arreglos contiguos, sin índices/cachés con dict/set ni herramientas prohibidas.
- **Interfaces**: consola `historia <t>` / `historia #k`; GUI L/Escape; `--replay ... --hasta t`; `--checkpoint-cada K`.
- **Performance Goals**: <50 ms con >=5000 acciones para el K medido; máximo K acciones aplicadas por consulta; memoria O(D + A + B·S); recorte sin recorrer el prefijo histórico.
- **Scope**: FR-001..017, FR-019/020 y SC-001..005; FR-018 retirado. K=50 es candidato, no resultado medido. Se comparan 10,50,200 y sin checkpoints.

## Constitution Check

| Regla | Resultado de diseño y comprobación |
|---|---|
| I. Estructuras propias | Arreglos contiguos y binaria propia; no se proponen dict/set como índice/caché, heapq, bisect, collections, grafos externos, sorted() ni list.sort() |
| II. Determinismo | Misma semilla/versiones y mismas líneas intercaladas; orden estable de deltas; consultas sin azar |
| III. MVC | Modelo histórico solo datos; presentación en controlador/vistas; retirar import de controlador en bitácora mediante parser inyectado. La dependencia existente en persistencia se comunica a Kim, sin refactorizarla desde esta tarea |
| IV. Datos generales | Sin ids/nombres de criptas concretas; semilla fija solo en escenarios sintéticos |
| V. Presupuesto HTTP | Consultas y observaciones de reconstrucción locales; no precargar ni descargar para consultar; el ensamblado mantiene su contador ordinario |
| VI. Rendimiento medido | Matriz definida; ninguna afirmación de 50 ms o K definitivo hasta ejecutar las mediciones |
| VII. Spec antes de código | Solo documentos; spec intacto en esta revisión; commits del integrante |
| Puntos únicos | Captura donde ya hay mutaciones/inversos; escrituras iniciales anteriores al checkpoint 0 se absorben sin canalizarlas; reloj y pergamino conservan su implementación |

Kim entregó las marcas IR_A en `69dbc30`, pendiente de verificar con T007/T008. FR-014 aún depende de su integración de carga v4; simultaneidad depende de la frontera del motor de Mariano. Son condiciones de integración a probar, no autorizaciones para editar sus archivos. Sin excepciones a las estructuras prohibidas ni nuevas dependencias.

## Project Structure

### Documentación

`plan.md`, `research.md`, `data-model.md`, `quickstart.md` y `contracts/{c1-captura,comandos-interfaz,persistencia}.md`. Esta revisión actualiza plan y tareas; spec, checklist y contratos permanecen intactos.

### Lista final de archivos que tocará Axel al implementar

| Archivo | Cambio limitado |
|---|---|
| `modelo/juego/registro.py` | Captura de atributos/celdas en `Registro.cambiar`, identidad/fronteras de grupo; preservar lambdas, `inverso`, `deshacer_ultimo` y pila de 5 |
| `modelo/juego/linea_tiempo.py` (nuevo) | Deltas, grupos, checkpoints, recorte/reubicación y consultas |
| `modelo/juego/resumen_historico.py` (nuevo) | Proyección, copia explícita, normalización/adopción de entidades y filtrado histórico |
| `modelo/juego/partida.py` | Solo `cambiar`, `_lista_agregar/_lista_quitar`, `_inv_agregar/_inv_quitar/_inv_al_frente`, `_accion` y `usar_pergamino`: instrumentación sin cambiar las operaciones/inversos actuales |
| `controlador/orden.py` | HISTORIA fuera de `ORDENES_DE_PARTIDA`; parser de selector |
| `controlador/controlador.py` | Solo HISTORIA: despacho sin cancelar IR_A, presentación y acceso desde el flujo final; no editar `_ejecutar_ir_a` por cuenta de Axel |
| `controlador/reproductor.py` | Leer/intercalar comentarios existentes, observar sin viajar, replay completo antes de consultar t y propagar K; lector compartible con carga |
| `controlador/aplicacion.py` | **autorizado por Jeferson**: en `_armar`, llamar `inicializar_historia` después de `partida.iniciar()` y antes del bucle de órdenes previas, propagar K; conservar en `self.ordenes` y `registrar_comentario` las líneas intercaladas (órdenes y `# ir a X`), ofrecer `lineas_para_reconstruir()` y conectar el aplicador; inyectar el parser de bitácora en sus llamadores propios y facilitar acceso de solo lectura al reporte existente. Solo estas adaptaciones, sujetas a las restricciones obligatorias de abajo |
| `controlador/resumen_historia.py` (nuevo) | Formateador común sin importar vistas |
| `modelo/datos/bitacora_partida.py` | Solo retirar dependencia de `controlador.orden`: parser/fábrica inyectado como adaptación mínima; conservar formato, encabezado, escritura y omisión de comentarios de su API ordinaria |
| `vista/vista_consola.py` | Parser/ayuda, resumen histórico y final; reporte canónico, marca cazador y conservar costos |
| `vista/vista_pygame.py` | Diálogo/panel L/Escape, modo final y presentación de reporte/cazador; preservar costos |
| `vista/controles_gui.py` | L historia, H/F1 ayuda; botón/texto de ayuda correspondiente |
| `vista/vista_base.py` | Adaptadores mínimos de presentación/entrada histórica y final compatibles con las vistas |
| `main.py` | Exclusivamente las líneas acordadas abajo, con Jeferson |
| `bench/bench_linea_tiempo.py` (nuevo) | Comparaciones de consulta, memoria, recorte y sobrecosto C1 |
| `tests/test_linea_tiempo.py` (nuevo) | FR-001..006,009..013; SC-002..004 |
| `tests/test_historia_interfaces.py` (nuevo) | FR-005,015..017,019,020 |
| `tests/test_historia_persistencia.py` (nuevo) | FR-007,008,014 y contrato de comentarios/carga |
| `tests/test_bench_linea_tiempo.py` (nuevo) | Integridad de las mediciones SC-001,005 |

No se crea `modelo/datos/registro_reconstruccion.py`. Los benches `historial` e `inventario` se repiten sin modificarlos. Los demás archivos de motor/datos solo aparecen en pedidos a sus dueños.

### Restricciones obligatorias de Jeferson

1. En `_armar` se conserva exactamente la condición `partida_nueva and ordenes_previas is None and exigir_versiones is None` para verificar resolubilidad. Solo se verifica una partida nueva; se omite si se proporcionan `ordenes_previas` (incluso una secuencia vacía), si `partida_nueva=False` o si se exige versión. Tampoco cambia al cargar un guardado v4.
2. Al reconstruir, los comentarios no se pasan a `Controlador.ejecutar`, no cuentan como órdenes ni como órdenes rechazadas. Se conservan intercalados para reescribirlos en el log; las marcas `# ir a X` se aplican por el adaptador de observación de T044, sin viajar ni consumir tiempo.
3. No se tocan `verificar()`, `ErrorNoResoluble`, `reporte_resolubilidad` ni `--verificar`/`--forzar` de `main.py`. El alcance sobre el reporte solo permite leer/proporcionar el resultado ya calculado para presentarlo; no modificar su cálculo, almacenamiento ni contrato.
4. Antes de publicar son obligatorias, además de las pruebas de la capacidad, las regresiones `venv\Scripts\python.exe -m tests.test_resolubilidad`, `venv\Scripts\python.exe -m tests.test_resolubilidad_integracion` y `venv\Scripts\python.exe -m tests.test_replay_puntajes` (T065).

### Líneas acordadas de main.py

1. `BENCHES`: añadir `("linea_tiempo", "bench_linea_tiempo.py")`, conservando los demás.
2. `leer_argumentos`: `--checkpoint-cada K` entero positivo y `--hasta T` entero no negativo válido con replay. Sin nuevos metadatos en log/guardado; K efectivo procede de CLI/configuración del proceso o default medido.
3. `correr_replay`: pasar `hasta` y K por nombre a `reproducir`, conservando parámetros/códigos actuales.
4. `correr_interactivo`: propagar K al ensamblado propio de aplicación (**autorizado por Jeferson**) y proporcionar acceso de solo lectura a `app.reporte_resolubilidad`. No añadir observador de registros externos ni nuevas escrituras al log.
5. Mantener despacho de bench/replay/verificar antes de crear vista; sin imports globales de vistas/Pygame.

## Auditoría reducida de mutaciones

| Archivo y función real | Resolución desde el alcance propio |
|---|---|
| `Registro.cambiar` | Ya admite atributos y celdas de listas; copiar anterior/nuevo normalizados y leer el reloj al anotar |
| `Partida._lista_*`, `_inv_*` | Capturar operación, instancia y posición; reversible solo si agregó inverso real. Pergaminos en agregar/quitar no registran inverso; `_inv_al_frente` conserva el suyo |
| `Partida._accion` | Registrar fronteras pre/post y checkpoint cada K; conservar su inverso manual de reloj y el resto de su comportamiento |
| `Partida._avanzar` | Intacto. No necesita emitir deltas de reloj: tiempo se lee en cada cambio y en fronteras; el reloj del resumen temporal se fija a t |
| `Partida.iniciar`, `Actor.mover_a`, `Sala.marcar_visita_jugador` | Posición/rastro/evento pendiente iniciales se absorben tomando checkpoint 0 después de `iniciar()`. Sin cambios en esos métodos |
| `Mapa.incorporar`, `Partida._incorporar` | No editarlos. Normalizar/adoptar entidad al primer encuentro en C1 o en la foto inicial. Capturar base anterior al primer cambio y alta una sola vez; no barrer el mapa entero cada acción |
| `Partida._morir/_entrar` y efectos | Vida, victoria/derrota, velocidad, veneno y antorcha ya usan `cambiar`; capturar allí sin editar estos métodos ni `efectos.py` |
| `Partida._explorar_sala/_recordar_puerta` | Ya usan `cambiar` para celdas/contadores de Kim; no editarlos ni observar desde HISTORIA |
| `Partida.cambiar_estado_puerta` | Ya pasa por C1; mantener C2 y evitar doble captura sin editar su implementación |
| `Controlador._ejecutar_ir_a` | Su observación exterior pasa por C1; posición/frecuencia del comentario de reconstrucción se pide a Kim |
| `Partida.usar_pergamino` | Instrumentar grupo retirado y leer reloj restaurado; recortar/reubicar exclusivamente la historia, sin reaplicar persistentes sobre el juego ni cambiar inversos |

La proyección incorpora enemigos ya conocidos al checkpoint y altas al primer uso C1; solo expone enemigos de la sala histórica. Tokens auxiliares se asignan desde el normalizador a objetos compatibles, sin cambiar constructores de actor/objeto. Si alguna entidad no admite la adaptación, se eleva el pedido mínimo a su dueño antes de ampliar archivos.

## Diseño por bloques

1. **Captura y proyección (FR-001,004,005,013):** datos por valor, sin agenda/funciones/random. No deducir cambios inspeccionando lambdas. Captura reversible/no reversible según comportamiento existente. Inicialización de `LineaTiempo` después de `iniciar()` por el ensamblado, antes de reejecutar órdenes.
2. **Checkpoints y consultas (FR-002,003,006,011,012):** uno en frontera 0, después cada K acciones; selección `#k` en O(1) con `(k-1)//K`, t con binaria propia. Frontera predecisión evita incluir el efecto tomado al mismo entero de reloj. Aplicar como máximo K acciones; contar externos aparte. No ejecutar eventos pendientes para consultar.
3. **Pergamino (FR-009,010):** retirar reversibles y checkpoints del sufijo, reubicar persistentes posteriores al reloj restaurado, mantener anteriores/simultáneos. Reconstruir solo proyección; no cambiar `_en_retroceso`, lambdas, consumo ni notificaciones del motor. Comparar las consultas actuales con el estado real; una divergencia se documenta y coordina, no se corrige escribiendo sobre el juego desde historia.
4. **Carga/replay (FR-007,008,014):** [contrato](contracts/persistencia.md). Leer comentarios y órdenes en su secuencia original; comentario llama observación, nunca el viaje completo. No truncar el log al recortar historia. Reconstruir todo el flujo antes de resolver `--hasta`, porque un pergamino posterior puede eliminar acciones anteriores. Sin nuevos formatos ni K persistido: distinta K puede reconstruir idénticos estados con distribución distinta de checkpoints.
5. **Interfaces (FR-015..017,019,020):** HISTORIA sin log/grupo/tiempo ni cancelación del viaje, L/Escape y H/F1 ayuda. Flujo final no duplica `al_terminar`/puntajes. Usar reporte disponible en app y `formatear_reporte`, respetando 003/FR-015/018. Costos ya visibles se conservan; añadir marca textual/gráfica de cazador.

## Pedidos a otros integrantes

Son contratos mínimos propuestos, no trabajo que Axel incorpora a su lista de archivos.

| Dueño y archivo/función | Cambio mínimo o confirmación | Motivo y firma necesaria |
|---|---|---|
| **Kim**, tramo IR_A de `controlador/controlador.py:Controlador._ejecutar_ir_a` | **Entregado en `69dbc30`, pendiente de verificar con T007/T008**: comentario `# ir a X` antes de cada observación exterior efectiva, después del callback de cancelación, incluidos intentos sin paso | T043 conserva pendiente la verificación de posición, frecuencia y ausencia de observación fantasma. Sin nueva sintaxis ni nuevas órdenes |
| **Kim**, contrato IR_A/modelo existente | Confirmar que reproducir la marca llama una vez a `Partida._observar_puertas()` con grupo cerrado, sin planificar, viajar ni consumir tiempo | Adaptador en reproductor: `reproducir_observacion_ir_a(partida, destino: int) -> None`; usa método existente, no requiere editar Partida fuera de puntos únicos |
| **Kim**, `persistencia_partida.py:foto_de`, `PersistenciaPartida.cargar` y guardado v4 | Conservar comentarios `# ir a X` intercalados con órdenes como cadenas en el campo de líneas ya existente; al cargar, usar el lector/aplicador de reproductor en vez de interpretar cada línea como Orden | `iterar_lineas_reconstruccion(lineas)`, `aplicar_linea_reconstruccion(controlador, linea) -> bool`. Ningún bloque/campo/versión binaria nuevo; no saltarse la validación antes de reemplazar la partida |
| **Kim**, `persistencia_partida.py` (dependencia MVC existente) | Retirar el import de `controlador.orden` y recibir parser/aplicador como callback, no importar reproductor desde modelo | Retirar la dependencia corresponde a la dueña; Axel solo ofrece funciones en controlador. Entrega obligatoria de T046, sin cambiar el formato del guardado |
| **Mariano**, `agenda_eventos.py:AgendaEventos.siguiente` y frontera del motor | Confirmar mediante caso de eventos simultáneos que se entrega el estado exigido antes de cada decisión; si no, indicar el ajuste mínimo a cargo de Mariano | Axel no edita agenda ni `_avanzar`, ni drena eventos desde historia. FR-002 no se declara probado mientras falle este caso |
| **Mariano/Kim**, solo si una prueba demuestra mutación observable posterior a inicio que elude C1 | Indicar punto único ya existente o adaptación mínima en el archivo del dueño | Primero resolver adopción en `resumen_historico.py`; no solicitar cambios preventivos en actor, sala, objetos, mapa, conocimiento, inventario o efectos |

No se piden cambios en `actor.py`, `sala.py`, `objetos.py` por inicialización, ni en `efectos.py` por campos ya capturados. No se piden cambios de estructuras a `inventario.py`, `mapa.py` o `conocimiento.py` cuando su lectura/adopción desde archivos propios basta. La observación normal de puertas no se mueve al controlador de Axel.

## Dependencias y paralelismo del alcance actualizado

T011/T024/T045/T048 son implementación propia de Axel, **autorizado por Jeferson**, y dejan de ser pedidos externos. Orden por contratos y archivo compartido: T010 → T011; T011 + T023 → T024; T024 + T044 → T045; T045 → T048; T047 + T048 → T049. T047 requiere T024 para inicialización y K en ambas fuentes de replay. No solapar cambios en aplicación ni en main (T048 → T049 → T061).

Las ramas de núcleo, vistas y bench avanzan cuando sus dependencias técnicas estén listas, sin esperar el cierre global T050. T031 usa el inicializador directamente y T051 usa el contrato de presentación; no requieren esperar el ensamblado. Las dependencias externas restantes son T025 (Mariano, simultáneos), T043 (Kim, entregado en 69dbc30 y pendiente de verificar con T007/T008) y T046 (Kim, carga v4 e import MVC, sin cambio de responsabilidad/alcance). T025 y T046 conservan sus tareas; T046 requiere T044/T045 para cerrar. Estas entregas condicionan sus casos reales de integración en T050/T065, no el inicio de código independiente.
## Complejidad y memoria

A acciones vigentes; D datos de cambios; S proyección; B=1+floor(A/K); E_K deltas de hasta K acciones; U externos; L costo de secuencias/inventario; R salida.

| Operación/alternativa | Tiempo | Memoria |
|---|---|---|
| Capturar | O(1) amortizado más normalización/posición real | O(tamaño del cambio) |
| Checkpoint | O(S), cada K acciones | O(B·S) |
| Consulta elegida | O(log B + S + E_K + U + L + R); para #k se elimina log B | O(S) temporal, historia O(D+A+B·S) |
| Sin checkpoints | O(S+D_hasta_t+L+R) | O(D+A+S) |
| Desde actual hacia atrás | O(S+D_despues_t+L+R) | O(D+A+S) |
| Copia por acción, solo referencia | O(S+R), más ubicación | O(A·S), descartada |
| Recorte | Deltas/persistentes/destinos del sufijo y suma de tamaños de checkpoints liberados | Sin retener ramas/fotos invalidadas |

K no acota eventos automáticos ni tamaño del mapa. Los directorios conservan capacidad contigua con longitud lógica; no copian el prefijo al recortar. Contabilizar reserva real y liberar bases sin referencias. Con cinco grupos de retroceso, el contador no puede caer más de cinco bajo el máximo de la misma sesión; al cambiar sesión se reemplazan directorios. Ver detalles en [data-model.md](data-model.md).

## Mediciones y aceptación

`bench/bench_linea_tiempo.py` usa `bench/generador_criptas.py:generar_cripta` y su catálogo real, semilla fija y >=5000 acciones aceptadas. Misma carga para K=10,50,200 y sin checkpoints; comparar adelante/atrás y copias de proyección por acción como referencia. Medir total de consulta (copia/aplicación/formato), máximo/mediana, grupos aplicados, memoria retenida/pico y recorte de 1–5 grupos con longitud histórica creciente.

Repetir `bench_historial` y `bench_inventario` (§5.6) sin cambiarlos. Como deshacen Registro directamente o usan Inventario sin Partida, añadir en el bench nuevo variantes integradas que sí midan C1. Elegir K por resultados y documentarlos durante implementación; esta revisión no ejecuta ni inventa mediciones.

Pruebas nuevas cubren todos los FR/SC, comentarios en inicio/bloqueo posterior/cancelación de IR_A, carga con observación sin paso, reubicación, inventario completo, simultaneidad, L/H/F1 y pantalla final. Las regresiones se ejecutan sin modificar los tests existentes. Guía en [quickstart.md](quickstart.md).

## Riesgos y cierre de integración

- **Marcas IR_A:** entregadas por Kim en `69dbc30`, pendientes de verificar con T007/T008; no declarar FR-014 completo antes de comprobar también conservación/carga v4.
- **Inverso y persistente sobre el mismo destino:** comprobar igualdad de proyección y juego; no reescribir el comportamiento del pergamino desde esta feature.
- **Eventos simultáneos pendientes:** prueba de frontera y pedido a Mariano; no cambiar el reloj ni ejecutar agenda desde consultas.
- **Carga pierde comentarios:** Axel conserva la secuencia en aplicación (T045, autorizado por Jeferson); la entrega externa de Kim sigue siendo v4 y el retiro del import MVC (T046).
- **Token/alta o copia filtra estado actual:** normalizar al primer C1, copiar dinámicos por valor y filtrar conocimiento histórico.
- **Latencia/memoria mayores de lo esperado:** medir tamaño real de salida, capacidad reservada y liberación de checkpoints; default pendiente de datos.

El diseño reducido y los contratos quedan listos para desglosar tareas propias y pedidos externos por separado. No se marca como implementado ningún contrato pendiente.
