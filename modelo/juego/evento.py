from typing import Any, Callable


class Evento:

    def __init__(self, tiempo_siguiente: int, secuencia: int, actor: Any,
                 accion: Callable[[int], None], descripcion: str = "") -> None:
        self.tiempo_siguiente = tiempo_siguiente
        self.secuencia = secuencia
        self.actor = actor
        self.accion = accion
        self.descripcion = descripcion
        self.valido = True

    def cancelar(self) -> None:
        self.valido = False

    def ejecutar(self, ahora: int) -> None:
        if self.valido:
            self.accion(ahora)

    def __lt__(self, otro: "Evento") -> bool:
        return (self.tiempo_siguiente, self.secuencia) < (otro.tiempo_siguiente, otro.secuencia)

    def __repr__(self) -> str:
        return f"Evento(t={self.tiempo_siguiente}, seq={self.secuencia}, {self.descripcion!r})"