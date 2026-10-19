from modelo.juego.errores import ErrorPresupuesto, ErrorRed
from modelo.datos.fuente_datos import TAM_LOTE_MAX
from modelo.estructuras.lista_ordenada import ListaOrdenada


def id_de_referencia(elemento):
    if isinstance(elemento, str):
        return elemento
    if isinstance(elemento, dict):
        if "tipo" in elemento:
            return elemento["tipo"]
        if "id" in elemento:
            return elemento["id"]
    return None


def ids_de_contenido(entrada):
    ids = []
    vistos = ListaOrdenada()
    for campo in ("enemigos", "objetos", "trampas"):
        if campo in entrada:
            for elemento in entrada[campo]:
                id_ = id_de_referencia(elemento)
                if id_ is not None and not vistos.contiene(id_):
                    vistos.insertar(id_, True)
                    ids.append(id_)
    return ids


class ResolutorCatalogo:
    def __init__(self, fuente, ejecutor, local, presupuesto, tam_lote=TAM_LOTE_MAX):
        self.fuente = fuente
        self.ejecutor = ejecutor
        self.local = local
        self.presupuesto = presupuesto
        self.tam_lote = min(tam_lote, TAM_LOTE_MAX)
        self.pendientes = []          
        self._marcados = ListaOrdenada()   
        self._en_vuelo = []             
        self._siguiente = 0
        self.solicitudes_enviadas = 0
        self.ids_solicitados = 0
        self.ids_ya_locales = 0

    def pedir(self, ids):
        for id_ in ids:
            if id_ is None or self._marcados.contiene(id_):
                continue
            if self.local.disponible(id_):
                self.ids_ya_locales += 1
                continue
            self._marcados.insertar(id_, True)
            self.pendientes.append(id_)

    def lanzar(self, forzar=False):
        while len(self.pendientes) >= self.tam_lote or (forzar and len(self.pendientes) > 0):
            if not self.presupuesto.reservar():
                raise ErrorPresupuesto("catálogo", self.presupuesto.limite)
            grupo = self.pendientes[:self.tam_lote]
            del self.pendientes[:self.tam_lote]
            tarea = self.ejecutor.enviar(self.fuente.catalogo, grupo)
            self._en_vuelo.append([tarea, grupo])
            self.solicitudes_enviadas += 1
            self.ids_solicitados += len(grupo)

    def _incorporar(self, tarea, grupo):
        for id_ in grupo:
            self._marcados.eliminar(id_)
        try:
            cuerpo = tarea.resultado_o_error()
        finally:
            tarea.resultado = None     
        recibidos = ListaOrdenada()
        for ficha in cuerpo["entidades"]:
            self.local.guardar(ficha["id"], ficha)
            recibidos.insertar(ficha["id"], True)
            if ficha.get("clase") == "enemigo" and "suelta" in ficha:
                self.pedir(ficha["suelta"])        
        cuerpo = None             
        for id_ in grupo:
            if not recibidos.contiene(id_):
                raise ErrorRed("catálogo", "el servidor no devolvió la ficha " + str(id_))

    def sondear(self):
        while self._siguiente < len(self._en_vuelo):
            tarea, grupo = self._en_vuelo[self._siguiente]
            if not tarea.terminada():
                break
            self._siguiente += 1
            self._soltar_lote(self._siguiente - 1)
            self._incorporar(tarea, grupo)

    def esperar(self, ids=None):
        if ids is not None:
            self.pedir(ids)
        while True:
            self.lanzar(forzar=True)
            if self._siguiente >= len(self._en_vuelo):
                break
            tarea, grupo = self._en_vuelo[self._siguiente]
            tarea.esperar_fin()
            self._siguiente += 1
            self._soltar_lote(self._siguiente - 1)
            self._incorporar(tarea, grupo)

    def _soltar_lote(self, posicion):
        self._en_vuelo[posicion] = None

    def respuestas_retenidas(self):
        total = 0
        for entrada in self._en_vuelo:
            if entrada is not None and entrada[0].resultado is not None:
                total += 1
        return total

    def disponible(self, id_):
        return self.local.disponible(id_)

    def obtener(self, id_):
        ficha = self.local.obtener(id_)
        if ficha is None:
            self.esperar([id_])
            ficha = self.local.obtener(id_)
        return ficha