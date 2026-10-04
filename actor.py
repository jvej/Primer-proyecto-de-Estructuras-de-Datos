"""Actor base y enemigos (§2.8: guardián, errante, rastreador)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Actor:
    nombre: str
    vida: int
    ataque: int
    defensa: int
    velocidad: int
    sala: Optional["Sala"] = None
    evento_pendiente: Optional["Evento"] = None  # para poder cancelarlo al morir

    def esta_vivo(self) -> bool:
        return self.vida > 0

    def recibir_dano(self, dano: int) -> None:
        self.vida = max(0, self.vida - dano)


@dataclass
class Enemigo(Actor):
    comportamiento: str = "guardian"  # "guardian" | "errante" | "rastreador"
    id_instancia: str = ""  # ej. "e-201"; único dentro de la cripta (§3.3)