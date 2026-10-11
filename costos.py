"""Costo de acción según §2.3: max(1, costo_base * 100 // velocidad)."""

COSTO_MOVER = 100
COSTO_ATACAR = 100
COSTO_ESPERAR = 100
COSTO_USAR_EQUIPAR = 50
COSTO_RECOGER_SOLTAR = 25
COSTO_ABRIR_PUERTA = 50
COSTO_ACTIVACION = 100       # §2.4: primera acción de un enemigo recién activado
COSTO_TURNO_ENEMIGO = 100    # §2.8: atacar, moverse o esperar cuestan lo mismo


def costo_accion(costo_base: int, velocidad: int) -> int:
    return max(1, costo_base * 100 // velocidad)