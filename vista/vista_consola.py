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
    puntajes ........... tabla de puntajes
    guardar | cargar | salir | ayuda
"""

import unicodedata

from controlador.orden import (ABRIR, AYUDA, ATACAR, CARGAR, EQUIPAR, ESPERAR, GUARDAR, INV_ANTERIOR,
                   INV_INICIO, INV_ORDENAR, INV_SIGUIENTE, INVENTARIO, MOVER, Orden,
                   PERGAMINO, PUNTAJES, RECOGER, SALIR, SOLTAR, USAR)
from vista.vista_base import Vista


def lineas_mapa_dibujado(mapa, ancho=None):
    """ASCII por bloques completos de casillas; los costos quedan en la tabla."""
    import shutil
    import unicodedata

    def ascii_texto(valor):
        return unicodedata.normalize('NFKD', str(valor)).encode('ascii', 'ignore').decode('ascii')

    def etiqueta(c):
        return '(?)' if c.id is None else '[%s%s]' % ('@' if c.es_jugador else '', c.id)

    def marca(conexion, horizontal):
        if conexion.estado == 'abierta':
            return '-' if horizontal else '|'
        if conexion.estado == 'cerrada':
            return 'K' if conexion.llave is not None else 'X'
        return '?'

    def estado(conexion):
        texto = 'no observada' if conexion.estado == 'desconocida' else conexion.estado
        if conexion.llave is not None:
            texto += ', llave ' + str(conexion.llave)
        return texto

    if not mapa.casillas:
        return ['Mapa conocido: vacio']
    ancho = max(12, ancho or shutil.get_terminal_size((100, 24)).columns)
    etiquetas = [etiqueta(c) for c in mapa.casillas]
    celda = max(len(e) for e in etiquetas) + 6
    minimo_x = min(c.x for c in mapa.casillas)
    maximo_x = max(c.x for c in mapa.casillas)
    minimo_y = min(c.y for c in mapa.casillas)
    maximo_y = max(c.y for c in mapa.casillas)
    columnas = max(1, ancho // celda)
    lineas = ['Mapa conocido (dibujado):']
    bloque = 0
    for inicio in range(minimo_x, maximo_x + 1, columnas):
        fin = min(inicio + columnas - 1, maximo_x)
        bloque += 1
        lineas.append('Bloque %s: columnas %s a %s' % (bloque, inicio, fin))
        ancho_bloque = (fin - inicio + 1) * celda
        # Margen vertical para las puertas N/S incluso en las filas extremas.
        lienzo = [[' '] * ancho_bloque for _ in range((maximo_y - minimo_y) * 4 + 5)]
        # Primero las conexiones para que nunca tapen una etiqueta de sala.
        for conexion in mapa.conexiones:
            if conexion.fuera_cuadricula:
                continue
            a, b = mapa.casillas[conexion.origen], mapa.casillas[conexion.destino]
            ax, bx = (a.x - inicio) * celda + celda // 2, (b.x - inicio) * celda + celda // 2
            ay, by = (a.y - minimo_y) * 4 + 2, (b.y - minimo_y) * 4 + 2
            if ay == by:
                for x in range(max(0, min(ax, bx)), min(ancho_bloque - 1, max(ax, bx)) + 1):
                    lienzo[ay][x] = marca(conexion, True)
            elif inicio <= a.x <= fin:
                for y in range(min(ay, by), max(ay, by) + 1):
                    lienzo[y][ax] = marca(conexion, False)
        for c, texto in zip(mapa.casillas, etiquetas):
            if inicio <= c.x <= fin:
                x = (c.x - inicio) * celda + (celda - len(texto)) // 2
                y = (c.y - minimo_y) * 4 + 2
                for i, caracter in enumerate(texto):
                    lienzo[y][x + i] = caracter
        # Una marca por salida en su lado; la tabla conserva todas sus etiquetas.
        for conexion in mapa.conexiones:
            c = mapa.casillas[conexion.origen]
            if not inicio <= c.x <= fin:
                continue
            texto = etiquetas[conexion.origen]
            izquierda = (c.x - inicio) * celda + (celda - len(texto)) // 2
            x = (c.x - inicio) * celda + celda // 2
            y = (c.y - minimo_y) * 4 + 2
            if conexion.direccion == 'N':
                y -= 1
            elif conexion.direccion == 'S':
                y += 1
            elif conexion.direccion == 'E':
                x = izquierda + len(texto)
            else:
                x = izquierda - 1
            lienzo[y][x] = marca(conexion, conexion.direccion in ('E', 'O'))
        lineas.extend(''.join(fila).rstrip() for fila in lienzo)
    lineas.append('Leyenda: [id] explorada; [@id] jugador; (?) avistada; -/| abierta; X cerrada; K con llave; ? puerta no observada.')
    for c in mapa.casillas:
        if c.es_jugador:
            lineas.append('Sala actual: %s - %s' % (c.id, c.nombre or 'sin nombre'))
            break
    lineas.append('Exploradas: %s | Avistadas: %s' % (mapa.exploradas, mapa.avistadas))
    lineas.append('Salidas conocidas (destino ? = sala desconocida):')
    cursor_salida = 0
    for indice, c in enumerate(mapa.casillas):
        if c.id is not None:
            lineas.append('Sala %s: %s' % (c.id, c.nombre or 'sin nombre'))
            while cursor_salida < len(mapa.conexiones) and mapa.conexiones[cursor_salida].origen == indice:
                conexion = mapa.conexiones[cursor_salida]
                destino = mapa.casillas[conexion.destino]
                lineas.append('  %s -> %s (costo %s, %s)' % (
                    conexion.direccion, '?' if destino.id is None else destino.id,
                    conexion.costo, estado(conexion)))
                cursor_salida += 1
    fuera = [c for c in mapa.conexiones if c.fuera_cuadricula]
    if fuera:
        lineas.append('Conexiones fuera de la cuadricula:')
        for conexion in fuera:
            a, b = mapa.casillas[conexion.origen], mapa.casillas[conexion.destino]
            lineas.append('  sala %s <-> sala %s (%s, costo %s, %s)' % (
                '?' if a.id is None else a.id, '?' if b.id is None else b.id,
                conexion.direccion, conexion.costo, estado(conexion)))
    return [ascii_texto(linea) for linea in lineas]
from controlador.orden import MAPA, interpretar_ir_a
from controlador.orden import HISTORIA, interpretar_historia

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
    if not texto.isdigit() or int(texto) < 1:
        return None
    return int(texto) - 1


def interpretar(linea, partida):
    partes = linea.strip().lower().split()
    if len(partes) == 0:
        return "Escribe un comando (o 'ayuda')."
    comando = partes[0]
    argumentos = partes[1:]

    if comando == HISTORIA:
        try:
            return interpretar_historia(linea, partida.reloj.tiempo_actual, partida.acciones)
        except ValueError as error:
            return str(error)

    if comando == "ir" and argumentos[:1] == ["a"]:
        try:
            return interpretar_ir_a(linea)
        except ValueError as error:
            return str(error)
    if comando == "mapa":
        return Orden(MAPA) if not argumentos else "Uso: mapa"

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
    if comando in ("puntajes", "puntos", "tabla"):
        return Orden(PUNTAJES)
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
            return Orden(tipo, 0)     
        return "Hay %d %s: indica el número (por ejemplo '%s 1')." % (cantidad, que, tipo)
    return "Uso: %s [número]" % tipo


AYUDA_TEXTO = """Comandos (los números se cuentan desde 1, como se ven en pantalla):
  historia <t> | historia #k   consultar por instante o antes de la acción k (también al final)
  ir a <sala>        viajar a una sala explorada, paso a paso
  mapa               dibujar el mapa conocido y las puertas recordadas
                     [@id] jugador; (?) avistada; -/| abierta; X cerrada; K con llave
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
  puntajes           ver la tabla de puntajes
  guardar | cargar | salir | ayuda"""


class VistaConsola(Vista):
    def __init__(self, entrada=input, salida=print):
        self._entrada = entrada
        self._salida = salida
        self._respuesta_final = None

    def mostrar_historia(self, texto):
        self._salida(texto)

    def pedir_orden_final(self, partida):
        while True:
            texto = self._leer("Final: historia <t> o historia #k; Enter para continuar: ")
            if texto is None or not texto.strip():
                return None
            partes = texto.strip().lower().split()
            if partes[0] == HISTORIA:
                resultado = interpretar(texto, partida)
                if isinstance(resultado, Orden):
                    return resultado
                self._salida(resultado)
            elif partes in (["salir"], ["q"]):
                return Orden(SALIR)
            elif partes == ["continuar"]:
                return None
            elif partes in (["s"], ["si"], ["sí"], ["y"], ["yes"], ["n"], ["no"]):
                # Una respuesta del flujo anterior sigue perteneciendo a la
                # siguiente confirmación de repetición/sesión, sin perderla.
                self._respuesta_final = texto
                return None
            else:
                self._salida("Usa historia <t>, historia #k, salir o Enter para continuar.")

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

    def pedir_nombre(self):
        texto = self._leer("Tu nombre: ")
        if texto is None or texto.strip() == "":
            return "Jugador"
        return texto.strip()

    def confirmar(self, pregunta):
        texto = self._respuesta_final
        self._respuesta_final = None
        if texto is None:
            texto = self._leer(pregunta + " (s/n): ")
        else:
            self._salida(pregunta + " (s/n): " + texto)
        if texto is None:
            return True
        return texto.strip().lower() in ("s", "si", "sí", "y", "yes")

    def _leer(self, indicacion):
        try:
            return self._entrada(indicacion)
        except (EOFError, KeyboardInterrupt):
            return None

    def mostrar_partida(self, partida):
        self._mostrar_reporte_inicio()
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

    def mostrar_puntajes(self, registros):
        self._salida("\nTabla de puntajes (victorias primero, luego menor tiempo y menos acciones):")
        if len(registros) == 0:
            self._salida("  (todavía no hay partidas terminadas)")
            return
        self._salida("  #  %-14s %-22s %-9s %8s %10s %8s" % (
            "Jugador", "Cripta", "Resultado", "Acciones", "Derrotados", "Tiempo"))
        i = 1
        for r in registros:
            self._salida(" %2d  %-14s %-22s %-9s %8d %10d %8d" % (
                i, r.nombre[:14], (r.id_cripta + " v" + r.version_cripta)[:22], r.resultado,
                r.acciones, r.derrotados, r.tiempo))
            i += 1

    def mostrar_aviso(self, texto):
        self._salida(texto)

    def mostrar_reporte_resolubilidad(self, reporte):
        self._salida(reporte.formatear_reporte())

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

    def _texto_salidas(self, partida):
        textos = []
        for direccion, estado, id_vecino, llave, costo in partida.salidas_visibles():
            if estado == "cerrada":
                detalle = "cerrada" + (", llave %s" % llave if llave else "")
            else:
                detalle = estado
            destino = "desconocida" if id_vecino is None else "sala %s" % id_vecino
            textos.append("%s -> %s (costo %s, %s)" % (direccion, destino, costo, detalle))
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
        comportamiento = unicodedata.normalize("NFD", str(enemigo.comportamiento or "")).strip().lower()
        comportamiento = "".join(letra for letra in comportamiento if unicodedata.category(letra) != "Mn")
        marca = " [CAZADOR]" if comportamiento == "cazador" else ""
        return "%s%s  vida %d/%d" % (enemigo.etiqueta(), marca, enemigo.vida, enemigo.vida_max)

    def _texto_objeto(self, objeto):
        return "%s (%s)  peso %s  valor %s" % (objeto.nombre, objeto.clase, objeto.peso, objeto.valor)
