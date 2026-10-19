def calcular_dano(atacante, defensor, rng) -> int:
    """rng: el azar del modelo (cualquier objeto con randint, ver azar.py)."""
    return max(1, atacante.ataque_efectivo() + rng.randint(0, 4) - defensor.defensa_efectivo())