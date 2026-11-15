# Decisiones tecnicas y trazabilidad de 002

Revision: 2026-11-13. Base: `75cc63eae09b3c7c85d388f44457086ba443da8a`,
rama integracion-002-003. Documento exclusivo de 002; no sustituye el registro
global del equipo. Evidencia reutilizada de las ejecuciones reales de la sesion;
no se volvieron a ejecutar pruebas ni benchmarks para esta edicion documental.

Se conserva la distincion entre diseno, implementacion y aceptacion oficial.
Fuentes: spec.md, plan.md, research.md, data-model.md y contratos de contracts/.
El extracto oficial aportado no equivale a un PDF completo versionado aqui.
Alternativas documentadas en research.md: atributos en Sala/arbol/listas para
conocimiento; decrease_key frente a eliminacion perezosa; busqueda desde jugador
frente a inversa desde destino; benchmark independiente frente a --bench. Son
alternativas de diseno documentadas, no experimentos comparativos. No consta
una evaluacion adicional para las demas decisiones; no se inventan alternativas.

## D01. Conocimiento indexado por sala

- **Problema:** Consultar sin indices hash ni recorridos globales.
- **Decision:** ConocimientoMapa(n, salas_por_indice, mapa) conserva referencias y almacena N estados y 4N memorias por Sala.indice; contadores mantenidos.
- **Justificacion:** Consultas por indice y resumen O(1), por ID O(log N) con busqueda binaria; espacio O(N).
- **Archivos:** modelo/juego/conocimiento.py; modelo/juego/mapa.py
- **Estado:** Implementada
- **Pruebas/evidencia:** test_conocimiento; test_conocimiento_partida

## D02. Estados y memoria de puertas

- **Problema:** Separar existencia, exploracion y observacion de informacion precargada.
- **Decision:** Salas 0/1/2: desconocida/avistada/explorada. Puertas 0/1/2: desconocida/abierta/cerrada. Observar sincroniza ambos extremos sin explorar la vecina; cambios remotos no actualizan memoria.
- **Justificacion:** Identificar una puerta no revela IDs, nombres ni contenido de salas no exploradas.
- **Archivos:** modelo/juego/conocimiento.py; modelo/juego/partida.py; contracts/contrato_c2_puertas.md
- **Estado:** Implementada
- **Pruebas/evidencia:** test_conocimiento; test_conocimiento_partida; test_mapa_consola

## D03. Reversion y permanentes FR-010 de 004

- **Problema:** Evitar que un inverso antiguo borre observaciones permanentes posteriores.
- **Decision:** Partida.cambiar registra estados y contadores; solo memoria_puertas usa generaciones por celda. El inverso captura generacion y restaura si sigue vigente. Un permanente incrementa generacion incluso con el mismo valor. Captura C1 historica antes de escribir, luego inverso/barrera y escritura.
- **Justificacion:** O(1) por celda y O(cambios) por grupo; conserva identidad, limite de cinco grupos y notificaciones. No protege estado_salas, inventario ni contadores. FR-010 de 002 es privacidad, un requisito distinto.
- **Archivos:** modelo/juego/registro.py; modelo/juego/partida.py
- **Estado:** Implementada e integrada con captura/recorte 004; no declara completa 004
- **Pruebas/evidencia:** test_fr010_generaciones_002 (12); test_linea_tiempo.test_FR010_destino_compartido_inverso_y_persistente

## D04. Antorcha y mundo real

- **Problema:** Revelar topologia sin activar contenido remoto.
- **Decision:** Partida.iniciar establece conocimiento inicial; _entrar con antorcha explora vecinas incluso por salida cerrada, sin propagacion recursiva ni observacion de puertas remotas.
- **Justificacion:** Los helpers actualizan solo salas reveladas y salidas, mantienen contadores y reversibilidad.
- **Archivos:** modelo/juego/partida.py; modelo/juego/conocimiento.py
- **Estado:** Implementada
- **Pruebas/evidencia:** test_conocimiento_partida (9)

## D05. Dijkstra y monticulo propios

- **Problema:** Calcular distancias ponderadas deterministas respetando restricciones.
- **Decision:** Monticulo binario contiguo, eliminacion perezosa, dijkstra_acotado stateless con filtro, cota inclusiva y arreglos/tokens de cada llamador. Dijkstra usa tuplas distancia/ID/indice.
- **Justificacion:** Sin heapq, bisect, collections, networkx ni indices hash. Marcas evitan limpiar arreglos entre busquedas; no evita recorrer el componente alcanzable.
- **Archivos:** modelo/estructuras/monticulo_min.py; modelo/estructuras/dijkstra.py; contracts/contrato_c3_dijkstra.md
- **Estado:** Implementada como proveedor e integrada en los casos de cazador probados
- **Pruebas/evidencia:** test_niebla_ir_a; test_terreno_cazador

## D06. Planificacion conocida de IR_A

- **Problema:** Elegir pasos minimos sin consultar puertas fisicas ni salas desconocidas.
- **Decision:** Dijkstra inverso desde destino, solo extremos explorados y memoria abierta; seleccion por (costo + distancia vecina, ID vecina). No ejecuta acciones.
- **Justificacion:** Costo depende del componente alcanzable, no solo de longitud de ruta. No se ha optimizado tras medir.
- **Archivos:** controlador/planificador_rutas.py; modelo/juego/conocimiento.py
- **Estado:** Implementada; rendimiento oficial pendiente
- **Pruebas/evidencia:** test_planificador_rutas (9)

## D07. Viaje compuesto y marcas intercaladas

- **Problema:** Conservar tiempo, eventos, log y retroceso individual.
- **Decision:** IR_A fuera de ORDENES_DE_PARTIDA. Pasos MOVER ordinarios con recalculo y parada por llegada, enemigos, dano incluso curado, fin o bloqueo; nunca abre puertas. Tras callbacks/cancelacion, una marca # ir a X inmediatamente antes de cada observacion exterior efectiva, aunque no haya movimiento.
- **Justificacion:** No inventa acciones ni deduplica observaciones; sustituir Partida recrea planificador. Aplicacion conecta log activo y conserva cadenas. Leer_log ordinario omite comentarios; lector 004 repite marcas como observacion, sin viajar.
- **Archivos:** controlador/controlador.py; modelo/juego/orden.py; controlador/orden.py; modelo/datos/bitacora_partida.py; controlador/aplicacion.py; main.py
- **Estado:** Implementada, incluido registro real y T045/T046
- **Pruebas/evidencia:** test_ir_a_compuesto (27); test_comentarios_ir_a_002 (7); test_integracion_comentarios_002 (5)

## D08. Cancelacion por observador opcional

- **Problema:** Atender eventos sin hilos ni pasos extra.
- **Decision:** agregar_observador_viaje recibe funcion(Partida)->bool antes de observar/recalcular/mover; comprueba token e identidad. False cancela; excepciones se propagan y finalizan viaje. Callback no ejecuta acciones.
- **Justificacion:** Cancelacion sin tiempo extra; pasos anteriores permanecen reversibles.
- **Archivos:** controlador/controlador.py; vista/vista_pygame.py; main.py
- **Estado:** Implementada y conectada a Pygame
- **Pruebas/evidencia:** test_ir_a_compuesto; test_ir_a_grafico_002 (13)

## D09. Mapa privado en consola y Pygame

- **Problema:** Evitar que la vista exponga mapa precargado o apertura remota.
- **Decision:** mapa_conocido filtra salas y salidas; salidas_visibles conserva cinco campos, con ID None para no exploradas. MAPA sin tiempo. M muestra mapa; V devuelve IR_A; Escape cancela; R deja un pergamino pendiente ligado a Partida fuera del callback; QUIT prevalece y lo descarta.
- **Justificacion:** Modelo filtra; vistas no planifican. No imprimen sala None. Consulta completa O(N), consultas individuales O(1).
- **Archivos:** modelo/juego/partida.py; vista/vista_base.py; vista/vista_consola.py; vista/vista_pygame.py; vista/controles_gui.py
- **Estado:** Implementada; interfaces HISTORIA de 004 pendientes
- **Pruebas/evidencia:** test_mapa_consola (7); test_ir_a_grafico_002 (13)

## D10. Benchmarks reproducibles integrados

- **Problema:** Medir operaciones reales sin red, vista ni certificaciones inventadas.
- **Decision:** perf_counter_ns; semillas fijas 20261110/17, datos sinteticos 10/100/1000, preparacion/calentamiento excluidos. Adaptador main([]) y registro BENCHES. Exploracion sin/con antorcha, celda protegida, pergamino real, Dijkstra, planificacion y recalculo.
- **Justificacion:** Maximos individuales salvo consultas por lote; por-cambio amortizado no es maximo individual. Conserva GC normal y sobrecosto Python.
- **Archivos:** tests/bench_niebla_ir_a.py; bench/bench_mapa_conocido.py; main.py
- **Estado:** Instrumentacion implementada y medida; SC-001 oficial y comparacion T030 pendientes
- **Pruebas/evidencia:** test_bench_mapa_conocido_002 (4); ejecucion CLI real

## Persistencia v4 y T045/T046

Estado: implementada y probada. Codec VERSION_FORMATO=4, CRPT, encabezado
<4sHIQI>. General: N uint16, N estados, P uint16, P entradas <HBB>; P cuenta
posiciones de memoria, no puertas unicas. Ceros omitidos y restaurados como
cero. Enemigos conservan instancia/tipo/vida/tiempo_siguiente; rango viene de
catalogo. Se validan valores, duplicados, indices, offsets, truncamientos y
consumo exacto. No hay CRC implementado ni exigencia encontrada de CRC en C7.

foto_de copia estados/memoria y admite cadenas u Orden para compatibilidad.
Guardar usa app.lineas_para_reconstruir() sin perder orden o marcas repetidas.
El codec decodifica una fotografia, no reconstruye objetos vivos. Cargar usa
app.preparar_reconstruccion y el callback del controlador candidato; dentro del
contexto aplica lineas y valida N, indices, estados, salidas, simetria, sala
actual, contadores por recuento O(N) y coincidencia exacta con replay.
No reemplaza ConocimientoMapa, arreglos ni Registro. Solo salida normal publica;
un fallo conserva sesion, log y capacidad de seguir jugando. No activa
resolubilidad. Condicion conservada:
`if partida_nueva and ordenes_previas is None and exigir_versiones is None:`.
Callback T045: True incluye comentarios ignorados; False significa orden
rechazada. No confundir con el ayudante de bajo nivel del reproductor.
Pruebas: test_guardado_v4_002 (15), test_carga_v4_002 (11) y casos FR014 de
test_historia_persistencia (incluido import Orden del modelo, K distinta y rollback).

## Trazabilidad y evidencia de la integracion

Las pruebas citadas son modulos dentro de tests/, ejecutados con el Python del
venv como -m tests.<modulo>. Implementado/probado no significa enumeracion
exhaustiva de todos los estados posibles ni cierre global de T031.

| Requisito 002 | Implementacion | Prueba aprobada | Estado | Evidencia pendiente |
|---|---|---|---|---|
| FR-001 | ConocimientoMapa y _explorar_sala | test_conocimiento; test_conocimiento_partida | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-002 | Partida.iniciar | test_conocimiento_partida, test_FR002_inicio_solo_sala_inicial_y_puertas_locales | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-003 | mapa_conocido/salidas_visibles | test_mapa_consola, test_FR003_FR006_mapa_usa_memoria_no_estado_fisico | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-004 | Filtrado IDs/nombres/contenido | test_mapa_consola, test_FR004_FR005_mapa_no_filtra_ids_nombres_ni_contenido | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-005 | Filtro de rutas y mapa | test_planificador_rutas, test_FR015_no_usa_intermedias_avistadas_o_desconocidas | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-006 | Observaciones locales y C2 | test_conocimiento_partida; test_terreno_cazador | Funcional verificado | Coordinacion motor de simultaneos T025 de 004 |
| FR-007 | Antorcha en _entrar | test_conocimiento_partida, test_FR007_FR008_antorcha_revela_sin_observar_puertas_remotas | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-008 | Revelacion sin activacion remota | test_conocimiento_partida, mismo caso FR007/FR008 | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-009 | MAPA fuera de acciones | test_mapa_consola, test_FR009_mapa_es_consulta_sin_tiempo_historial_ni_log | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-010 | Privacidad de modelo y vistas | test_mapa_consola; test_ir_a_grafico_002 | Funcional verificado | No confundir con FR-010 de 004 |
| FR-011 | Fotografia y carga v4 | test_guardado_v4_002; test_carga_v4_002 | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-012 | Registro y generaciones de memoria | test_conocimiento; test_conocimiento_partida; test_fr010_generaciones_002 | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-013 | Captura C1 historica previa | test_linea_tiempo, test_FR010_destino_compartido_inverso_y_persistente; test_historia_persistencia, test_FR010_comentario_ir_a_observa_sin_accion | Captura integrada | Frontera de simultaneos FR002 de 004 pendiente |
| FR-014 | Parser y destino explorado | test_ir_a_compuesto; test_planificador_rutas | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-015 | Dijkstra inverso sobre memoria | test_planificador_rutas, test_FR015_prefiere_mas_pasos_con_menor_costo | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-016 | Seleccion costo/ID primer vecino | test_planificador_rutas, test_FR016_empate_elige_menor_id_del_primer_vecino | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-017 | MOVER ordinario por paso | test_ir_a_compuesto, test_FR017_FR018_pasos_ordinarios_costos_y_recalculo | Funcional verificado | Coordinacion motor de simultaneos T025 de 004 |
| FR-018 | Recalculo previo al paso | test_ir_a_compuesto, test_FR018_evento_cierra_puerta_y_se_recalcula | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-019 | Paradas por dano/enemigos/bloqueo | test_ir_a_compuesto; test_ir_a_grafico_002 | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-020 | Avisos de detencion | test_ir_a_compuesto, casos de destino y paradas | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-021 | Nunca abrir automaticamente | test_ir_a_compuesto, test_FR021_nunca_abre_puertas_ni_usa_llaves | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-022 | Marcas y movimientos intercalados | test_comentarios_ir_a_002; test_integracion_comentarios_002; test_carga_v4_002 | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-023 | Pergamino individual y cancelacion | test_ir_a_compuesto; test_ir_a_grafico_002; test_carga_v4_002 | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| FR-024 | Rechazo v3 y rollback | test_guardado_v4_002, test_FR024_version_3_rechazada_explicita; test_carga_v4_002 | Funcional verificado | Cierre global T031, sin incidencia especifica nueva |
| SC-001 | Planificar/recalcular por Dijkstra | Benchmark sintetico | Pendiente oficial | Falta cripta oficial; 1000 sinteticas superan 5 ms |
| SC-002 | Consultas indexadas y resumen O(1) | test_conocimiento, test_SC002_resumen_no_recorre_arreglos; 10^6 consultas/lote | Instrumentado y medido | Medicion no prueba por si sola complejidad |
| SC-003 | Helpers sin/con antorcha | test_bench_mapa_conocido_002; benchmark | Instrumentado y medido | Comparar grado/salas reveladas; helpers no son accion completa |
| SC-004 | Celda protegida y pergamino real | test_bench_mapa_conocido_002; benchmark | Instrumentado y medido | Promedio amortizado por cambio no es maximo individual |
| SC-005 | Costo minimo y desempate | test_niebla_ir_a; test_planificador_rutas | Aprobado en casos automatizados | No equivale a enumerar todos los grafos |

## Mediciones reales de la sesion

Python 3.13.18, Windows 11. Datos de consola ya obtenidos, no una ejecucion nueva
de esta revision. mapa_conocido: semilla 20261110; 7 x 20 = 140 muestras por
operacion; consultas 7 lotes de 10^6; viaje semilla 17, 7 x 8 = 56 muestras.
Preparacion y calentamiento fuera del tiempo; duracion CLI 17,9 s.

| N / E cuadricula | Planificar media / max ms | Dijkstra completo media / max ms | Recalculo en linea media / max ms |
|---|---|---|---|
| 10 / 13 | 0,074946 / 0,478600 | 0,074772 / 0,445500 | 0,072150 / 0,304300 |
| 100 / 180 | 0,972790 / 1,944900 | 0,951705 / 2,030800 | 0,494302 / 1,063700 |
| 1000 / 1936 | 11,755245 / 15,624900 | 11,273351 / 14,268700 | 4,934320 / 6,149000 |

El recalculo en viaje usa linea E=N-1, no cuadricula. No se identifica esa
cuadricula como la cripta oficial. Medicion historica anterior comunicada:
planificacion 1000 salas, media aproximada 8,548 ms (8,547739), max 12,153700 ms.
No se usa esa cifra como certificacion ni como linea base equivalente controlada;
su diferencia con la media actual no demuestra una regresion.

| N | Consulta estado / puerta / resumen, ns/op medios | Explorar normal media / max ms | Antorcha media / max ms | Pergamino real media / max ms |
|---|---|---|---|---|
| 10 | 240,77 / 299,82 / 70,84 | 0,011506 / 0,020200 | 0,027586 / 0,153100 | 0,026214 / 0,036900 |
| 100 | 236,11 / 323,62 / 72,42 | 0,014630 / 0,050300 | 0,026729 / 0,049000 | 0,024857 / 0,036000 |
| 1000 | 216,63 / 320,87 / 72,63 | 0,018046 / 0,066800 | 0,040142 / 0,153800 | 0,041257 / 0,056200 |

| N | Registrar celda media / max ms | Invertir celda media / max ms |
|---|---|---|
| 10 | 0,000599 / 0,001200 | 0,000847 / 0,001100 |
| 100 | 0,000575 / 0,000900 | 0,000766 / 0,001000 |
| 1000 | 0,000722 / 0,004200 | 0,001333 / 0,037900 |

Consultas: maximos de lote, no maximo individual. Grados explorados 3/3/4.
Pergamino revierte 17 cambios totales de movimiento; por-cambio es promedio
amortizado, no latencia individual. Ciclo de 20 ms con cazadores no evaluado.

### T030: cuatro benchmarks ejecutados; comparacion pendiente

Ejecutados mediante CLI en temporal externo; codigo final 0 y ningun archivo
restante. Cache/lista/ordenamiento trabajan en memoria; guardado crea/elimina
BIN/JSON relativos al temporal. No se modificaron esos benchmarks.
Estadisticos propios de cada script, no todos media/maximo. Ordenamiento incluye
referencia sorted() solo comparativa, no usada en estructuras evaluadas.

| Benchmark | Duracion | Resultado representativo real |
|---|---|---|
| cache | 23,7 s | tope 25: acierto 1,109 us; fallo 0,773 us; desalojo 5,316 us; tope 10000: desalojo 1016,718 us |
| lista_ordenada | 9,9 s | N=10000: busqueda 1,868 us vs lineal 191,228 us; insercion individual 2914,076 ms vs masiva 41,140 ms |
| ordenamiento | 23,0 s | N=5000 aleatorio, medianas: insercion 959,994 ms; merge 17,039 ms; automatico 17,137 ms |
| guardado | 1,0 s | N=5000: binario 404,2 KB vs JSON 563,0 KB; medianas carga 33,294 ms vs 12,734 ms; una sala binaria 0,0853 ms |

No hay linea base equivalente localizada; no certificar ausencia de regresiones.

## Verificación posterior sobre 18b9364

42/42 módulos ejecutados por separado y 229/229 unittest conjuntos aprobados,
sin errores; ejecución conjunta de 140,442 s. Dos corridas nuevas de los cinco
benchmarks terminaron con código 0. La sección 17.5 del
[documento global](../../DECISIONES.md#175-evidencia-empírica-y-funcional)
registra condiciones, valores Parte I/II, variabilidad y límites. No se vuelven
a ejecutar aquí ni se reemplazan las mediciones históricas anteriores.

Los máximos de planificación de 1000 salas sintéticas fueron 39,5715 y
16,4738 ms; no representan la cripta oficial de SC-001. La matriz funcional
anterior conserva sus requisitos y pruebas, pero sus referencias a fallos
compartidos pendientes corresponden a la revisión histórica, ya superada.

## Pendientes y coordinacion

- SC-001: identificar y medir la cripta oficial, sin redefinirla.
- T030: comparacion con linea base equivalente; ejecucion y reporte ya realizados.
- T031: cierre integral FR/SC pendiente; regresiones nuevas 42/42 módulos y 229/229 unittest aprobados.
- Interfaces HISTORIA, replay hasta, eventos simultáneos y falso positivo GUI: corregidos en la integración final; ya no constituyen fallos abiertos.
- T045/T046 y FR-010 integrados y verificados; se conserva la autoría de las entregas de cada integrante.
- research.md conserva estimaciones de memoria no medidas en objetos Python.
- spec.md conserva requisitos e identifica implementación funcional con rendimiento pendiente. El checklist previo evalúa especificación, no entrega.
