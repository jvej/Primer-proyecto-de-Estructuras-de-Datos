import os
import time
from contextlib import contextmanager

from modelo.datos.almacen_cripta import AlmacenCripta
from modelo.datos.almacen_fichas import AlmacenFichas
from modelo.datos.almacen_local_cache import AlmacenLocalCache
from modelo.juego.bitacora_pantalla import BitacoraPantalla
from modelo.datos.bitacora_partida import (MAX_REPETICIONES, BitacoraPartida, EncabezadoLog,
                                           podar_logs)
from controlador.controlador import Controlador
from modelo.datos.ejecutor_red import EjecutorRed
from modelo.juego.errores import ErrorCripta, ErrorPresupuesto, ErrorRed
from modelo.datos.esqueleto import descargar_esqueleto
from modelo.juego.inventario import Inventario
from modelo.juego.linea_tiempo import K_DEFECTO
from modelo.estructuras.ordenamiento import ordenar
from modelo.juego.partida import Partida
from modelo.juego.resumen_historico import inicializar_historia
from modelo.juego.resolubilidad import ResultadoResolubilidad, verificar_resolubilidad
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


class ErrorNoResoluble(ErrorCripta):
    """Impide iniciar una partida y permite mostrar su diagnóstico en la vista."""

    def __init__(self, reporte):
        self.reporte = reporte
        super().__init__(reporte.formatear_reporte())


class Aplicacion:
    def __init__(self, fuente, presupuesto, carpeta=CARPETA_DEFECTO, cache_size=CACHE_DEFECTO,
                 semilla=None, nombre="Jugador", registrar_log=True, registrar_puntajes=True,
                 forzar=False, checkpoint_cada=K_DEFECTO):
        self.fuente = fuente
        self.presupuesto = presupuesto
        self.carpeta = carpeta
        self.cache_size = cache_size
        self.semilla_fija = semilla
        self.nombre = nombre
        self.registrar_log = registrar_log
        self.registrar_puntajes = registrar_puntajes
        self.forzar = forzar
        self.checkpoint_cada = checkpoint_cada
        self.reporte_resolubilidad: ResultadoResolubilidad | None = None
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
        self._lineas_reconstruccion = []
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
                      partida_nueva=True, validar=None, forzar=None):
        try:
            with self._armar(id_cripta, semilla, ordenes_previas, exigir_versiones,
                             partida_nueva, validar,
                             self.forzar if forzar is None else forzar) as (partida, _):
                pass
        except ErrorNoResoluble:
            self._cerrar_partida_actual()
            self.partida = None
            self.precarga = None
            self.ordenes = []
            self._lineas_reconstruccion = []
            raise
        return partida

    @contextmanager
    def preparar_reconstruccion(self, id_cripta, semilla=None, exigir_versiones=None):
        """Contexto para la carga v4 sin reemplazar todavía la sesión actual.

        Firma: preparar_reconstruccion(id_cripta, semilla=None,
        exigir_versiones=None) -> ContextManager[tuple[Partida,
        Callable[[str], bool]]]. Entrega (partida_candidata, aplicar_linea).
        aplicar_linea(linea: str) -> bool usa siempre el mismo controlador
        candidato, sin vista; conserva las líneas aceptadas en su orden real.
        Blancos y otros comentarios devuelven True sin ejecutarse ni guardarse;
        una orden rechazada devuelve False y obliga a abortar la carga. Un
        formato inválido lanza ValueError.

        Persistencia debe reconstruir y validar DENTRO del with, y lanzar una
        excepción si falla. Solo una salida normal publica la partida y su log;
        cualquier excepción cierra los recursos candidatos y conserva la sesión
        anterior. El callback solo puede usarse dentro del with. Las solicitudes
        realizadas durante el intento siguen contando en el presupuesto.
        """
        limite = self.presupuesto.limite
        anteriores = (self.partidas_creadas, self._presupuesto_listo,
                      self.version_catalogo, self.almacen_catalogo, self.local)
        try:
            with self._armar(id_cripta, semilla, [], exigir_versiones, False,
                             preparar_controlador=True) as candidato:
                yield candidato
        except BaseException:
            (self.partidas_creadas, self._presupuesto_listo,
             self.version_catalogo, self.almacen_catalogo, self.local) = anteriores
            self.presupuesto.fijar_limite(limite)
            raise

    def _preparar_cripta(self, id_cripta, exigir_versiones=None):
        """Comparte datos, control de versiones y esqueleto entre juego e inspección."""
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
        return datos, esqueleto, almacen_cripta

    def _verificar_cripta(self, id_cripta, datos, esqueleto, almacen_cripta):
        if almacen_cripta.tiene_llaves():
            respuesta = almacen_cripta.leer_llaves()
        else:
            try:
                respuesta = self.fuente.llaves(id_cripta)
            except (ErrorRed, ErrorPresupuesto) as error:
                causa = ("presupuesto_solicitudes agotado" if isinstance(error, ErrorPresupuesto)
                         else "error de red")
                self.reporte_resolubilidad = ResultadoResolubilidad(
                    "NO VERIFICADA", motivo="no se pudo consultar /llaves: %s: %s" % (causa, error))
                return self.reporte_resolubilidad
            almacen_cripta.guardar_llaves(respuesta)

        ubicaciones = respuesta["llaves"] if isinstance(respuesta, dict) else respuesta
        catalogo = []
        for ubicacion in ubicaciones:
            id_llave = ubicacion["id"]
            if self.local.disponible(id_llave):
                ficha = self.local.obtener(id_llave)
                if ficha is not None:
                    catalogo.append(ficha)
        self.reporte_resolubilidad = verificar_resolubilidad(
            esqueleto, ubicaciones, datos["sala_inicial"], datos["sala_salida"],
            datos["llave_salida"], catalogo_llaves=catalogo)
        return self.reporte_resolubilidad

    def verificar(self, id_cripta) -> ResultadoResolubilidad:
        """Inspecciona sin inicializar motor, ejecutor, precarga ni bitácora."""
        datos, esqueleto, almacen_cripta = self._preparar_cripta(id_cripta)
        return self._verificar_cripta(id_cripta, datos, esqueleto, almacen_cripta)

    @contextmanager
    def _armar(self, id_cripta, semilla, ordenes_previas, exigir_versiones, partida_nueva,
               validar=None, forzar=False, preparar_controlador=False):
        # Import local: reproductor también importa Aplicacion.
        from controlador.reproductor import (aplicar_linea_reconstruccion,
                                             iterar_lineas_reconstruccion)
        from modelo.juego.orden import Orden

        if partida_nueva and self.partidas_creadas > 0 and not self._presupuesto_listo:
            self.presupuesto.reiniciar()
        if partida_nueva:
            self._presupuesto_listo = False
        self.partidas_creadas += 1

        datos, esqueleto, almacen_cripta = self._preparar_cripta(id_cripta, exigir_versiones)
        if partida_nueva and ordenes_previas is None and exigir_versiones is None:
            reporte = self._verificar_cripta(id_cripta, datos, esqueleto, almacen_cripta)
            if not reporte.es_resoluble() and not forzar:
                raise ErrorNoResoluble(reporte)

        ejecutor = EjecutorRed()
        log = None
        adoptada = False
        activo = True
        partida = None
        try:
            # La caché candidata no desaloja fichas ni modifica la caché viva.
            def ficha_en_uso(id_ficha):
                return partida is not None and partida.ficha_en_uso(id_ficha)

            local = AlmacenLocalCache(self.cache_size, self.almacen_catalogo, ficha_en_uso)
            resolutor = ResolutorCatalogo(self.fuente, ejecutor, local, self.presupuesto)
            precarga = PrecargaContenido(self.fuente, id_cripta, esqueleto, ejecutor,
                                         self.presupuesto, resolutor, almacen_cripta,
                                         reserva=RESERVA_PRECARGA)
            inventario = Inventario(datos["inventario_max"], ordenar)
            bitacora = BitacoraPantalla(MENSAJES_EN_PANTALLA)
            if semilla is None:
                semilla = self.semilla_fija if self.semilla_fija is not None else semilla_nueva()

            partida = Partida(datos, esqueleto, precarga, resolutor, inventario, bitacora, semilla)
            partida.iniciar()
            inicializar_historia(partida, self.checkpoint_cada)

            # El inicio ordinario no necesita un planificador de reconstrucción.
            # La carga v4 sí lo obtiene antes de recibir su callback candidato.
            reconstructor = Controlador(partida) if preparar_controlador else None
            ordenes = []
            lineas = []
            numero = 0
            rechazada = False

            def aplicar_linea(linea: str) -> bool:
                nonlocal reconstructor, numero, rechazada
                if not activo:
                    raise RuntimeError("La reconstrucción candidata ya terminó")
                if rechazada:
                    raise ErrorVersion("la reconstrucción contiene una orden rechazada")
                try:
                    for texto in iterar_lineas_reconstruccion((linea,)):
                        if reconstructor is None:
                            reconstructor = Controlador(partida)
                        comentario = texto.startswith("#")
                        if not comentario:
                            numero += 1
                        if not aplicar_linea_reconstruccion(reconstructor, texto):
                            rechazada = True
                            return False
                        if comentario:
                            texto = "# " + texto[1:].lstrip()
                        else:
                            orden = Orden.desde_texto(texto)
                            ordenes.append(orden)
                            texto = orden.a_texto()
                        lineas.append(texto)
                        return True
                    return True
                except BaseException:
                    rechazada = True
                    raise

            if ordenes_previas is not None:
                for orden in ordenes_previas:
                    texto = orden if isinstance(orden, str) else orden.a_texto()
                    if not aplicar_linea(texto) and rechazada:
                        raise ErrorVersion("la orden %d (%s) fue rechazada al reconstruir la partida"
                                           % (numero, texto))
            if validar is not None:
                validar(partida)

            yield partida, aplicar_linea
            if rechazada:
                raise ErrorVersion("la reconstrucción contiene una línea inválida o rechazada")
            if self.registrar_log:
                encabezado = EncabezadoLog(id_cripta, str(datos.get("version", "")),
                                           self.version_catalogo, semilla,
                                           self.nombre, fecha_actual())
                log = BitacoraPartida(self._ruta_log_nueva(id_cripta), encabezado)
                for texto in lineas:
                    if texto.startswith("#"):
                        log.anotar_comentario(texto[2:])
                    else:
                        log.anotar(Orden.desde_texto(texto))

            ejecutor_anterior, log_anterior = self.ejecutor, self.log
            self.partida, self.precarga, self.ejecutor = partida, precarga, ejecutor
            self.local, self.log = local, log
            self.ordenes, self._lineas_reconstruccion = ordenes, lineas
            adoptada = True
            if ejecutor_anterior is not None:
                ejecutor_anterior.cerrar()
            if log_anterior is not None:
                log_anterior.cerrar()
        finally:
            activo = False
            if not adoptada:
                ejecutor.cerrar()
                if log is not None:
                    log.cerrar()

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
        self._lineas_reconstruccion.append(orden.a_texto())
        if self.log is not None:
            self.log.anotar(orden)

    def registrar_comentario(self, texto: str) -> None:
        # Mismo saneamiento y prefijo que BitacoraPartida.anotar_comentario.
        self._lineas_reconstruccion.append("# " + str(texto).replace("\n", " ").replace("\r", " "))
        if self.log is not None:
            self.log.anotar_comentario(texto)

    def lineas_para_reconstruir(self) -> list[str]:
        """Copia de órdenes y comentarios intercalados tal como se escriben al log."""
        return self._lineas_reconstruccion.copy()

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
