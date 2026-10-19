import os

from controlador.reproductor import preparar_reproduccion
from modelo.datos.bitacora_partida import MAX_REPETICIONES, listar_logs

class ServicioRepeticiones:
    def __init__(self, aplicacion, crear_fuente, carpeta, cache_size):
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
        self.aplicacion.detener_red()        
        fuente, presupuesto = self.crear_fuente()
        return preparar_reproduccion(ruta, fuente, presupuesto, self.carpeta, self.cache_size)