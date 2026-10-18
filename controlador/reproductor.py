"""Reproducción de una partida desde su log (§4.11): --replay partida.log

Sin vista interactiva (§6): usa el Controlador con vista=None y le da las órdenes del
log, en orden, sacándolas de una cola FIFO.

Antes de reproducir compara las versiones del log con las que hay disponibles:
  1. Si la fuente actual (red u --offline) publica las mismas versiones -> se usa.
  2. Si no, pero existe una copia local con esas versiones -> se usa la copia
     (fuente_almacen.py) y se avisa.
  3. Si no hay ninguna de las dos -> NO se reproduce: se informa que no se puede
     garantizar una reproducción fiel (no se juega en silencio contra datos distintos).

Durante la reproducción, si una orden del log es rechazada, la partida ya se desvió del
original: se detiene y se informa en qué línea.

Hay dos formas de usarlo:
  - reproducir(...): todo de una vez, sin vista (--replay en la consola).
  - preparar_reproduccion(...): deja la partida lista y las órdenes en su cola, para que
    el Controlador las dé una por una mientras la Vista las muestra (repetición en la
    ventana). Los pasos 1 y 2 son los mismos en los dos casos.

No imprime: devuelve un ResultadoReplay con las líneas de texto del informe.
"""

from controlador.aplicacion import Aplicacion
from controlador.controlador import Controlador
from modelo.datos.almacen_cripta import AlmacenCripta
from modelo.datos.almacen_fichas import AlmacenFichas
from modelo.datos.bitacora_partida import ErrorLog, leer_log
from modelo.datos.fuente_almacen import FuenteAlmacen
from modelo.juego.errores import ErrorCripta


class ResultadoReplay:
    def __init__(self):
        self.reproducido = False     # True si se ejecutaron todas las órdenes
        self.fiel = False            # True si los datos tenían las versiones del log
        self.ordenes = 0
        self.partida = None
        self.lineas = []

    def anotar(self, texto):
        self.lineas.append(texto)

    def texto(self):
        return "\n".join(self.lineas)


class Reproduccion:
    """Una partida reconstruida desde su log, lista para darle las órdenes una por una."""

    def __init__(self, encabezado, partida, ordenes, aplicacion):
        self.encabezado = encabezado
        self.partida = partida
        self.ordenes = ordenes            # ColaFIFO de Orden, en el orden del log
        self.total = len(ordenes)
        self.aplicacion = aplicacion

    def cerrar(self):
        """Cierra el hilo de red de la aplicación usada para reproducir."""
        if self.aplicacion is not None:
            self.aplicacion.cerrar()
            self.aplicacion = None


def preparar_reproduccion(ruta_log, fuente, presupuesto, carpeta, cache_size=25):
    """Pasos 1 y 2: revisa las versiones y arma la partida inicial con la semilla del log.
    Devuelve (Reproduccion o None, ResultadoReplay). Si es None, el informe dice por qué.
    Quien recibe la Reproduccion debe llamar a cerrar() al terminar."""
    resultado = ResultadoReplay()
    try:
        encabezado, ordenes = leer_log(ruta_log)
    except ErrorLog as error:
        resultado.anotar("No se puede reproducir: %s" % error)
        return None, resultado
    resultado.anotar("Reproduciendo %s: cripta %s (versión %s), catálogo %s, semilla %d, jugador %s"
                     % (ruta_log, encabezado.id_cripta, encabezado.version_cripta,
                        encabezado.version_catalogo, encabezado.semilla, encabezado.jugador or "-"))

    # ---------------------------------------------------- 1. ¿qué datos usar?
    aplicacion = Aplicacion(fuente, presupuesto, carpeta, cache_size, nombre=encabezado.jugador,
                            registrar_log=False, registrar_puntajes=False)
    try:
        version_cripta, version_catalogo = aplicacion.versiones_actuales(encabezado.id_cripta)
    except ErrorCripta as error:
        version_cripta, version_catalogo = None, None
        resultado.anotar("No se pudieron consultar las versiones actuales: %s" % error)

    if version_cripta == encabezado.version_cripta and version_catalogo == encabezado.version_catalogo:
        resultado.anotar("Las versiones del log coinciden con las disponibles.")
    elif aplicacion.hay_copia_local(encabezado.id_cripta, encabezado.version_cripta,
                                    encabezado.version_catalogo):
        resultado.anotar("Las versiones actuales (%s / %s) no son las del log; se usa la copia "
                         "local compatible." % (version_cripta, version_catalogo))
        fuente_local = FuenteAlmacen(
            encabezado.id_cripta,
            AlmacenCripta(aplicacion.ruta_cripta(encabezado.id_cripta, encabezado.version_cripta),
                          encabezado.version_cripta),
            encabezado.version_cripta,
            AlmacenFichas(aplicacion.ruta_catalogo(encabezado.version_catalogo),
                          encabezado.version_catalogo),
            encabezado.version_catalogo)
        aplicacion = Aplicacion(fuente_local, fuente_local.presupuesto, carpeta, cache_size,
                                nombre=encabezado.jugador, registrar_log=False,
                                registrar_puntajes=False)
    else:
        resultado.anotar("NO SE PUEDE GARANTIZAR UNA REPRODUCCIÓN FIEL: el log es de la versión "
                         "de cripta %s y catálogo %s; lo disponible es %s / %s y no hay una copia "
                         "local compatible. No se reproduce."
                         % (encabezado.version_cripta, encabezado.version_catalogo,
                            version_cripta, version_catalogo))
        aplicacion.cerrar()
        return None, resultado
    resultado.fiel = True

    # ---------------------------------------------------- 2. partida inicial
    try:
        partida = aplicacion.crear_partida(encabezado.id_cripta, semilla=encabezado.semilla,
                                           exigir_versiones=(encabezado.version_cripta,
                                                             encabezado.version_catalogo))
    except ErrorCripta as error:
        resultado.anotar("No se puede reproducir: %s" % error)
        aplicacion.cerrar()
        return None, resultado
    resultado.partida = partida
    return Reproduccion(encabezado, partida, ordenes, aplicacion), resultado


def anotar_final(resultado, partida, aplicacion=None):
    """Paso 3: el informe con el estado en que quedó la partida."""
    resultado.anotar("Órdenes reproducidas: %d" % resultado.ordenes)
    resultado.anotar("Estado final: %s | reloj %d | vida %d/%d | sala %s | acciones %d | "
                     "enemigos derrotados %d" % (partida.estado, partida.reloj.tiempo_actual,
                                                 partida.jugador.vida, partida.jugador.vida_max,
                                                 partida.jugador.sala.id, partida.acciones,
                                                 partida.derrotados))
    resultado.anotar("Últimos mensajes:")
    for mensaje in partida.bitacora.ultimos():
        resultado.anotar("  " + mensaje)
    if aplicacion is not None:
        resultado.anotar(aplicacion.reporte())


def reproducir(ruta_log, fuente, presupuesto, carpeta, cache_size=25, mostrar_cada=False):
    """mostrar_cada: True agrega al informe una línea por cada orden reproducida."""
    reproduccion, resultado = preparar_reproduccion(ruta_log, fuente, presupuesto, carpeta,
                                                    cache_size)
    if reproduccion is None:
        return resultado
    partida = reproduccion.partida
    ordenes = reproduccion.ordenes

    # ---------------------------------------------------- 3. reproducir
    controlador = Controlador(partida)          # sin vista (§6)
    numero = 0
    detenido = False
    while not ordenes.vacia():
        orden = ordenes.sacar()
        numero += 1
        if partida.estado != "jugando":
            resultado.anotar("La partida terminó (%s) antes de la orden %d del log; el resto se "
                             "ignora." % (partida.estado, numero))
            detenido = True
            break
        if not controlador.ejecutar(orden):
            ultimo = partida.bitacora.ultimos()
            motivo = ultimo[-1] if len(ultimo) > 0 else "rechazada"
            resultado.anotar("DIVERGENCIA en la orden %d (%s): %s. La reproducción se detiene."
                             % (numero, orden.a_texto(), motivo))
            detenido = True
            break
        resultado.ordenes += 1
        if mostrar_cada:
            resultado.anotar("  %4d  t=%-6d %-12s vida %d  sala %s" % (
                numero, partida.reloj.tiempo_actual, orden.a_texto(), partida.jugador.vida,
                partida.jugador.sala.id))
    resultado.reproducido = not detenido

    # ---------------------------------------------------- 4. informe
    anotar_final(resultado, partida, reproduccion.aplicacion)
    reproduccion.cerrar()
    return resultado