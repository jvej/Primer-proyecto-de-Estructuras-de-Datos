from almacen_fichas import AlmacenFichas


class AlmacenCripta:
    def __init__(self, ruta, version_cripta):
        self.almacen = AlmacenFichas(ruta, version_cripta)

    def se_descarto(self):
        return self.almacen.se_descarto

    def tiene_generales(self):
        return self.almacen.contiene("general")

    def guardar_generales(self, datos):
        self.almacen.guardar("general", datos)

    def leer_generales(self):
        return self.almacen.leer("general")

    def tiene_pagina(self, numero):
        return self.almacen.contiene("pagina_" + str(numero))

    def guardar_pagina(self, numero, datos):
        self.almacen.guardar("pagina_" + str(numero), datos)

    def leer_pagina(self, numero):
        return self.almacen.leer("pagina_" + str(numero))

    def tiene_sala(self, id_sala):
        return self.almacen.contiene("sala_" + str(id_sala))

    def guardar_sala(self, id_sala, contenido):
        self.almacen.guardar("sala_" + str(id_sala), contenido)

    def leer_sala(self, id_sala):
        return self.almacen.leer("sala_" + str(id_sala))

    def salas_faltantes(self, ids_salas):
        faltan = []
        for id_sala in ids_salas:
            if not self.tiene_sala(id_sala):
                faltan.append(id_sala)
        return faltan