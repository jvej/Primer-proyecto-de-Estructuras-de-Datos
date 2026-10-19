MOVER = "mover"
ABRIR = "abrir"
ATACAR = "atacar"
ESPERAR = "esperar"
RECOGER = "recoger"
USAR = "usar"
EQUIPAR = "equipar"
SOLTAR = "soltar"
PERGAMINO = "pergamino"

INVENTARIO = "inventario"
INV_SIGUIENTE = "inv_siguiente"
INV_ANTERIOR = "inv_anterior"
INV_INICIO = "inv_inicio"
INV_ORDENAR = "inv_ordenar"
GUARDAR = "guardar"
CARGAR = "cargar"
AYUDA = "ayuda"
PUNTAJES = "puntajes"
SALIR = "salir"

VER_REPETICIONES = "__repeticiones__"

ORDENES_DE_PARTIDA = (MOVER, ABRIR, ATACAR, ESPERAR, RECOGER, USAR, EQUIPAR, SOLTAR, PERGAMINO)


class Orden:
    __slots__ = ("tipo", "argumento", "extra")

    def __init__(self, tipo, argumento=None, extra=None):
        self.tipo = tipo
        self.argumento = argumento
        self.extra = extra

    def es_de_partida(self):
        return self.tipo in ORDENES_DE_PARTIDA

    def __eq__(self, otra):
        return (isinstance(otra, Orden) and self.tipo == otra.tipo
                and self.argumento == otra.argumento and self.extra == otra.extra)

    def __repr__(self):
        return "Orden(%r, %r, %r)" % (self.tipo, self.argumento, self.extra)

    def a_texto(self):
        """Una línea del log: 'mover N', 'recoger 0', 'esperar'... Solo órdenes de partida
        ya resueltas (el argumento es una dirección, una posición o nada)."""
        if not self.es_de_partida():
            raise ValueError("solo las órdenes de partida van al log: %r" % (self,))
        if self.argumento is None:
            return self.tipo
        return "%s %s" % (self.tipo, self.argumento)

    @staticmethod
    def desde_texto(linea):
        """Inversa de a_texto(). Lanza ValueError si la línea no es una orden válida."""
        partes = linea.split()
        if len(partes) == 0 or partes[0] not in ORDENES_DE_PARTIDA:
            raise ValueError("orden desconocida: %r" % linea)
        tipo = partes[0]
        if tipo in SIN_ARGUMENTO:
            if len(partes) != 1:
                raise ValueError("'%s' no lleva argumento: %r" % (tipo, linea))
            return Orden(tipo)
        if len(partes) != 2:
            raise ValueError("'%s' lleva exactamente un argumento: %r" % (tipo, linea))
        if tipo in CON_DIRECCION:
            if partes[1] not in ("N", "S", "E", "O"):
                raise ValueError("dirección no válida: %r" % linea)
            return Orden(tipo, partes[1])
        if tipo in CON_OBJETO and es_clave(partes[1]):
            return Orden(tipo, partes[1])
        if not partes[1].isdigit():
            raise ValueError("posición no válida: %r" % linea)
        return Orden(tipo, int(partes[1]))


def es_clave(argumento):
    """True si el argumento es "@<entero>" (objeto del inventario por su etiqueta fija)."""
    if not isinstance(argumento, str) or len(argumento) < 2 or argumento[0] != "@":
        return False
    numero = argumento[1:]
    if numero[0] == "-":
        numero = numero[1:]
    return numero.isdigit()


def clave_de_argumento(argumento):
    return int(argumento[1:])


SIN_ARGUMENTO = (ESPERAR, PERGAMINO)
CON_DIRECCION = (MOVER, ABRIR)
CON_OBJETO = (USAR, EQUIPAR, SOLTAR)