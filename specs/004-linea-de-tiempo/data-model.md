# Modelo de datos: línea de tiempo de alcance reducido

Tipos propuestos en `modelo/juego/linea_tiempo.py` y `modelo/juego/resumen_historico.py`. El modelo no importa controlador, vistas ni archivos. No cambia clases de otros integrantes.

## 1. Inicialización e identidad

`inicializar_historia(partida, checkpoint_cada: int) -> None`, en `resumen_historico.py`, se conecta después de `Partida.iniciar()` y antes de reejecutar órdenes. Crea proyección/checkpoint 0 y conecta la captura de Registro con un lector de `partida.reloj.tiempo_actual`. No requiere cambiar constructor ni `iniciar()` de Partida.

Los datos iniciales incluyen posición/rastro/actores/conocimiento ya preparados. No se canalizan `Actor.mover_a` o `Sala.marcar_visita_jugador` de esa inicialización. Las entidades posteriores se adoptan al primer encuentro en C1, antes de aplicar su primer cambio; se conserva alta/base una sola vez, sin barrido completo por acción ni cambios en `Mapa.incorporar`.

Sala se identifica por `Sala.indice`, conservando su id entero externo. Actor/objeto reciben token por instancia desde el normalizador; `Objeto.id` solo identifica ficha. Usar atributos auxiliares de los objetos existentes cuando sean compatibles; no editar actor.py/objetos.py para añadirlos. Bases estáticas se copian una vez y se comparten como datos inmutables. Los objetos sin referencias del motor/historia se liberan; no hay tabla global creciente por token.

## 2. ProyeccionHistorica y ResumenHistorico

La proyección almacena datos propios:

- Reloj de la frontera, contador de acciones, derrotados y estado (`jugando`, `victoria`, `derrota`).
- Jugador: sala, vida/vida_max, estadísticas base/efectivas y equipo por token.
- Inventario en orden real, tokens y atributos dinámicos necesarios, como usos. No contiene nodos/cursor de Inventario ni una vista ordenada auxiliar.
- Vida, sala/presencia y bases necesarias de enemigos incorporados. El resultado solo muestra enemigos vivos de la sala histórica. Copiar solo enemigos locales del checkpoint no permitiría consultar otra sala correctamente.
- Efectos como datos derivados de campos capturados: veneno, velocidad temporal y antorcha; nunca un Evento/función.
- `estado_salas[N]`, `memoria_puertas[4*N]` y contadores. Mostrar exploradas/avistadas y puertas recordadas respetando la ocultación de 002.

El resumen es la salida filtrada de esa proyección. No lee puertas/vida actuales para completar el pasado. Las copias dinámicas son independientes del motor y de otros resultados. No se copian agenda, azar, precarga, cachés ni bitácora.

## 3. DeltaHistorico

| Campo | Significado |
|---|---|
| secuencia_origen | Orden estable de captura |
| instante_origen, instante | Reloj leído al anotar y tiempo efectivo tras reubicación |
| grupo/frontera | Acción de origen o cola exterior |
| reversible | Esta mutación tiene inverso efectivo según el comportamiento actual |
| destino/tipo, token o índice | Entidad/celda de proyección, no acceso desde consulta a objeto vivo |
| campo/posición | Atributo normalizado o índice contiguo |
| operación | ASIGNAR, INSERTAR, QUITAR, MOVER, ALTA |
| anterior/nuevo | Valores normalizados por copia |
| elemento/posición vieja/nueva | Token y orden para secuencias |
| anclas de orden | Vecinos/clave necesarios para aplicar un persistente si el sufijo eliminó elementos intermedios |

Cada delta obtiene tiempo del lector de reloj, también cuando procede directamente de `Registro.cambiar`. No se crean deltas de reloj por cada `_avanzar`; se conserva el inverso manual que ya tiene `_accion`. El reloj entre eventos se representa en la consulta por t y por las fronteras para #k.

`PosicionInventario` tiene nodos vivos y no se almacena en checkpoints. Consultar/aplicar un objeto por token en la secuencia puede costar O(I), incluido en las complejidades; no se usa índice hash.

## 4. Grupos y fronteras

Arreglo contiguo de grupos por acción aceptada vigente y referencia directa al último grupo. La pila reversible conserva solo sus cinco grupos; la historia conserva todos los grupos vigentes aunque ya no sean deshacibles.

Cada frontera b es el estado antes de la acción b+1, con reloj/cursor y deltas exteriores posteriores al cierre de b. HISTORIA/ayuda/inventario/mapa/rechazos no crean grupo ni frontera de acción. Cada paso aceptado de IR_A sí cuenta.

Los efectos de la acción iniciada a t están después de su corte predecisión aunque el reloj entero sea el mismo. La frontera se lee del motor; no se drena la agenda al consultar. Confirmar con Mariano que todos los eventos automáticos exigidos de t ocurrieron antes de publicarla; si el motor no lo cumple, el ajuste corresponde al dueño.

En un final inmediato, la frontera terminal actual tiene prioridad para consultar el reloj actual, según la igualdad exigida por FR-010. #k sigue usando su cursor preacción. Si N vuelve a cero tras pergamino, #1 usa la frontera inicial vigente con persistentes reubicados.

## 5. PuntoControl

Campos: acciones completadas b, reloj de frontera, cursor y copia explícita de proyección. Existe b=0 después de iniciar y luego b múltiplo de K después de cerrar la acción en `_accion`. `checkpoints[b//K]` ubica ese punto.

Las colas exteriores se aplican después del cursor: recibir una observación o reubicar persistentes no provoca otra copia completa. Descartar un grupo retira solo checkpoints posteriores al contador restaurado, sin volver a copiar un checkpoint anterior.

Directorios de grupos/fronteras/checkpoints: capacidad reservada y longitud lógica sobre almacenamiento contiguo. Al recortar solo limpiar sufijo; no slicing/copia del prefijo ni reducción implícita de capacidad. Medir la reserva real: por los cinco grupos de pergamino el contador no baja más de cinco bajo su máximo de esa sesión; al cambiar/cargar sesión se crea almacenamiento nuevo. Liberar deltas/bases/fotos sin referencias; la liberación de cada foto cuesta según su tamaño.

## 6. Consulta

1. Validar t entero no negativo/no futuro o k entre 1 y N+1.
2. #k ubica bloque en `(k-1)//K`; t usa binaria propia sobre tiempos de checkpoints y corte de decisión dentro del bloque.
3. Copiar proyección anterior, aplicar deltas hasta el cursor de #k o el corte temporal de t, como máximo K acciones; medir deltas externos aparte.
4. Para t entre eventos, fijar reloj del resultado a t; para #k usar el reloj de frontera.
5. Filtrar/formatear usando solo datos históricos. La consulta nunca observa, carga, ejecuta agenda, registra log ni altera retroceso.

Costo O(log B + S + E_K + U + L + R), eliminando log B para selección de #k. Memoria histórica O(D+A+B·S), con capacidad real y catálogo compartido contabilizados; memoria temporal O(S).

## 7. Retroceso exclusivamente histórico

En `usar_pergamino`, instrumentar la captura de consumo y referencia del grupo, respetando las mutaciones y los inversos actuales. Después de `deshacer_ultimo`, leer el reloj restaurado r; retirar reversibles y checkpoints del sufijo; conservar persistentes y reubicar los de tiempo mayor que r a r, tras sus eventos y antes de la siguiente decisión. Los de tiempo menor/igual conservan su instante.

Aplicar/reordenar esos persistentes solo en la proyección histórica, por token/anclas y orden estable. Ajustar sus anteriores analíticos para la alternativa de reconstrucción hacia atrás. No reaplicarlos al motor, no añadir nuevos inversos ni modificar el consumo o `_en_retroceso`.

Comparar la proyección con el estado real después de retroceder. Si el comportamiento actual pisa un persistente, elevar el caso al dueño con prueba; no convertir una divergencia en un cambio de juego oculto. El recorte visita solo deltas/persistentes del sufijo y las fotos descartadas, incluyendo su costo de liberación.

## 8. Reconstrucción sin datos persistidos nuevos

No se serializan estas clases. Al cargar/reproducir se reejecutan líneas existentes de órdenes y comentarios `# ir a X`; cada marca llama el mismo método de observación sin grupo/tiempo, mediante callback de controlador. Kim conserva esas líneas en v4 y Jeferson su intercalación en memoria. K es configuración de ejecución, no campo nuevo del archivo; una K diferente cambia distribución de checkpoints, no estados históricos.

## 9. Invariantes y condiciones de integración

- Checkpoints: `1+floor(N/K)`; ninguna copia completa por acción.
- Acciones, reloj, agenda, azar y pergamino mantienen su comportamiento actual.
- Deltas de vida/efectos/conocimiento se capturan en los puntos únicos ya usados.
- `consulta_t(reloj_actual) == consulta_accion(N+1) == resumen vivo`; probar tras inicio/acción/observación/pergamino/final.
- No referencias a grupos eliminados ni copias de estado para cada acción.
- La fidelidad de FR-014 exige marcas completas en cada observación exterior y conservación intercalada en carga; no se presupone que el código actual ya lo hace.
