"""Fuente de datos que lee SOLO la copia local persistida (§3.4, §4.11).

Implementa el mismo contrato que ClienteHTTP y ClienteOffline (fuente_datos.py), así
el resto del programa no sabe de dónde vienen los datos.

Se usa para reproducir un log cuya versión de cripta o de catálogo ya no es la que
publica el servicio, pero de la que existe una copia local compatible (lo que se fue
guardando en disco mientras se jugó: datos generales, páginas del esqueleto,
contenido de salas y fichas del catálogo, ver almacen_cripta.py / almacen_fichas.py).

Si falta algo (por ejemplo, una sala que nunca se descargó), lanza
ErrorDatosNoDisponibles: la reproducción se detiene y lo informa, en vez de seguir
con datos distintos.
"""

from errores import ErrorDatosNoDisponibles
from fuente_datos import FuenteDatos, validar_lote
from presupuesto_red import PresupuestoRed


class FuenteAlmacen(FuenteDatos):
    def __init__(self, id_cripta, almacen_cripta, version_cripta, almacen_catalogo, version_catalogo):
        self.id_cripta = id_cripta
        self.almacen_cripta = almacen_cripta
        self.version_cripta_local = version_cripta
        self.almacen_catalogo = almacen_catalogo
        self.version_catalogo_local = version_catalogo
        self.presupuesto = PresupuestoRed(activo=False)     # nada de esto es red

    def _exigir_cripta(self, id_cripta):
        if str(id_cripta) != str(self.id_cripta):
            raise ErrorDatosNoDisponibles("copia local", "solo hay copia de %s" % self.id_cripta)

    def listar_criptas(self):
        return {"criptas": [{"id": self.id_cripta, "nombre": "(copia local)"}]}

    def datos_cripta(self, id_cripta):
        self._exigir_cripta(id_cripta)
        if not self.almacen_cripta.tiene_generales():
            raise ErrorDatosNoDisponibles("datos generales de %s" % id_cripta,
                                          "no están en la copia local")
        return self.almacen_cripta.leer_generales()

    def pagina_esqueleto(self, id_cripta, pagina):
        self._exigir_cripta(id_cripta)
        if not self.almacen_cripta.tiene_pagina(pagina):
            raise ErrorDatosNoDisponibles("esqueleto de %s página %s" % (id_cripta, pagina),
                                          "no está en la copia local")
        return self.almacen_cripta.leer_pagina(pagina)

    def contenido_salas(self, id_cripta, ids_salas):
        self._exigir_cripta(id_cripta)
        validar_lote("contenido", ids_salas)
        entradas = []
        for id_sala in ids_salas:
            if not self.almacen_cripta.tiene_sala(id_sala):
                raise ErrorDatosNoDisponibles("contenido de sala %s" % id_sala,
                                              "no está en la copia local")
            entradas.append(self.almacen_cripta.leer_sala(id_sala))
        return {"contenido": entradas}

    def catalogo(self, ids):
        validar_lote("catálogo", ids)
        fichas = []
        for id_ficha in ids:
            ficha = self.almacen_catalogo.leer(id_ficha)
            if ficha is None:
                raise ErrorDatosNoDisponibles("ficha %s" % id_ficha, "no está en la copia local")
            fichas.append(ficha)
        return {"entidades": fichas}

    def version_cripta(self, id_cripta):
        self._exigir_cripta(id_cripta)
        return {"id": self.id_cripta, "version": self.version_cripta_local}

    def version_catalogo(self):
        return {"version": self.version_catalogo_local}