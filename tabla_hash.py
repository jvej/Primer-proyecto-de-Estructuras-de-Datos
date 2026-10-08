TAMANO_INICIAL = 16
FACTOR_CARGA = 0.75   


class TablaHash:
    def __init__(self):
        self.cubetas = []
        for i in range(TAMANO_INICIAL):
            self.cubetas.append([])
        self.total = 0

    def _hash(self, clave):
        h = 0
        for letra in clave:
            h = (h * 31 + ord(letra)) % 1000000007
        return h

    def _cubeta_de(self, clave):
        return self._hash(clave) % len(self.cubetas)

    def insertar(self, clave, valor):
        cubeta = self.cubetas[self._cubeta_de(clave)]
        for par in cubeta:
            if par[0] == clave:
                par[1] = valor        
                return
        cubeta.append([clave, valor])
        self.total += 1
        if self.total > len(self.cubetas) * FACTOR_CARGA:
            self._agrandar()

    def buscar(self, clave):
        cubeta = self.cubetas[self._cubeta_de(clave)]
        for par in cubeta:
            if par[0] == clave:
                return par[1]
        return None

    def contiene(self, clave):
        cubeta = self.cubetas[self._cubeta_de(clave)]
        for par in cubeta:
            if par[0] == clave:
                return True
        return False

    def eliminar(self, clave):
        """Devuelve True si la clave existía."""
        cubeta = self.cubetas[self._cubeta_de(clave)]
        for i in range(len(cubeta)):
            if cubeta[i][0] == clave:
                cubeta.pop(i)
                self.total -= 1
                return True
        return False

    def cantidad(self):
        return self.total

    def claves(self):
        resultado = []
        for cubeta in self.cubetas:
            for par in cubeta:
                resultado.append(par[0])
        return resultado

    def _agrandar(self):
        viejas = self.cubetas
        self.cubetas = []
        for i in range(len(viejas) * 2):
            self.cubetas.append([])
        for cubeta in viejas:
            for par in cubeta:
                self.cubetas[self._cubeta_de(par[0])].append(par)

    def cubeta_mas_larga(self):
        """Sirve para medir qué tan bien reparte la función hash."""
        mayor = 0
        for cubeta in self.cubetas:
            if len(cubeta) > mayor:
                mayor = len(cubeta)
        return mayor