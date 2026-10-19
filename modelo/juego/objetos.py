class Objeto:
    def __init__(self, ficha) -> None:
        self.id = ficha["id"]
        self.clase = ficha.get("clase", "")  
        self.nombre = ficha.get("nombre", self.id)
        self.peso = ficha.get("peso", 0)
        self.valor = ficha.get("valor", 0)
        self.ataque_bonus = ficha.get("ataque_bonus", 0)
        self.defensa_bonus = ficha.get("defensa_bonus", 0)
        self.cura = ficha.get("cura", 0)
        self.modificador_velocidad = ficha.get("modificador_velocidad", 0)
        self.duracion = ficha.get("duracion", 0)
        self.abre = ficha.get("abre")
        self.usos = ficha.get("usos", 1)     

    def es_pergamino(self) -> bool:
        return self.clase == "pergamino_retroceso"

    def __repr__(self) -> str:
        return f"Objeto({self.nombre!r})"


class Trampa:
    def __init__(self, instancia, ficha) -> None:
        self.instancia = instancia
        self.id = ficha["id"]
        self.nombre = ficha.get("nombre", self.id)
        self.dano = ficha.get("daño", 0)
        self.veneno = ficha.get("veneno", 0)     
        self.rearme = ficha.get("rearme", 300)     
        self.armada = True

    def __repr__(self) -> str:
        return f"Trampa({self.nombre!r}, armada={self.armada})"