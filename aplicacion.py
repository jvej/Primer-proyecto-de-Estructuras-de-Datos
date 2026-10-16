"""Aplicación: arma las piezas de una partida y lleva lo que no es del juego (§6).

Es la capa de "composición": aquí se juntan la fuente de datos (HTTP, offline o copia
local), la caché y la persistencia (Kim), la precarga y el resolutor (Jeferson), el
modelo (Mariano) y la bitácora de replay, los puntajes y el guardado (Axel).

  - NO es el Modelo: la Partida sigue sin saber de red, disco ni interfaz.
  - NO es el Controlador: no interpreta órdenes; el Controlador la recibe ya armada a
    través de funciones (listar_criptas, crear_partida, al_terminar) y de la
    persistencia (guardar/cargar), igual que antes.
  - NO imprime: devuelve textos para que la vista (o main en --replay) los muestre.

Archivos que genera, dentro de `carpeta` (por defecto ./datos_cripta):
    catalogo/catalogo_<version>.bin      fichas del catálogo (caché persistente, §4.4)
    criptas/<id>__<version>.bin          generales, esqueleto y contenido (§4.4)
    partidas/<id>_<fecha>.log            bitácoras de replay (§4.11)
    guardados/partida.bin                partida guardada (§4.10)
    puntajes.txt                         tabla de puntajes (§2.12)
"""

import os
import time

from almacen_cripta import AlmacenCripta
from almacen_fichas import AlmacenFichas
from almacen_local_cache import AlmacenLocalCache
from bitacora_pantalla import BitacoraPantalla
from bitacora_partida import BitacoraPartida, EncabezadoLog
from controlador import Controlador
from ejecutor_red import EjecutorRed
from errores import ErrorCripta
from esqueleto import descargar_esqueleto
from inventario import Inventario
from ordenamiento import ordenar
from partida import Partida
from precarga_contenido import PrecargaContenido
from puntajes import TablaPuntajes
from resolutor_catalogo import ResolutorCatalogo

CARPETA_DEFECTO = "datos_cripta"
CACHE_DEFECTO = 25
MENSAJES_EN_PANTALLA = 20      # §4.8
RESERVA_PRECARGA = 2           # solicitudes que la precarga especulativa deja libres


def nombre_seguro(texto):
    """Para usar un id o una versión dentro de un nombre de archivo."""
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
    """Semilla para una partida nueva. Se elige FUERA del modelo (el modelo solo usa
    random.Random(semilla)); queda escrita en el log y en el guardado."""
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
        self.local = None              # AlmacenLocalCache: caché con tope + disco
        self.partida = None
        self.ejecutor = None
        self.precarga = None
        self.log = None
        self.ordenes = []              # órdenes aceptadas de la partida actual (para guardar)
        self.partidas_creadas = 0
        os.makedirs(carpeta, exist_ok=True)

    # ------------------------------------------------------------ datos
    def listar_criptas(self):
        respuesta = self.fuente.listar_criptas()
        if isinstance(respuesta, dict):
            return respuesta.get("criptas", [])
        return respuesta

    def _preparar_catalogo(self):
        """Una sola vez por ejecución: valida la caché persistente con la versión global
        del catálogo (consulta liviana) sin descargar fichas (§4.4)."""
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
                      partida_nueva=True):
        """Arma una partida lista para jugar.

        semilla: None = la de --semilla o una nueva.
        ordenes_previas: órdenes que se re-ejecutan sin interfaz antes de devolverla
            (cargar una partida guardada, camino A: re-simulación determinista).
        exigir_versiones: (version_cripta, version_catalogo) que deben coincidir con los
            datos obtenidos; si no coinciden se lanza ErrorVersion.
        partida_nueva: True reinicia el presupuesto de red (es por partida, §5.1). Al
            cargar una partida guardada se continúa la misma partida: no se reinicia.

        Si algo falla, la partida que se estaba jugando sigue intacta (útil al cargar).
        """
        anterior = (self.partida, self.ejecutor, self.precarga, self.log, self.ordenes)
        self.ejecutor = None
        self.log = None
        try:
            partida = self._armar(id_cripta, semilla, ordenes_previas, exigir_versiones,
                                  partida_nueva)
        except BaseException:
            if self.ejecutor is not None:
                self.ejecutor.cerrar()
            if self.log is not None:
                self.log.cerrar()
            self.partida, self.ejecutor, self.precarga, self.log, self.ordenes = anterior
            raise
        if anterior[1] is not None:
            anterior[1].cerrar()                       # el hilo de red de la partida anterior
        if anterior[3] is not None:
            anterior[3].cerrar()                       # su log queda completo en disco
        return partida

    def _armar(self, id_cripta, semilla, ordenes_previas, exigir_versiones, partida_nueva):
        if partida_nueva and self.partidas_creadas > 0:
            self.presupuesto.reiniciar()
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
        self.partida = partida            # la caché pregunta a esta partida qué fichas están en uso
        self.precarga = precarga
        partida.iniciar()

        self.ordenes = []
        if ordenes_previas:
            reconstructor = Controlador(partida)          # sin vista y sin observadores
            numero = 0
            for orden in ordenes_previas:
                numero += 1
                if not reconstructor.ejecutar(orden):
                    raise ErrorVersion("la orden %d (%s) fue rechazada al reconstruir la partida"
                                       % (numero, orden.a_texto()))
                self.ordenes.append(orden)

        if self.registrar_log:
            encabezado = EncabezadoLog(id_cripta, version, self.version_catalogo, semilla,
                                       self.nombre, fecha_actual())
            self.log = BitacoraPartida(self._ruta_log_nueva(id_cripta), encabezado, self.ordenes)
        return partida

    def _ruta_log_nueva(self, id_cripta):
        carpeta = os.path.join(self.carpeta, "partidas")
        base = "%s_%s" % (nombre_seguro(id_cripta), time.strftime("%Y%m%d_%H%M%S"))
        ruta = os.path.join(carpeta, base + ".log")
        n = 2
        while os.path.exists(ruta):                    # nunca se mezclan dos partidas
            ruta = os.path.join(carpeta, "%s_%d.log" % (base, n))
            n += 1
        return ruta

    # -------------------------------------------- observador del Controlador
    def registrar_orden(self, orden):
        """Cada orden de partida ACEPTADA (ya resuelta) llega aquí."""
        self.ordenes.append(orden)
        if self.log is not None:
            self.log.anotar(orden)

    def al_terminar(self, partida):
        """Victoria o derrota: puntaje (§2.12), cierre del log y reporte de red (§5.1)."""
        lineas = []
        if self.registrar_puntajes and partida.estado != "jugando":
            self.puntajes.registrar(partida, self.nombre, fecha_actual())
            lineas.append("Partida anotada en la tabla de puntajes.")
        if self.log is not None:
            lineas.append("Bitácora de la partida: %s" % self.log.ruta)
            self.log.cerrar()
            self.log = None
        lineas.append(self.reporte())
        return "\n".join(lineas)

    def reporte(self):
        cache = self.local.cache if self.local is not None else None
        texto = "--- Red y caché ---\n" + self.presupuesto.reporte(cache)
        if self.precarga is not None:
            texto += "\n" + self.precarga.estadisticas()
        return texto

    # ------------------------------------------------------------ cierre
    def _cerrar_partida_actual(self):
        if self.log is not None:
            self.log.cerrar()
            self.log = None
        if self.ejecutor is not None:
            self.ejecutor.cerrar()
            self.ejecutor = None

    def cerrar(self):
        """Salida controlada: cierra el log (lo jugado queda guardado) y el hilo de red."""
        ruta = self.log.ruta if self.log is not None else None
        self._cerrar_partida_actual()
        return ruta

    # ---------------------------------------------- versiones (replay y cargar)
    def versiones_actuales(self, id_cripta):
        """(version_cripta, version_catalogo) que publica hoy la fuente. 2 consultas livianas."""
        version = str(self.fuente.version_cripta(id_cripta)["version"])
        catalogo = str(self.fuente.version_catalogo()["version"])
        return version, catalogo

    def hay_copia_local(self, id_cripta, version_cripta, version_catalogo):
        return (os.path.exists(self.ruta_cripta(id_cripta, version_cripta))
                and os.path.exists(self.ruta_catalogo(version_catalogo)))