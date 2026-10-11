"""Activación de enemigos al entrar el jugador a una sala (§2.4).

Varios enemigos activados en el mismo instante se programan en orden
ascendente de id_instancia, para que los números de secuencia salgan
deterministas sin depender del orden de la lista de contenido.
El orden usa ordenar() de ordenamiento.py (§4.9 prohíbe sorted()).
"""

import random
from typing import List

from actor import Actor, Enemigo
from agenda_eventos import AgendaEventos
from costos import COSTO_ACTIVACION, costo_accion
from motor_enemigos import agendar_turno
from ordenamiento import ordenar


def activar_enemigos(
    agenda: AgendaEventos,
    enemigos: List[Enemigo],
    reloj_actual: int,
    jugador: Actor,
    azar: random.Random,
    bitacora: List[str],
) -> None:
    for enemigo in ordenar(enemigos, clave=lambda e: e.id_instancia):
        tiempo = reloj_actual + costo_accion(COSTO_ACTIVACION, enemigo.velocidad)
        agendar_turno(agenda, enemigo, tiempo, jugador, azar, bitacora)