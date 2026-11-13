"""Controlador de órdenes ordinarias y viaje compuesto IR_A.

Integración pendiente: Aplicacion/main deben conectar los comentarios al log
activo; Pygame todavía no ofrece entrada de IR_A. Los comentarios se emiten
únicamente a los observadores conectados.
"""

from modelo.juego.errores import ErrorCripta
from controlador.planificador_rutas import PlanificadorRutas
from controlador.orden import IR_A, MAPA, interpretar_ir_a
from controlador.orden import (ABRIR, AYUDA, ATACAR, CARGAR, EQUIPAR, ESPERAR, GUARDAR, INV_ANTERIOR,
                               INV_INICIO, INV_ORDENAR, INV_SIGUIENTE, INVENTARIO, MOVER, Orden,
                               ORDENES_DE_PARTIDA, PERGAMINO, PUNTAJES, RECOGER, SALIR, SOLTAR, USAR,
                               VER_REPETICIONES, clave_de_argumento, es_clave)
from modelo.juego.sala import DIRECCIONES


class Controlador:
    def __init__(self, partida=None, vista=None, persistencia=None, puntajes=None,
                 al_terminar=None, repeticiones=None):
        self._partida = None
        self._planificador = None
        self._viaje_activo = False
        self._token_viaje = 0
        self.partida = partida
        self.vista = vista
        self.persistencia = persistencia
        self.puntajes = puntajes
        self.al_terminar = al_terminar
        self.repeticiones = repeticiones
        self._observadores = []
        self._observadores_comentarios = []
        self._observadores_viaje = []
        self._terminado = False

    @property
    def partida(self):
        return self._partida

    @partida.setter
    def partida(self, nueva):
        self._partida = nueva
        self._token_viaje += 1
        self._planificador = None
        if nueva is not None and hasattr(nueva, "conocimiento"):
            self._planificador = PlanificadorRutas(nueva.mapa, nueva.conocimiento)

    @property
    def terminado(self):
        return self._terminado

    def agregar_observador(self, funcion):
        """funcion(orden) se llama con cada orden de partida ACEPTADA, ya resuelta."""
        self._observadores.append(funcion)

    def agregar_observador_comentarios(self, funcion):
        """Conexión opcional pendiente en Aplicacion/main (C4)."""
        self._observadores_comentarios.append(funcion)

    def agregar_observador_viaje(self, funcion):
        """funcion(partida) -> bool, antes de cada paso de IR_A.

        True continúa y False cancela sin acciones ni tiempo adicionales. Corre
        tras la validación preliminar, fuera del grupo reversible y del adaptador
        C1. El callback debe limitarse a eventos/presentación, sin ejecutar
        acciones de juego. Sus excepciones se propagan; no se ocultan.
        """
        self._observadores_viaje.append(funcion)

    def ejecutar(self, orden):
        """Ejecuta una orden. Devuelve True si fue aceptada (las rechazadas no cambian
        nada ni consumen tiempo; el motivo queda en la bitácora de la partida)."""
        if isinstance(orden, str):
            try:
                orden = interpretar_ir_a(orden)
            except ValueError as error:
                self._avisar(str(error))
                return False
        if self._viaje_activo:
            self._token_viaje += 1
            if orden.tipo == IR_A:
                self._avisar("Viaje automático cancelado; repite la orden para iniciar otro.")
                return False
        if orden.tipo == IR_A:
            return self._ejecutar_ir_a(orden)
        if orden.tipo in ORDENES_DE_PARTIDA:
            return self._ejecutar_de_partida(orden)
        return self._ejecutar_de_interfaz(orden)

    def _ejecutar_ir_a(self, orden):
        p = self.partida
        if p is None or p.estado != "jugando" or not p.esperando:
            self._avisar("No se puede iniciar el viaje: no es el turno de una partida activa.")
            return False
        planificador = self._planificador
        paso = planificador.siguiente_paso(p.jugador.sala, orden.argumento)
        if paso.estado != "paso":
            self._avisar(paso.motivo)
            return paso.estado == "destino"

        self._token_viaje += 1
        token = self._token_viaje
        self._viaje_activo = True
        try:
            for observador in self._observadores_comentarios:
                observador("ir a %s" % orden.argumento)
            while token == self._token_viaje and self.partida is p:
                for observador in self._observadores_viaje:
                    continuar = observador(p)
                    if token != self._token_viaje or self.partida is not p:
                        self._avisar("Viaje automático cancelado por otra orden o cambio de partida.")
                        return True
                    if type(continuar) is not bool:
                        raise TypeError("el observador de viaje debe devolver bool")
                    if not continuar:
                        self._token_viaje += 1
                        self._avisar("Viaje automático cancelado antes del siguiente paso.")
                        return True
                # Observar es local y no avanza el reloj; el planificador solo
                # recibe la memoria, nunca el estado físico de las puertas.
                p._observar_puertas()
                paso = planificador.siguiente_paso(p.jugador.sala, orden.argumento)
                if paso.estado == "destino":
                    self._avisar("Has llegado a tu destino.")
                    return True
                if paso.estado != "paso":
                    self._avisar("Viaje automático interrumpido: ruta bloqueada por puerta cerrada o sin ruta conocida.")
                    return True
                aceptada, recibio_dano = self._mover_en_viaje(p, paso.direccion)
                if token != self._token_viaje or self.partida is not p:
                    self._avisar("Viaje automático cancelado por otra orden o cambio de partida.")
                    return True
                if recibio_dano:
                    self._avisar("Viaje automático interrumpido: has recibido daño.")
                    return True
                if p.estado != "jugando":
                    self._avisar("Viaje automático terminado: %s." % p.estado)
                    return True
                if p.enemigos_en_sala():
                    self._avisar("Viaje automático interrumpido: presencia de enemigos vivos en la sala.")
                    return True
                if not aceptada:
                    mensajes = p.bitacora.ultimos()
                    motivo = mensajes[-1] if mensajes else "movimiento rechazado"
                    self._avisar("Viaje automático interrumpido: " + motivo)
                    return True
                if p.jugador.sala.id == orden.argumento:
                    self._avisar("Has llegado a tu destino.")
                    return True
            self._avisar("Viaje automático cancelado por otra orden o cambio de partida.")
            return True
        finally:
            self._viaje_activo = False

    def _mover_en_viaje(self, partida, direccion):
        """Detecta daño aunque una curación posterior recupere la vida.

        Adaptador temporal del punto C1: delega todos los cambios al método
        original sin añadir grupos ni alterar inversos. Se retira incluso ante
        excepciones. No añade observadores permanentes a Partida/historia.
        """
        cambiar_original = partida.cambiar
        metodo_de_clase = getattr(cambiar_original, "__func__", None) is type(partida).cambiar
        recibio_dano = False

        def cambiar(objeto, campo, valor):
            nonlocal recibio_dano
            if objeto is partida.jugador and campo == "vida" and valor < objeto.vida:
                recibio_dano = True
            return cambiar_original(objeto, campo, valor)

        partida.cambiar = cambiar
        try:
            aceptada = self._ejecutar_de_partida(Orden(MOVER, direccion))
            return aceptada, recibio_dano
        finally:
            if metodo_de_clase:
                del partida.cambiar
            else:
                partida.cambiar = cambiar_original

    def _ejecutar_de_partida(self, orden):
        resuelta = self._resolver(orden)
        if resuelta is None:
            return False
        aceptada = self._aplicar(resuelta)
        if aceptada:
            for observador in self._observadores:
                observador(resuelta)
        return aceptada

    def _resolver(self, orden):
        """Valida los argumentos y convierte "el objeto actual" en una posición concreta."""
        tipo = orden.tipo
        if tipo == MOVER or tipo == ABRIR:
            if orden.argumento not in DIRECCIONES:
                return self._rechazar("Dirección desconocida.")
        elif tipo == ATACAR or tipo == RECOGER:
            if not isinstance(orden.argumento, int):
                return self._rechazar("Falta indicar cuál.")
        elif tipo == USAR or tipo == EQUIPAR or tipo == SOLTAR:
            inventario = self.partida.inventario
            if orden.argumento is None:
                actual = inventario.objeto_actual()
                if actual is None:
                    return self._rechazar("El inventario está vacío.")
                return Orden(tipo, "@%d" % inventario.clave_de(actual))
            if es_clave(orden.argumento):
                return Orden(tipo, orden.argumento)
            if not isinstance(orden.argumento, int) or not 0 <= orden.argumento < len(inventario):
                return self._rechazar("No tienes ese objeto.")
        return Orden(tipo, orden.argumento, orden.extra)

    def _aplicar(self, orden):
        partida = self.partida
        tipo = orden.tipo
        if tipo == MOVER:
            return partida.mover(orden.argumento)
        if tipo == ABRIR:
            return partida.abrir(orden.argumento)
        if tipo == ATACAR:
            return partida.atacar(orden.argumento)
        if tipo == ESPERAR:
            return partida.esperar()
        if tipo == RECOGER:
            return partida.recoger(orden.argumento)
        if tipo == PERGAMINO:
            return partida.usar_pergamino()
        if es_clave(orden.argumento):
            objeto = partida.inventario.objeto_por_clave(clave_de_argumento(orden.argumento))
            if objeto is None:
                self._rechazar("No tienes ese objeto.")
                return False
        else:
            objeto = partida.inventario.objeto_en(orden.argumento)  
        if tipo == USAR:
            return partida.usar(objeto)
        if tipo == EQUIPAR:
            return partida.equipar(objeto)
        return partida.soltar(objeto)

    def _ejecutar_de_interfaz(self, orden):
        tipo = orden.tipo
        if tipo == MAPA:
            if self.vista is not None:
                self.vista.mostrar_mapa(self.partida.mapa_conocido())
            return True
        inventario = self.partida.inventario if self.partida is not None else None
        if tipo == INVENTARIO:
            self._mostrar_inventario()
            return True
        if tipo == INV_SIGUIENTE or tipo == INV_ANTERIOR or tipo == INV_INICIO:
            if tipo == INV_SIGUIENTE:
                movido = inventario.siguiente()
            elif tipo == INV_ANTERIOR:
                movido = inventario.anterior()
            else:
                inventario.ir_al_inicio()
                movido = True
            self._mostrar_inventario()
            return movido
        if tipo == INV_ORDENAR:
            return self._ordenar_inventario(orden)
        if tipo == GUARDAR:
            return self._guardar()
        if tipo == CARGAR:
            return self._cargar()
        if tipo == PUNTAJES:
            return self._mostrar_puntajes()
        if tipo == AYUDA:
            if self.vista is not None:
                self.vista.mostrar_ayuda()
            return True
        if tipo == SALIR:
            if self.vista is None or self.vista.confirmar("¿Seguro que quieres salir?"):
                self._terminado = True
            return True
        return False

    def _ordenar_inventario(self, orden):
        inventario = self.partida.inventario
        try:
            ordenados = inventario.vista_ordenada(orden.argumento, bool(orden.extra))
        except ValueError as error:
            self._avisar(str(error))
            return False
        if self.vista is not None:
            pares = []
            for objeto in ordenados:
                pares.append((inventario.indice_de(objeto), objeto))
            self.vista.mostrar_vista_ordenada(orden.argumento, bool(orden.extra), pares)
        return True

    def _guardar(self):
        if self.persistencia is None:
            self._avisar("Guardar todavía no está disponible.")
            return False
        self._avisar(self.persistencia.guardar(self.partida))
        return True

    def _cargar(self):
        if self.persistencia is None:
            self._avisar("Cargar todavía no está disponible.")
            return False
        try:
            nueva = self.persistencia.cargar()
        except ErrorCripta as error:
            self._avisar(str(error))
            return False
        if nueva is None:
            self._avisar("No hay una partida guardada que cargar.")
            return False
        self.partida = nueva
        self._avisar("Partida cargada.")
        return True
    
    def correr_partida(self):
        """Juega la partida actual con la vista hasta que termine o el usuario salga."""
        while not self._terminado and self.partida.estado == "jugando":
            self.vista.mostrar_partida(self.partida)
            self.ejecutar(self.vista.pedir_orden(self.partida))
        if self.partida.estado != "jugando":
            self.vista.mostrar_partida(self.partida)
            self.vista.mostrar_fin(self.partida)
            if self.al_terminar is not None:
                self.vista.mostrar_aviso(self.al_terminar(self.partida))

    def correr_sesion(self, listar_criptas, crear_partida):
        while not self._terminado:
            try:
                criptas = listar_criptas()
            except ErrorCripta as error:
                self.vista.mostrar_aviso(str(error))
                return
            id_cripta = self.vista.elegir_cripta(criptas)
            if id_cripta is None:
                return
            if id_cripta == VER_REPETICIONES:
                self._menu_repeticiones()
                continue
            try:
                self.partida = crear_partida(id_cripta)
            except ErrorCripta as error:
                self.vista.mostrar_aviso(str(error))
                continue
            self.correr_partida()
            if (not self._terminado and self.partida.estado != "jugando" and self._hay_repeticiones()
                    and self.repeticiones.ultima() is not None
                    and self.vista.confirmar("¿Ver la repetición de esta partida?")):
                self.ver_repeticion(self.repeticiones.ultima())
            if self._terminado or not self.vista.confirmar("¿Jugar otra cripta?"):
                return

    def _hay_repeticiones(self):
        return (self.repeticiones is not None and self.vista is not None
                and self.vista.soporta_repeticion())

    def _menu_repeticiones(self):
        if not self._hay_repeticiones():
            return
        try:
            entradas = self.repeticiones.listar()
        except (ErrorCripta, OSError) as error:
            self.vista.mostrar_aviso("No se pudieron leer las repeticiones: %s" % error)
            return
        ruta = self.vista.elegir_repeticion(entradas)
        if ruta is not None:
            self.ver_repeticion(ruta)

    def ver_repeticion(self, ruta):
        try:
            reproduccion, informe = self.repeticiones.preparar(ruta)
        except ErrorCripta as error:
            self.vista.mostrar_aviso("No se puede reproducir: %s" % error)
            return
        if reproduccion is None:
            self.vista.fin_de_repeticion(None, informe.lineas)
            return
        try:
            partida = reproduccion.partida
            ejecutor = Controlador(partida)      
            numero = 0
            motivo = None
            while not reproduccion.ordenes.vacia():
                if partida.estado != "jugando":
                    motivo = "La partida terminó antes de la orden %d; el resto se ignora." % (numero + 1)
                    break
                orden = reproduccion.ordenes.sacar()
                numero += 1
                self.vista.mostrar_partida(partida)
                if not self.vista.paso_de_repeticion(partida, orden, numero, reproduccion.total):
                    motivo = "Repetición detenida en la orden %d de %d." % (numero, reproduccion.total)
                    break
                if not ejecutor.ejecutar(orden):
                    ultimo = partida.bitacora.ultimos()
                    motivo = ("DIVERGENCIA en la orden %d (%s): %s. La repetición se detiene."
                              % (numero, orden.a_texto(), ultimo[-1] if len(ultimo) > 0 else "rechazada"))
                    break
            self.vista.mostrar_partida(partida)
            lineas = ["Partida de %s en %s (%s)." % (reproduccion.encabezado.jugador or "-",
                                                      reproduccion.encabezado.id_cripta,
                                                      reproduccion.encabezado.fecha or "sin fecha")]
            if motivo is not None:
                lineas.append(motivo)
            else:
                lineas.append("Se reprodujeron las %d órdenes." % reproduccion.total)
            lineas.append("Resultado: %s · tiempo %d · acciones %d · derrotados %d · vida %d/%d" % (
                _texto_estado(partida.estado), partida.reloj.tiempo_actual, partida.acciones,
                partida.derrotados, partida.jugador.vida, partida.jugador.vida_max))
            self.vista.fin_de_repeticion(partida, lineas)
        finally:
            reproduccion.cerrar()

    def _mostrar_puntajes(self):
        if self.puntajes is None:
            self._avisar("La tabla de puntajes no está disponible.")
            return False
        if self.vista is not None:
            self.vista.mostrar_puntajes(self.puntajes.listar())
        return True

    def _mostrar_inventario(self):
        if self.vista is not None:
            self.vista.mostrar_inventario(self.partida)

    def _avisar(self, texto):
        """Con vista, un aviso de la aplicación; sin vista (replay), a la bitácora."""
        if self.vista is not None:
            self.vista.mostrar_aviso(texto)
        elif self.partida is not None:
            self.partida.bitacora.agregar(texto)

    def _rechazar(self, motivo):
        self.partida.bitacora.agregar(motivo)
        return None


def _texto_estado(estado):
    if estado == "victoria":
        return "victoria"
    if estado == "derrota":
        return "derrota"
    return "sin terminar"
