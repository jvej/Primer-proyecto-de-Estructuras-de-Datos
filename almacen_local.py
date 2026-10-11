from tabla_hash import TablaHash


class AlmacenLocal:
    def disponible(self, id_ficha):
        raise NotImplementedError

    def obtener(self, id_ficha):
        raise NotImplementedError

    def guardar(self, id_ficha, ficha):
        raise NotImplementedError


class AlmacenLocalMemoria(AlmacenLocal):
    """Implementación simple (sin tope ni disco) para pruebas y para trabajar sin la caché."""

    def __init__(self):
        self._tabla = TablaHash()

    def disponible(self, id_ficha):
        return self._tabla.contiene(id_ficha)

    def obtener(self, id_ficha):
        return self._tabla.buscar(id_ficha)

    def guardar(self, id_ficha, ficha):
        self._tabla.insertar(id_ficha, ficha)