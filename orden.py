"""Orden: el vocabulario común entre la Vista y el Controlador (MVC, §6).

Una Orden es un dato simple: qué quiere hacer el jugador, sin lógica ni
dependencias. La Vista traduce lo que el usuario escribe a una Orden; el
Controlador la ejecuta sobre el Modelo. Como no depende de ninguna vista, el
replay (§4.11) puede dar las mismas órdenes leyéndolas de un log, sin interfaz.

Los argumentos son siempre datos serializables:
    MOVER, ABRIR ............ dirección "N" | "S" | "E" | "O"
    ATACAR .................. posición (desde 0) en la lista de enemigos de la sala
    RECOGER ................. posición (desde 0) en la lista de objetos del suelo
    USAR, EQUIPAR, SOLTAR ... posición (desde 0) en el orden real del inventario;
                              None = "el objeto que el cursor está viendo"
    INV_ORDENAR ............. criterio "peso" | "valor" | "nombre" (extra: descendente)
"""

# --- órdenes que cambian la partida (van al log de replay) ---
MOVER = "mover"
ABRIR = "abrir"
ATACAR = "atacar"
ESPERAR = "esperar"
RECOGER = "recoger"
USAR = "usar"
EQUIPAR = "equipar"
SOLTAR = "soltar"
PERGAMINO = "pergamino"

# --- órdenes de consulta o de interfaz (no cambian la partida, no van al log) ---
INVENTARIO = "inventario"
INV_SIGUIENTE = "inv_siguiente"
INV_ANTERIOR = "inv_anterior"
INV_INICIO = "inv_inicio"
INV_ORDENAR = "inv_ordenar"
GUARDAR = "guardar"
CARGAR = "cargar"
AYUDA = "ayuda"
SALIR = "salir"

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