from modelo.datos.almacen_local import AlmacenLocal
from modelo.estructuras.cache import Cache


class AlmacenLocalCache(AlmacenLocal):
    def __init__(self, tope, almacen_disco, en_uso=None):
        self.cache = Cache(tope=tope, en_uso=en_uso)
        self.disco = almacen_disco         

    def disponible(self, id_ficha):
        return self.cache.contiene(id_ficha) or self.disco.contiene(id_ficha)

    def obtener(self, id_ficha):
        ficha = self.cache.obtener(id_ficha)     
        if ficha is not None:
            return ficha
        ficha = self.disco.leer(id_ficha)      
        if ficha is not None:
            self.cache.poner(id_ficha, ficha)
        return ficha

    def guardar(self, id_ficha, ficha):
        self.disco.guardar(id_ficha, ficha)
        self.cache.poner(id_ficha, ficha)