from modelo.estructuras.lista_ordenada import ListaOrdenada


class AlmacenLocal:
    def disponible(self, id_ficha):
        raise NotImplementedError

    def obtener(self, id_ficha):
        raise NotImplementedError

    def guardar(self, id_ficha, ficha):
        raise NotImplementedError


class AlmacenLocalMemoria(AlmacenLocal):
    def __init__(self):
        self._tabla = ListaOrdenada()

    def disponible(self, id_ficha):
        return self._tabla.contiene(id_ficha)

    def obtener(self, id_ficha):
        return self._tabla.buscar(id_ficha)

    def guardar(self, id_ficha, ficha):
        self._tabla.insertar(id_ficha, ficha)