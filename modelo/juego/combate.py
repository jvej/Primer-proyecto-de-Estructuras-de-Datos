"""Fórmula de daño (§2.6): max(1, ataque + randint(0,4) - defensa).

Se usan el ataque y la defensa EFECTIVOS: el jugador suma el ataque_bonus de su arma
y el defensa_bonus de su armadura equipadas (§2.7). Para un enemigo son sus valores
del catálogo (Actor.ataque_efectivo() devuelve el ataque base).
"""


def calcular_dano(atacante, defensor, rng) -> int:
    """rng: el azar del modelo (cualquier objeto con randint, ver azar.py)."""
    return max(1, atacante.ataque_efectivo() + rng.randint(0, 4) - defensor.defensa_efectivo())