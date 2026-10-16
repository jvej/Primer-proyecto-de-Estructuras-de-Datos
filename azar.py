"""Azar reproducible y reversible del modelo (§2.6, §2.11).

Envuelve una instancia propia random.Random(semilla) (nunca el generador global).

Reversible: la PRIMERA vez que se usa dentro de un grupo del registro de retroceso,
guarda el estado del generador y anota cómo devolverlo. Así un pergamino deshace
también las tiradas: repetir la misma acción después de retroceder da el mismo
resultado (no sirve para "volver a tirar los dados").

No es una copia del estado del juego: es solo el estado del generador, y solo en
los grupos que realmente lo usan (esperar o moverse sin combate no lo guardan).

"""
import random
class AzarReversible:
    def __init__(self, semilla, registro=None):
        self._rng = random.Random(semilla)
        self._registro = registro
        self._grupo_visto = None    # último grupo en el que ya se guardó el estado

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