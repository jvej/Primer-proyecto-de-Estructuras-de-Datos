"""Conecta el comportamiento de enemigos (§2.8) con la agenda de eventos (§4.1).

Cada turno, al ejecutarse, resuelve la acción y agenda su propio siguiente
turno con el mismo costo 100 — así el enemigo sigue actuando hasta que muere
(en cuyo caso simplemente no se reagenda, sin tocar los eventos ya agendados).
"""

import random
from typing import List

"""Conecta el comportamiento de enemigos (§2.8) con la agenda de eventos (§4.1).

Cada turno, al ejecutarse, resuelve la acción y agenda su siguiente turno con
costo 100. El siguiente tiempo se calcula con el reloj del momento de ejecutar
(ahora), nunca con uno guardado al agendar.
"""

import random
from typing import List

from actor import Actor, Enemigo
from agenda_eventos import AgendaEventos
from comportamiento import resolver_turno_enemigo
from costos import COSTO_TURNO_ENEMIGO, costo_accion
from evento import Evento


def agendar_turno(
    agenda: AgendaEventos,
    enemigo: Enemigo,
    tiempo: int,
    jugador: Actor,
    azar: random.Random,
    bitacora: List[str],
) -> Evento:
    def accion(ahora: int) -> None:
        bitacora.append(resolver_turno_enemigo(enemigo, jugador, azar, ahora))
        if enemigo.esta_vivo():
            siguiente = ahora + costo_accion(COSTO_TURNO_ENEMIGO, enemigo.velocidad)
            agendar_turno(agenda, enemigo, siguiente, jugador, azar, bitacora)

    evento = Evento(
        tiempo_siguiente=tiempo,
        secuencia=agenda.nueva_secuencia(),
        actor=enemigo,
        accion=accion,
        descripcion=f"turno de {enemigo.nombre} ({enemigo.id_instancia})",
    )
    enemigo.evento_pendiente = evento   # siempre, incluido el primer turno
    agenda.agendar(evento)
    return evento


def matar_enemigo(agenda: AgendaEventos, enemigo: Enemigo) -> None:
    """Cancela el turno pendiente del enemigo sin recorrer la agenda (§4.1)."""
    enemigo.vida = 0
    if enemigo.evento_pendiente is not None:
        agenda.cancelar(enemigo.evento_pendiente)