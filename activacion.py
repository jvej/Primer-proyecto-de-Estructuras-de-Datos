"""Activación de enemigos al entrar el jugador a una sala (§2.4).

Cuando varios enemigos se activan en el mismo instante, deben programarse
en orden ascendente de id_instancia para que los números de secuencia
salgan deterministas, sin depender del orden de la lista de contenido.
"""

from typing import Callable, List

from actor import Enemigo
from agenda_eventos import AgendaEventos
from costos import COSTO_ACTIVACION, costo_accion
from evento import Evento


def activar_enemigos(
    agenda: AgendaEventos,
    enemigos: List[Enemigo],
    reloj_actual: int,
    ejecutar_turno: Callable[[Enemigo], None],
) -> None:
    """Agenda la primera acción de cada enemigo recién activado.

    ejecutar_turno(enemigo) es la función que el motor usará para resolver
    el turno de ese enemigo cuando le toque (atacar, moverse o esperar,
    según §2.8 — eso vive en el módulo de comportamiento, no aquí).
    """
    for enemigo in sorted(enemigos, key=lambda e: e.id_instancia):
        tiempo_siguiente = reloj_actual + costo_accion(COSTO_ACTIVACION, enemigo.velocidad)
        evento = Evento(
            tiempo_siguiente=tiempo_siguiente,
            secuencia=agenda.nueva_secuencia(),
            actor=enemigo,
            accion=lambda e=enemigo: ejecutar_turno(e),
            descripcion=f"activación de {enemigo.nombre} ({enemigo.id_instancia})",
        )
        enemigo.evento_pendiente = evento
        agenda.agendar(evento)