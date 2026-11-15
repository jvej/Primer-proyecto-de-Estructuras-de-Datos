# Contrato C4: viaje IR_A, comentarios y reconstruccion

Participantes: Kim (002) y Axel (004). Estado: integrado en `75cc63e`;
la interfaz HISTORIA y replay `hasta` de 004 no se declaran terminados.

## Orden y planificacion

`IR_A = "ir_a"` se define en `modelo/juego/orden.py` y se reexporta desde
`controlador/orden.py`. `interpretar_ir_a` acepta `ir a <id>`; IR_A queda fuera
de ORDENES_DE_PARTIDA y no admite a_texto como accion ordinaria.
PlanificadorRutas valida destino explorado y calcula sobre salas exploradas y
puertas recordadas abiertas. No consulta aperturas fisicas. Minimiza suma de
costos y desempata por el menor ID de primer vecino. Cada instancia posee sus
arreglos y tokens C3; sustituir Partida recrea el planificador.

Destino invalido/no explorado o ausencia de ruta inicial: rechazo sin tiempo.
Destino actual: aviso sin accion. El viaje nunca abre puertas automaticamente.

## Secuencia y marcas exteriores

Por cada iteracion efectiva:

1. Callbacks de viaje y comprobacion de token e identidad de partida.
2. Si continua, emitir exactamente `# ir a X` mediante observadores de comentarios.
3. Llamar una vez a Partida._observar_puertas fuera del grupo de accion.
4. Recalcular con el conocimiento vigente.
5. Si existe paso, ejecutar Orden(MOVER, direccion) ordinaria.
6. Evaluar llegada, dano (incluso seguido de curacion), enemigos vivos,
   fin de partida y bloqueo; informar el motivo especifico.

Cancelar antes de observar no emite marca ni consume tiempo. Observar y
quedarse sin ruta conserva la marca sin inventar un movimiento. Pueden existir
marcas repetidas legitimas: no deduplicarlas. Cada movimiento conserva tiempo,
eventos y grupo reversible propios. El pergamino deshace solo el ultimo paso y
no reanuda el viaje.

## Bitacora y lectores

BitacoraPartida.anotar_comentario escribe el prefijo `# `; Aplicacion conserva
ordenes y marcas en su orden de aparicion y main conecta el log activo.
`leer_log` ordinario sigue ignorando comentarios: no es el lector que garantiza
reconstruccion historica. El lector 004 iterar_lineas_reconstruccion conserva
marcas IR_A; aplicar_linea_reconstruccion llama reproducir_observacion_ir_a
sin planificar, mover, gastar tiempo ni crear un grupo. Los otros comentarios
se ignoran. Ningun comentario se ejecuta como Orden.

El callback entregado por Aplicacion.preparar_reconstruccion devuelve True
para lineas validas y comentarios ignorados, False para ordenes rechazadas;
formato invalido lanza ValueError. No confundirlo con el ayudante de bajo nivel,
que tambien devuelve False para comentarios ignorados.

## T045/T046 y FR-010 de 004

Guardar usa Aplicacion.lineas_para_reconstruir(). Cargar entrega cada cadena,
incluidas marcas repetidas, al callback de la candidata dentro del contexto
transaccional. Compara fotografia y replay antes de publicar la nueva sesion.
No reemplaza arreglos utilizados por inversos. No cambia formato binario.

Una observacion permanente posterior invalida inversos anteriores de esa celda
de memoria mediante generaciones privadas. Si el valor observado no cambia,
tambien avanza la generacion. Solo memoria_puertas esta protegida. La captura C1
historica ocurre antes de la escritura y el recorte conserva persistentes.
Esto es FR-010 de 004, distinto del FR-010 de privacidad de 002.

## Interfaz grafica y pruebas

V abre el dialogo; Escape cancela sin SALIR; R cancela y deja un unico pergamino
pendiente ligado a la partida, ejecutado fuera del callback. QUIT prevalece y
lo descarta. Callback atender_viaje solo procesa eventos/presentacion.

Evidencia: tests/test_planificador_rutas.py, test_ir_a_compuesto.py,
test_comentarios_ir_a_002.py, test_integracion_comentarios_002.py,
test_ir_a_grafico_002.py, test_carga_v4_002.py y casos FR010/FR014 de
test_historia_persistencia.py. La prueba de eventos simultaneos de 004 y las
interfaces historicas tienen pendientes separados; ver DECISIONES.md.
