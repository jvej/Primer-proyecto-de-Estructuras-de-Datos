"""Comportamiento de enemigos (§2.8): guardián, errante, rastreador."""

import random

from actor import Actor, Enemigo
from combate import calcular_dano
from sala import DIRECCIONES, Sala


def resolver_turno_enemigo(
    enemigo: Enemigo, jugador: Actor, azar: random.Random, ahora: int
) -> str:
    """Decide y ejecuta la acción del turno de un enemigo.

    No programa el siguiente evento: el costo es 100 en los tres casos
    (atacar, mover, esperar), eso lo hace motor_enemigos (§2.8).
    Devuelve una descripción corta para la bitácora en pantalla (§4.8).
    """
    if jugador.sala is enemigo.sala:
        return _atacar(enemigo, jugador, azar)

    if enemigo.comportamiento == "guardian":
        return f"{enemigo.nombre} espera (guardián)"
    elif enemigo.comportamiento == "errante":
        return _errante(enemigo, azar)
    elif enemigo.comportamiento == "rastreador":
        return _rastreador(enemigo, ahora)
    return f"{enemigo.nombre} espera (comportamiento desconocido)"


def _atacar(enemigo: Enemigo, jugador: Actor, azar: random.Random) -> str:
    dano = calcular_dano(enemigo, jugador, azar)
    jugador.recibir_dano(dano)
    return f"{enemigo.nombre} ataca y hace {dano} de daño (vida jugador: {jugador.vida})"


def _salidas_abiertas(sala: Sala):
    """Índices de las salidas por las que un enemigo puede pasar (los enemigos no abren puertas)."""
    indices = []
    for i in range(len(sala.salidas)):
        salida = sala.salidas[i]
        if salida is not None and salida.esta_abierta():
            indices.append(i)
    return indices


def _errante(enemigo: Enemigo, azar: random.Random) -> str:
    opciones = _salidas_abiertas(enemigo.sala)
    if not opciones:
        return f"{enemigo.nombre} espera (errante sin salidas)"
    i = opciones[azar.randint(0, len(opciones) - 1)]
    destino = enemigo.sala.vecino(i)
    enemigo.mover_a(destino)
    return f"{enemigo.nombre} se mueve al azar hacia {destino.id} ({DIRECCIONES[i]})"


def _rastreador(enemigo: Enemigo, ahora: int) -> str:
    """Examina solo las salas vecinas: costo proporcional a las salidas (§4.7)."""
    mejor = None
    for i in _salidas_abiertas(enemigo.sala):
        vecino = enemigo.sala.vecino(i)
        if not vecino.rastro_fresco(ahora):
            continue
        # Rastro más reciente; en empate exacto, menor id de sala (§2.9).
        if (mejor is None
                or vecino.ultimo_instante_jugador > mejor.ultimo_instante_jugador
                or (vecino.ultimo_instante_jugador == mejor.ultimo_instante_jugador
                    and vecino.id < mejor.id)):
            mejor = vecino

    if mejor is None:
        return f"{enemigo.nombre} espera (sin rastro fresco cerca)"
    enemigo.mover_a(mejor)
    return f"{enemigo.nombre} sigue el rastro hacia {mejor.id}"