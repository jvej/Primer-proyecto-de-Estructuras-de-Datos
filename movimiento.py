"""Movimiento del jugador: entrar a una sala actualiza su rastro (§2.9).

Pendiente (siguiente etapa): cobrar tiempo, esperar contenido no cargado (§4.2),
activar enemigos y disparar trampas al entrar.
"""

from actor import Actor
from sala import DIRECCIONES


def mover_jugador(jugador: Actor, direccion: str, tiempo_actual: int) -> str:
    i = DIRECCIONES.index(direccion)
    salida = jugador.sala.salidas[i]

    if salida is None:
        return f"no se puede mover: no hay salida al {direccion}"
    if not salida.esta_abierta():
        return "no se puede mover: la puerta está cerrada"

    destino = salida.otro_lado(jugador.sala)
    jugador.mover_a(destino)
    destino.marcar_visita_jugador(tiempo_actual)
    return f"el jugador entra a {destino.id}"