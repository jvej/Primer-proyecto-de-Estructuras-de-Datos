from modelo.juego.comportamiento import resolver_turno
from modelo.juego.costos import COSTO_TURNO_ENEMIGO, costo_accion


def agendar_turno(partida, enemigo, tiempo):
    def accion(ahora):
        resolver_turno(partida, enemigo, ahora)
        if enemigo.esta_vivo() and partida.estado == "jugando":
            agendar_turno(partida, enemigo,
                          ahora + costo_accion(COSTO_TURNO_ENEMIGO, enemigo.velocidad))

    evento = partida.programar(tiempo, accion, enemigo, f"turno de {enemigo.etiqueta()}")
    partida.cambiar(enemigo, "evento_pendiente", evento)  
    return evento