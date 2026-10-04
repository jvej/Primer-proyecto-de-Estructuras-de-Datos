"""Comportamiento de enemigos (§2.8): guardián, errante, rastreador."""

import random

from actor import Actor, Enemigo
from combate import calcular_dano
from sala import DIRECCIONES, Sala


def resolver_turno_enemigo(
    enemigo: Enemigo, jugador: Actor, azar: random.Random, tiempo_actual: int
) -> str:
    """Decide y ejecuta la acción del turno de un enemigo.

    No programa el siguiente evento: el costo es 100 en los tres casos
    (atacar, mover, esperar), eso lo hace el motor (§2.8, última línea).
    Devuelve una descripción corta para la bitácora en pantalla (§4.8).
    """
    if jugador.sala is enemigo.sala:
        return _atacar(enemigo, jugador, azar)

    if enemigo.comportamiento == "guardian":
        return f"{enemigo.nombre} espera (guardián)"
    elif enemigo.comportamiento == "errante":
        return _errante(enemigo, azar)
    elif enemigo.comportamiento == "rastreador":
        return _rastreador(enemigo, tiempo_actual)
    return f"{enemigo.nombre} espera (comportamiento desconocido)"


def _atacar(enemigo: Enemigo, jugador: Actor, azar: random.Random) -> str:
    dano = calcular_dano(enemigo, jugador, azar)
    jugador.recibir_dano(dano)
    return f"{enemigo.nombre} ataca y hace {dano} de daño (vida jugador: {jugador.vida})"


def _salidas_abiertas_transitables(sala: Sala):
    return [i for i, estado in enumerate(sala.salidas) if estado == "abierta" and sala.vecino[i] is not None]


def _errante(enemigo: Enemigo, azar: random.Random) -> str:
    opciones = _salidas_abiertas_transitables(enemigo.sala)
    if not opciones:
        return f"{enemigo.nombre} espera (errante sin salidas)"
    i = opciones[azar.randint(0, len(opciones) - 1)]
    destino = enemigo.sala.vecino[i]
    enemigo.sala = destino
    return f"{enemigo.nombre} se mueve al azar hacia {destino.id} ({DIRECCIONES[i]})"


def _rastreador(enemigo: Enemigo, tiempo_actual: int) -> str:
    candidatos = []
    for i in _salidas_abiertas_transitables(enemigo.sala):
        vecino = enemigo.sala.vecino[i]
        if vecino.rastro_fresco(tiempo_actual):
            candidatos.append(vecino)

    if not candidatos:
        return f"{enemigo.nombre} espera (sin rastro fresco cerca)"

    # Rastro más reciente primero; empate exacto -> menor id de sala (§2.9).
    mejor = min(candidatos, key=lambda s: (-s.ultimo_instante_jugador, s.id))
    enemigo.sala = mejor
    return f"{enemigo.nombre} sigue el rastro hacia {mejor.id}"