"""Registro de cambios invertibles (§2.11, §4.6).

No guarda copias del estado: guarda, por cada cambio, la función que lo deshace.
Los cambios de una acción del jugador (y de lo que ocurre hasta su siguiente
decisión) forman un grupo. Se conservan los últimos 5 grupos.
"""

MAX_ACCIONES = 5


class Registro:
    def __init__(self) -> None:
        self._grupos = []       # hasta MAX_ACCIONES grupos; cada grupo es una lista de funciones
        self._abierto = None    # grupo en construcción (None = no hay acción en curso)

    def abrir_grupo(self) -> None:
        self._abierto = []

    def cerrar_grupo(self) -> None:
        if self._abierto is None:
            return
        self._grupos.append(self._abierto)
        self._abierto = None
        if len(self._grupos) > MAX_ACCIONES:
            del self._grupos[0]          # se descarta lo más antiguo

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

    def deshacer_ultimo(self) -> None:
        grupo = self._grupos.pop()
        for i in range(len(grupo) - 1, -1, -1):    # en orden inverso al que ocurrió
            grupo[i]()