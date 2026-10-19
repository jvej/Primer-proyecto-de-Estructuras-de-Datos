import os

from modelo.estructuras.cola_fifo import ColaFIFO
from modelo.estructuras.ordenamiento import ordenar
from controlador.orden import Orden

MARCA = "CRIPTA-LOG"
VERSION_LOG = 1
SEPARADOR = "---"
CAMPOS = ("id_cripta", "version_cripta", "version_catalogo", "semilla", "jugador", "fecha")
OBLIGATORIOS = ("id_cripta", "version_cripta", "version_catalogo", "semilla")
EXTENSION = ".log"
MAX_REPETICIONES = 20      


class ErrorLog(Exception):
    """El archivo no es un log de Cripta válido."""


class EncabezadoLog:
    def __init__(self, id_cripta, version_cripta, version_catalogo, semilla, jugador="", fecha=""):
        self.id_cripta = str(id_cripta)
        self.version_cripta = str(version_cripta)
        self.version_catalogo = str(version_catalogo)
        self.semilla = int(semilla)
        self.jugador = _limpio(jugador)
        self.fecha = _limpio(fecha)

    def valor(self, campo):
        return getattr(self, campo)

    def __repr__(self):
        return "EncabezadoLog(%s v%s, catálogo %s, semilla %d)" % (
            self.id_cripta, self.version_cripta, self.version_catalogo, self.semilla)


def _limpio(texto):
    return str(texto).replace("\n", " ").replace("\r", " ")


class BitacoraPartida:
    def __init__(self, ruta, encabezado, ordenes_previas=()):
        carpeta = os.path.dirname(ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        self.ruta = ruta
        self.encabezado = encabezado
        self.lineas = 0
        self._archivo = open(ruta, "a", encoding="utf-8")
        self._escribir(MARCA + " " + str(VERSION_LOG))
        for campo in CAMPOS:
            self._escribir("%s=%s" % (campo, encabezado.valor(campo)))
        self._escribir(SEPARADOR)
        for orden in ordenes_previas:
            self.anotar(orden)

    def anotar(self, orden):
        if self._archivo is None:
            return
        self._escribir(orden.a_texto())
        self.lineas += 1

    def cerrar(self):
        if self._archivo is not None:
            self._archivo.close()
            self._archivo = None

    def _escribir(self, linea):
        self._archivo.write(linea + "\n")
        self._archivo.flush()


def leer_log(ruta):
    if not os.path.exists(ruta):
        raise ErrorLog("no existe el archivo de log: %s" % ruta)
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = f.read().split("\n")
    if len(lineas) == 0 or lineas[0].strip() != MARCA + " " + str(VERSION_LOG):
        raise ErrorLog("%s no es un log de Cripta (versión de log %d)" % (ruta, VERSION_LOG))

    campos = []
    valores = []
    i = 1
    while i < len(lineas) and lineas[i].strip() != SEPARADOR:
        linea = lineas[i]
        if "=" not in linea:
            raise ErrorLog("línea %d del encabezado sin '=': %r" % (i + 1, linea))
        posicion = linea.index("=")
        campos.append(linea[:posicion].strip())
        valores.append(linea[posicion + 1:].strip())
        i += 1
    if i >= len(lineas):
        raise ErrorLog("el log no tiene la línea separadora '%s'" % SEPARADOR)
    for campo in OBLIGATORIOS:
        if campo not in campos:
            raise ErrorLog("al encabezado le falta el campo '%s'" % campo)

    def valor(campo):
        return valores[campos.index(campo)] if campo in campos else ""

    try:
        encabezado = EncabezadoLog(valor("id_cripta"), valor("version_cripta"),
                                   valor("version_catalogo"), int(valor("semilla")),
                                   valor("jugador"), valor("fecha"))
    except ValueError:
        raise ErrorLog("la semilla del log no es un número: %r" % valor("semilla"))

    ordenes = ColaFIFO()
    i += 1
    while i < len(lineas):
        linea = lineas[i].strip()
        if linea != "":
            try:
                ordenes.agregar(Orden.desde_texto(linea))
            except ValueError as error:
                raise ErrorLog("línea %d: %s" % (i + 1, error))
        i += 1
    return encabezado, ordenes

class EntradaLog:
    __slots__ = ("ruta", "id_cripta", "jugador", "fecha", "ordenes")

    def __init__(self, ruta, encabezado, ordenes):
        self.ruta = ruta
        self.id_cripta = encabezado.id_cripta
        self.jugador = encabezado.jugador
        self.fecha = encabezado.fecha         
        self.ordenes = ordenes         


def _logs_por_antiguedad(carpeta):
    if not os.path.isdir(carpeta):
        return []
    pares = []
    for nombre in os.listdir(carpeta):
        ruta = os.path.join(carpeta, nombre)
        if nombre.endswith(EXTENSION) and os.path.isfile(ruta):
            pares.append((os.path.getmtime(ruta), ruta))
    return ordenar(pares, clave=lambda par: par[0], descendente=True)


def listar_logs(carpeta, maximo=MAX_REPETICIONES):
    entradas = []
    for _instante, ruta in _logs_por_antiguedad(carpeta):
        if len(entradas) >= maximo:
            break
        try:
            encabezado, ordenes = leer_log(ruta)
        except (ErrorLog, OSError, UnicodeDecodeError):
            continue
        if len(ordenes) > 0:
            entradas.append(EntradaLog(ruta, encabezado, len(ordenes)))
    return entradas


def podar_logs(carpeta, conservar):
    """Borra las bitácoras más viejas y deja solo las `conservar` más nuevas."""
    pares = _logs_por_antiguedad(carpeta)
    for i in range(max(0, conservar), len(pares)):
        try:
            os.remove(pares[i][1])
        except OSError:
            pass      