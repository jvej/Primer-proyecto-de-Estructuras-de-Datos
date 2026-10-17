"""Registro de cambios invertibles (§2.11, §4.6).

No guarda copias del estado: guarda, por cada cambio, la función que lo deshace.
Los cambios de una acción del jugador (y de lo que ocurre hasta su siguiente
decisión) forman un grupo.

Estructuras:
  - Un grupo es una PILA de inversos (lista usada solo con append): al deshacer se
    recorren del último al primero, en orden inverso al que ocurrieron.
  - Los grupos se guardan en una PILA ACOTADA sobre un arreglo circular de
    MAX_ACCIONES casillas. Apilar con la pila llena sobrescribe el grupo más
    antiguo (se descarta lo más antiguo, §4.6) en O(1), sin desplazar elementos.
    Desapilar saca el más reciente, también en O(1).
"""

MAX_ACCIONES = 5


class PilaAcotada:
    """Pila de capacidad fija: al llenarse, apilar descarta el elemento más antiguo."""

    def __init__(self, capacidad):
        if capacidad < 1:
            raise ValueError("la capacidad debe ser al menos 1")
        self._datos = [None] * capacidad
        self._capacidad = capacidad
        self._inicio = 0        # posición del elemento más antiguo
        self._cantidad = 0

    def __len__(self):
        return self._cantidad

    def apilar(self, elemento):
        """Devuelve el elemento descartado (el más antiguo) o None si no hubo descarte."""
        if self._cantidad < self._capacidad:
            posicion = (self._inicio + self._cantidad) % self._capacidad
            self._datos[posicion] = elemento
            self._cantidad += 1
            return None
        descartado = self._datos[self._inicio]       # llena: el más antiguo se pierde
        self._datos[self._inicio] = elemento
        self._inicio = (self._inicio + 1) % self._capacidad
        return descartado

    def desapilar(self):
        if self._cantidad == 0:
            raise IndexError("la pila está vacía")
        self._cantidad -= 1
        posicion = (self._inicio + self._cantidad) % self._capacidad
        elemento = self._datos[posicion]
        self._datos[posicion] = None                  # suelta la referencia
        return elemento

    def elementos(self):
        """Lista nueva del más antiguo al más reciente."""
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
        self._abierto = None    # grupo en construcción (None = no hay acción en curso)

    def abrir_grupo(self) -> None:
        self._abierto = []

    def cerrar_grupo(self) -> None:
        if self._abierto is None:
            return
        self._grupos.apilar(self._abierto)
        self._abierto = None

    def grupo_abierto(self):
        """El grupo en construcción (para saber si ya se anotó algo en él) o None."""
        return self._abierto

    def inverso(self, deshacer) -> None:
        """Anota cómo deshacer un cambio ya hecho. Fuera de un grupo no hace nada."""
        if self._abierto is not None:
            self._abierto.append(deshacer)

    def cambiar(self, objeto, campo: str, valor) -> None:
        """Único punto por donde cambian los atributos del estado del juego."""
        anterior = getattr(objeto, campo)
        setattr(objeto, campo, valor)
        if self._abierto is not None:
            self._abierto.append(lambda: setattr(objeto, campo, anterior))

    def puede_deshacer(self) -> bool:
        return len(self._grupos) > 0

    def acciones_deshacibles(self) -> int:
        return len(self._grupos)

    def cambios_registrados(self) -> int:
        """Total de inversos guardados en el historial (para el bench)."""
        total = 0
        for grupo in self._grupos.elementos():
            total += len(grupo)
        return total

    def deshacer_ultimo(self) -> None:
        grupo = self._grupos.desapilar()
        for i in range(len(grupo) - 1, -1, -1):    # en orden inverso al que ocurrió
            grupo[i]()