"""Fórmula de daño (§2.6): max(1, ataque + randint(0,4) - defensa)."""

import random


def calcular_dano(atacante, defensor, rng: random.Random) -> int:
    return max(1, atacante.ataque + rng.randint(0, 4) - defensor.defensa)