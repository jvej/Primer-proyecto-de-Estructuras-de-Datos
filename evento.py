"""Representa un evento programado en la agenda de eventos."""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Evento:
    """Un evento futuro: se ejecuta en tiempo_siguiente, desempatado por secuencia."""

    tiempo_siguiente: int
    secuencia: int
    actor: Any
    accion: Callable[[], None]
    descripcion: str = ""
    valido: bool = True

    def cancelar(self) -> None:
        """Invalida el evento sin tener que buscarlo ni sacarlo del heap todavía."""
        self.valido = False

    def ejecutar(self) -> None:
        if self.valido:
            self.accion()

    def __lt__(self, otro: "Evento") -> bool:
        return (self.tiempo_siguiente, self.secuencia) < (otro.tiempo_siguiente, otro.secuencia)