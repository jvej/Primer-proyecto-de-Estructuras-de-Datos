"""Sala: salidas y rastro del jugador (§2.9, §4.7)."""

from dataclasses import dataclass, field
from typing import List, Optional

DIRECCIONES = ("N", "S", "E", "O")


@dataclass
class Sala:
    id: str
    # lista paralela a DIRECCIONES (no dict): None | "abierta" | "cerrada"
    salidas: List[Optional[str]] = field(default_factory=lambda: [None, None, None, None])
    actores: List["Actor"] = field(default_factory=list)
    ultimo_instante_jugador: Optional[int] = None

    def estado_salida(self, direccion: str) -> Optional[str]:
        return self.salidas[DIRECCIONES.index(direccion)]

    def fijar_salida(self, direccion: str, estado: Optional[str]) -> None:
        self.salidas[DIRECCIONES.index(direccion)] = estado

    def marcar_visita_jugador(self, tiempo_actual: int) -> None:
        self.ultimo_instante_jugador = tiempo_actual

    def rastro_fresco(self, tiempo_actual: int, limite: int = 400) -> bool:
        if self.ultimo_instante_jugador is None:
            return False
        return (tiempo_actual - self.ultimo_instante_jugador) < limite

    def num_salidas(self) -> int:
        # El costo de decisión de un rastreador debe depender de esto,
        # no del tamaño de la cripta — por eso existe este metodo.
        return sum(1 for s in self.salidas if s is not None)