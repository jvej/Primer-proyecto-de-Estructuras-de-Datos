"""Animaciones de la interfaz gráfica: QUÉ animar y CUÁNDO (sin Pygame, §6).

Las animaciones solo DIBUJAN resultados que el Modelo ya calculó. Nada de aquí cambia
la partida, calcula daño ni programa eventos. Después de cada orden, el Controlador
llama vista.mostrar_partida(partida) y la vista le pasa la partida a Animador.observar,
que compara lo que ve ahora con lo que vio la vez anterior (solo lectura):

  - el jugador atacó (la última orden fue ATACAR y se aceptó) ... ataque del jugador
  - un enemigo tiene menos vida que antes ............. daño de ese enemigo (+ número)
  - un enemigo de la sala murió ....................... muerte (se dibuja en su último lugar)
  - el jugador tiene menos vida que antes ............. daño del jugador (+ número)
  - el jugador murió .................................. muerte del jugador (queda tendido)
  - un mensaje nuevo dice "<enemigo> te ataca" ......... ataque de ese enemigo
  - el jugador entró a otra sala (última orden MOVER) .. correr desde la puerta
  - el jugador abrió una puerta (la vista lo pide) ..... correr de vuelta desde ella
  - un mensaje nuevo dice "¡Trampa! ..." .............. efecto de la trampa sobre el jugador
                                                         y su daño; si acaba de entrar a la
                                                         sala, ambos empiezan cuando termina
                                                         de correr (llega y entonces salta)
La animación de ABRIR la puerta con la llave la dibuja la vista ANTES de entregar la
orden (como correr hasta la puerta): es solo dibujo y el Modelo decide si se abre.

Los tiempos son de la VENTANA (milisegundos reales), no del reloj virtual: a 30 o 60
FPS la partida es la misma, solo cambia la suavidad del dibujo. Tras un retroceso o una
carga no se anima nada (el estado "salta", no ocurrió una acción).

Sin diccionarios: las animaciones activas y la foto anterior son listas pequeñas
(los actores de una sala), recorridas linealmente.
"""

from controlador.orden import ATACAR, CARGAR, MOVER, PERGAMINO

REPOSO = "reposo"
ATAQUE = "ataque"
DANO = "dano"
MUERTE = "muerte"
CORRER = "correr"
ABRIR_PUERTA = "abrir"
TRAMPA = "trampa"

CUADRO_MS = 140             # duración de cada cuadro de ataque / daño / muerte
REPOSO_MS = 450             # duración de cada cuadro de reposo (respiración)
CUADROS_MAXIMOS = 3         # ataque y muerte tienen 3 cuadros; daño, 1
DURACION_NUMERO_MS = 900    # el número de daño flota y desaparece
CORRER_CUADRO_MS = 80       # la carrera cambia de cuadro más rápido y se repite
CORRER_MS = 600             # lo que tarda en cruzar (dura igual que pasos.ogg: 2 pasos)
ABRIR_CUADRO_MS = 160       # cada cuadro de abrir la puerta con la llave
ABRIR_CUADROS = 4
ABRIR_MS = ABRIR_CUADRO_MS * ABRIR_CUADROS
DESTELLO_MS = 700           # brillo de la puerta recién abierta
TRAMPA_CUADRO_MS = 120      # cada cuadro del efecto de una trampa
TRAMPA_CUADROS = 4
TRAMPA_MS = TRAMPA_CUADRO_MS * TRAMPA_CUADROS


class Animacion:
    __slots__ = ("actor", "tipo", "inicio", "centro", "cantidad", "dato")

    def __init__(self, actor, tipo, inicio, centro=None, cantidad=0, dato=None):
        self.actor = actor
        self.tipo = tipo
        self.inicio = inicio        # ms de la ventana en que empieza (puede ser futuro)
        self.centro = centro        # dónde dibujarla si el actor ya no está en la sala
        self.cantidad = cantidad    # daño recibido (para el número flotante)
        self.dato = dato            # trampa: id de la ficha de la trampa que saltó


class Animador:
    def __init__(self):
        self.activas = []           # [Animacion]
        self._foto = []             # [(enemigo, vida)] de la sala, la vez anterior
        self._vida_jugador = None
        self._total_mensajes = 0
        self._acciones = 0
        self._sala = None

    def reiniciar(self, partida=None):
        """Nueva partida o partida cargada: se toma la foto sin animar nada."""
        self.activas = []
        self._foto = []
        self._vida_jugador = None
        self._sala = None
        if partida is not None:
            self._tomar_foto(partida)

    # ------------------------------------------------------------ detección
    def observar(self, partida, ahora, ultima_orden, centros):
        """centros: [(actor, (x, y))] donde se dibujó cada actor en el último cuadro."""
        if self._vida_jugador is None or ultima_orden in (PERGAMINO, CARGAR):
            self._tomar_foto(partida)
            return
        jugador = partida.jugador
        retraso = 0
        if ultima_orden == MOVER and partida.sala_actual() is not self._sala:
            self._agregar(Animacion(jugador, CORRER, ahora))
            retraso = CORRER_MS             # la trampa salta cuando termina de entrar
        trampas = self._trampas_disparadas(partida)
        for id_trampa in trampas:
            self._agregar(Animacion(jugador, TRAMPA, ahora + retraso, dato=id_trampa))
        if len(trampas) == 0:
            retraso = 0                     # sin trampa, el daño se ve en el momento
        if ultima_orden == ATACAR and partida.acciones > self._acciones:   # solo si se aceptó
            self._agregar(Animacion(jugador, ATAQUE, ahora))
        misma_sala = partida.sala_actual() is self._sala
        for enemigo, vida_antes in self._foto:
            perdida = vida_antes - enemigo.vida
            if not enemigo.esta_vivo():
                if misma_sala:
                    self._agregar(Animacion(enemigo, MUERTE, ahora, _centro_de(enemigo, centros),
                                            max(0, perdida)))
            elif perdida > 0 and enemigo.sala is partida.sala_actual():
                self._agregar(Animacion(enemigo, DANO, ahora, None, perdida))
        perdida = self._vida_jugador - jugador.vida
        if not jugador.esta_vivo():
            self._agregar(Animacion(jugador, MUERTE, ahora, None, max(0, perdida)))
        elif perdida > 0:
            self._agregar(Animacion(jugador, DANO, ahora + retraso, None, perdida))
        for enemigo in partida.enemigos_en_sala():
            if self._ataco(partida, enemigo):
                self._agregar(Animacion(enemigo, ATAQUE, ahora))
        self._tomar_foto(partida)

    def correr(self, actor, ahora):
        """La vista pide una carrera (por ejemplo, volver de la puerta que acaba de abrir)."""
        self._agregar(Animacion(actor, CORRER, ahora))

    def _mensajes_nuevos(self, partida):
        bitacora = partida.bitacora
        nuevos = bitacora.total_historico - self._total_mensajes
        mensajes = bitacora.ultimos()
        resultado = []
        for i in range(max(0, len(mensajes) - nuevos), len(mensajes)):
            resultado.append(mensajes[i])
        return resultado

    def _trampas_disparadas(self, partida):
        """Ids de las trampas que saltaron en esta orden ("¡Trampa! <nombre>." en la bitácora)."""
        ids = []
        for mensaje in self._mensajes_nuevos(partida):
            if not mensaje.startswith("¡Trampa!"):
                continue
            encontrada = None
            for trampa in partida.trampas_en_sala():
                if trampa.nombre in mensaje:
                    encontrada = trampa.id
            ids.append(encontrada if encontrada is not None else "")
        return ids

    def _ataco(self, partida, enemigo):
        prefijo = enemigo.etiqueta() + " te ataca"
        for mensaje in self._mensajes_nuevos(partida):
            if mensaje.startswith(prefijo):
                return True
        return False

    def _tomar_foto(self, partida):
        self._foto = []
        for enemigo in partida.enemigos_en_sala():
            self._foto.append((enemigo, enemigo.vida))
        self._vida_jugador = partida.jugador.vida
        self._total_mensajes = partida.bitacora.total_historico
        self._acciones = partida.acciones
        self._sala = partida.sala_actual()

    def _agregar(self, animacion):
        """Una animación por actor y tipo: la nueva reemplaza a la anterior del mismo tipo.
        La muerte reemplaza a cualquier otra del mismo actor."""
        restantes = []
        for vieja in self.activas:
            mismo = vieja.actor is animacion.actor
            if mismo and (vieja.tipo == animacion.tipo or animacion.tipo == MUERTE):
                continue
            restantes.append(vieja)
        restantes.append(animacion)
        self.activas = restantes

    # ------------------------------------------------------------ consulta
    def estado(self, actor, ahora):
        """(tipo, ms_desde_que_empezó) de lo que el actor está haciendo ahora.
        Prioridad: muerte > daño > correr > ataque > reposo."""
        elegida = None
        for animacion in self.activas:
            if animacion.actor is not actor or animacion.inicio > ahora:
                continue                    # de otro actor, o todavía no empieza
            if elegida is None or _prioridad(animacion.tipo) > _prioridad(elegida.tipo):
                elegida = animacion
        if elegida is None:
            return REPOSO, ahora
        transcurrido = ahora - elegida.inicio
        if elegida.tipo != MUERTE and transcurrido >= duracion(elegida.tipo):
            return REPOSO, ahora
        return elegida.tipo, transcurrido

    def fantasmas(self, ahora):
        """Enemigos que murieron y todavía están cayendo: [(actor, centro, ms)]."""
        resultado = []
        for animacion in self.activas:
            if (animacion.tipo == MUERTE and animacion.centro is not None
                    and 0 <= ahora - animacion.inicio < duracion(MUERTE) + CUADRO_MS):
                resultado.append((animacion.actor, animacion.centro, ahora - animacion.inicio))
        return resultado

    def numeros(self, ahora):
        """Números de daño flotando: [(actor, centro_o_None, cantidad, ms)]."""
        resultado = []
        for animacion in self.activas:
            transcurrido = ahora - animacion.inicio
            if animacion.cantidad > 0 and 0 <= transcurrido < DURACION_NUMERO_MS:
                resultado.append((animacion.actor, animacion.centro, animacion.cantidad, transcurrido))
        return resultado

    def efectos_trampa(self, ahora):
        """Trampas que están saltando ahora: [(actor, id_trampa, ms)]."""
        resultado = []
        for animacion in self.activas:
            transcurrido = ahora - animacion.inicio
            if animacion.tipo == TRAMPA and 0 <= transcurrido < TRAMPA_MS:
                resultado.append((animacion.actor, animacion.dato, transcurrido))
        return resultado

    def limpiar(self, ahora):
        """Quita las animaciones terminadas (la muerte del jugador se queda: sigue tendido)."""
        vigentes = []
        for animacion in self.activas:
            transcurrido = ahora - animacion.inicio
            fin = max(duracion(animacion.tipo) + CUADRO_MS, DURACION_NUMERO_MS)
            if transcurrido < fin or (animacion.tipo == MUERTE and animacion.centro is None):
                vigentes.append(animacion)
        self.activas = vigentes


def duracion(tipo):
    if tipo == CORRER:
        return CORRER_MS
    if tipo == ABRIR_PUERTA:
        return ABRIR_MS
    if tipo == TRAMPA:
        return TRAMPA_MS
    if tipo == DANO:
        return CUADRO_MS * 2            # el único cuadro de daño se sostiene un poco más
    return CUADRO_MS * CUADROS_MAXIMOS


def indice_de_cuadro(tipo, transcurrido, cantidad_cuadros):
    """Qué cuadro mostrar. Reposo se repite; los demás avanzan y se quedan en el último."""
    if cantidad_cuadros <= 0:
        return -1
    if tipo == REPOSO:
        return (transcurrido // REPOSO_MS) % cantidad_cuadros
    if tipo == CORRER:
        return (transcurrido // CORRER_CUADRO_MS) % cantidad_cuadros
    if tipo == ABRIR_PUERTA:
        return min(transcurrido // ABRIR_CUADRO_MS, cantidad_cuadros - 1)
    if tipo == TRAMPA:
        return min(transcurrido // TRAMPA_CUADRO_MS, cantidad_cuadros - 1)
    paso = duracion(tipo) // cantidad_cuadros if tipo != DANO else duracion(tipo)
    return min(transcurrido // max(1, paso), cantidad_cuadros - 1)


def _prioridad(tipo):
    if tipo == MUERTE:
        return 4
    if tipo == DANO:
        return 3
    if tipo == CORRER:
        return 2
    if tipo == ATAQUE:
        return 1
    return 0


def _centro_de(actor, centros):
    for otro, centro in centros:
        if otro is actor:
            return centro
    return None