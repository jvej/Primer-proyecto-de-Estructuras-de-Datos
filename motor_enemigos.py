"""Conecta el comportamiento de enemigos (§2.8) con la agenda de eventos (§4.1).

Cada turno, al ejecutarse, resuelve la acción y agenda su propio siguiente
turno con el mismo costo 100 — así el enemigo sigue actuando hasta que muere
(en cuyo caso simplemente no se reagenda, sin tocar los eventos ya agendados).
"""

import random
from typing import List

from actor import Actor, Enemigo
from agenda_eventos import AgendaEventos
from comportamiento import resolver_turno_enemigo
from costos import costo_accion
from evento import Evento


def agendar_turno(
    agenda: AgendaEventos,
    enemigo: Enemigo,
    tiempo: int,
    jugador: Actor,
    azar: random.Random,
    bitacora: List[str],
) -> Evento:
    def accion() -> None:
        descripcion = resolver_turno_enemigo(enemigo, jugador, azar, tiempo)
        bitacora.append(descripcion)
        if enemigo.esta_vivo():
            siguiente_tiempo = tiempo + costo_accion(100, enemigo.velocidad)
            enemigo.evento_pendiente = agendar_turno(
                agenda, enemigo, siguiente_tiempo, jugador, azar, bitacora
            )

    evento = Evento(
        tiempo_siguiente=tiempo,
        secuencia=agenda.nueva_secuencia(),
        actor=enemigo,
        accion=accion,
        descripcion=f"turno de {enemigo.nombre} ({enemigo.id_instancia})",
    )
    agenda.agendar(evento)
    return evento


def matar_enemigo(agenda: AgendaEventos, enemigo: Enemigo) -> None:
    """Cancela el evento futuro del enemigo sin recorrer la agenda (§4.1)."""
    enemigo.vida = 0
    if enemigo.evento_pendiente is not None:
        agenda.cancelar(enemigo.evento_pendiente)