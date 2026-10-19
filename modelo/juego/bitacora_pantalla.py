CAPACIDAD_DEFECTO = 20


class BitacoraPantalla:
    def __init__(self, capacidad=CAPACIDAD_DEFECTO):
        if capacidad < 1:
            raise ValueError("la capacidad debe ser al menos 1")
        self.capacidad = capacidad
        self._mensajes = [None] * capacidad
        self._inicio = 0           
        self._cantidad = 0
        self.total_historico = 0  

    def agregar(self, mensaje):
        if self._cantidad < self.capacidad:
            posicion = (self._inicio + self._cantidad) % self.capacidad
            self._cantidad += 1
        else:                                  
            posicion = self._inicio
            self._inicio = (self._inicio + 1) % self.capacidad
        self._mensajes[posicion] = mensaje
        self.total_historico += 1

    def ultimos(self):
        resultado = []
        for i in range(self._cantidad):
            resultado.append(self._mensajes[(self._inicio + i) % self.capacidad])
        return resultado

    def __len__(self):
        return self._cantidad