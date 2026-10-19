from modelo.juego.errores import ErrorCripta
from controlador.orden import (ABRIR, AYUDA, ATACAR, CARGAR, EQUIPAR, ESPERAR, GUARDAR, INV_ANTERIOR,
                               INV_INICIO, INV_ORDENAR, INV_SIGUIENTE, INVENTARIO, MOVER, Orden,
                               ORDENES_DE_PARTIDA, PERGAMINO, PUNTAJES, RECOGER, SALIR, SOLTAR, USAR,
                               VER_REPETICIONES, clave_de_argumento, es_clave)
from modelo.juego.sala import DIRECCIONES


class Controlador:
    def __init__(self, partida=None, vista=None, persistencia=None, puntajes=None,
                 al_terminar=None, repeticiones=None):
        self.partida = partida
        self.vista = vista
        self.persistencia = persistencia
        self.puntajes = puntajes
        self.al_terminar = al_terminar
        self.repeticiones = repeticiones
        self._observadores = []
        self._terminado = False

    @property
    def terminado(self):
        return self._terminado

    def agregar_observador(self, funcion):
        """funcion(orden) se llama con cada orden de partida ACEPTADA, ya resuelta."""
        self._observadores.append(funcion)

    def ejecutar(self, orden):
        """Ejecuta una orden. Devuelve True si fue aceptada (las rechazadas no cambian
        nada ni consumen tiempo; el motivo queda en la bitácora de la partida)."""
        if orden.tipo in ORDENES_DE_PARTIDA:
            return self._ejecutar_de_partida(orden)
        return self._ejecutar_de_interfaz(orden)

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
        else:
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