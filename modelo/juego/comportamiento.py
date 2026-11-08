from modelo.juego.combate import calcular_dano
from modelo.juego.costos import COSTO_ATACAR, COSTO_ESPERAR
from modelo.juego.sala import DIRECCIONES, Sala


def resolver_turno(partida, enemigo, ahora) -> int:
    if partida.jugador.sala is enemigo.sala:
        _atacar(partida, enemigo)
        return COSTO_ATACAR
    elif enemigo.comportamiento == "errante":
        return _errante(partida, enemigo)
    elif enemigo.comportamiento == "rastreador":
        return _rastreador(partida, enemigo, ahora)
    return COSTO_ESPERAR


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


def _errante(partida, enemigo) -> int:
    opciones = _salidas_abiertas(enemigo.sala)
    if len(opciones) == 0:
        return COSTO_ESPERAR
    i = opciones[partida.azar.randint(0, len(opciones) - 1)]
    salida = enemigo.sala.salidas[i]
    _ir_a(partida, enemigo, enemigo.sala.vecino(i))
    return salida.costo


def _rastreador(partida, enemigo, ahora) -> int:
    mejor = None
    indice_mejor = None
    for i in _salidas_abiertas(enemigo.sala):
        vecino = enemigo.sala.vecino(i)
        if not vecino.rastro_fresco(ahora):
            continue
        if (mejor is None
                or vecino.ultimo_instante_jugador > mejor.ultimo_instante_jugador
                or (vecino.ultimo_instante_jugador == mejor.ultimo_instante_jugador
                    and vecino.id < mejor.id)):
            mejor = vecino
            indice_mejor = i
    if mejor is not None:
        salida = enemigo.sala.salidas[indice_mejor]
        _ir_a(partida, enemigo, mejor)
        return salida.costo
    return COSTO_ESPERAR
