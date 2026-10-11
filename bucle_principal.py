"""Bucle principal del juego (§2.3)."""

from typing import Callable

from agenda_eventos import AgendaEventos


class Reloj:
    def __init__(self) -> None:
        self.tiempo_actual = 0


def correr(agenda: AgendaEventos, reloj: Reloj, partida_activa: Callable[[], bool]) -> None:
    """Consume la agenda en orden hasta que no queden eventos o la partida termine.

    partida_activa: devolver False detiene el bucle (victoria o derrota, §2.12).
    """
    while partida_activa() and len(agenda) > 0:
        evento = agenda.siguiente()
        if evento is None:
            break
        reloj.tiempo_actual = evento.tiempo_siguiente
        evento.ejecutar(reloj.tiempo_actual)