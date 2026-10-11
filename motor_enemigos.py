"""Conecta el comportamiento de enemigos (§2.8) con la agenda de eventos (§4.1).

Cada turno, al ejecutarse, resuelve la acción y agenda su siguiente turno con
costo 100. El siguiente tiempo se calcula con el reloj del momento de ejecutar
(ahora), nunca con uno guardado al agendar.
"""

from comportamiento import resolver_turno
from costos import COSTO_TURNO_ENEMIGO, costo_accion


def agendar_turno(partida, enemigo, tiempo):
    def accion(ahora):
        resolver_turno(partida, enemigo, ahora)
        if enemigo.esta_vivo() and partida.estado == "jugando":
            agendar_turno(partida, enemigo,
                          ahora + costo_accion(COSTO_TURNO_ENEMIGO, enemigo.velocidad))

    evento = partida.programar(tiempo, accion, enemigo, f"turno de {enemigo.etiqueta()}")
    partida.cambiar(enemigo, "evento_pendiente", evento)   # siempre, incluido el primer turno
    return evento