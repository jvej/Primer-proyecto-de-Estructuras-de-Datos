"""Actor base y enemigos (§2.2, §2.8: guardián, errante, rastreador)."""

from typing import Optional


class Actor:
    def __init__(self, nombre: str, vida: int, ataque: int, defensa: int, velocidad: int,
                 sala=None, vida_max: Optional[int] = None) -> None:
        self.nombre = nombre
        self.vida_max = vida if vida_max is None else vida_max
        self.vida = vida            # puede ser menor que vida_max (§2.2)
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.sala = None
        self.evento_pendiente = None  # su próximo turno; sirve para cancelarlo o reprogramarlo
        if sala is not None:
            self.mover_a(sala)

    @property
    def tiempo_siguiente(self) -> Optional[int]:
        """Se lee del evento pendiente para no guardar el mismo dato en dos lugares."""
        if self.evento_pendiente is None or not self.evento_pendiente.valido:
            return None
        return self.evento_pendiente.tiempo_siguiente

    def esta_vivo(self) -> bool:
        return self.vida > 0

    def recibir_dano(self, dano: int) -> None:
        self.vida = max(0, self.vida - dano)

    def curar(self, cantidad: int) -> None:
        """Curación y regeneración nunca superan vida_max (Apéndice B)."""
        self.vida = min(self.vida_max, self.vida + cantidad)

    def mover_a(self, destino) -> None:
        """Único lugar donde cambia la sala de un actor (mantiene sala.actores al día)."""
        if self.sala is not None:
            self.sala.actores.remove(self)
        self.sala = destino
        destino.actores.append(self)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.nombre!r}, vida={self.vida}/{self.vida_max})"


class Enemigo(Actor):
    def __init__(self, nombre: str, vida: int, ataque: int, defensa: int, velocidad: int,
                 comportamiento: str = "guardian", id_instancia: str = "",
                 sala=None, vida_max: Optional[int] = None) -> None:
        super().__init__(nombre, vida, ataque, defensa, velocidad, sala, vida_max)
        self.comportamiento = comportamiento  # "guardian" | "errante" | "rastreador"
        self.id_instancia = id_instancia      # ej. "e-201"; único dentro de la cripta (§3.3)