import os
import time

from modelo.datos.almacen_cripta import AlmacenCripta
from modelo.datos.almacen_fichas import AlmacenFichas
from modelo.datos.almacen_local_cache import AlmacenLocalCache
from modelo.juego.bitacora_pantalla import BitacoraPantalla
from modelo.datos.bitacora_partida import (MAX_REPETICIONES, BitacoraPartida, EncabezadoLog,
                                           podar_logs)
from controlador.controlador import Controlador
from modelo.datos.ejecutor_red import EjecutorRed
from modelo.juego.errores import ErrorCripta
from modelo.datos.esqueleto import descargar_esqueleto
from modelo.juego.inventario import Inventario
from modelo.estructuras.ordenamiento import ordenar
from modelo.juego.partida import Partida
from modelo.datos.precarga_contenido import PrecargaContenido
from modelo.datos.puntajes import TablaPuntajes
from modelo.datos.resolutor_catalogo import ResolutorCatalogo

CARPETA_DEFECTO = "datos_cripta"
CACHE_DEFECTO = 25
MENSAJES_EN_PANTALLA = 20     
RESERVA_PRECARGA = 2       


def nombre_seguro(texto):
    resultado = ""
    for caracter in str(texto):
        if caracter.isalnum() or caracter in "-_.":
            resultado += caracter
        else:
            resultado += "_"
    return resultado or "_"


def fecha_actual():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def semilla_nueva():
    return int(time.time() * 1000) % 2147483647


class ErrorVersion(ErrorCripta):
    """Los datos de la cripta o del catálogo ya no son los de la partida a reconstruir."""


class Aplicacion:
    def __init__(self, fuente, presupuesto, carpeta=CARPETA_DEFECTO, cache_size=CACHE_DEFECTO,
                 semilla=None, nombre="Jugador", registrar_log=True, registrar_puntajes=True):
        self.fuente = fuente
        self.presupuesto = presupuesto
        self.carpeta = carpeta
        self.cache_size = cache_size
        self.semilla_fija = semilla
        self.nombre = nombre
        self.registrar_log = registrar_log
        self.registrar_puntajes = registrar_puntajes
        self.puntajes = TablaPuntajes(os.path.join(carpeta, "puntajes.txt"))
        self.ruta_guardado = os.path.join(carpeta, "guardados", "partida.bin")

        self.version_catalogo = None
        self.almacen_catalogo = None
        self.local = None           
        self.partida = None
        self.ejecutor = None
        self.precarga = None
        self.log = None
        self.ultimo_log = None       
        self.ordenes = []            
        self.partidas_creadas = 0
        self._presupuesto_listo = False  
        os.makedirs(carpeta, exist_ok=True)

    def listar_criptas(self):
        if self.partidas_creadas > 0 and not self._presupuesto_listo:
            self.presupuesto.reiniciar()
            self._presupuesto_listo = True
        respuesta = self.fuente.listar_criptas()
        if isinstance(respuesta, dict):
            return respuesta.get("criptas", [])
        return respuesta

    def _preparar_catalogo(self):
        if self.local is not None:
            return
        self.version_catalogo = str(self.fuente.version_catalogo()["version"])
        carpeta = os.path.join(self.carpeta, "catalogo")
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, "catalogo_%s.bin" % nombre_seguro(self.version_catalogo))
        self.almacen_catalogo = AlmacenFichas(ruta, self.version_catalogo)
        self.local = AlmacenLocalCache(self.cache_size, self.almacen_catalogo, self._ficha_en_uso)

    def _ficha_en_uso(self, id_ficha):
        return self.partida is not None and self.partida.ficha_en_uso(id_ficha)

    def ruta_cripta(self, id_cripta, version):
        return os.path.join(self.carpeta, "criptas",
                            "%s__%s.bin" % (nombre_seguro(id_cripta), nombre_seguro(version)))

    def ruta_catalogo(self, version):
        return os.path.join(self.carpeta, "catalogo", "catalogo_%s.bin" % nombre_seguro(version))

    # ------------------------------------------------------------ partida
    def crear_partida(self, id_cripta, semilla=None, ordenes_previas=None, exigir_versiones=None,
                      partida_nueva=True, validar=None):
        anterior = (self.partida, self.ejecutor, self.precarga, self.log, self.ordenes)
        self.ejecutor = None
        self.log = None
        try:
            partida = self._armar(id_cripta, semilla, ordenes_previas, exigir_versiones,
                                  partida_nueva, validar)
        except BaseException:
            if self.ejecutor is not None:
                self.ejecutor.cerrar()
            if self.log is not None:
                self.log.cerrar()
            self.partida, self.ejecutor, self.precarga, self.log, self.ordenes = anterior
            raise
        if anterior[1] is not None:
            anterior[1].cerrar()                      
        if anterior[3] is not None:
            anterior[3].cerrar()                      
        return partida

    def _armar(self, id_cripta, semilla, ordenes_previas, exigir_versiones, partida_nueva,
               validar=None):
        if partida_nueva and self.partidas_creadas > 0 and not self._presupuesto_listo:
            self.presupuesto.reiniciar()
        if partida_nueva:
            self._presupuesto_listo = False
        self.partidas_creadas += 1

        datos = self.fuente.datos_cripta(id_cripta)
        if "presupuesto_solicitudes" in datos:
            self.presupuesto.fijar_limite(datos["presupuesto_solicitudes"])
        version = str(datos.get("version", ""))
        self._preparar_catalogo()
        if exigir_versiones is not None:
            if version != exigir_versiones[0] or self.version_catalogo != exigir_versiones[1]:
                raise ErrorVersion(
                    "la partida es de la versión de cripta %s / catálogo %s, pero los datos "
                    "disponibles son %s / %s" % (exigir_versiones[0], exigir_versiones[1],
                                                 version, self.version_catalogo))

        os.makedirs(os.path.join(self.carpeta, "criptas"), exist_ok=True)
        almacen_cripta = AlmacenCripta(self.ruta_cripta(id_cripta, version), version)
        if not almacen_cripta.tiene_generales():
            almacen_cripta.guardar_generales(datos)
        esqueleto = descargar_esqueleto(self.fuente, id_cripta, almacen_cripta)

        self.ejecutor = EjecutorRed()
        resolutor = ResolutorCatalogo(self.fuente, self.ejecutor, self.local, self.presupuesto)
        precarga = PrecargaContenido(self.fuente, id_cripta, esqueleto, self.ejecutor,
                                     self.presupuesto, resolutor, almacen_cripta,
                                     reserva=RESERVA_PRECARGA)
        inventario = Inventario(datos["inventario_max"], ordenar)
        bitacora = BitacoraPantalla(MENSAJES_EN_PANTALLA)
        if semilla is None:
            semilla = self.semilla_fija if self.semilla_fija is not None else semilla_nueva()

        partida = Partida(datos, esqueleto, precarga, resolutor, inventario, bitacora, semilla)
        self.partida = partida         
        self.precarga = precarga
        partida.iniciar()

        self.ordenes = []
        if ordenes_previas:
            reconstructor = Controlador(partida)       
            numero = 0
            for orden in ordenes_previas:
                numero += 1
                if not reconstructor.ejecutar(orden):
                    raise ErrorVersion("la orden %d (%s) fue rechazada al reconstruir la partida"
                                       % (numero, orden.a_texto()))
                self.ordenes.append(orden)
        if validar is not None:
            validar(partida)         

        if self.registrar_log:
            encabezado = EncabezadoLog(id_cripta, version, self.version_catalogo, semilla,
                                       self.nombre, fecha_actual())
            self.log = BitacoraPartida(self._ruta_log_nueva(id_cripta), encabezado, self.ordenes)
        return partida

    def _ruta_log_nueva(self, id_cripta):
        carpeta = os.path.join(self.carpeta, "partidas")
        podar_logs(carpeta, MAX_REPETICIONES - 1)  
        base = "%s_%s" % (nombre_seguro(id_cripta), time.strftime("%Y%m%d_%H%M%S"))
        ruta = os.path.join(carpeta, base + ".log")
        n = 2
        while os.path.exists(ruta):        
            ruta = os.path.join(carpeta, "%s_%d.log" % (base, n))
            n += 1
        return ruta

    def registrar_orden(self, orden):
        self.ordenes.append(orden)
        if self.log is not None:
            self.log.anotar(orden)

    def al_terminar(self, partida):
        lineas = []
        if self.registrar_puntajes and partida.estado != "jugando":
            self.puntajes.registrar(partida, self.nombre, fecha_actual())
            lineas.append("Partida anotada en la tabla de puntajes.")
        if self.log is not None:
            lineas.append("Bitácora de la partida: %s" % self.log.ruta)
            self.ultimo_log = self.log.ruta
            self.log.cerrar()
            self.log = None
        lineas.append(self.reporte())
        return "\n".join(lineas)

    def reporte(self):
        cache = self.local.cache if self.local is not None else None
        texto = "--- Red y caché ---\n" + self.presupuesto.reporte(cache)
        if cache is not None and cache.desbordes > 0:
            texto += "\nVeces que la caché pasó su tope (todas las fichas en uso): %d" % cache.desbordes
        if self.precarga is not None:
            texto += "\n" + self.precarga.estadisticas()
        return texto

    def _cerrar_partida_actual(self):
        if self.log is not None:
            self.log.cerrar()
            self.log = None
        if self.ejecutor is not None:
            self.ejecutor.cerrar()
            self.ejecutor = None

    def detener_red(self):
        if self.partida is not None and self.partida.estado == "jugando":
            return
        if self.ejecutor is not None:
            self.ejecutor.cerrar()
            self.ejecutor = None

    def cerrar(self):
        ruta = self.log.ruta if self.log is not None else None
        self._cerrar_partida_actual()
        return ruta

    def versiones_actuales(self, id_cripta):
        version = str(self.fuente.version_cripta(id_cripta)["version"])
        catalogo = str(self.fuente.version_catalogo()["version"])
        return version, catalogo

    def hay_copia_local(self, id_cripta, version_cripta, version_catalogo):
        return (os.path.exists(self.ruta_cripta(id_cripta, version_cripta))
                and os.path.exists(self.ruta_catalogo(version_catalogo)))