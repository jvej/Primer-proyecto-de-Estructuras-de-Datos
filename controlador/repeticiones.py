"""Repeticiones en la ventana (§4.11): la lista de las últimas partidas y su preparación.

Se le entrega al Controlador ya armado (desde main.py), igual que la persistencia y los
puntajes: así el Controlador no sabe de archivos, de red ni de dónde están los logs.

  listar()        -> las últimas partidas (máx. 20), de la más nueva a la más vieja
  ultima()        -> la ruta del log de la partida que acaba de terminar, o None
  preparar(ruta)  -> (Reproduccion o None, ResultadoReplay)

Cada repetición usa una fuente de datos y un presupuesto NUEVOS (crear_fuente): no gasta
las solicitudes de la partida del jugador. No escribe log ni puntajes.
"""

import os

from controlador.reproductor import preparar_reproduccion
from modelo.datos.bitacora_partida import MAX_REPETICIONES, listar_logs


class ServicioRepeticiones:
    def __init__(self, aplicacion, crear_fuente, carpeta, cache_size):
        """crear_fuente() -> (fuente, presupuesto): la misma fábrica que usa main.py."""
        self.aplicacion = aplicacion
        self.crear_fuente = crear_fuente
        self.carpeta = carpeta
        self.cache_size = cache_size

    def listar(self):
        return listar_logs(os.path.join(self.carpeta, "partidas"), MAX_REPETICIONES)

    def ultima(self):
        ruta = self.aplicacion.ultimo_log
        if ruta is None or not os.path.exists(ruta):
            return None
        return ruta

    def preparar(self, ruta):
        self.aplicacion.detener_red()          # la partida anterior ya no pide nada a la red
        fuente, presupuesto = self.crear_fuente()
        return preparar_reproduccion(ruta, fuente, presupuesto, self.carpeta, self.cache_size)