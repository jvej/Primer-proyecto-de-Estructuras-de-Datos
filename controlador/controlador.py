"""Controlador (MVC, §6): traduce las Órdenes del usuario en operaciones del Modelo
y coordina el flujo de la aplicación.

Reglas del Controlador:
  - NO imprime ni lee teclado (no hay print ni input aquí): habla con la Vista
    solo a través de la interfaz de vista_base.py.
  - NO conoce a ninguna vista concreta, ni HTTP, ni archivos: la persistencia y la
    creación de la partida le llegan desde fuera (ver correr_sesion y Persistencia).
  - Con vista=None sirve para --replay y --bench: ejecutar(orden) funciona igual,
    sin interfaz.

Todo lo que cambia la partida pasa por ejecutar(); cada orden aceptada se avisa a los
observadores ya con sus argumentos resueltos (posiciones concretas, nunca "el actual"),
que es lo que necesita el log de replay (§4.11).

Persistencia (guardar/cargar, §4.10) es un objeto opcional con:
    guardar(partida) -> str   (mensaje para el usuario)
    cargar() -> Partida o None (puede lanzar ErrorCripta con el motivo)
Si no se entrega, esas órdenes avisan que aún no están disponibles.

puntajes (§2.12) es un objeto opcional con listar() -> registros ya ordenados.
al_terminar(partida) -> str es opcional: se llama al ganar o perder (registrar el
puntaje, cerrar el log, reporte de red) y su texto se muestra como aviso.
"""

from modelo.juego.errores import ErrorCripta
from controlador.orden import (ABRIR, AYUDA, ATACAR, CARGAR, EQUIPAR, ESPERAR, GUARDAR, INV_ANTERIOR,
                   INV_INICIO, INV_ORDENAR, INV_SIGUIENTE, INVENTARIO, MOVER, Orden,
                   ORDENES_DE_PARTIDA, PERGAMINO, PUNTAJES, RECOGER, SALIR, SOLTAR, USAR,
                   clave_de_argumento, es_clave)
from modelo.juego.sala import DIRECCIONES


class Controlador:
    def __init__(self, partida=None, vista=None, persistencia=None, puntajes=None,
                 al_terminar=None):
        self.partida = partida
        self.vista = vista
        self.persistencia = persistencia
        self.puntajes = puntajes
        self.al_terminar = al_terminar
        self._observadores = []
        self._terminado = False

    @property
    def terminado(self):
        return self._terminado

    def agregar_observador(self, funcion):
        """funcion(orden) se llama con cada orden de partida ACEPTADA, ya resuelta."""
        self._observadores.append(funcion)

    # ------------------------------------------------------------ una orden
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
                # "El que se está viendo" se identifica por la etiqueta fija de su nodo, en
                # O(1) y sin calcular su posición: así soltar/usar/equipar desde el cursor
                # no depende de dónde esté el objeto (§4.5). La etiqueta va al log.
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
            objeto = partida.inventario.objeto_en(orden.argumento)   # número elegido por el usuario
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

    # ---------------------------------------------------------------- flujo
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
        """Flujo completo: elegir cripta, jugar, y repetir si el usuario quiere.

        listar_criptas() -> lista de {id, nombre, salas, dificultad}
        crear_partida(id_cripta) -> Partida lista para jugar
        Ambas las entrega quien arma la aplicación (main.py): así el Controlador no
        sabe si los datos vienen de la red o de disco (--offline).
        """
        while not self._terminado:
            try:
                criptas = listar_criptas()
            except ErrorCripta as error:
                self.vista.mostrar_aviso(str(error))
                return
            id_cripta = self.vista.elegir_cripta(criptas)
            if id_cripta is None:
                return
            try:
                self.partida = crear_partida(id_cripta)
            except ErrorCripta as error:
                self.vista.mostrar_aviso(str(error))
                continue
            self.correr_partida()
            if self._terminado or not self.vista.confirmar("¿Jugar otra cripta?"):
                return

    # ------------------------------------------------------------ internos
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