"""Cliente HTTP del servicio Cripta (§3.1, §5.1)."""
import threading
import time
import uuid
from urllib.parse import quote

import requests

from errores import ErrorRed
from fuente_datos import FuenteDatos, validar_lote
from presupuesto_red import PresupuestoRed

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
TIMEOUT_DEFECTO = 10
MAX_REINTENTOS_429 = 5
ESPERA_429_DEFECTO = 1


class ClienteHTTP(FuenteDatos):
    def __init__(self, presupuesto=None, base_url=BASE_URL, timeout=TIMEOUT_DEFECTO,
                 sesion=None, dormir=time.sleep, max_reintentos_429=MAX_REINTENTOS_429):
        self.client_id = str(uuid.uuid4())       # una sola vez por ejecución
        self.presupuesto = presupuesto if presupuesto is not None else PresupuestoRed()
        self.base_url = base_url
        self.timeout = timeout
        self.sesion = sesion if sesion is not None else requests.Session()
        self.dormir = dormir
        self.max_reintentos_429 = max_reintentos_429
        self.esperas_429 = 0
        self._cabeceras = {"X-Cripta-Client-Id": self.client_id}
        self._cerrojo = threading.Lock()

    def _segundos_espera(self, respuesta):
        try:
            cuerpo = respuesta.json()
            espera = float(cuerpo["reintentar_en"])
            if espera >= 0:
                return espera
        except (ValueError, KeyError, TypeError):
            pass
        return ESPERA_429_DEFECTO

    def _get(self, operacion, ruta):
        url = self.base_url + ruta
        reintentos = 0
        while True:
            self.presupuesto.registrar(operacion)          # cuenta también los reintentos
            try:
                with self._cerrojo:
                    respuesta = self.sesion.get(url, headers=self._cabeceras,
                                                timeout=self.timeout)
            except requests.exceptions.Timeout as e:
                raise ErrorRed(operacion, "tiempo de espera agotado (%s s) en %s"
                               % (self.timeout, url)) from e
            except requests.exceptions.RequestException as e:
                raise ErrorRed(operacion, "error de conexión en %s: %s" % (url, e)) from e

            if respuesta.status_code == 200:
                try:
                    return respuesta.json()
                except ValueError as e:
                    raise ErrorRed(operacion, "la respuesta de %s no es JSON válido" % url,
                                   200) from e
            if respuesta.status_code == 429:
                reintentos += 1
                if reintentos > self.max_reintentos_429:
                    raise ErrorRed(operacion, "HTTP 429 persistente tras %d reintentos"
                                   % self.max_reintentos_429, 429)
                self.esperas_429 += 1
                self.dormir(self._segundos_espera(respuesta))   # tiempo real, no virtual
                continue
            raise ErrorRed(operacion, "HTTP %d en %s: %s"
                           % (respuesta.status_code, url, respuesta.text[:200]),
                           respuesta.status_code)

    def listar_criptas(self):
        return self._get("listar criptas", "/criptas")

    def datos_cripta(self, id_cripta):
        return self._get("datos generales de " + str(id_cripta),
                         "/criptas/" + quote(str(id_cripta)))

    def pagina_esqueleto(self, id_cripta, pagina):
        return self._get("esqueleto de %s página %s" % (id_cripta, pagina),
                         "/criptas/%s/salas?pagina=%d" % (quote(str(id_cripta)), pagina))

    def contenido_salas(self, id_cripta, ids_salas):
        validar_lote("contenido", ids_salas)
        lista = ",".join(str(i) for i in ids_salas)
        return self._get("contenido de salas %s de %s" % (lista, id_cripta),
                         "/criptas/%s/contenido?salas=%s" % (quote(str(id_cripta)), lista))

    def catalogo(self, ids):
        validar_lote("catálogo", ids)
        lista = ",".join(quote(str(i)) for i in ids)
        return self._get("catálogo de " + lista, "/catalogo?ids=" + lista)

    def version_cripta(self, id_cripta):
        return self._get("versión de " + str(id_cripta),
                         "/criptas/%s/version" % quote(str(id_cripta)))

    def version_catalogo(self):
        return self._get("versión del catálogo", "/catalogo/version")