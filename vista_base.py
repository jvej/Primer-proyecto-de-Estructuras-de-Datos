"""Vista: lo que el Controlador necesita de cualquier interfaz (§6).

La consola (vista_consola.py) la implementa hoy; una interfaz gráfica la
implementaría mañana sin cambiar el Controlador ni el Modelo.

Reglas de la Vista:
  - Puede LEER el modelo (partida, inventario, bitácora) para mostrarlo.
  - NO lo modifica: todo lo que el usuario quiera hacer lo devuelve como Orden.
  - NO conoce al Controlador.
"""

from abc import ABC, abstractmethod


class Vista(ABC):
    @abstractmethod
    def elegir_cripta(self, criptas):
        """criptas: lista de {id, nombre, salas, dificultad}. Devuelve un id o None (salir)."""

    @abstractmethod
    def pedir_orden(self, partida):
        """Pide al usuario qué hacer y devuelve una Orden. Si se cierra la entrada, Orden(SALIR)."""

    @abstractmethod
    def mostrar_partida(self, partida):
        """Sala, salidas, enemigos, suelo, vida, efectos y los últimos 20 mensajes (§10.2)."""

    @abstractmethod
    def mostrar_inventario(self, partida):
        """Inventario en su orden real, con el cursor y lo equipado."""

    @abstractmethod
    def mostrar_vista_ordenada(self, criterio, descendente, pares):
        """pares: [(posicion_real, objeto)] ya ordenados. No cambia el orden real."""

    @abstractmethod
    def mostrar_aviso(self, texto):
        """Un mensaje de la aplicación que no es del juego (errores de carga, guardado...)."""

    @abstractmethod
    def mostrar_ayuda(self):
        """Lista de comandos."""

    @abstractmethod
    def mostrar_fin(self, partida):
        """Pantalla final: victoria o derrota con el resumen."""

    @abstractmethod
    def confirmar(self, pregunta):
        """Pregunta de sí/no. Devuelve True o False."""