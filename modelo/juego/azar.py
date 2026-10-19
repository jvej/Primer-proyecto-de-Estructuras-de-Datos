import random
class AzarReversible:
    def __init__(self, semilla, registro=None):
        self._rng = random.Random(semilla)
        self._registro = registro
        self._grupo_visto = None   

    def randint(self, a, b):
        self._antes_de_usar()
        return self._rng.randint(a, b)

    def _antes_de_usar(self):
        if self._registro is None:
            return
        grupo = self._registro.grupo_abierto()
        if grupo is None or grupo is self._grupo_visto:
            return
        self._grupo_visto = grupo
        estado = self._rng.getstate()
        self._registro.inverso(lambda: self._rng.setstate(estado))