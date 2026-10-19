from typing import List, Optional

DIRECCIONES = ("N", "S", "E", "O")
OPUESTAS = (1, 0, 3, 2)  
LIMITE_RASTRO = 400      


class Salida:
    def __init__(self, sala_a: "Sala", sala_b: "Sala", estado: str = "abierta",
                 llave: Optional[str] = None, cierre_automatico: Optional[int] = None) -> None:
        self.sala_a = sala_a
        self.sala_b = sala_b
        self.estado = estado                       
        self.llave = llave                          
        self.cierre_automatico = cierre_automatico  
        self.evento_cierre = None                  
    def esta_abierta(self) -> bool:
        return self.estado == "abierta"

    def otro_lado(self, sala: "Sala") -> "Sala":
        return self.sala_b if sala is self.sala_a else self.sala_a


class Sala:
    def __init__(self, id: int, nombre: str = "") -> None:
        self.id = id
        self.nombre = nombre
        self.salidas: List[Optional[Salida]] = [None, None, None, None]
        self.actores: list = []     
        self.objetos: list = []   
        self.trampas: list = []
        self.ultimo_instante_jugador: Optional[int] = None
        self.incorporada = False     

    def conectar(self, direccion: str, otra: "Sala", estado: str = "abierta",
                 llave: Optional[str] = None, cierre_automatico: Optional[int] = None) -> Salida:
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
        if self.ultimo_instante_jugador is None:
            return False
        return (tiempo_actual - self.ultimo_instante_jugador) < limite

    def num_salidas(self) -> int:
        total = 0
        for salida in self.salidas:
            if salida is not None:
                total += 1
        return total

    def __repr__(self) -> str:
        return f"Sala({self.id})"