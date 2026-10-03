"""Sala: salidas y rastro del jugador (§2.1, §2.9, §4.7)."""

from dataclasses import dataclass, field
from typing import List, Optional

DIRECCIONES = ("N", "S", "E", "O")
OPUESTA = {"N": "S", "S": "N", "E": "O", "O": "E"}


@dataclass
class Sala:
    id: int
    # listas paralelas a DIRECCIONES (no dict): salidas[i] es el estado
    # ("abierta" | "cerrada" | None) y vecino[i] la sala conectada en esa dirección.
    salidas: List[Optional[str]] = field(default_factory=lambda: [None, None, None, None])
    vecino: List[Optional["Sala"]] = field(default_factory=lambda: [None, None, None, None])
    actores: List["Actor"] = field(default_factory=list)
    ultimo_instante_jugador: Optional[int] = None

    def estado_salida(self, direccion: str) -> Optional[str]:
        return self.salidas[DIRECCIONES.index(direccion)]

    def fijar_salida(self, direccion: str, estado: Optional[str]) -> None:
        self.salidas[DIRECCIONES.index(direccion)] = estado

    def conectar(self, direccion: str, otra: "Sala", estado: str = "abierta") -> None:
        """Conecta esta sala con otra en ambos sentidos (§2.1: cada salida conecta exactamente dos salas)."""
        i = DIRECCIONES.index(direccion)
        self.salidas[i] = estado
        self.vecino[i] = otra
        j = DIRECCIONES.index(OPUESTA[direccion])
        otra.salidas[j] = estado
        otra.vecino[j] = self

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