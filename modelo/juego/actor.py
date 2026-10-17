"""Actores: jugador y enemigos (§2.2, §2.8)."""

from typing import Optional


class Actor:
    def __init__(self, nombre: str, vida: int, ataque: int, defensa: int, velocidad: int,
                 sala=None, vida_max: Optional[int] = None) -> None:
        self.nombre = nombre
        self.vida_max = vida if vida_max is None else vida_max
        self.vida = vida                # puede ser menor que vida_max (§2.2)
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.velocidad_base = velocidad
        self.sala = None
        self.evento_pendiente = None    # su próximo turno: sirve para cancelarlo o reprogramarlo
        self.evento_veneno = None       # próximo pulso de veneno, si está envenenado
        self.evento_regeneracion = None
        if sala is not None:
            self.mover_a(sala)

    @property
    def tiempo_siguiente(self) -> Optional[int]:
        """Se lee del evento pendiente para no guardar el mismo dato en dos lugares."""
        if self.evento_pendiente is None or not self.evento_pendiente.valido:
            return None
        return self.evento_pendiente.tiempo_siguiente

    def ataque_efectivo(self) -> int:
        return self.ataque

    def defensa_efectivo(self) -> int:
        return self.defensa

    def esta_vivo(self) -> bool:
        return self.vida > 0

    def etiqueta(self) -> str:
        return self.nombre

    def mover_a(self, destino) -> None:
        """Mueve al actor sin registrar (solo preparación inicial y pruebas).
        Durante la partida se usa Partida._mover_actor, que sí registra el cambio."""
        if self.sala is not None:
            self.sala.actores.remove(self)
        self.sala = destino
        destino.actores.append(self)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.nombre!r}, vida={self.vida}/{self.vida_max})"


class Jugador(Actor):
    def __init__(self, vida_max: int, ataque: int, defensa: int, velocidad: int) -> None:
        super().__init__("Jugador", vida_max, ataque, defensa, velocidad, None, vida_max)
        self.arma = None
        self.armadura = None
        self.antorcha_encendida = False
        self.abrio_salida = False       # abrió la puerta de salida con su llave (§2.12)

    def ataque_efectivo(self) -> int:
        return self.ataque + (self.arma.ataque_bonus if self.arma is not None else 0)

    def defensa_efectivo(self) -> int:
        return self.defensa + (self.armadura.defensa_bonus if self.armadura is not None else 0)


class Enemigo(Actor):
    def __init__(self, nombre: str, vida: int, ataque: int, defensa: int, velocidad: int,
                 comportamiento: str = "guardian", id_instancia: str = "",
                 sala=None, vida_max: Optional[int] = None,
                 suelta=None, regeneracion: int = 0, tipo: str = "") -> None:
        super().__init__(nombre, vida, ataque, defensa, velocidad, sala, vida_max)
        self.comportamiento = comportamiento    # "guardian" | "errante" | "rastreador"
        self.id_instancia = id_instancia        # ej. "e-201"; único dentro de la cripta (§3.3)
        self.activo = False                     # se activa al entrar el jugador a su sala (§2.4)
        self.suelta = [] if suelta is None else suelta   # ids de objetos que deja al morir
        self.regeneracion = regeneracion        # vida que recupera cada 200 unidades (0 = ninguna)
        self.tipo = tipo                        # id de su ficha de catálogo

    def etiqueta(self) -> str:
        if self.id_instancia == "":
            return self.nombre
        return f"{self.nombre} [{self.id_instancia}]"