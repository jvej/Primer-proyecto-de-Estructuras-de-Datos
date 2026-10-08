from errores import ErrorRed
from cola_fifo import ColaFIFO
from tabla_hash import TablaHash

DIRECCIONES = ("N", "S", "E", "O")


class Esqueleto:
    def __init__(self):
        self.ids = []                 # posición -> id de sala
        self.vecinos = []             # posición -> lista de ids vecinos (orden N, S, E, O)
        self._indice = TablaHash()    # str(id) -> posición

    def agregar_pagina(self, cuerpo):
        """cuerpo: JSON de GET /criptas/<id>/salas?pagina=n"""
        for sala in cuerpo["salas"]:
            vecinos = []
            for direccion in DIRECCIONES:
                if direccion in sala["salidas"]:
                    vecinos.append(sala["salidas"][direccion]["sala"])
            self._indice.insertar(str(sala["id"]), len(self.ids))
            self.ids.append(sala["id"])
            self.vecinos.append(vecinos)

    def existe(self, id_sala):
        return self._indice.contiene(str(id_sala))

    def cantidad(self):
        return len(self.ids)

    def vecinos_de(self, id_sala):
        return self.vecinos[self._indice.buscar(str(id_sala))]

    def cercanas(self, origen, maximo, filtro=None):
        resultado = []
        if not self.existe(origen):
            return resultado
        visitada = [False] * len(self.ids)
        cola = ColaFIFO()
        posicion = self._indice.buscar(str(origen))
        visitada[posicion] = True
        cola.agregar([origen, 0])
        while not cola.vacia() and len(resultado) < maximo:
            actual = cola.sacar()
            if filtro is None or filtro(actual[0]):
                resultado.append(actual)
            for vecino in self.vecinos_de(actual[0]):
                pos = self._indice.buscar(str(vecino))
                if pos is not None and not visitada[pos]:
                    visitada[pos] = True
                    cola.agregar([vecino, actual[1] + 1])
        return resultado


def descargar_esqueleto(fuente, id_cripta, almacen=None):
    esqueleto = Esqueleto()
    pagina = 1
    total = 1
    while pagina <= total:
        if almacen is not None and almacen.tiene_pagina(pagina):
            cuerpo = almacen.leer_pagina(pagina)
        else:
            cuerpo = fuente.pagina_esqueleto(id_cripta, pagina)
            if almacen is not None:
                almacen.guardar_pagina(pagina, cuerpo)
        if "salas" not in cuerpo:
            raise ErrorRed("esqueleto de %s página %d" % (id_cripta, pagina),
                           "la respuesta no trae la lista de salas")
        total = cuerpo.get("total_paginas", 1)
        esqueleto.agregar_pagina(cuerpo)
        pagina += 1
    return esqueleto