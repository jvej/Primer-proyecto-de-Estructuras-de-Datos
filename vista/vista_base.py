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
        """criptas: lista de {id, nombre, salas, dificultad}. Devuelve un id, None (salir)
        o orden.VER_REPETICIONES (solo si la vista muestra repeticiones)."""

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
    def mostrar_puntajes(self, registros):
        """registros: tabla de puntajes ya ordenada (puntajes.RegistroPuntaje)."""

    @abstractmethod
    def pedir_nombre(self):
        """Nombre del jugador para el log y la tabla de puntajes."""

    @abstractmethod
    def confirmar(self, pregunta):
        """Pregunta de sí/no. Devuelve True o False."""

    # ------------------------------------------------ repeticiones (§4.11)
    # No son abstractos: una vista que no muestra repeticiones (la consola) no los
    # necesita; para ella el replay sigue siendo --replay.
    def soporta_repeticion(self):
        """True si esta vista puede mostrar una repetición paso a paso."""
        return False

    def elegir_repeticion(self, entradas):
        """entradas: bitacora_partida.EntradaLog, de la más nueva a la más vieja.
        Devuelve la ruta elegida o None (volver)."""
        return None

    def paso_de_repeticion(self, partida, orden, numero, total):
        """Antes de ejecutar cada orden de la repetición. Devuelve False para detenerla."""
        return True

    def fin_de_repeticion(self, partida, lineas):
        """La repetición terminó (completa, detenida o desviada): lineas es el informe."""
        self.mostrar_aviso("\n".join(lineas))