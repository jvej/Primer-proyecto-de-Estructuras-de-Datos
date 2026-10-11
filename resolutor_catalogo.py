from errores import ErrorPresupuesto, ErrorRed
from fuente_datos import TAM_LOTE_MAX
from tabla_hash import TablaHash


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
    vistos = TablaHash()
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
        self.pendientes = []            # ids por enviar, en orden de descubrimiento
        self._marcados = TablaHash()    # ids pendientes o en vuelo (evita pedir dos veces)
        self._en_vuelo = []             # [tarea, ids] en orden de envío
        self._siguiente = 0
        self.solicitudes_enviadas = 0
        self.ids_solicitados = 0
        self.ids_ya_locales = 0

    def pedir(self, ids):
        """Registra ids que se necesitarán. No hace red todavía."""
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
        cuerpo = tarea.resultado_o_error()
        recibidos = TablaHash()
        for ficha in cuerpo["entidades"]:
            self.local.guardar(ficha["id"], ficha)
            recibidos.insertar(ficha["id"], True)
            if ficha.get("clase") == "enemigo" and "suelta" in ficha:
                self.pedir(ficha["suelta"])          # lo que suelta también necesita ficha
        for id_ in grupo:
            if not recibidos.contiene(id_):
                raise ErrorRed("catálogo", "el servidor no devolvió la ficha " + str(id_))

    def sondear(self):
        """Incorpora, en orden de envío, los lotes ya terminados. No bloquea."""
        while self._siguiente < len(self._en_vuelo):
            tarea, grupo = self._en_vuelo[self._siguiente]
            if not tarea.terminada():
                break
            self._siguiente += 1
            self._incorporar(tarea, grupo)

    def esperar(self, ids=None):
        """Bloquea (tiempo real) hasta que 'ids' (y lo que suelten) estén disponibles."""
        if ids is not None:
            self.pedir(ids)
        while True:
            self.lanzar(forzar=True)
            if self._siguiente >= len(self._en_vuelo):
                break
            tarea, grupo = self._en_vuelo[self._siguiente]
            tarea.esperar_fin()
            self._siguiente += 1
            self._incorporar(tarea, grupo)

    def disponible(self, id_):
        return self.local.disponible(id_)

    def obtener(self, id_):
        """Ficha lista para usar; si no estuviera disponible se resuelve en este momento."""
        ficha = self.local.obtener(id_)
        if ficha is None:
            self.esperar([id_])
            ficha = self.local.obtener(id_)
        return ficha