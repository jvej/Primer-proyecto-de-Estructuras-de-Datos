MAX_ACCIONES = 5


class PilaAcotada:
    def __init__(self, capacidad):
        if capacidad < 1:
            raise ValueError("la capacidad debe ser al menos 1")
        self._datos = [None] * capacidad
        self._capacidad = capacidad
        self._inicio = 0        
        self._cantidad = 0

    def __len__(self):
        return self._cantidad

    def apilar(self, elemento):
        if self._cantidad < self._capacidad:
            posicion = (self._inicio + self._cantidad) % self._capacidad
            self._datos[posicion] = elemento
            self._cantidad += 1
            return None
        descartado = self._datos[self._inicio]      
        self._datos[self._inicio] = elemento
        self._inicio = (self._inicio + 1) % self._capacidad
        return descartado

    def desapilar(self):
        if self._cantidad == 0:
            raise IndexError("la pila está vacía")
        self._cantidad -= 1
        posicion = (self._inicio + self._cantidad) % self._capacidad
        elemento = self._datos[posicion]
        self._datos[posicion] = None              
        return elemento

    def elementos(self):
        resultado = []
        for i in range(self._cantidad):
            resultado.append(self._datos[(self._inicio + i) % self._capacidad])
        return resultado

    def tope(self):
        if self._cantidad == 0:
            return None
        return self._datos[(self._inicio + self._cantidad - 1) % self._capacidad]


class Registro:
    def __init__(self, max_acciones=MAX_ACCIONES) -> None:
        self._grupos = PilaAcotada(max_acciones)
        self._abierto = None  

    def abrir_grupo(self) -> None:
        self._abierto = []

    def cerrar_grupo(self) -> None:
        if self._abierto is None:
            return
        self._grupos.apilar(self._abierto)
        self._abierto = None

    def grupo_abierto(self):
        return self._abierto

    def inverso(self, deshacer) -> None:
        if self._abierto is not None:
            self._abierto.append(deshacer)

    def cambiar(self, objeto, campo: str, valor) -> None:
        anterior = getattr(objeto, campo)
        setattr(objeto, campo, valor)
        if self._abierto is not None:
            self._abierto.append(lambda: setattr(objeto, campo, anterior))

    def puede_deshacer(self) -> bool:
        return len(self._grupos) > 0

    def acciones_deshacibles(self) -> int:
        return len(self._grupos)

    def cambios_registrados(self) -> int:
        total = 0
        for grupo in self._grupos.elementos():
            total += len(grupo)
        return total

    def deshacer_ultimo(self) -> None:
        grupo = self._grupos.desapilar()
        for i in range(len(grupo) - 1, -1, -1):  
            grupo[i]()