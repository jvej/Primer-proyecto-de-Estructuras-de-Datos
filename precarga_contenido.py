from errores import ErrorCripta, ErrorDatosNoDisponibles, ErrorPresupuesto, ErrorRed
from fuente_datos import TAM_LOTE_MAX
from resolutor_catalogo import ids_de_contenido
from tabla_hash import TablaHash


class _Solicitud:
    def __init__(self, tarea, ids):
        self.tarea = tarea
        self.ids = ids
        self.procesada = False
        self.error = None


class PrecargaContenido:
    def __init__(self, fuente, id_cripta, esqueleto, ejecutor, presupuesto,
                 resolutor=None, almacen=None, profundidad=2, reserva=0,
                 tam_lote=TAM_LOTE_MAX):
       
        self.fuente = fuente
        self.id_cripta = id_cripta
        self.esqueleto = esqueleto
        self.ejecutor = ejecutor
        self.presupuesto = presupuesto
        self.resolutor = resolutor
        self.almacen = almacen
        self.profundidad = profundidad
        self.reserva = reserva
        self.tam_lote = min(tam_lote, TAM_LOTE_MAX)
        self._contenidos = TablaHash()      # str(id) -> entrada de contenido incorporada
        self._solicitadas = TablaHash()     # str(id) -> True (pedida, en vuelo o incorporada)
        self._solicitud_de = TablaHash()    # str(id) -> _Solicitud
        self._solicitudes = []              # en orden de envío
        self._siguiente = 0                 # próxima solicitud por incorporar
        self.errores = []                   # fallos de precarga especulativa
        self.lotes_enviados = 0
        self.salas_pedidas_red = 0
        self.salas_desde_disco = 0
        self.esperas_bloqueantes = 0

    # ---------- consultas ----------
    def tiene_contenido(self, id_sala):
        return self._contenidos.contiene(str(id_sala))

    def contenido_de(self, id_sala):
        entrada = self._contenidos.buscar(str(id_sala))
        if entrada is None:
            raise ErrorDatosNoDisponibles("contenido de sala " + str(id_sala),
                                          "aún no está incorporado; usar asegurar()")
        return entrada

    def sala_lista(self, id_sala):
        """True si el contenido y las fichas de lo que contiene ya están en memoria/disco."""
        entrada = self._contenidos.buscar(str(id_sala))
        if entrada is None:
            return False
        if self.resolutor is None:
            return True
        for id_ in ids_de_contenido(entrada):
            if not self.resolutor.disponible(id_):
                return False
        return True

    # ---------- incorporación en orden ----------
    def _incorporar(self, solicitud):
        solicitud.procesada = True
        try:
            cuerpo = solicitud.tarea.resultado_o_error()
            entradas = cuerpo["contenido"]
        except (ErrorCripta, KeyError, TypeError) as e:
            solicitud.error = e if isinstance(e, ErrorCripta) else ErrorRed(
                "contenido de salas", "respuesta con formato inesperado: %r" % (e,))
            for id_ in solicitud.ids:
                self._solicitadas.eliminar(str(id_))     # podrá pedirse de nuevo
            self.errores.append(solicitud.error)
            return
        for entrada in entradas:
            clave = str(entrada["sala"])
            self._contenidos.insertar(clave, entrada)
            if self.almacen is not None:
                self.almacen.guardar_sala(entrada["sala"], entrada)
            if self.resolutor is not None:
                self.resolutor.pedir(ids_de_contenido(entrada))
        for id_ in solicitud.ids:
            if not self._contenidos.contiene(str(id_)):
                self._solicitadas.eliminar(str(id_))
                solicitud.error = ErrorRed("contenido de salas",
                                           "el servidor no devolvió la sala %s" % id_)
                self.errores.append(solicitud.error)
        solicitud.tarea.resultado = None                 # libera la respuesta cruda
        if self.resolutor is not None:
            try:
                self.resolutor.lanzar(forzar=False)      # solo lotes completos de 10
            except ErrorPresupuesto as e:                # reaparecerá en asegurar()
                self.errores.append(e)

    def sondear(self):
        while self._siguiente < len(self._solicitudes):
            solicitud = self._solicitudes[self._siguiente]
            if not solicitud.tarea.terminada():
                break
            self._siguiente += 1
            self._incorporar(solicitud)
        if self.resolutor is not None:
            try:
                self.resolutor.sondear()
            except ErrorCripta as e:
                self.errores.append(e)

    def _esperar_solicitud(self, solicitud):
        while not solicitud.procesada:
            actual = self._solicitudes[self._siguiente]
            actual.tarea.esperar_fin()
            self._siguiente += 1
            self._incorporar(actual)

    # ---------- planificación ----------
    def _ya_solicitada(self, id_sala):
        return self._solicitadas.contiene(str(id_sala))

    def _en_disco(self, id_sala):
        return self.almacen is not None and self.almacen.tiene_sala(id_sala)

    def _cargar_de_disco(self, id_sala):
        entrada = self.almacen.leer_sala(id_sala)
        clave = str(id_sala)
        self._solicitadas.insertar(clave, True)
        self._contenidos.insertar(clave, entrada)
        self.salas_desde_disco += 1
        if self.resolutor is not None:
            self.resolutor.pedir(ids_de_contenido(entrada))

    def _enviar_lote(self, ids, forzado):
        if not forzado:
            restantes = self.presupuesto.restantes()
            if restantes is not None and restantes <= self.reserva:
                return None
        if not self.presupuesto.reservar():
            if forzado:
                raise ErrorPresupuesto("contenido de salas " + ",".join(str(i) for i in ids),
                                       self.presupuesto.limite)
            return None
        tarea = self.ejecutor.enviar(self.fuente.contenido_salas, self.id_cripta, ids)
        solicitud = _Solicitud(tarea, ids)
        self._solicitudes.append(solicitud)
        for id_ in ids:
            self._solicitadas.insertar(str(id_), True)
            self._solicitud_de.insertar(str(id_), solicitud)
        self.lotes_enviados += 1
        self.salas_pedidas_red += len(ids)
        return solicitud

    def _planificar(self, origen, forzado, limite_distancia):
        while True:
            cercanas = self.esqueleto.cercanas(origen, self.tam_lote,
                                               lambda s: not self._ya_solicitada(s))
            if len(cercanas) == 0:
                return None
            if limite_distancia is not None and cercanas[0][1] > limite_distancia:
                return None
            de_disco = [c[0] for c in cercanas if self._en_disco(c[0])]
            if len(de_disco) > 0:
                for id_ in de_disco:
                    self._cargar_de_disco(id_)
                continue
            ids = [c[0] for c in cercanas]
            return self._enviar_lote(ids, forzado)

    # ---------- API para el controlador ----------
    def al_entrar(self, id_sala):
        self.sondear()
        self._planificar(id_sala, False, self.profundidad)
        self._vaciar_fichas_cercanas(id_sala)

    def _vaciar_fichas_cercanas(self, id_sala):
        if self.resolutor is None or len(self.resolutor.pendientes) == 0:
            return
        urgentes = self.esqueleto.cercanas(
            id_sala, 20, lambda s: self.tiene_contenido(s) and not self.sala_lista(s))
        if len(urgentes) > 0 and urgentes[0][1] <= self.profundidad:
            try:
                self.resolutor.lanzar(forzar=True)
            except ErrorPresupuesto as e:
                self.errores.append(e)

    def asegurar(self, id_sala):
        """Bloquea hasta que la sala y las fichas de su contenido estén listas.
        Lanza ErrorRed/ErrorPresupuesto/ErrorDatosNoDisponibles si no es posible."""
        if not self.esqueleto.existe(id_sala):
            raise ErrorDatosNoDisponibles("contenido de sala " + str(id_sala),
                                          "la sala no existe en el esqueleto")
        self.sondear()
        clave = str(id_sala)
        if self.sala_lista(id_sala):
            return
        self.esperas_bloqueantes += 1
        if not self._ya_solicitada(id_sala):
            if self._en_disco(id_sala):
                self._cargar_de_disco(id_sala)
            else:
                self._planificar(id_sala, True, self.profundidad)
        solicitud = self._solicitud_de.buscar(clave)
        if not self._contenidos.contiene(clave) and solicitud is not None:
            self._esperar_solicitud(solicitud)
            if solicitud.error is not None and not self._contenidos.contiene(clave):
                raise solicitud.error
        if not self._contenidos.contiene(clave):
            raise ErrorDatosNoDisponibles("contenido de sala " + clave, "no se pudo obtener")
        if self.resolutor is not None:
            self.resolutor.esperar(ids_de_contenido(self._contenidos.buscar(clave)))

    def iniciar(self, id_sala_inicial):
        """Antes de aceptar la primera acción (§2.4)."""
        self.asegurar(id_sala_inicial)
        self.al_entrar(id_sala_inicial)

    def estadisticas(self):
        return ("lotes de contenido enviados=%d, salas pedidas a la red=%d, salas leídas de "
                "disco=%d, esperas bloqueantes=%d" % (self.lotes_enviados,
                 self.salas_pedidas_red, self.salas_desde_disco, self.esperas_bloqueantes))