
import json
import os

from errores import ErrorDatosNoDisponibles
from fuente_datos import FuenteDatos, validar_lote
from presupuesto_red import PresupuestoRed


def _seguro(texto):
    texto = str(texto)
    if texto == "" or "/" in texto or "\\" in texto or ".." in texto:
        raise ErrorDatosNoDisponibles("ruta offline", "identificador no válido: %r" % texto)
    return texto


class ClienteOffline(FuenteDatos):
    def __init__(self, carpeta):
        self.carpeta = carpeta
        self.presupuesto = PresupuestoRed(activo=False)   # nada cuenta como solicitud

    def _ruta_criptas(self):
        return os.path.join(self.carpeta, "criptas.json")

    def _ruta_general(self, id_cripta):
        return os.path.join(self.carpeta, "criptas", _seguro(id_cripta), "general.json")

    def _ruta_version_cripta(self, id_cripta):
        return os.path.join(self.carpeta, "criptas", _seguro(id_cripta), "version.json")

    def _ruta_pagina(self, id_cripta, pagina):
        return os.path.join(self.carpeta, "criptas", _seguro(id_cripta),
                            "salas_%d.json" % pagina)

    def _ruta_sala(self, id_cripta, id_sala):
        return os.path.join(self.carpeta, "criptas", _seguro(id_cripta),
                            "contenido_%s.json" % _seguro(id_sala))

    def _ruta_ficha(self, id_ficha):
        return os.path.join(self.carpeta, "catalogo", _seguro(id_ficha) + ".json")

    def _ruta_version_catalogo(self):
        return os.path.join(self.carpeta, "catalogo", "version.json")

    def _leer(self, operacion, ruta):
        if not os.path.exists(ruta):
            raise ErrorDatosNoDisponibles(operacion, "no existe el archivo " + ruta)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError) as e:
            raise ErrorDatosNoDisponibles(operacion, "no se pudo leer %s: %s" % (ruta, e))

    def listar_criptas(self):
        return self._leer("listar criptas", self._ruta_criptas())

    def datos_cripta(self, id_cripta):
        return self._leer("datos generales de " + str(id_cripta), self._ruta_general(id_cripta))

    def pagina_esqueleto(self, id_cripta, pagina):
        return self._leer("esqueleto de %s página %s" % (id_cripta, pagina),
                          self._ruta_pagina(id_cripta, pagina))

    def contenido_salas(self, id_cripta, ids_salas):
        validar_lote("contenido", ids_salas)
        entradas = []
        for id_sala in ids_salas:
            entradas.append(self._leer("contenido de sala %s de %s" % (id_sala, id_cripta),
                                       self._ruta_sala(id_cripta, id_sala)))
        return {"contenido": entradas}

    def catalogo(self, ids):
        validar_lote("catálogo", ids)
        fichas = []
        for id_ficha in ids:
            fichas.append(self._leer("ficha de catálogo " + str(id_ficha),
                                     self._ruta_ficha(id_ficha)))
        return {"entidades": fichas}

    def version_cripta(self, id_cripta):
        return self._leer("versión de " + str(id_cripta), self._ruta_version_cripta(id_cripta))

    def version_catalogo(self):
        return self._leer("versión del catálogo", self._ruta_version_catalogo())