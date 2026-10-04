"""Movimiento del jugador: entrar a una sala actualiza su rastro (§2.9)."""

from actor import Actor
from sala import DIRECCIONES


def mover_jugador(jugador: Actor, direccion: str, tiempo_actual: int) -> str:
    sala_actual = jugador.sala
    i = DIRECCIONES.index(direccion)

    if sala_actual.salidas[i] != "abierta":
        return "no se puede mover: salida no existe o está cerrada"

    destino = sala_actual.vecino[i]
    if destino is None:
        return "no se puede mover: destino desconocido (falta precargar, §4.2)"

    jugador.sala = destino
    destino.marcar_visita_jugador(tiempo_actual)
    return f"el jugador entra a {destino.id}"