"""Sala y Salida: el mapa de la cripta (§2.1) y el rastro del jugador (§2.9, §4.7)."""

from typing import List, Optional

DIRECCIONES = ("N", "S", "E", "O")
OPUESTAS = (1, 0, 3, 2)   # OPUESTAS[i] = índice de la dirección contraria a DIRECCIONES[i]
LIMITE_RASTRO = 400       # §2.9: un rastro de 400 unidades o más ya no sirve


class Salida:
    """Una puerta entre dos salas. Ambas salas comparten este mismo objeto,
    así abrirla o cerrarla desde un lado la cambia para los dos."""

    def __init__(self, sala_a: "Sala", sala_b: "Sala", estado: str = "abierta",
                 llave: Optional[str] = None, cierre_automatico: Optional[int] = None) -> None:
        self.sala_a = sala_a
        self.sala_b = sala_b
        self.estado = estado                        # "abierta" | "cerrada"
        self.llave = llave                          # id de la llave que la abre, o None
        self.cierre_automatico = cierre_automatico  # unidades tras abrirse, o None
        self.evento_cierre = None                   # cierre programado, si lo hay (§2.10)

    def esta_abierta(self) -> bool:
        return self.estado == "abierta"

    def otro_lado(self, sala: "Sala") -> "Sala":
        return self.sala_b if sala is self.sala_a else self.sala_a


class Sala:
    def __init__(self, id: int, nombre: str = "") -> None:
        self.id = id
        self.nombre = nombre
        # lista paralela a DIRECCIONES (sin dict): Salida o None
        self.salidas: List[Optional[Salida]] = [None, None, None, None]
        self.actores: list = []      # jugador y enemigos presentes (dormidos o activos)
        self.objetos: list = []      # objetos en el suelo
        self.trampas: list = []
        self.ultimo_instante_jugador: Optional[int] = None
        self.incorporada = False     # ya se creó su contenido en el modelo

    def conectar(self, direccion: str, otra: "Sala", estado: str = "abierta",
                 llave: Optional[str] = None, cierre_automatico: Optional[int] = None) -> Salida:
        """Crea UNA salida y la pone en ambas salas (§2.1: conecta exactamente dos)."""
        i = DIRECCIONES.index(direccion)
        salida = Salida(self, otra, estado, llave, cierre_automatico)
        self.salidas[i] = salida
        otra.salidas[OPUESTAS[i]] = salida
        return salida

    def vecino(self, i: int) -> Optional["Sala"]:
        salida = self.salidas[i]
        if salida is None:
            return None
        return salida.otro_lado(self)

    def marcar_visita_jugador(self, tiempo_actual: int) -> None:
        self.ultimo_instante_jugador = tiempo_actual

    def rastro_fresco(self, tiempo_actual: int, limite: int = LIMITE_RASTRO) -> bool:
        """La caducidad se detecta al consultar: O(1), sin eventos ni limpiezas (§4.7)."""
        if self.ultimo_instante_jugador is None:
            return False
        return (tiempo_actual - self.ultimo_instante_jugador) < limite

    def num_salidas(self) -> int:
        # El costo de decisión de un rastreador depende de esto, no del tamaño de la cripta.
        total = 0
        for salida in self.salidas:
            if salida is not None:
                total += 1
        return total

    def __repr__(self) -> str:
        return f"Sala({self.id})"