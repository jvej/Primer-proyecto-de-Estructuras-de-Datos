import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from bitacora_pantalla import BitacoraPantalla
from cliente_http import ClienteHTTP
from ejecutor_red import EjecutorRed
from errores import ErrorPresupuesto, ErrorRed
from esqueleto import Esqueleto, descargar_esqueleto
from almacen_local import AlmacenLocalMemoria
from precarga_contenido import PrecargaContenido
from presupuesto_red import PresupuestoRed
from resolutor_catalogo import ResolutorCatalogo, ids_de_contenido
from fuente_datos import FuenteDatos


class RespuestaFalsa:
    def __init__(self, codigo, cuerpo=None, texto=""):
        self.status_code = codigo
        self._cuerpo = cuerpo
        self.text = texto

    def json(self):
        if self._cuerpo is None:
            raise ValueError("sin json")
        return self._cuerpo


class SesionFalsa:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []

    def get(self, url, headers=None, timeout=None):
        self.llamadas.append([url, headers, timeout])
        return self.respuestas.pop(0)


class FuenteFalsa(FuenteDatos):

    def __init__(self, n=40, latencia=0.02, presupuesto=None):
        self.n = n
        self.latencia = latencia
        self.presupuesto = presupuesto or PresupuestoRed(activo=False)
        self.lotes_contenido = []
        self.lotes_catalogo = []

    def pagina_esqueleto(self, id_cripta, pagina):
        salas = []
        for i in range(1, self.n + 1):
            salidas = []
            if i > 1:
                salidas.append('"S": {"sala": %d}' % (i - 1))
            if i < self.n:
                salidas.append('"N": {"sala": %d}' % (i + 1))
            import json
            salas.append(json.loads('{"id": %d, "nombre": "s%d", "salidas": {%s}}'
                                    % (i, i, ",".join(salidas))))
        return {"pagina": 1, "total_paginas": 1, "salas": salas}

    def contenido_salas(self, id_cripta, ids):
        self.presupuesto.registrar("contenido")
        time.sleep(self.latencia)
        self.lotes_contenido.append(list(ids))
        res = []
        for i in ids:
            res.append({"sala": i,
                        "enemigos": [{"instancia": "e%d" % i, "tipo": "ent_%d" % (i % 7),
                                      "vida": 5}],
                        "objetos": ["itm_%d" % (i % 5)], "trampas": []})
        return {"contenido": res}

    def catalogo(self, ids):
        self.presupuesto.registrar("catalogo")
        time.sleep(self.latencia)
        self.lotes_catalogo.append(list(ids))
        fichas = []
        for id_ in ids:
            f = {"id": id_, "clase": "enemigo" if id_.startswith("ent") else "arma"}
            if f["clase"] == "enemigo":
                f["suelta"] = ["itm_drop"]
            fichas.append(f)
        return {"entidades": fichas}


def armar(n=40, latencia=0.02, limite=None):
    presupuesto = PresupuestoRed(limite)
    fuente = FuenteFalsa(n, latencia, presupuesto)
    ejecutor = EjecutorRed()
    local = AlmacenLocalMemoria()
    resolutor = ResolutorCatalogo(fuente, ejecutor, local, presupuesto)
    esq = descargar_esqueleto(fuente, "c")
    pre = PrecargaContenido(fuente, "c", esq, ejecutor, presupuesto, resolutor)
    return fuente, ejecutor, resolutor, pre, presupuesto


class TestBitacora(unittest.TestCase):
    def test_solo_los_ultimos_20(self):
        b = BitacoraPantalla()
        for i in range(1, 51):
            b.agregar("m%d" % i)
        u = b.ultimos()
        self.assertEqual(len(u), 20)
        self.assertEqual(u[0], "m31")
        self.assertEqual(u[-1], "m50")
        self.assertEqual(len(b._mensajes), 20)
        self.assertEqual(b.total_historico, 50)

    def test_pocos_mensajes(self):
        b = BitacoraPantalla()
        b.agregar("a"); b.agregar("b")
        self.assertEqual(b.ultimos(), ["a", "b"])


class TestCliente(unittest.TestCase):
    def test_cabecera_429_y_conteo(self):
        sesion = SesionFalsa([RespuestaFalsa(429, {"error": "x", "reintentar_en": 3}),
                              RespuestaFalsa(200, {"ok": 1})])
        esperas = []
        p = PresupuestoRed(5)
        c = ClienteHTTP(p, sesion=sesion, dormir=esperas.append)
        self.assertEqual(c.listar_criptas(), {"ok": 1})
        self.assertEqual(esperas, [3.0])
        self.assertEqual(p.realizadas, 2)                 # el reintento cuenta
        self.assertEqual(sesion.llamadas[0][1]["X-Cripta-Client-Id"], c.client_id)
        self.assertEqual(sesion.llamadas[1][1]["X-Cripta-Client-Id"], c.client_id)
        self.assertIsNotNone(sesion.llamadas[0][2])       # timeout explícito

    def test_error_con_contexto(self):
        c = ClienteHTTP(sesion=SesionFalsa([RespuestaFalsa(500, None, "boom")]))
        with self.assertRaises(ErrorRed) as cm:
            c.datos_cripta("cripta-01")
        self.assertIn("datos generales de cripta-01", str(cm.exception))

    def test_presupuesto_se_respeta(self):
        p = PresupuestoRed(1)
        c = ClienteHTTP(p, sesion=SesionFalsa([RespuestaFalsa(200, {}), RespuestaFalsa(200, {})]))
        c.listar_criptas()
        with self.assertRaises(ErrorPresupuesto):
            c.listar_criptas()
        self.assertEqual(p.realizadas, 1)

    def test_lote_maximo(self):
        c = ClienteHTTP(sesion=SesionFalsa([]))
        with self.assertRaises(ValueError):
            c.catalogo(["a"] * 11)


class TestResolutor(unittest.TestCase):
    def test_lotes_sin_repetir(self):
        p = PresupuestoRed(None)
        f = FuenteFalsa(1, 0, p)
        e = EjecutorRed()
        local = AlmacenLocalMemoria()
        r = ResolutorCatalogo(f, e, local, p)
        ids = ["itm_%d" % i for i in range(25)]
        r.pedir(ids + ids[:5])                             # repetidos
        r.esperar()
        self.assertEqual(len(f.lotes_catalogo), 3)         # 10 + 10 + 5
        self.assertTrue(all(len(l) <= 10 for l in f.lotes_catalogo))
        r.pedir(ids)                                       # ya disponibles: sin red
        r.esperar()
        self.assertEqual(len(f.lotes_catalogo), 3)
        e.cerrar()

    def test_suelta_se_resuelve(self):
        p = PresupuestoRed(None)
        f = FuenteFalsa(1, 0, p)
        e = EjecutorRed()
        r = ResolutorCatalogo(f, e, AlmacenLocalMemoria(), p)
        r.esperar(["ent_1"])
        self.assertTrue(r.disponible("itm_drop"))
        e.cerrar()


class TestPrecarga(unittest.TestCase):
    def test_nunca_en_sala_sin_contenido_y_lotes(self):
        f, e, r, pre, p = armar()
        pre.iniciar(1)
        actual = 1
        for destino in range(2, 31):
            pre.asegurar(destino)
            self.assertTrue(pre.sala_lista(destino))
            pre.al_entrar(destino)
        todas = []
        for lote in f.lotes_contenido:
            self.assertLessEqual(len(lote), 10)
            todas += lote
        self.assertEqual(len(todas), len(set(todas)))      # ninguna sala dos veces
        e.cerrar()

    def test_orden_de_incorporacion_es_el_de_solicitud(self):
        f, e, r, pre, p = armar(latencia=0.01)
        pre.iniciar(1)
        pre.al_entrar(15)
        pre.al_entrar(30)
        pre.sondear()
        pre.asegurar(30)
        secuencias = [s.tarea.secuencia for s in pre._solicitudes]
        self.assertEqual(secuencias, sorted(secuencias))
        e.cerrar()

    def test_presupuesto_agotado_lanza_error(self):
        f, e, r, pre, p = armar(limite=1)
        with self.assertRaises(ErrorPresupuesto):
            pre.iniciar(1)                                  # contenido (1) + catálogo (no cabe)
        e.cerrar()


class _ManejadorFalso(BaseHTTPRequestHandler):
    ids_cliente = []
    rutas = []
    ya_limitado = [False]

    def log_message(self, *args):
        pass

    def _responder(self, codigo, cuerpo):
        datos = json.dumps(cuerpo).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        _ManejadorFalso.ids_cliente.append(self.headers.get("X-Cripta-Client-Id"))
        _ManejadorFalso.rutas.append(self.path)
        if self.headers.get("X-Cripta-Client-Id") is None:
            return self._responder(400, {"error": "falta X-Cripta-Client-Id"})
        if self.path.startswith("/v1/criptas/c1/contenido") and not _ManejadorFalso.ya_limitado[0]:
            _ManejadorFalso.ya_limitado[0] = True
            return self._responder(429, {"error": "demasiadas", "reintentar_en": 0})
        if self.path == "/v1/criptas":
            return self._responder(200, {"criptas": [{"id": "c1"}]})
        if self.path == "/v1/criptas/c1":
            return self._responder(200, {"id": "c1", "presupuesto_solicitudes": 9})
        if self.path.startswith("/v1/criptas/c1/contenido"):
            return self._responder(200, {"contenido": [{"sala": 1}]})
        if self.path.startswith("/v1/catalogo?ids="):
            return self._responder(200, {"entidades": []})
        self._responder(404, {"error": "no existe"})


class TestServidorLocal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.servidor = HTTPServer(("127.0.0.1", 0), _ManejadorFalso)
        cls.hilo = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.hilo.start()
        cls.base = "http://127.0.0.1:%d/v1" % cls.servidor.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()

    def test_flujo_completo_con_429(self):
        import requests
        sesion = requests.Session()
        sesion.trust_env = False                       # sin proxies del entorno
        p = PresupuestoRed(9)
        c = ClienteHTTP(p, base_url=self.base, sesion=sesion, dormir=lambda s: None)
        self.assertEqual(c.listar_criptas()["criptas"][0]["id"], "c1")
        datos = c.datos_cripta("c1")
        p.fijar_limite(datos["presupuesto_solicitudes"])
        self.assertEqual(c.contenido_salas("c1", [1, 2, 3])["contenido"][0]["sala"], 1)
        self.assertEqual(c.catalogo(["a", "b"]), {"entidades": []})
        self.assertEqual(p.realizadas, 5)              # 4 llamadas + 1 reintento por el 429
        self.assertEqual(c.esperas_429, 1)
        usados = set(i for i in _ManejadorFalso.ids_cliente if i == c.client_id)
        self.assertEqual(len(usados), 1)               # siempre el mismo UUID
        self.assertIn("/v1/criptas/c1/contenido?salas=1,2,3", _ManejadorFalso.rutas)
        with self.assertRaises(ErrorRed) as cm:
            c.version_catalogo()                       # el servidor falso responde 404
        self.assertIn("versión del catálogo", str(cm.exception))


if __name__ == "__main__":
    unittest.main()