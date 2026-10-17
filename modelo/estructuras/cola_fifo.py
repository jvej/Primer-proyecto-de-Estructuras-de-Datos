"""Cola FIFO propia sobre lista (índice de cabeza, sin pop(0))."""


class ColaFIFO:
    def __init__(self):
        self._datos = []
        self._cabeza = 0

    def agregar(self, elemento):
        self._datos.append(elemento)

    def sacar(self):
        if self._cabeza >= len(self._datos):
            raise IndexError("cola vacía")
        elemento = self._datos[self._cabeza]
        self._datos[self._cabeza] = None
        self._cabeza += 1
        if self._cabeza > 32 and self._cabeza * 2 > len(self._datos):
            self._datos = self._datos[self._cabeza:]     # compacta de vez en cuando
            self._cabeza = 0
        return elemento

    def vacia(self):
        return self._cabeza >= len(self._datos)

    def __len__(self):
        return len(self._datos) - self._cabeza