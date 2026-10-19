from controlador.orden import ATACAR, CARGAR, MOVER, PERGAMINO

REPOSO = "reposo"
ATAQUE = "ataque"
DANO = "dano"
MUERTE = "muerte"
CORRER = "correr"
ABRIR_PUERTA = "abrir"
TRAMPA = "trampa"

CUADRO_MS = 140           
REPOSO_MS = 450            
CUADROS_MAXIMOS = 3         
DURACION_NUMERO_MS = 900    
CORRER_CUADRO_MS = 80       
CORRER_MS = 600          
ABRIR_CUADRO_MS = 160       
ABRIR_CUADROS = 4
ABRIR_MS = ABRIR_CUADRO_MS * ABRIR_CUADROS
DESTELLO_MS = 700         
TRAMPA_CUADRO_MS = 120     
TRAMPA_CUADROS = 4
TRAMPA_MS = TRAMPA_CUADRO_MS * TRAMPA_CUADROS


class Animacion:
    __slots__ = ("actor", "tipo", "inicio", "centro", "cantidad", "dato")

    def __init__(self, actor, tipo, inicio, centro=None, cantidad=0, dato=None):
        self.actor = actor
        self.tipo = tipo
        self.inicio = inicio       
        self.centro = centro        
        self.cantidad = cantidad   
        self.dato = dato           


class Animador:
    def __init__(self):
        self.activas = []           
        self._foto = []          
        self._vida_jugador = None
        self._total_mensajes = 0
        self._acciones = 0
        self._sala = None

    def reiniciar(self, partida=None):
        self.activas = []
        self._foto = []
        self._vida_jugador = None
        self._sala = None
        if partida is not None:
            self._tomar_foto(partida)

    # ------------------------------------------------------------ detección
    def observar(self, partida, ahora, ultima_orden, centros, correr_ms=CORRER_MS):
        if self._vida_jugador is None or ultima_orden in (PERGAMINO, CARGAR):
            self._tomar_foto(partida)
            return
        jugador = partida.jugador
        retraso = 0
        if ultima_orden == MOVER and partida.sala_actual() is not self._sala:
            self._agregar(Animacion(jugador, CORRER, ahora, dato=correr_ms))
            retraso = correr_ms 
        trampas = self._trampas_disparadas(partida)
        for id_trampa in trampas:
            self._agregar(Animacion(jugador, TRAMPA, ahora + retraso, dato=id_trampa))
        if len(trampas) == 0:
            retraso = 0               
        if ultima_orden == ATACAR and partida.acciones > self._acciones: 
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

    def correr(self, actor, ahora, correr_ms=CORRER_MS):
        self._agregar(Animacion(actor, CORRER, ahora, dato=correr_ms))

    def _mensajes_nuevos(self, partida):
        bitacora = partida.bitacora
        nuevos = bitacora.total_historico - self._total_mensajes
        mensajes = bitacora.ultimos()
        resultado = []
        for i in range(max(0, len(mensajes) - nuevos), len(mensajes)):
            resultado.append(mensajes[i])
        return resultado

    def _trampas_disparadas(self, partida):
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
        restantes = []
        for vieja in self.activas:
            mismo = vieja.actor is animacion.actor
            if mismo and (vieja.tipo == animacion.tipo or animacion.tipo == MUERTE):
                continue
            restantes.append(vieja)
        restantes.append(animacion)
        self.activas = restantes

    def estado(self, actor, ahora):
        """(tipo, ms_desde_que_empezó) de lo que el actor está haciendo ahora.
        Prioridad: muerte > daño > correr > ataque > reposo."""
        elegida = None
        for animacion in self.activas:
            if animacion.actor is not actor or animacion.inicio > ahora:
                continue          
            if elegida is None or _prioridad(animacion.tipo) > _prioridad(elegida.tipo):
                elegida = animacion
        if elegida is None:
            return REPOSO, ahora
        transcurrido = ahora - elegida.inicio
        if elegida.tipo != MUERTE and transcurrido >= _duracion_de(elegida):
            return REPOSO, ahora
        return elegida.tipo, transcurrido

    def fantasmas(self, ahora):
        resultado = []
        for animacion in self.activas:
            if (animacion.tipo == MUERTE and animacion.centro is not None
                    and 0 <= ahora - animacion.inicio < duracion(MUERTE) + CUADRO_MS):
                resultado.append((animacion.actor, animacion.centro, ahora - animacion.inicio))
        return resultado

    def numeros(self, ahora):
        resultado = []
        for animacion in self.activas:
            transcurrido = ahora - animacion.inicio
            if animacion.cantidad > 0 and 0 <= transcurrido < DURACION_NUMERO_MS:
                resultado.append((animacion.actor, animacion.centro, animacion.cantidad, transcurrido))
        return resultado

    def efectos_trampa(self, ahora):
        resultado = []
        for animacion in self.activas:
            transcurrido = ahora - animacion.inicio
            if animacion.tipo == TRAMPA and 0 <= transcurrido < TRAMPA_MS:
                resultado.append((animacion.actor, animacion.dato, transcurrido))
        return resultado

    def limpiar(self, ahora):
        vigentes = []
        for animacion in self.activas:
            transcurrido = ahora - animacion.inicio
            fin = max(_duracion_de(animacion) + CUADRO_MS, DURACION_NUMERO_MS)
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
        return CUADRO_MS * 2       
    return CUADRO_MS * CUADROS_MAXIMOS


def _duracion_de(animacion):
    if animacion.tipo == CORRER and animacion.dato:
        return animacion.dato
    return duracion(animacion.tipo)


def indice_de_cuadro(tipo, transcurrido, cantidad_cuadros):
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