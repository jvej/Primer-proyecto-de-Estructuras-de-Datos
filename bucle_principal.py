"""Bucle principal del juego (§2.3)."""

from dataclasses import dataclass
from typing import Callable

from agenda_eventos import AgendaEventos


@dataclass
class Reloj:
    tiempo_actual: int = 0


def correr(agenda: AgendaEventos, reloj: Reloj, partida_activa: Callable[[], bool]) -> None:
    """Consume la agenda en orden hasta que no queden eventos o la partida termine.

    partida_activa: callable sin argumentos; devolver False detiene el bucle
    (por ejemplo, al llegar a victoria o derrota, §2.12).
    """
    while partida_activa() and len(agenda) > 0:
        evento = agenda.siguiente()
        if evento is None:
            break
        reloj.tiempo_actual = evento.tiempo_siguiente
        evento.ejecutar()