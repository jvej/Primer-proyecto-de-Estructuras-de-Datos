"""Vista gráfica con Pygame (MVC, §6). Implementa vista_base.Vista, igual que la consola.

Cómo encaja sin tocar el Modelo ni el Controlador:
  - El Controlador llama pedir_orden(partida) y espera una Orden. Aquí esa llamada
    corre el bucle de la ventana (dibujar, leer teclado y ratón) hasta que el jugador
    elige una acción, y la devuelve. Es el mismo contrato que input() en la consola.
  - La vista solo LEE la partida para dibujarla. Las teclas se traducen a Orden en
    controles_gui.py (sin Pygame), así consola y ventana mandan las mismas órdenes.
  - El reloj virtual solo avanza dentro del Modelo, al ejecutar una orden. Los cuadros
    por segundo, los avisos temporales y la selección de enemigo usan tiempo real de
    la ventana y no cambian la partida: 30 o 60 FPS dan el mismo resultado.
  - Elegir enemigo u objeto, mirar el inventario, la ayuda o los puntajes no son
    órdenes de partida: no consumen tiempo ni van al log de replay.
  - Mantener una tecla pulsada NO repite la acción (solo cuenta cada pulsación).

Imágenes ("Poses personajes/"), PNG con fondo transparente, todos mirando a la derecha
(los enemigos se voltean solos para mirar al jugador):
    <personaje>.png                    imagen estática
    <personaje>_reposo_1.png, _2 ...   respiración (se repite)
    <personaje>_ataque_1.png ...       ataque
    <personaje>_dano_1.png             recibe daño
    <personaje>_muerte_1.png ...       muere (se queda en el último cuadro)
    <personaje>_correr_1.png ...       corre hacia la puerta / desde la puerta (se repite)
    jugador_abrir_1.png ...            abre una puerta con la llave (una sola versión para
                                       todas las del jugador)
    trampa_<id>_1.png ... / trampa_1.png ...   efecto de una trampa al saltar (sobre el
                                       jugador): primero el de esa trampa, si no el genérico
    fondo_menu.png                     fondo de la pantalla para escribir el nombre
    fondo_sala_1.png, _2, _3 ...       fondos de la pantalla de elegir cripta: cada vez que
                                       se abre se elige uno al azar (las salas no llevan fondo)
    objeto_<id>.png / objeto_<clase>.png   icono de un objeto del suelo: primero el de su
                                       id exacto (objeto_itm_daga.png), si no el de su clase
                                       (objeto_arma.png); si no hay ninguno, una tarjeta de texto
Personajes: jugador (manos vacías), jugador_espada (arma equipada), jugador_antorcha
(antorcha encendida), jugador_armado (arma y antorcha), guardian, errante, rastreador
y enemigo (respaldo para cualquier comportamiento desconocido).
Se eligen por comportamiento, no por id de cripta ni de catálogo (sin importar tildes ni
mayúsculas: "Guardián" de la API usa guardian.png). Si falta un cuadro
se usa la imagen estática; si falta todo, una figura simple. Nunca se cae el juego.

Animaciones (animaciones_gui.py): solo DIBUJAN resultados que el Modelo ya calculó
(quién atacó, quién perdió vida, quién murió). Usan tiempo real de la ventana, nunca
el reloj virtual, así que no cambian la partida ni el replay.
"""

import os
import random
import unicodedata

import pygame

from vista.animaciones_gui import (ABRIR_MS, ABRIR_PUERTA, ATAQUE, CORRER, CORRER_MS, DANO,
                                   DESTELLO_MS, MUERTE, REPOSO, TRAMPA, Animador, duracion,
                                   indice_de_cuadro)
from vista.controles_gui import (AYUDA_LINEAS, BOTONES, SIG_ENEMIGO, SIG_SUELO, ajustar_posicion,
                                 orden_para_tecla, siguiente_posicion)
from controlador.orden import ABRIR, ATACAR, CARGAR, MOVER, Orden, RECOGER, SALIR
from vista.vista_base import Vista

ANCHO, ALTO = 1280, 720
FPS = 30
CARPETA_SPRITES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Poses personajes")

# ------------------------------------------------------------------ colores
FONDO = (18, 15, 20)
PANEL = (34, 29, 36)
BORDE = (92, 74, 58)
TEXTO = (226, 214, 190)
TEXTO_TENUE = (150, 140, 125)
DORADO = (224, 170, 80)
SUELO_SALA = (52, 44, 40)
MURO = (78, 66, 58)
ABIERTA = (70, 150, 90)
CERRADA = (165, 60, 50)
VIDA = (190, 50, 50)
VIDA_FONDO = (70, 30, 30)
SELECCION = (250, 210, 90)
COLOR_JUGADOR = (70, 140, 80)
COLOR_GUARDIAN = (120, 140, 175)
COLOR_ERRANTE = (190, 70, 60)
COLOR_RASTREADOR = (150, 90, 200)
COLOR_ENEMIGO = (160, 160, 160)

# --------------------------------------------------------------- distribución
SALA = pygame.Rect(30, 92, 820, 430)
INVENTARIO = pygame.Rect(870, 74, 390, 300)
MENSAJES = pygame.Rect(870, 384, 390, 326)
BOTONERA_Y = 536
AVISOS_Y = 624

ALTO_SPRITE = 120
SUELO_Y = SALA.y + 230      # altura del centro de los personajes en la sala
TAMANO_ICONO = 52           # lado del icono de un objeto del suelo
MAX_ENEMIGOS_DIBUJADOS = 8
MAX_OBJETOS_DIBUJADOS = 6
DURACION_AVISO_MS = 7000
MAX_AVISOS = 6


def _fuente(tamano, negrita=False):
    return pygame.font.SysFont("consolas,dejavusansmono,menlo,couriernew", tamano, bold=negrita)


class Hoja:
    """Las imágenes de un personaje: la estática y los cuadros de cada animación."""
    __slots__ = ("estatica", "reposo", "ataque", "dano", "muerte", "correr")

    def __init__(self):
        self.estatica = None
        self.reposo = []
        self.ataque = []
        self.dano = []
        self.muerte = []
        self.correr = []

    def cuadros(self, tipo):
        if tipo == CORRER:
            return self.correr
        if tipo == ATAQUE:
            return self.ataque
        if tipo == DANO:
            return self.dano
        if tipo == MUERTE:
            return self.muerte
        return self.reposo

    def vacia(self):
        return (self.estatica is None and len(self.reposo) == 0 and len(self.ataque) == 0
                and len(self.dano) == 0 and len(self.muerte) == 0 and len(self.correr) == 0)


class Sprites:
    """Carga cada imagen una sola vez y la reutiliza. Sin diccionarios: una lista de
    pares (nombre, Hoja) con búsqueda lineal (son 8 personajes)."""

    PERSONAJES = ("jugador", "jugador_espada", "jugador_antorcha", "jugador_armado",
                  "guardian", "errante", "rastreador", "enemigo")
    # si falta la versión pedida del jugador, se usa la primera de esta lista que exista
    RESPALDO_JUGADOR = ("jugador", "jugador_espada", "jugador_antorcha", "jugador_armado")
    ANIMACIONES = (REPOSO, ATAQUE, DANO, MUERTE, CORRER)
    MAXIMO_CUADROS = 8

    def __init__(self, carpeta, alto):
        self.hojas = []
        self.avisos = []
        if not os.path.isdir(carpeta):
            self.avisos.append("Sin carpeta de sprites (%s): se usan figuras simples." % carpeta)
        for nombre in self.PERSONAJES:
            voltear = not nombre.startswith("jugador")      # los enemigos miran al jugador
            hoja = Hoja()
            hoja.estatica = self._cargar(carpeta, nombre + ".png", alto, voltear)
            for tipo in self.ANIMACIONES:
                for numero in range(1, self.MAXIMO_CUADROS + 1):
                    imagen = self._cargar(carpeta, "%s_%s_%d.png" % (nombre, tipo, numero), alto, voltear)
                    if imagen is None:
                        break
                    hoja.cuadros(tipo).append(imagen)
            self.hojas.append((nombre, hoja))
        self.abrir = []                 # jugador_abrir_N.png: una sola versión para todas
        for numero in range(1, self.MAXIMO_CUADROS + 1):
            imagen = self._cargar(carpeta, "jugador_abrir_%d.png" % numero, alto, False)
            if imagen is None:
                break
            self.abrir.append(imagen)
        self.carpeta = carpeta
        self.alto = alto
        self.iconos = []                # [(archivo, imagen o None)]: cada icono se carga una vez
        self.trampas = []               # [(id_trampa, [cuadros])]: se cargan la primera vez

    def _cargar(self, carpeta, archivo, alto, voltear):
        ruta = os.path.join(carpeta, archivo)
        if not os.path.exists(ruta):
            return None
        try:
            imagen = pygame.image.load(ruta).convert_alpha()
        except pygame.error as error:
            self.avisos.append("No se pudo cargar %s (%s): se usa otra imagen." % (ruta, error))
            return None
        ancho = max(1, imagen.get_width() * alto // max(1, imagen.get_height()))
        imagen = pygame.transform.smoothscale(imagen, (ancho, alto))
        if voltear:
            imagen = pygame.transform.flip(imagen, True, False)
        return imagen

    def hoja(self, nombre):
        """La hoja de ese personaje; si no tiene imágenes, la de respaldo:
        jugador -> la primera versión del jugador que exista; enemigo -> 'enemigo'."""
        pedida = self._buscar(nombre)
        if pedida is not None:
            return pedida
        if nombre.startswith("jugador"):
            for otro in self.RESPALDO_JUGADOR:
                hoja = self._buscar(otro)
                if hoja is not None:
                    return hoja
            return None
        return self._buscar("enemigo")

    def _buscar(self, nombre):
        for otro, hoja in self.hojas:
            if otro == nombre and not hoja.vacia():
                return hoja
        return None

    def icono(self, objeto):
        """Icono del objeto: objeto_<id>.png; si no existe, objeto_<clase>.png; si no, None."""
        imagen = self._icono("objeto_%s.png" % objeto.id)
        if imagen is None:
            imagen = self._icono("objeto_%s.png" % objeto.clase)
        return imagen

    def _icono(self, archivo):
        for otro, imagen in self.iconos:
            if otro == archivo:
                return imagen
        imagen = None
        ruta = os.path.join(self.carpeta, archivo)
        if os.path.exists(ruta):
            try:
                original = pygame.image.load(ruta).convert_alpha()
                lado = max(original.get_width(), original.get_height(), 1)
                imagen = pygame.transform.smoothscale(original, (
                    max(1, original.get_width() * TAMANO_ICONO // lado),
                    max(1, original.get_height() * TAMANO_ICONO // lado)))
            except pygame.error as error:
                self.avisos.append("No se pudo cargar %s (%s)." % (ruta, error))
        self.iconos.append((archivo, imagen))
        return imagen

    def cuadro_trampa(self, id_trampa, transcurrido):
        """Cuadro del efecto de la trampa: trampa_<id>_N.png o, si no hay, trampa_N.png."""
        cuadros = self._cuadros_trampa(id_trampa)
        if len(cuadros) == 0:
            cuadros = self._cuadros_trampa("")
        i = indice_de_cuadro(TRAMPA, transcurrido, len(cuadros))
        return cuadros[i] if i >= 0 else None

    def _cuadros_trampa(self, id_trampa):
        for otro, cuadros in self.trampas:
            if otro == id_trampa:
                return cuadros
        prefijo = "trampa_%s_" % id_trampa if id_trampa else "trampa_"
        cuadros = []
        for numero in range(1, self.MAXIMO_CUADROS + 1):
            imagen = self._cargar(self.carpeta, "%s%d.png" % (prefijo, numero), self.alto, False)
            if imagen is None:
                break
            cuadros.append(imagen)
        self.trampas.append((id_trampa, cuadros))
        return cuadros

    def imagen(self, nombre, tipo, transcurrido):
        """El cuadro que toca ahora, o None si ese personaje no tiene ninguna imagen."""
        if tipo == ABRIR_PUERTA:
            i = indice_de_cuadro(tipo, transcurrido, len(self.abrir))
            if i >= 0:
                return self.abrir[i]
            tipo = REPOSO                   # sin cuadros de abrir: se queda en reposo
        hoja = self.hoja(nombre)
        if hoja is None:
            return None
        cuadros = hoja.cuadros(tipo)
        i = indice_de_cuadro(tipo, transcurrido, len(cuadros))
        if i >= 0:
            return cuadros[i]
        if hoja.estatica is not None:
            return hoja.estatica
        if len(hoja.reposo) > 0:
            return hoja.reposo[0]
        return None


class VistaPygame(Vista):
    def __init__(self, carpeta_sprites=CARPETA_SPRITES, fps=FPS):
        pygame.init()
        pygame.display.set_caption("CRIPTA")
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()
        self.fps = fps
        self.fuente = _fuente(16)
        self.fuente_chica = _fuente(13)
        self.fuente_media = _fuente(20, True)
        self.fuente_grande = _fuente(34, True)
        self.sprites = Sprites(carpeta_sprites, ALTO_SPRITE)
        self.animador = Animador()
        self.ultima_orden = None        # tipo de la última orden entregada (para animar)
        self.centros = []               # [(actor, (x, y))] dónde se dibujó cada actor
        self.halo = self._crear_halo()
        self.fondo_menu, self.fondos_nivel = self._cargar_fondos(carpeta_sprites)
        self.fondo_nivel = None         # el fondo elegido al azar para la pantalla de criptas
        self.azar = random.Random()     # propio de la vista: no toca el azar del Modelo
        self.saliendo = None            # (dirección, inicio_ms) mientras corre hacia una puerta
        self.volver_de = None           # puerta recién abierta: el jugador vuelve corriendo
        self.entrando_por = None        # dirección de la puerta por la que acaba de entrar
        self.abriendo = None            # (dirección, inicio_ms) mientras usa la llave
        self.destello = None            # (dirección, inicio_ms) brillo de la puerta abierta
        self.partida = None
        self.fin = None                 # partida terminada cuyo resumen se muestra
        self.resumen_fin = []
        self.enemigo_elegido = 0
        self.objeto_elegido = 0
        self.avisos = []                # [texto, instante_real_en_que_desaparece]
        self.zonas = []                 # [(rect, accion)] zonas clicables del cuadro actual
        self.resaltar_inventario_hasta = 0
        self.cerrada = False
        for texto in self.sprites.avisos:
            self.mostrar_aviso(texto)

    # ================================================================ entrada
    def elegir_cripta(self, criptas):
        self.partida = None
        self.fin = None
        self.animador.reiniciar()
        self.fondo_nivel = None
        if len(self.fondos_nivel) > 0:              # uno distinto al azar cada vez
            self.fondo_nivel = self.fondos_nivel[self.azar.randrange(len(self.fondos_nivel))]
        elegida = 0
        while not self.cerrada:
            for evento in self._eventos():
                if evento.type == pygame.KEYDOWN:
                    tecla = pygame.key.name(evento.key)
                    if tecla == "escape":
                        return None
                    if tecla == "up":
                        elegida = (elegida - 1) % max(1, len(criptas))
                    elif tecla == "down":
                        elegida = siguiente_posicion(elegida, len(criptas))
                    elif tecla in ("return", "enter", "space") and len(criptas) > 0:
                        return self._cripta_elegida(criptas[elegida])
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    accion = self._zona_en(evento.pos)
                    if accion is not None and accion[0] == "cripta":
                        return self._cripta_elegida(criptas[accion[1]])
            self._dibujar_menu(criptas, elegida)
            self._mostrar_cuadro()
        return None

    def _cripta_elegida(self, cripta):
        self._dibujar_cargando("Cargando %s..." % cripta.get("nombre", cripta.get("id")))
        return cripta.get("id")

    def pedir_orden(self, partida):
        self.partida = partida
        self.fin = None
        while not self.cerrada:
            for evento in self._eventos():
                resultado = None
                if evento.type == pygame.KEYDOWN:
                    shift = bool(evento.mod & pygame.KMOD_SHIFT)
                    resultado = orden_para_tecla(pygame.key.name(evento.key), shift,
                                                 self.enemigo_elegido, self.objeto_elegido)
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    resultado = self._clic_en_partida(evento.pos)
                orden = self._aplicar_seleccion(resultado, partida)
                if orden is not None:
                    return self._entregar(orden)
            self._dibujar_partida(partida)
            self._mostrar_cuadro()
        return Orden(SALIR)

    def _aplicar_seleccion(self, resultado, partida):
        """Las selecciones solo cambian lo que se dibuja; las órdenes pasan tal cual."""
        if resultado == SIG_ENEMIGO:
            self.enemigo_elegido = siguiente_posicion(self.enemigo_elegido,
                                                      len(partida.enemigos_en_sala()))
            return None
        if resultado == SIG_SUELO:
            self.objeto_elegido = siguiente_posicion(self.objeto_elegido,
                                                     len(partida.objetos_en_sala()))
            return None
        return resultado

    def _clic_en_partida(self, posicion):
        accion = self._zona_en(posicion)
        if accion is None:
            return None
        if accion[0] == "tecla":
            return orden_para_tecla(accion[1], False, self.enemigo_elegido, self.objeto_elegido)
        if accion[0] == "puerta":
            return Orden(ABRIR if accion[2] == "cerrada" else MOVER, accion[1])
        if accion[0] == "enemigo":          # primer clic elige, segundo clic ataca
            if self.enemigo_elegido == accion[1]:
                return Orden(ATACAR, accion[1])
            self.enemigo_elegido = accion[1]
            return None
        if accion[0] == "suelo":            # primer clic elige, segundo clic recoge
            if self.objeto_elegido == accion[1]:
                return Orden(RECOGER, accion[1])
            self.objeto_elegido = accion[1]
        return None

    def _entregar(self, orden):
        """Antes de devolver una orden que puede esperar a la red (entrar a una sala nueva,
        cargar), se deja dibujado un aviso: la espera es de tiempo real, no virtual."""
        self.ultima_orden = orden.tipo
        if orden.tipo == MOVER:
            self._correr_hacia(orden.argumento)
            self.entrando_por = _opuesta(orden.argumento)
            self._dibujar_cargando("Entrando...", sobre_partida=True)
        elif orden.tipo == ABRIR:
            self._abrir_puerta(orden.argumento)
        elif orden.tipo == CARGAR:
            self._dibujar_cargando("Cargando partida...", sobre_partida=True)
        return orden

    def _correr_hacia(self, direccion):
        """Antes de entregar MOVER, el jugador corre hasta la puerta (solo dibujo, tiempo
        real). Si la salida no existe o está cerrada no corre: el Modelo la rechazará."""
        if self.partida is None or self._salida(direccion) not in ("abierta",):
            return
        self.saliendo = (direccion, pygame.time.get_ticks())
        self._esperar_dibujando(self.saliendo[1], CORRER_MS)
        self.saliendo = None

    def _abrir_puerta(self, direccion):
        """Antes de entregar ABRIR: corre hasta la puerta y usa la llave (solo dibujo).
        Solo se anima si la puerta está cerrada y el jugador lleva la llave que la abre;
        si no, el Modelo rechazará la orden con su mensaje y aquí no se dibuja nada."""
        if self.partida is None:
            return
        estado, llave = self._salida(direccion, con_llave=True)
        if estado != "cerrada" or llave is None or not self._lleva_llave(llave):
            return
        self.saliendo = (direccion, pygame.time.get_ticks())
        self._esperar_dibujando(self.saliendo[1], CORRER_MS)
        self.saliendo = None
        self.abriendo = (direccion, pygame.time.get_ticks())
        self._esperar_dibujando(self.abriendo[1], ABRIR_MS)
        self.abriendo = None
        self.destello = (direccion, pygame.time.get_ticks())
        self.volver_de = direccion              # al mostrar la partida, corre de vuelta

    def _esperar_dibujando(self, inicio, duracion_ms):
        while not self.cerrada and pygame.time.get_ticks() - inicio < duracion_ms:
            if len(pygame.event.get(pygame.QUIT)) > 0:   # las teclas quedan en cola, no se pierden
                self.cerrada = True
            self._dibujar_partida(self.partida)
            self._mostrar_cuadro()

    def _salida(self, direccion, con_llave=False):
        """Estado de la salida en esa dirección ('abierta' / 'cerrada' / None si no hay)."""
        for otra, estado, _vecino, llave in self.partida.salidas_visibles():
            if otra == direccion:
                return (estado, llave) if con_llave else estado
        return (None, None) if con_llave else None

    def _lleva_llave(self, id_llave):
        """Misma regla que el Modelo para saber si una llave abre la puerta (solo lectura)."""
        for objeto in self.partida.inventario.objetos():
            if objeto.clase == "llave" and (objeto.id == id_llave or objeto.abre == id_llave):
                return True
        return False

    def pedir_nombre(self):
        texto = ""
        while not self.cerrada:
            for evento in self._eventos():
                if evento.type != pygame.KEYDOWN:
                    continue
                tecla = pygame.key.name(evento.key)
                if tecla in ("return", "enter"):
                    return texto.strip() if texto.strip() != "" else "Jugador"
                if tecla == "escape":
                    return "Jugador"
                if tecla == "backspace":
                    texto = texto[:-1]
                elif evento.unicode and evento.unicode.isprintable() and len(texto) < 16:
                    texto += evento.unicode
            self._pintar_fondo(self.fondo_menu)
            self._texto(self.fuente_grande, "CRIPTA", DORADO, ANCHO // 2, 200, centro=True)
            self._texto(self.fuente_media, "Escribe tu nombre y pulsa Enter", TEXTO,
                        ANCHO // 2, 300, centro=True)
            caja = pygame.Rect(ANCHO // 2 - 200, 340, 400, 48)
            pygame.draw.rect(self.pantalla, PANEL, caja)
            pygame.draw.rect(self.pantalla, DORADO, caja, 2)
            self._texto(self.fuente_media, texto + "_", TEXTO, caja.x + 14, caja.y + 12)
            self._mostrar_cuadro()
        return "Jugador"

    def confirmar(self, pregunta):
        if self.cerrada:
            return True
        botones = (("s", "Sí (S)"), ("n", "No (N)"))
        while not self.cerrada:
            for evento in self._eventos():
                if evento.type == pygame.KEYDOWN:
                    tecla = pygame.key.name(evento.key)
                    if tecla in ("s", "y", "return", "enter"):
                        return True
                    if tecla in ("n", "escape"):
                        return False
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    accion = self._zona_en(evento.pos)
                    if accion is not None and accion[0] == "tecla":
                        return accion[1] == "s"
            self._dibujar_fondo_de_dialogo()
            caja = self._caja_centrada(560, 150 if self.fin is None else 120,
                                       ALTO // 2 + (0 if self.fin is None else 210))
            self._texto(self.fuente_media, pregunta, TEXTO, caja.centerx, caja.y + 24, centro=True)
            x = caja.centerx - 150
            for tecla, etiqueta in botones:
                self._boton(pygame.Rect(x, caja.bottom - 58, 130, 38), etiqueta, tecla)
                x += 170
            self._mostrar_cuadro()
        return True

    # ================================================================ salida
    def mostrar_partida(self, partida):
        if partida is not self.partida:             # partida nueva o cargada: sin animar
            self.animador.reiniciar(partida)
        else:
            self.animador.observar(partida, pygame.time.get_ticks(), self.ultima_orden, self.centros)
        if self.volver_de is not None:              # vuelve corriendo desde la puerta que abrió
            self.entrando_por = self.volver_de
            self.animador.correr(partida.jugador, pygame.time.get_ticks())
            self.volver_de = None
        self.ultima_orden = None
        self.partida = partida
        self.enemigo_elegido = ajustar_posicion(self.enemigo_elegido, len(partida.enemigos_en_sala()))
        self.objeto_elegido = ajustar_posicion(self.objeto_elegido, len(partida.objetos_en_sala()))

    def mostrar_inventario(self, partida):
        self.partida = partida
        self.resaltar_inventario_hasta = pygame.time.get_ticks() + 700

    def mostrar_vista_ordenada(self, criterio, descendente, pares):
        lineas = ["El orden real del inventario no cambia; los números son los reales.", ""]
        for posicion, objeto in pares:
            lineas.append("%2d) %s" % (posicion + 1, self._texto_objeto(objeto)))
        if len(pares) == 0:
            lineas.append("(vacío)")
        self._modal("Inventario por %s (%s)" % (criterio, "descendente" if descendente else "ascendente"),
                    lineas)

    def mostrar_puntajes(self, registros):
        lineas = ["Victorias primero, luego menor tiempo y menos acciones.", ""]
        if len(registros) == 0:
            lineas.append("(todavía no hay partidas terminadas)")
        else:
            lineas.append(" #  %-12s %-12s %-9s %8s %6s %7s" % (
                "Jugador", "Cripta", "Resultado", "Acciones", "Derr.", "Tiempo"))
        i = 1
        for r in registros:
            lineas.append("%2d  %-12s %-12s %-9s %8d %6d %7d" % (
                i, r.nombre[:12], r.id_cripta[:12], r.resultado, r.acciones, r.derrotados, r.tiempo))
            i += 1
            if i > 15:
                break
        self._modal("Tabla de puntajes", lineas)

    def mostrar_aviso(self, texto):
        print(texto)                    # también en la consola, por si la ventana se cierra
        fin = pygame.time.get_ticks() + DURACION_AVISO_MS
        for linea in str(texto).splitlines():
            if linea.strip() == "":
                continue
            self.avisos.append([linea, fin])
            if self.fin is not None:    # el resumen final no se borra con el tiempo
                self.resumen_fin.append(linea)
        while len(self.avisos) > MAX_AVISOS:
            self.avisos.pop(0)

    def mostrar_ayuda(self):
        self._modal("Controles", list(AYUDA_LINEAS))

    def mostrar_fin(self, partida):
        self.partida = partida
        self.fin = partida
        self.resumen_fin = []           # lo que avise la aplicación al terminar (puntaje, log)

    def cerrar(self):
        """Antes de cerrar la ventana, si quedó algún aviso (por ejemplo un error al
        cargar las criptas) se muestra para que no se pierda."""
        if not self.cerrada and self.partida is None and len(self.avisos) > 0:
            lineas = []
            for texto, _fin in self.avisos:
                lineas.append(texto)
            self._modal("Aviso", lineas)
        pygame.quit()

    # ============================================================ eventos y cuadro
    def _eventos(self):
        eventos = pygame.event.get()
        for evento in eventos:
            if evento.type == pygame.QUIT:
                self.cerrada = True
        return eventos

    def _mostrar_cuadro(self):
        pygame.display.flip()
        self.reloj.tick(self.fps)

    def _zona_en(self, posicion):
        for rect, accion in self.zonas:
            if rect.collidepoint(posicion):
                return accion
        return None

    def _modal(self, titulo, lineas):
        """Ventana encima del juego hasta que se pulse una tecla o se haga clic."""
        while not self.cerrada:
            for evento in self._eventos():
                if evento.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    return
            self._dibujar_fondo_de_dialogo()
            alto = min(ALTO - 80, 110 + 22 * len(lineas))
            caja = self._caja_centrada(820, alto, ALTO // 2)
            self._texto(self.fuente_media, titulo, DORADO, caja.centerx, caja.y + 18, centro=True)
            y = caja.y + 58
            for linea in lineas:
                if y > caja.bottom - 40:
                    break
                self._texto(self.fuente, linea, TEXTO, caja.x + 28, y, ancho_max=caja.w - 56)
                y += 22
            self._texto(self.fuente_chica, "Pulsa cualquier tecla para volver", TEXTO_TENUE,
                        caja.centerx, caja.bottom - 26, centro=True)
            self._mostrar_cuadro()

    # ================================================================ dibujo
    def _dibujar_menu(self, criptas, elegida):
        self.zonas = []
        self._pintar_fondo(self.fondo_nivel)
        self._texto(self.fuente_grande, "CRIPTA", DORADO, ANCHO // 2, 90, centro=True)
        self._texto(self.fuente, "Elige una cripta (flechas y Enter, o clic). Esc: salir",
                    TEXTO_TENUE, ANCHO // 2, 150, centro=True)
        y = 210
        for i in range(len(criptas)):
            cripta = criptas[i]
            rect = pygame.Rect(ANCHO // 2 - 330, y, 660, 64)
            pygame.draw.rect(self.pantalla, PANEL, rect)
            pygame.draw.rect(self.pantalla, SELECCION if i == elegida else BORDE, rect, 3 if i == elegida else 1)
            self._texto(self.fuente_media, "%s" % cripta.get("nombre", cripta.get("id")), TEXTO,
                        rect.x + 20, rect.y + 10)
            self._texto(self.fuente, "%s  ·  %s salas  ·  dificultad %s" % (
                cripta.get("id"), cripta.get("salas", "?"), cripta.get("dificultad", "?")),
                TEXTO_TENUE, rect.x + 20, rect.y + 38)
            self.zonas.append((rect, ("cripta", i)))
            y += 78
        self._dibujar_avisos(ANCHO // 2 - 330, y + 20)

    def _dibujar_partida(self, partida):
        self.zonas = []
        self.centros = []
        self.animador.limpiar(pygame.time.get_ticks())
        self.pantalla.fill(FONDO)
        self._dibujar_barra_superior(partida)
        self._dibujar_sala(partida)
        self._dibujar_inventario(partida)
        self._dibujar_mensajes(partida)
        self._dibujar_botonera()
        self._dibujar_avisos(SALA.x, AVISOS_Y)

    def _dibujar_barra_superior(self, partida):
        jugador = partida.jugador
        sala = partida.sala_actual()
        pygame.draw.rect(self.pantalla, PANEL, pygame.Rect(0, 0, ANCHO, 64))
        pygame.draw.line(self.pantalla, BORDE, (0, 64), (ANCHO, 64), 2)
        self._texto(self.fuente_media, "Sala %s: %s" % (sala.id, sala.nombre or "sin nombre"),
                    DORADO, 20, 10)
        self._texto(self.fuente, "Tiempo %d   ·   Acciones %d   ·   %s" % (
            partida.reloj.tiempo_actual, partida.acciones, partida.id_cripta), TEXTO_TENUE, 20, 38)
        self._barra_vida(pygame.Rect(560, 12, 220, 18), jugador.vida, jugador.vida_max)
        self._texto(self.fuente, "Vida %d/%d" % (jugador.vida, jugador.vida_max), TEXTO, 790, 12)
        self._texto(self.fuente, "Ataque %d   Defensa %d" % (
            jugador.ataque_efectivo(), jugador.defensa_efectivo()), TEXTO, 560, 38)
        self._texto(self.fuente, "Arma: %s" % (jugador.arma.nombre if jugador.arma else "-"),
                    TEXTO, 910, 12, ancho_max=350)
        self._texto(self.fuente, "Armadura: %s" % (jugador.armadura.nombre if jugador.armadura else "-"),
                    TEXTO, 910, 38, ancho_max=350)

    def _dibujar_sala(self, partida):
        pygame.draw.rect(self.pantalla, SUELO_SALA, SALA)
        pygame.draw.rect(self.pantalla, MURO, SALA, 10)
        efectos = partida.efectos_activos()
        if len(efectos) > 0:
            self._texto(self.fuente, "Efectos: " + ", ".join(efectos), DORADO, SALA.x, SALA.y - 22)
        for direccion, estado, id_vecino, llave in partida.salidas_visibles():
            self._dibujar_puerta(direccion, estado, id_vecino, llave)
        y = SALA.y + 20
        for trampa in partida.trampas_en_sala():
            self._texto(self.fuente_chica, "Trampa: %s (%s)" % (
                trampa.nombre, "armada" if trampa.armada else "desarmada"), CERRADA, SALA.x + 22, y)
            y += 18
        jugador = partida.jugador
        centro_jugador, hacia = self._posicion_jugador(jugador)
        if jugador.antorcha_encendida:              # la antorcha se ve como un halo de luz
            self.pantalla.blit(self.halo, self.halo.get_rect(center=centro_jugador))
        self._dibujar_actor(jugador, self._version_jugador(jugador), COLOR_JUGADOR,
                            centro_jugador, "Tú", False, hacia)
        self._dibujar_trampas_activas(jugador, centro_jugador)
        self._dibujar_enemigos(partida.enemigos_en_sala())
        self._dibujar_caidos()
        self._dibujar_numeros()
        self._dibujar_suelo(partida.objetos_en_sala())

    def _dibujar_trampas_activas(self, jugador, centro):
        """Efecto de la trampa que acaba de saltar, encima del jugador (solo dibujo)."""
        for actor, id_trampa, transcurrido in self.animador.efectos_trampa(pygame.time.get_ticks()):
            if actor is not jugador:
                continue
            imagen = self.sprites.cuadro_trampa(id_trampa, transcurrido)
            if imagen is not None:
                self.pantalla.blit(imagen, imagen.get_rect(center=centro))
            else:                                   # sin imágenes: un destello rojo
                rect = pygame.Rect(0, 0, 110, 120)
                rect.center = centro
                self._destello(rect)

    def _posicion_jugador(self, jugador):
        """Dónde se dibuja el jugador y hacia dónde mira (1 derecha, -1 izquierda).
        Al salir corre del centro a la puerta; al entrar, de la puerta al centro."""
        centro = (SALA.x + 170, SUELO_Y)
        ahora = pygame.time.get_ticks()
        if self.abriendo is not None:               # junto a la puerta, usando la llave
            puerta = _punto_de_puerta(self.abriendo[0])
            return puerta, (-1 if puerta[0] < centro[0] else 1)
        if self.saliendo is not None:
            puerta = _punto_de_puerta(self.saliendo[0])
            avance = min(1.0, (ahora - self.saliendo[1]) / CORRER_MS)
            return _entre(centro, puerta, avance), (-1 if puerta[0] < centro[0] else 1)
        tipo, transcurrido = self.animador.estado(jugador, ahora)
        if tipo == CORRER and self.entrando_por is not None:
            puerta = _punto_de_puerta(self.entrando_por)
            avance = min(1.0, transcurrido / CORRER_MS)
            return _entre(puerta, centro, avance), (-1 if centro[0] < puerta[0] else 1)
        return centro, 1

    def _version_jugador(self, jugador):
        """Qué imagen del jugador usar según lo que lleva: arma equipada y/o antorcha encendida."""
        con_arma = jugador.arma is not None
        if con_arma and jugador.antorcha_encendida:
            return "jugador_armado"
        if con_arma:
            return "jugador_espada"
        if jugador.antorcha_encendida:
            return "jugador_antorcha"
        return "jugador"

    def _dibujar_puerta(self, direccion, estado, id_vecino, llave):
        color = ABIERTA if estado != "cerrada" else CERRADA
        if direccion == "N":
            rect = pygame.Rect(SALA.centerx - 50, SALA.y - 6, 100, 22)
            etiqueta = (rect.centerx, rect.bottom + 6)
        elif direccion == "S":
            rect = pygame.Rect(SALA.centerx - 50, SALA.bottom - 16, 100, 22)
            etiqueta = (rect.centerx, rect.y - 20)
        elif direccion == "E":
            rect = pygame.Rect(SALA.right - 16, SALA.centery - 50, 22, 100)
            etiqueta = (rect.x - 70, rect.centery - 8)
        else:
            rect = pygame.Rect(SALA.x - 6, SALA.centery - 50, 22, 100)
            etiqueta = (rect.right + 70, rect.centery - 8)
        if (self.destello is not None and self.destello[0] == direccion and estado != "cerrada"
                and pygame.time.get_ticks() - self.destello[1] < DESTELLO_MS):
            brillo = rect.inflate(30, 30)                 # la puerta recién abierta brilla
            velo = pygame.Surface((brillo.w, brillo.h), pygame.SRCALPHA)
            velo.fill((250, 210, 90, 110))
            self.pantalla.blit(velo, brillo)
        pygame.draw.rect(self.pantalla, color, rect)
        pygame.draw.rect(self.pantalla, TEXTO, rect, 1)
        texto = "%s: sala %s" % (direccion, id_vecino)
        if estado == "cerrada":
            texto += " (cerrada)"
        self._texto(self.fuente_chica, texto, TEXTO, etiqueta[0], etiqueta[1], centro=True)
        if estado == "cerrada" and llave:
            self._texto(self.fuente_chica, "llave: %s" % llave, TEXTO_TENUE,
                        etiqueta[0], etiqueta[1] + 15, centro=True)
        self.zonas.append((rect.inflate(16, 16), ("puerta", direccion, estado)))

    def _dibujar_enemigos(self, enemigos):
        for i in _orden_de_dibujo(min(len(enemigos), MAX_ENEMIGOS_DIBUJADOS)):
            enemigo = enemigos[i]
            columna = i % 4
            fila = i // 4                       # la segunda fila queda detrás, más arriba
            centro = (SALA.x + 400 + columna * 122 + fila * 61, SUELO_Y - fila * 70)
            tipo = _tipo_de_enemigo(enemigo.comportamiento)
            color = self._color_de(tipo)
            rect = self._dibujar_actor(enemigo, tipo, color, centro,
                                       _acortar_ids(enemigo.etiqueta()), i == self.enemigo_elegido, -1)
            self.zonas.append((rect, ("enemigo", i)))
        if len(enemigos) > MAX_ENEMIGOS_DIBUJADOS:
            self._texto(self.fuente_chica, "+%d enemigos más" % (len(enemigos) - MAX_ENEMIGOS_DIBUJADOS),
                        TEXTO, SALA.right - 160, SALA.y + 20)
            
    def _dibujar_actor(self, actor, nombre_sprite, color, centro, etiqueta, elegido, hacia):
        """hacia: 1 si mira a la derecha (jugador), -1 si mira a la izquierda (enemigos)."""
        self.centros.append((actor, centro))
        ahora = pygame.time.get_ticks()
        tipo, transcurrido = self.animador.estado(actor, ahora)
        if self.saliendo is not None and actor is self.partida.jugador:
            tipo, transcurrido = CORRER, ahora - self.saliendo[1]
        if self.abriendo is not None and actor is self.partida.jugador:
            tipo, transcurrido = ABRIR_PUERTA, ahora - self.abriendo[1]
        dibujo = centro
        if tipo == ATAQUE and transcurrido < duracion(ATAQUE):    # embestida hacia el rival
            dibujo = (centro[0] + hacia * 16, centro[1])
        voltear = hacia < 0 and nombre_sprite.startswith("jugador")
        rect = self._dibujar_cuerpo(nombre_sprite, color, dibujo, tipo, transcurrido, voltear)
        if elegido:
            pygame.draw.rect(self.pantalla, SELECCION, rect.inflate(12, 12), 3)
            self._texto(self.fuente_chica, "objetivo", SELECCION, rect.centerx, rect.y - 34, centro=True)
        self._texto(self.fuente_chica, etiqueta, TEXTO, centro[0], rect.bottom + 6,
                    centro=True, ancho_max=116)
        self._barra_vida(pygame.Rect(centro[0] - 40, rect.bottom + 24, 80, 7), actor.vida, actor.vida_max)
        return rect.inflate(20, 50)

    def _dibujar_cuerpo(self, nombre_sprite, color, centro, tipo, transcurrido, voltear=False):
        """El sprite del cuadro que toca o, si no hay imágenes, la figura provisional.
        voltear: el jugador mira a la izquierda (corre hacia la puerta oeste)."""
        imagen = self.sprites.imagen(nombre_sprite, tipo, transcurrido)
        if imagen is not None and voltear:
            imagen = pygame.transform.flip(imagen, True, False)
        if imagen is not None:
            rect = imagen.get_rect(center=centro)
            self.pantalla.blit(imagen, rect)
            if tipo == DANO and len(self.sprites.hoja(nombre_sprite).dano) == 0:
                self._destello(rect)                # sin cuadro de daño: destello rojo
            return rect
        rect = pygame.Rect(0, 0, 70, 70)
        rect.center = centro
        if tipo == MUERTE:
            rect = pygame.Rect(rect.x - 10, rect.bottom - 24, 90, 24)     # figura "tendida"
            pygame.draw.rect(self.pantalla, TEXTO_TENUE, rect)
            return rect
        self._figura(nombre_sprite, VIDA if tipo == DANO else color, rect)
        return rect

    def _dibujar_caidos(self):
        """Enemigos que acaban de morir: su animación de muerte en el último lugar donde estaban."""
        ahora = pygame.time.get_ticks()
        for actor, centro, transcurrido in self.animador.fantasmas(ahora):
            tipo = _tipo_de_enemigo(actor.comportamiento)
            self._dibujar_cuerpo(tipo, self._color_de(tipo), centro, MUERTE, transcurrido)

    def _dibujar_numeros(self):
        """Daño recibido flotando hacia arriba sobre quien lo recibió."""
        ahora = pygame.time.get_ticks()
        for actor, centro, cantidad, transcurrido in self.animador.numeros(ahora):
            if centro is None:
                for otro, lugar in self.centros:
                    if otro is actor:
                        centro = lugar
            if centro is None:
                continue
            subida = transcurrido * 50 // 900
            self._texto(self.fuente_media, "-%d" % cantidad, VIDA, centro[0], centro[1] - 70 - subida,
                        centro=True)

    def _destello(self, rect):
        velo = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        velo.fill((220, 40, 40, 90))
        self.pantalla.blit(velo, rect)

    def _cargar_fondos(self, carpeta):
        """fondo_menu.png (nombre) y fondo_sala_N.png (elegir cripta), a pantalla completa.
        Se escalan una sola vez, recortando lo que sobre para no deformarlos."""
        menu = _cargar_cubriendo(os.path.join(carpeta, "fondo_menu.png"), ANCHO, ALTO)
        niveles = []
        for numero in range(1, 21):
            fondo = _cargar_cubriendo(os.path.join(carpeta, "fondo_sala_%d.png" % numero),
                                      ANCHO, ALTO)
            if fondo is None:
                break
            niveles.append(fondo)
        return menu, niveles

    def _pintar_fondo(self, fondo):
        """Fondo de una pantalla de menú, oscurecido para que el texto se lea."""
        if fondo is None:
            self.pantalla.fill(FONDO)
            return
        self.pantalla.blit(fondo, (0, 0))
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((0, 0, 0, 140))
        self.pantalla.blit(velo, (0, 0))

    def _crear_halo(self):
        halo = pygame.Surface((240, 240), pygame.SRCALPHA)
        for radio, alfa in ((120, 25), (95, 35), (70, 45)):
            pygame.draw.circle(halo, (255, 160, 60, alfa), (120, 120), radio)
        return halo

    def _figura(self, nombre, color, rect):
        """Figura provisional según el comportamiento (o el jugador)."""
        if nombre == "jugador" or nombre == "rastreador":
            pygame.draw.circle(self.pantalla, color, rect.center, rect.w // 2)
        elif nombre == "guardian":
            pygame.draw.rect(self.pantalla, color, rect)
        elif nombre == "errante":
            pygame.draw.polygon(self.pantalla, color,
                                ((rect.centerx, rect.y), (rect.right, rect.bottom), (rect.x, rect.bottom)))
        else:
            pygame.draw.polygon(self.pantalla, color, ((rect.centerx, rect.y), (rect.right, rect.centery),
                                                       (rect.centerx, rect.bottom), (rect.x, rect.centery)))
        pygame.draw.rect(self.pantalla, FONDO, rect, 1)

    def _dibujar_suelo(self, objetos):
        """Objetos del suelo: el nombre arriba y el icono debajo (o la clase en texto si no
        hay icono). Primer clic elige, segundo clic recoge."""
        if len(objetos) == 0:
            return
        self._texto(self.fuente_chica, "En el suelo (F o clic: elegir · G o 2º clic: recoger)",
                    TEXTO_TENUE, SALA.x + 30, SALA.bottom - 110)
        for i in range(min(len(objetos), MAX_OBJETOS_DIBUJADOS)):
            objeto = objetos[i]
            rect = pygame.Rect(SALA.x + 30 + i * 128, SALA.bottom - 92, 118, 80)
            pygame.draw.rect(self.pantalla, PANEL, rect)
            pygame.draw.rect(self.pantalla, SELECCION if i == self.objeto_elegido else BORDE, rect,
                             3 if i == self.objeto_elegido else 1)
            self._texto(self.fuente_chica, objeto.nombre, TEXTO, rect.centerx, rect.y + 6,
                        centro=True, ancho_max=110)
            icono = self.sprites.icono(objeto)
            if icono is not None:
                self.pantalla.blit(icono, icono.get_rect(center=(rect.centerx, rect.y + 48)))
            else:
                self._texto(self.fuente_chica, objeto.clase, TEXTO_TENUE, rect.centerx, rect.y + 40,
                            centro=True, ancho_max=110)
            self.zonas.append((rect, ("suelo", i)))
        if len(objetos) > MAX_OBJETOS_DIBUJADOS:
            self._texto(self.fuente_chica, "+%d más (F)" % (len(objetos) - MAX_OBJETOS_DIBUJADOS),
                        TEXTO, SALA.right - 110, SALA.bottom - 60)

    def _dibujar_inventario(self, partida):
        inventario = partida.inventario
        jugador = partida.jugador
        resaltado = pygame.time.get_ticks() < self.resaltar_inventario_hasta
        pygame.draw.rect(self.pantalla, PANEL, INVENTARIO)
        pygame.draw.rect(self.pantalla, SELECCION if resaltado else BORDE, INVENTARIO, 2 if resaltado else 1)
        self._texto(self.fuente_media, "Inventario %d/%d" % (len(inventario), inventario.capacidad),
                    DORADO, INVENTARIO.x + 14, INVENTARIO.y + 10)
        self._texto(self.fuente_chica, "W/S: cursor   U: usar   Q: equipar   T: soltar",
                    TEXTO_TENUE, INVENTARIO.x + 14, INVENTARIO.y + 38)
        actual = inventario.objeto_actual()
        objetos = list(inventario.objetos())
        posicion_cursor = 0
        for i in range(len(objetos)):
            if objetos[i] is actual:
                posicion_cursor = i
        filas = 10
        inicio = 0 if len(objetos) <= filas else min(max(0, posicion_cursor - filas // 2), len(objetos) - filas)
        y = INVENTARIO.y + 62
        for i in range(inicio, min(len(objetos), inicio + filas)):
            objeto = objetos[i]
            if objeto is actual:
                pygame.draw.rect(self.pantalla, (60, 50, 40), pygame.Rect(INVENTARIO.x + 6, y - 2, INVENTARIO.w - 12, 22))
            equipado = "[E] " if (objeto is jugador.arma or objeto is jugador.armadura) else ""
            marca = ">" if objeto is actual else " "
            self._texto(self.fuente_chica, "%s %2d) %s%s" % (marca, i + 1, equipado, self._texto_objeto(objeto)),
                        SELECCION if objeto is actual else TEXTO, INVENTARIO.x + 10, y,
                        ancho_max=INVENTARIO.w - 20)
            y += 23
        if len(objetos) == 0:
            self._texto(self.fuente, "(vacío)", TEXTO_TENUE, INVENTARIO.x + 14, y)

    def _dibujar_mensajes(self, partida):
        pygame.draw.rect(self.pantalla, PANEL, MENSAJES)
        pygame.draw.rect(self.pantalla, BORDE, MENSAJES, 1)
        self._texto(self.fuente_media, "Últimos mensajes", DORADO, MENSAJES.x + 14, MENSAJES.y + 8)
        mensajes = partida.bitacora.ultimos()
        y = MENSAJES.y + 38
        for i in range(max(0, len(mensajes) - 20), len(mensajes)):     # los 20 más recientes
            color = TEXTO if i >= len(mensajes) - 3 else TEXTO_TENUE
            self._texto(self.fuente_chica, _acortar_ids(mensajes[i]), color, MENSAJES.x + 10, y,
                        ancho_max=MENSAJES.w - 20)
            y += 14

    def _dibujar_botonera(self):
        x = SALA.x
        y = BOTONERA_Y
        for i in range(len(BOTONES)):
            tecla, etiqueta = BOTONES[i]
            self._boton(pygame.Rect(x, y, 130, 36), etiqueta, tecla)
            x += 138
            if i == 5:
                x = SALA.x
                y += 42

    def _boton(self, rect, etiqueta, tecla):
        pygame.draw.rect(self.pantalla, PANEL, rect)
        pygame.draw.rect(self.pantalla, BORDE, rect, 1)
        self._texto(self.fuente, etiqueta, TEXTO, rect.centerx, rect.y + 9, centro=True)
        self.zonas.append((rect, ("tecla", tecla)))

    def _dibujar_avisos(self, x, y):
        ahora = pygame.time.get_ticks()
        vigentes = []
        for aviso in self.avisos:
            if aviso[1] > ahora:
                vigentes.append(aviso)
        self.avisos = vigentes
        for texto, _fin in self.avisos:
            self._texto(self.fuente_chica, texto, DORADO, x, y, ancho_max=820)
            y += 15

    def _dibujar_fondo_de_dialogo(self):
        """Lo que queda detrás de una pregunta o ventana: la partida, oscurecida, y el
        resumen final si la partida terminó."""
        if self.partida is not None:
            self._dibujar_partida(self.partida)
        else:
            self.pantalla.fill(FONDO)
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((0, 0, 0, 150))
        self.pantalla.blit(velo, (0, 0))
        self.zonas = []
        if self.fin is not None:
            self._dibujar_resumen_final(self.fin)

    def _dibujar_resumen_final(self, partida):
        caja = self._caja_centrada(760, 300, ALTO // 2 - 90)
        victoria = partida.estado == "victoria"
        self._texto(self.fuente_grande, "¡VICTORIA!" if victoria else "DERROTA",
                    ABIERTA if victoria else CERRADA, caja.centerx, caja.y + 20, centro=True)
        self._texto(self.fuente_media, "Acciones %d   ·   Derrotados %d   ·   Tiempo %d" % (
            partida.acciones, partida.derrotados, partida.reloj.tiempo_actual), TEXTO,
            caja.centerx, caja.y + 76, centro=True)
        y = caja.y + 118
        for texto in self.resumen_fin[-10:]:
            self._texto(self.fuente_chica, texto, TEXTO_TENUE, caja.x + 26, y, ancho_max=caja.w - 52)
            y += 16

    def _dibujar_cargando(self, texto, sobre_partida=False):
        if sobre_partida and self.partida is not None:
            self._dibujar_partida(self.partida)
        else:
            self.pantalla.fill(FONDO)
        caja = self._caja_centrada(420, 70, ALTO // 2)
        self._texto(self.fuente_media, texto, DORADO, caja.centerx, caja.y + 22, centro=True)
        pygame.display.flip()
        pygame.event.pump()             # la ventana sigue respondiendo al sistema

    # ============================================================== utilidades
    def _caja_centrada(self, ancho, alto, centro_y):
        caja = pygame.Rect(0, 0, ancho, alto)
        caja.center = (ANCHO // 2, centro_y)
        pygame.draw.rect(self.pantalla, PANEL, caja)
        pygame.draw.rect(self.pantalla, DORADO, caja, 2)
        return caja

    def _barra_vida(self, rect, vida, vida_max):
        pygame.draw.rect(self.pantalla, VIDA_FONDO, rect)
        if vida_max > 0 and vida > 0:
            lleno = pygame.Rect(rect.x, rect.y, max(1, rect.w * vida // vida_max), rect.h)
            pygame.draw.rect(self.pantalla, VIDA, lleno)

    def _texto(self, fuente, texto, color, x, y, centro=False, ancho_max=None):
        texto = str(texto)
        if ancho_max is not None and fuente.size(texto)[0] > ancho_max:
            while len(texto) > 1 and fuente.size(texto + "…")[0] > ancho_max:
                texto = texto[:-1]
            texto += "…"
        superficie = fuente.render(texto, True, color)
        if centro:
            x -= superficie.get_width() // 2
        self.pantalla.blit(superficie, (x, y))

    def _texto_objeto(self, objeto):
        return "%s (%s) p%s v%s" % (objeto.nombre, objeto.clase, objeto.peso, objeto.valor)

    def _color_de(self, comportamiento):
        if comportamiento == "guardian":
            return COLOR_GUARDIAN
        if comportamiento == "errante":
            return COLOR_ERRANTE
        if comportamiento == "rastreador":
            return COLOR_RASTREADOR
        return COLOR_ENEMIGO


def _tipo_de_enemigo(comportamiento):
    """Nombre de sprite del comportamiento: sin tildes, en minúsculas y sin espacios
    ("Guardián" -> "guardian"). Solo para dibujar; el Modelo no cambia."""
    texto = unicodedata.normalize("NFD", str(comportamiento or "")).strip().lower()
    limpio = ""
    for letra in texto:
        if unicodedata.category(letra) != "Mn":      # Mn = tilde u otra marca sobre la letra
            limpio += letra
    return limpio

def _acortar_ids(texto):
    """Para mostrar: 'Rata gigante [e-rata-cripta-02-4] te ataca' -> 'Rata gigante #4 te ataca'.
    Si el id no termina en número, se quita entero. El Modelo y el log no cambian."""
    resultado = ""
    i = 0
    while i < len(texto):
        abre = texto.find(" [", i)
        cierra = texto.find("]", abre + 2) if abre >= 0 else -1
        if abre < 0 or cierra < 0:
            resultado += texto[i:]
            break
        identificador = texto[abre + 2:cierra]
        numero = identificador[identificador.rfind("-") + 1:]
        resultado += texto[i:abre]
        if numero.isdigit():
            resultado += " #" + numero
        i = cierra + 1
    return resultado

def _opuesta(direccion):
    """Si sale por el norte, entra a la sala nueva por el sur, etc."""
    if direccion == "N":
        return "S"
    if direccion == "S":
        return "N"
    if direccion == "E":
        return "O"
    return "E"


def _punto_de_puerta(direccion):
    """Dónde se para el jugador junto a cada puerta de la sala dibujada."""
    if direccion == "N":
        return (SALA.centerx, SALA.y + 70)
    if direccion == "S":
        return (SALA.centerx, SALA.bottom - 110)
    if direccion == "E":
        return (SALA.right - 70, SUELO_Y)
    return (SALA.x + 70, SUELO_Y)


def _entre(desde, hasta, avance):
    return (int(desde[0] + (hasta[0] - desde[0]) * avance),
            int(desde[1] + (hasta[1] - desde[1]) * avance))


def _cargar_cubriendo(ruta, ancho, alto):
    """Carga una imagen y la escala para cubrir ancho x alto sin deformarla (recorta los
    bordes que sobren). None si no existe o no se puede abrir."""
    if not os.path.exists(ruta):
        return None
    try:
        imagen = pygame.image.load(ruta).convert()
    except pygame.error:
        return None
    escala = max(ancho / imagen.get_width(), alto / imagen.get_height())
    nueva = pygame.transform.smoothscale(imagen, (max(ancho, int(imagen.get_width() * escala) + 1),
                                                  max(alto, int(imagen.get_height() * escala) + 1)))
    x = (nueva.get_width() - ancho) // 2
    y = (nueva.get_height() - alto) // 2
    return nueva.subsurface(pygame.Rect(x, y, ancho, alto)).copy()


def _orden_de_dibujo(cantidad):
    """Primero la fila de atrás (posiciones 4..7) y luego la de adelante (0..3)."""
    orden = []
    for i in range(4, cantidad):
        orden.append(i)
    for i in range(min(4, cantidad)):
        orden.append(i)
    return orden