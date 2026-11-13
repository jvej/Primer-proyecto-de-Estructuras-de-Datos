# Contrato C1: instrumentación de alcance propio

Axel implementa en Registro, LineaTiempo, ResumenHistorico y únicamente los puntos únicos enumerados de Partida. Contratos ajenos se solicitan en `plan.md:Pedidos a otros integrantes`.

## Captura

| Punto real | Adaptación mínima |
|---|---|
| `Registro.cambiar(objeto, campo, valor)` | Conservar firma y soporte atributo/celda; capturar anterior/nuevo normalizados y tiempo leído al anotar |
| `Registro.abrir_grupo/cerrar_grupo` | Exponer identidad/fronteras para historia, sin sustituir los grupos inversos |
| `Registro.inverso/deshacer_ultimo` | Mantener lambdas y orden actual; exponer el grupo retirado para recortar historia, no inspeccionar lambdas |
| `Partida.cambiar` | Conservar delegación y compatibilidad con el adaptador de daño de IR_A; sin nuevos caminos de juego |
| `Partida._lista_agregar/_lista_quitar` | Delta de operación, elemento y posición, también si no hay inverso |
| `Partida._inv_agregar/_inv_quitar/_inv_al_frente` | Misma operación/inverso que hoy; capturar pergaminos sin inverso y traslado de equipamiento |
| `Partida._accion` | Fronteras/checkpoint al completar cada K acciones; conservar el inverso manual del reloj |
| `Partida.usar_pergamino` | Añadir observación del grupo/reloj y recorte histórico; no cambiar consumo, inversos ni comportamiento |

`reversible` significa inverso efectivo: registrar=True sin grupo abierto no basta. La captura C2 ocurre una vez al pasar por C1, sin editar `cambiar_estado_puerta` ni agregar doble suscripción.

## Reloj e inicio

`Partida._avanzar` queda intacto. Cada delta lee `reloj.tiempo_actual` a través del lector conectado a Registro/LineaTiempo; no necesita convertir movimientos del reloj en deltas. `_accion` mantiene su lambda inverso de reloj.

API propuesta propia: `inicializar_historia(partida, checkpoint_cada: int) -> None`, en `resumen_historico.py`. Jeferson la conecta después de `partida.iniciar()` y antes de reejecutar órdenes. No editar constructor/iniciar de Partida. Las escrituras iniciales de mover_a, visita y evento pendiente quedan en checkpoint 0.

Normalizar/adoptar entidades al primer encuentro C1 o foto inicial desde `resumen_historico.py`; no modificar clases de actor/sala/objeto, Mapa o Inventario por prevención. Las mutaciones de vida/efectos/conocimiento ya pasan por `cambiar` y se capturan allí.

## API histórica propuesta

- `LineaTiempo(checkpoint_cada, leer_reloj)`.
- `iniciar(proyeccion)` después del inicio.
- `abrir_accion(numero, reloj, cursor_preaccion)` / `cerrar_accion(numero, reloj, cursor_postaccion)`.
- `anotar(delta)`; tiempo leído al anotar y valores normalizados.
- `recortar(grupo, reloj_restaurado)`; elimina reversibles/reubica persistentes solo en historia.
- `consultar_t(t)` / `consultar_accion(k)`; resultado aislado o error sin mutación.

## Retroceso

No ampliar la pila de cinco grupos ni reaplicar cambios sobre la partida viva. Mantener `_en_retroceso`, silenciamiento C2 e invalidación global existentes. Reubicar persistentes posteriores al reloj restaurado a ese instante y conservar anteriores/simultáneos. La proyección usa anclas de orden y tokens para no duplicar pergaminos ni referir nodos vivos.

Las consultas del reloj actual y #N+1 deben coincidir con el estado real. Si una prueba encuentra que el inverso actual pisa un persistente, elevar el caso al dueño; esta feature no lo corrige alterando operaciones del juego.

## Frontera de eventos

La captura añade cortes pre/postacción para no incluir la decisión que empieza al mismo t. No procesa agenda. La confirmación de eventos automáticos simultáneos corresponde a Mariano; cualquier ajuste en sus archivos es pedido externo condicionado a una prueba que falle, no una modificación propia.

## Pruebas

`test_FR005_historia_sin_mutaciones`, `test_FR009_antorcha_revertida`, `test_FR010_reubicacion_y_estado_vivo`, `test_FR003_renumeracion`, `test_FR012_checkpoint_exacto`, `test_SC002_limite_K` y `test_SC004_recorte_local`. Añadir aserciones de comportamiento de reloj/pergamino idéntico antes/después de instrumentar, e inventario completo en el caso inverso/persistente.
