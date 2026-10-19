from modelo.juego.combate import calcular_dano
from modelo.juego.sala import DIRECCIONES, Sala


def resolver_turno(partida, enemigo, ahora) -> None:
    if partida.jugador.sala is enemigo.sala:
        _atacar(partida, enemigo)
    elif enemigo.comportamiento == "errante":
        _errante(partida, enemigo)
    elif enemigo.comportamiento == "rastreador":
        _rastreador(partida, enemigo, ahora)


def _atacar(partida, enemigo) -> None:
    dano = calcular_dano(enemigo, partida.jugador, partida.azar)
    partida.bitacora.agregar(f"{enemigo.etiqueta()} te ataca y te hace {dano} de daño.")
    partida.danar(partida.jugador, dano)


def _salidas_abiertas(sala: Sala):
    indices = []
    for i in range(len(sala.salidas)):
        salida = sala.salidas[i]
        if salida is not None and salida.esta_abierta():
            indices.append(i)
    return indices


def _ir_a(partida, enemigo, destino) -> None:
    partida._mover_actor(enemigo, destino)
    if destino is partida.jugador.sala:
        partida.bitacora.agregar(f"{enemigo.etiqueta()} entra a la sala.")


def _errante(partida, enemigo) -> None:
    opciones = _salidas_abiertas(enemigo.sala)
    if len(opciones) == 0:
        return
    i = opciones[partida.azar.randint(0, len(opciones) - 1)]
    _ir_a(partida, enemigo, enemigo.sala.vecino(i))


def _rastreador(partida, enemigo, ahora) -> None:
    mejor = None
    for i in _salidas_abiertas(enemigo.sala):
        vecino = enemigo.sala.vecino(i)
        if not vecino.rastro_fresco(ahora):
            continue
        if (mejor is None
                or vecino.ultimo_instante_jugador > mejor.ultimo_instante_jugador
                or (vecino.ultimo_instante_jugador == mejor.ultimo_instante_jugador
                    and vecino.id < mejor.id)):
            mejor = vecino
    if mejor is not None:
        _ir_a(partida, enemigo, mejor)