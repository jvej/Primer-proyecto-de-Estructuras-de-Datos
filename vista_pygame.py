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

Imágenes: si existe recursos/sprites/<nombre>.png se usa; si no, una figura simple.
Nombres: jugador, guardian, errante, rastreador y enemigo (respaldo para cualquier
comportamiento desconocido). Los sprites se eligen por comportamiento, no por id de
cripta ni de catálogo, así una cripta nueva se dibuja sin cambiar nada.

Esta primera versión es funcional (figuras y texto). Las animaciones se agregan después
sobre esta base, siempre como dibujo de resultados que ya calculó el Modelo.
"""

import os

import pygame

from controles_gui import (AYUDA_LINEAS, BOTONES, SIG_ENEMIGO, SIG_SUELO, ajustar_posicion,
                           orden_para_tecla, siguiente_posicion)
from orden import ABRIR, ATACAR, CARGAR, MOVER, Orden, RECOGER, SALIR
from vista_base import Vista

ANCHO, ALTO = 1280, 720
FPS = 30
CARPETA_SPRITES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recursos", "sprites")

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

MAX_ENEMIGOS_DIBUJADOS = 8
MAX_OBJETOS_DIBUJADOS = 6
DURACION_AVISO_MS = 7000
MAX_AVISOS = 6


def _fuente(tamano, negrita=False):
    return pygame.font.SysFont("consolas,dejavusansmono,menlo,couriernew", tamano, bold=negrita)


class Sprites:
    """Carga cada imagen una sola vez y la reutiliza. Sin diccionarios: dos listas
    paralelas y búsqueda lineal (son 5 nombres)."""

    NOMBRES = ("jugador", "guardian", "errante", "rastreador", "enemigo")

    def __init__(self, carpeta, alto):
        self.imagenes = []
        self.avisos = []
        if not os.path.isdir(carpeta):
            self.avisos.append("Sin carpeta de sprites (%s): se usan figuras simples." % carpeta)
        for nombre in self.NOMBRES:
            self.imagenes.append(self._cargar(carpeta, nombre, alto))

    def _cargar(self, carpeta, nombre, alto):
        ruta = os.path.join(carpeta, nombre + ".png")
        if not os.path.exists(ruta):
            return None
        try:
            imagen = pygame.image.load(ruta).convert_alpha()
        except pygame.error as error:
            self.avisos.append("No se pudo cargar %s (%s): se usa una figura." % (ruta, error))
            return None
        ancho = max(1, imagen.get_width() * alto // max(1, imagen.get_height()))
        return pygame.transform.smoothscale(imagen, (ancho, alto))

    def de(self, nombre):
        """La imagen de ese nombre; si falta, la de 'enemigo'; si también falta, None."""
        respaldo = None
        for i in range(len(self.NOMBRES)):
            if self.NOMBRES[i] == nombre and self.imagenes[i] is not None:
                return self.imagenes[i]
            if self.NOMBRES[i] == "enemigo":
                respaldo = self.imagenes[i]
        return respaldo if nombre != "jugador" else None


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
        self.sprites = Sprites(carpeta_sprites, 110)
        self.partida = None
        self.fin = None                 # partida terminada cuyo resumen se muestra
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
        if orden.tipo == MOVER:
            self._dibujar_cargando("Entrando...", sobre_partida=True)
        elif orden.tipo == CARGAR:
            self._dibujar_cargando("Cargando partida...", sobre_partida=True)
        return orden

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
            self.pantalla.fill(FONDO)
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
        fin = pygame.time.get_ticks() + DURACION_AVISO_MS
        for linea in str(texto).splitlines():
            if linea.strip() != "":
                self.avisos.append([linea, fin])
        while len(self.avisos) > MAX_AVISOS:
            self.avisos.pop(0)

    def mostrar_ayuda(self):
        self._modal("Controles", list(AYUDA_LINEAS))

    def mostrar_fin(self, partida):
        self.partida = partida
        self.fin = partida

    def cerrar(self):
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
        self.pantalla.fill(FONDO)
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
        self._dibujar_actor(partida.jugador, "jugador", COLOR_JUGADOR,
                            (SALA.x + 170, SALA.centery - 20), "Tú", False)
        self._dibujar_enemigos(partida.enemigos_en_sala())
        self._dibujar_suelo(partida.objetos_en_sala())

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
        for i in range(min(len(enemigos), MAX_ENEMIGOS_DIBUJADOS)):
            enemigo = enemigos[i]
            columna = i % 4
            fila = i // 4
            centro = (SALA.x + 380 + columna * 118, SALA.y + 110 + fila * 150)
            color = self._color_de(enemigo.comportamiento)
            rect = self._dibujar_actor(enemigo, enemigo.comportamiento, color, centro,
                                       enemigo.etiqueta(), i == self.enemigo_elegido)
            self.zonas.append((rect, ("enemigo", i)))
        if len(enemigos) > MAX_ENEMIGOS_DIBUJADOS:
            self._texto(self.fuente_chica, "+%d enemigos más" % (len(enemigos) - MAX_ENEMIGOS_DIBUJADOS),
                        TEXTO, SALA.right - 160, SALA.y + 20)

    def _dibujar_actor(self, actor, nombre_sprite, color, centro, etiqueta, elegido):
        imagen = self.sprites.de(nombre_sprite)
        if imagen is not None:
            rect = imagen.get_rect(center=centro)
            self.pantalla.blit(imagen, rect)
        else:
            rect = pygame.Rect(0, 0, 70, 70)
            rect.center = centro
            self._figura(nombre_sprite, color, rect)
        if elegido:
            pygame.draw.rect(self.pantalla, SELECCION, rect.inflate(12, 12), 3)
            self._texto(self.fuente_chica, "objetivo", SELECCION, rect.centerx, rect.y - 34, centro=True)
        self._texto(self.fuente_chica, etiqueta, TEXTO, rect.centerx, rect.bottom + 6,
                    centro=True, ancho_max=116)
        self._barra_vida(pygame.Rect(rect.centerx - 40, rect.bottom + 24, 80, 7), actor.vida, actor.vida_max)
        return rect.inflate(20, 50)

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
        if len(objetos) == 0:
            return
        self._texto(self.fuente_chica, "En el suelo (F o clic: elegir · G o 2º clic: recoger)",
                    TEXTO_TENUE, SALA.x + 30, SALA.bottom - 112)
        for i in range(min(len(objetos), MAX_OBJETOS_DIBUJADOS)):
            objeto = objetos[i]
            rect = pygame.Rect(SALA.x + 30 + i * 128, SALA.bottom - 90, 118, 58)
            pygame.draw.rect(self.pantalla, PANEL, rect)
            pygame.draw.rect(self.pantalla, SELECCION if i == self.objeto_elegido else BORDE, rect,
                             3 if i == self.objeto_elegido else 1)
            self._texto(self.fuente_chica, objeto.nombre, TEXTO, rect.x + 6, rect.y + 8, ancho_max=106)
            self._texto(self.fuente_chica, objeto.clase, TEXTO_TENUE, rect.x + 6, rect.y + 32, ancho_max=106)
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
            self._texto(self.fuente_chica, mensajes[i], color, MENSAJES.x + 10, y, ancho_max=MENSAJES.w - 20)
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
        for texto, _fin in self.avisos:
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