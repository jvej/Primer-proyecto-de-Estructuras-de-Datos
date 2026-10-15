"""Vista de consola (MVC, §6, §10.2). Implementa vista_base.Vista.

Lee el estado del modelo para mostrarlo y traduce lo que escribe el usuario a una
Orden (orden.py). No modifica el modelo y no conoce al Controlador.

`entrada` y `salida` se pueden cambiar (por defecto input y print): así las pruebas
pueden guionar una sesión completa, y una vista gráfica no necesita nada de esto.

Comandos (los números se cuentan desde 1, como se muestran en pantalla):
    n s e o | ir n ..... moverse         abrir n ........ abrir una puerta
    atacar [N] ......... atacar          esperar | x ..... esperar
    recoger [N] ........ recoger del suelo
    usar|equipar|soltar [N] ... sobre el objeto N del inventario; sin número, el que
                                se está viendo (el cursor)
    inv | sig | ant | inicio ... ver el inventario y mover el cursor
    ordenar peso|valor|nombre [desc] ... vista ordenada (no cambia el orden real)
    retroceso | r ...... usar un pergamino de retroceso
    guardar | cargar | salir | ayuda
"""

from orden import (ABRIR, AYUDA, ATACAR, CARGAR, EQUIPAR, ESPERAR, GUARDAR, INV_ANTERIOR,
                   INV_INICIO, INV_ORDENAR, INV_SIGUIENTE, INVENTARIO, MOVER, Orden,
                   PERGAMINO, RECOGER, SALIR, SOLTAR, USAR)
from vista_base import Vista

CRITERIOS = ("peso", "valor", "nombre")


def _direccion(texto):
    """'n'/'norte' -> 'N', etc. None si no es una dirección."""
    if texto in ("n", "norte"):
        return "N"
    if texto in ("s", "sur"):
        return "S"
    if texto in ("e", "este"):
        return "E"
    if texto in ("o", "oeste"):
        return "O"
    return None


def _numero(texto):
    """Número desde 1 -> posición desde 0. None si no es un número válido."""
    if not texto.isdigit() or int(texto) < 1:
        return None
    return int(texto) - 1


def interpretar(linea, partida):
    """Convierte una línea escrita en una Orden, o en un texto con el motivo si no se entiende."""
    partes = linea.strip().lower().split()
    if len(partes) == 0:
        return "Escribe un comando (o 'ayuda')."
    comando = partes[0]
    argumentos = partes[1:]

    if _direccion(comando) is not None and len(argumentos) == 0:
        return Orden(MOVER, _direccion(comando))
    if comando in ("ir", "mover"):
        if len(argumentos) == 1 and _direccion(argumentos[0]) is not None:
            return Orden(MOVER, _direccion(argumentos[0]))
        return "Uso: ir n | s | e | o"
    if comando == "abrir":
        if len(argumentos) == 1 and _direccion(argumentos[0]) is not None:
            return Orden(ABRIR, _direccion(argumentos[0]))
        return "Uso: abrir n | s | e | o"
    if comando in ("esperar", "x"):
        return Orden(ESPERAR)
    if comando in ("retroceso", "pergamino", "r"):
        return Orden(PERGAMINO)

    if comando == "atacar":
        return _con_posicion(ATACAR, argumentos, len(partida.enemigos_en_sala()), "enemigos")
    if comando == "recoger":
        return _con_posicion(RECOGER, argumentos, len(partida.objetos_en_sala()), "objetos en el suelo")

    if comando in ("usar", "equipar", "soltar"):
        tipo = USAR if comando == "usar" else (EQUIPAR if comando == "equipar" else SOLTAR)
        if len(argumentos) == 0:
            return Orden(tipo, None)
        if len(argumentos) == 1 and _numero(argumentos[0]) is not None:
            return Orden(tipo, _numero(argumentos[0]))
        return "Uso: %s [número del inventario]" % comando

    if comando in ("inv", "i", "inventario"):
        return Orden(INVENTARIO)
    if comando in ("sig", "siguiente"):
        return Orden(INV_SIGUIENTE)
    if comando in ("ant", "anterior"):
        return Orden(INV_ANTERIOR)
    if comando == "inicio":
        return Orden(INV_INICIO)
    if comando == "ordenar":
        if len(argumentos) in (1, 2) and argumentos[0] in CRITERIOS:
            if len(argumentos) == 1:
                return Orden(INV_ORDENAR, argumentos[0], False)
            if argumentos[1] in ("desc", "descendente"):
                return Orden(INV_ORDENAR, argumentos[0], True)
        return "Uso: ordenar peso|valor|nombre [desc]"

    if comando == "guardar":
        return Orden(GUARDAR)
    if comando == "cargar":
        return Orden(CARGAR)
    if comando in ("ayuda", "?", "h"):
        return Orden(AYUDA)
    if comando in ("salir", "q"):
        return Orden(SALIR)
    return "No entiendo '%s'. Escribe 'ayuda' para ver los comandos." % comando


def _con_posicion(tipo, argumentos, cantidad, que):
    """atacar/recoger: con número, ese; sin número, el único si hay uno solo."""
    if len(argumentos) == 1 and _numero(argumentos[0]) is not None:
        return Orden(tipo, _numero(argumentos[0]))
    if len(argumentos) == 0:
        if cantidad <= 1:
            return Orden(tipo, 0)       # si no hay ninguno, el modelo lo rechaza con su mensaje
        return "Hay %d %s: indica el número (por ejemplo '%s 1')." % (cantidad, que, tipo)
    return "Uso: %s [número]" % tipo


AYUDA_TEXTO = """Comandos (los números se cuentan desde 1, como se ven en pantalla):
  n s e o            moverse (también: ir n)
  abrir n|s|e|o      abrir una puerta con la llave
  atacar [N]         atacar al enemigo N de la sala
  esperar | x        esperar
  recoger [N]        recoger el objeto N del suelo
  usar|equipar|soltar [N]   actuar sobre el objeto N del inventario;
                     sin número, sobre el que estás viendo (cursor '>')
  inv                ver el inventario     sig | ant | inicio   mover el cursor
  ordenar peso|valor|nombre [desc]   vista ordenada (no cambia el orden real)
  retroceso | r      usar un pergamino de retroceso
  guardar | cargar | salir | ayuda"""


class VistaConsola(Vista):
    def __init__(self, entrada=input, salida=print):
        self._entrada = entrada
        self._salida = salida

    # ------------------------------------------------------------- entrada
    def elegir_cripta(self, criptas):
        self._salida("\nCriptas disponibles:")
        i = 1
        for cripta in criptas:
            self._salida("  %d) %s - %s (%s salas, dificultad %s)" % (
                i, cripta.get("id"), cripta.get("nombre", ""), cripta.get("salas", "?"),
                cripta.get("dificultad", "?")))
            i += 1
        while True:
            texto = self._leer("Elige una cripta (número, o 'salir'): ")
            if texto is None or texto.strip().lower() in ("salir", "q"):
                return None
            numero = _numero(texto.strip())
            if numero is not None and numero < len(criptas):
                return criptas[numero].get("id")
            self._salida("Opción no válida.")

    def pedir_orden(self, partida):
        while True:
            texto = self._leer("> ")
            if texto is None:
                return Orden(SALIR)
            resultado = interpretar(texto, partida)
            if isinstance(resultado, Orden):
                return resultado
            self._salida(resultado)

    def confirmar(self, pregunta):
        texto = self._leer(pregunta + " (s/n): ")
        if texto is None:
            return True
        return texto.strip().lower() in ("s", "si", "sí", "y", "yes")

    def _leer(self, indicacion):
        """Una línea del usuario, o None si la entrada se cerró (Ctrl+D / Ctrl+C)."""
        try:
            return self._entrada(indicacion)
        except (EOFError, KeyboardInterrupt):
            return None

    # -------------------------------------------------------------- salida
    def mostrar_partida(self, partida):
        jugador = partida.jugador
        sala = partida.sala_actual()
        escribir = self._salida
        escribir("")
        escribir("=" * 64)
        escribir("Sala %s: %s   |   tiempo %d   |   acciones %d" % (
            sala.id, sala.nombre or "sin nombre", partida.reloj.tiempo_actual, partida.acciones))
        escribir("Vida %d/%d   Ataque %d   Defensa %d   Arma: %s   Armadura: %s" % (
            jugador.vida, jugador.vida_max, jugador.ataque_efectivo(), jugador.defensa_efectivo(),
            jugador.arma.nombre if jugador.arma is not None else "-",
            jugador.armadura.nombre if jugador.armadura is not None else "-"))
        efectos = partida.efectos_activos()
        if len(efectos) > 0:
            escribir("Efectos: " + ", ".join(efectos))
        escribir("Salidas: " + self._texto_salidas(partida))
        self._lista_numerada("Enemigos", partida.enemigos_en_sala(), self._texto_enemigo)
        self._lista_numerada("En el suelo", partida.objetos_en_sala(), self._texto_objeto)
        trampas = partida.trampas_en_sala()
        if len(trampas) > 0:
            textos = []
            for t in trampas:
                textos.append("%s (%s)" % (t.nombre, "armada" if t.armada else "desarmada"))
            escribir("Trampas: " + ", ".join(textos))
        inventario = partida.inventario
        escribir("Inventario: %d/%d   (escribe 'inv' para verlo)" % (len(inventario), inventario.capacidad))
        escribir("--- Últimos mensajes ---")
        for mensaje in partida.bitacora.ultimos():
            escribir("  " + mensaje)

    def mostrar_inventario(self, partida):
        inventario = partida.inventario
        jugador = partida.jugador
        self._salida("\nInventario (%d/%d), en su orden real:" % (len(inventario), inventario.capacidad))
        if len(inventario) == 0:
            self._salida("  (vacío)")
            return
        actual = inventario.objeto_actual()
        i = 1
        for objeto in inventario.objetos():
            marca = ">" if objeto is actual else " "
            equipado = "  [equipado]" if (objeto is jugador.arma or objeto is jugador.armadura) else ""
            self._salida(" %s %d) %s%s" % (marca, i, self._texto_objeto(objeto), equipado))
            i += 1
        self._salida("El cursor '>' se mueve con 'sig' y 'ant'; 'soltar', 'equipar' y 'usar' "
                     "sin número actúan sobre él.")

    def mostrar_vista_ordenada(self, criterio, descendente, pares):
        self._salida("\nInventario ordenado por %s (%s). El orden real no cambia; "
                     "los números son los reales:" % (criterio, "descendente" if descendente else "ascendente"))
        if len(pares) == 0:
            self._salida("  (vacío)")
        for posicion, objeto in pares:
            self._salida("  %d) %s" % (posicion + 1, self._texto_objeto(objeto)))

    def mostrar_aviso(self, texto):
        self._salida(texto)

    def mostrar_ayuda(self):
        self._salida(AYUDA_TEXTO)

    def mostrar_fin(self, partida):
        self._salida("")
        self._salida("*" * 64)
        if partida.estado == "victoria":
            self._salida("¡VICTORIA! Saliste de la cripta.")
        else:
            self._salida("DERROTA. Has muerto.")
        self._salida("Acciones: %d   Enemigos derrotados: %d   Tiempo final: %d" % (
            partida.acciones, partida.derrotados, partida.reloj.tiempo_actual))
        self._salida("*" * 64)

    # ------------------------------------------------------------ internos
    def _texto_salidas(self, partida):
        textos = []
        for direccion, estado, id_vecino, llave in partida.salidas_visibles():
            if estado == "cerrada":
                detalle = "cerrada" + (", llave %s" % llave if llave else "")
            else:
                detalle = "abierta"
            textos.append("%s -> sala %s (%s)" % (direccion, id_vecino, detalle))
        return " | ".join(textos) if len(textos) > 0 else "ninguna"

    def _lista_numerada(self, titulo, elementos, formato):
        if len(elementos) == 0:
            self._salida("%s: ninguno" % titulo)
            return
        self._salida("%s:" % titulo)
        i = 1
        for elemento in elementos:
            self._salida("  %d) %s" % (i, formato(elemento)))
            i += 1

    def _texto_enemigo(self, enemigo):
        return "%s  vida %d/%d" % (enemigo.etiqueta(), enemigo.vida, enemigo.vida_max)

    def _texto_objeto(self, objeto):
        return "%s (%s)  peso %s  valor %s" % (objeto.nombre, objeto.clase, objeto.peso, objeto.valor)