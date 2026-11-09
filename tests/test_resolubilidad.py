"""Aceptación TDD de T003–T010; ejecutar con python -m tests.test_resolubilidad.

Las respuestas sintéticas son registros de entrada, nunca índices ni cachés.
No se simula el verificador: su importación debe fallar hasta implementar T018.
Las interfaces nuevas de integración (forzar en crear_partida) quedan expresadas
como expectativas de estas pruebas; no se agrega código de producción.
"""

from contextlib import ExitStack, contextmanager, redirect_stdout
from io import StringIO
from unittest.mock import patch

from modelo.datos.cliente_http import ClienteHTTP
from modelo.datos.cliente_offline import ClienteOffline
from modelo.datos.esqueleto import Esqueleto
from modelo.datos.fuente_almacen import FuenteAlmacen
from modelo.datos.presupuesto_red import PresupuestoRed
from modelo.juego.errores import ErrorCripta, ErrorPresupuesto, ErrorRed
from modelo.juego.resolubilidad import ResultadoResolubilidad, verificar_resolubilidad


def _esqueleto(salas):
    resultado = Esqueleto()
    resultado.agregar_pagina({"salas": salas})
    return resultado


class _Respuesta:
    def __init__(self, codigo, cuerpo):
        self.status_code = codigo
        self.cuerpo = cuerpo
        self.text = "respuesta sintética"

    def json(self):
        return self.cuerpo


class _Sesion:
    def __init__(self, respuestas):
        self.respuestas = respuestas
        self.llamadas = []

    def get(self, url, **opciones):
        self.llamadas.append(url)
        assert self.respuestas, "Solicitud HTTP inesperada"
        return self.respuestas.pop(0)


class _AlmacenMemoria:
    """Solo sustituye persistencia; conserva generales, páginas y llaves."""

    def __init__(self, datos, salas, llaves):
        self.datos = datos
        self.salas = salas
        self.llaves = llaves

    def tiene_generales(self):
        return True

    def leer_generales(self):
        return self.datos

    def tiene_pagina(self, pagina):
        return pagina == 1

    def leer_pagina(self, pagina):
        assert pagina == 1
        return {"salas": self.salas, "total_paginas": 1}

    def tiene_llaves(self):
        return self.llaves is not None

    def leer_llaves(self):
        assert self.llaves is not None
        return self.llaves

    def guardar_llaves(self, datos):
        self.llaves = datos


class _FuenteMemoria:
    def __init__(self, datos, salas, llaves, error=None):
        self.datos = datos
        self.salas = salas
        self.ubicaciones = llaves
        self.error = error
        self.consultas_llaves = 0

    def datos_cripta(self, id_cripta):
        if isinstance(self.error, ErrorRed) and self.error.codigo == 404:
            raise self.error
        return self.datos

    def version_cripta(self, id_cripta):
        return {"version": self.datos["version"]}

    def version_catalogo(self):
        return {"version": "sintetica"}

    def pagina_esqueleto(self, id_cripta, pagina):
        assert pagina == 1
        return {"salas": self.salas, "total_paginas": 1}

    def llaves(self, id_cripta):
        self.consultas_llaves += 1
        if self.error is not None:
            raise self.error
        return self.ubicaciones


@contextmanager
def _integracion_memoria(fuente, almacen):
    """Aísla disco, red y motor; mantiene la orquestación bajo prueba."""
    import controlador.aplicacion as aplicacion

    with ExitStack() as pila:
        pila.enter_context(patch.object(aplicacion.os, "makedirs"))
        pila.enter_context(patch.object(aplicacion, "AlmacenCripta", return_value=almacen))
        pila.enter_context(patch.object(aplicacion, "AlmacenFichas"))
        pila.enter_context(patch.object(aplicacion, "AlmacenLocalCache"))
        pila.enter_context(patch.object(aplicacion, "EjecutorRed"))
        pila.enter_context(patch.object(aplicacion, "ResolutorCatalogo"))
        pila.enter_context(patch.object(aplicacion, "PrecargaContenido"))
        motor = pila.enter_context(patch.object(aplicacion, "Partida"))
        # Cualquier intento accidental de red real falla inmediatamente.
        pila.enter_context(patch("requests.sessions.Session.request",
                                side_effect=AssertionError("Red real prohibida")))
        yield aplicacion, motor


def test_FR014_llave_salida_detras_de_su_propia_puerta_con_ciclo():
    salas = [
        {"id": 1, "salidas": {"E": {"sala": 2, "cerrada": True, "llave": "itm_salida"}}},
        {"id": 2, "salidas": {"O": {"sala": 1}}},
    ]
    llaves = [{"id": "itm_salida", "sala": 2}]
    for entrada in (salas, salas[::-1]):
        reporte = verificar_resolubilidad(_esqueleto(entrada), llaves, 1, 2, "itm_salida")
        assert reporte.estado == "NO RESOLUBLE"
        assert not reporte.es_resoluble()
        assert reporte.llaves_no_obtenibles == ["itm_salida"]
        assert reporte.frontera_bloqueada == [(1, "E", 2, "itm_salida")]
        assert reporte.ubicacion_llaves == [("itm_salida", "sala 2")]
        assert reporte.ciclos == ["itm_salida -> itm_salida [sala 1 (E)]"]


def test_FR002_llave_en_suelta_de_errante_en_sala_inicial():
    salas = [
        {"id": 1, "salidas": {"N": {"sala": 2, "cerrada": True, "llave": "itm_salida",
                                     "cierre_automatico": 1}}},
        {"id": 2, "salidas": {"S": {"sala": 1}}},
    ]
    enemigo = {"instancia": "e-sintetico", "comportamiento": "errante",
               "suelta": ["itm_salida"]}
    llaves = [{"id": enemigo["suelta"][0], "sala": 1, "enemigo": enemigo["instancia"]}]
    reporte = verificar_resolubilidad(_esqueleto(salas), llaves, 1, 2, "itm_salida")
    assert reporte.es_resoluble()
    assert reporte.orden_llaves == [(0, ["itm_salida"])]
    # La misma llave en un enemigo inicialmente inaccesible no está disponible.
    inaccesible = [{"id": "itm_salida", "sala": 2, "enemigo": enemigo["instancia"]}]
    reporte = verificar_resolubilidad(_esqueleto(salas), inaccesible, 1, 2, "itm_salida")
    assert not reporte.es_resoluble()
    assert reporte.ubicacion_llaves == [
        ("itm_salida", "sala 2 (suelta del enemigo e-sintetico)")]


def test_FR013_varios_ordenes_validos_mismo_orden_determinista():
    salas = [
        {"id": 1, "salidas": {"N": {"sala": 2}, "E": {"sala": 3}}},
        {"id": 2, "salidas": {"N": {"sala": 4, "cerrada": True, "llave": "itm_2"}}},
        {"id": 3, "salidas": {"E": {"sala": 5, "cerrada": True, "llave": "itm_10"}}},
        {"id": 4, "salidas": {"N": {"sala": 6, "cerrada": True, "llave": "itm_salida"}}},
        {"id": 5, "salidas": {"O": {"sala": 4}}},
        {"id": 6, "salidas": {"S": {"sala": 4}}},
    ]
    llaves = [{"id": "itm_2", "sala": 2}, {"id": "itm_10", "sala": 3},
              {"id": "itm_salida", "sala": 4}, {"id": "itm_0", "sala": 5}]
    esperado = [(0, ["itm_10", "itm_2"]), (1, ["itm_0", "itm_salida"])]
    textos = []
    for entrada, ubicaciones in ((salas, llaves), (salas[::-1], llaves[::-1]), (salas, llaves)):
        reporte = verificar_resolubilidad(_esqueleto(entrada), ubicaciones, 1, 6, "itm_salida")
        assert reporte.es_resoluble()
        assert reporte.orden_llaves == esperado
        textos.append(reporte.formatear_reporte())
    assert textos[0] == textos[1] == textos[2]


def test_FR015_cripta_no_resoluble_sin_forzar_no_inicia():
    from main import leer_argumentos

    salas = [{"id": 1, "salidas": {"E": {"sala": 2, "cerrada": True, "llave": "itm_fin"}}},
             {"id": 2, "salidas": {"O": {"sala": 1}}}]
    datos = {"id": "sintetica", "version": "1", "sala_inicial": 1, "sala_salida": 2,
             "llave_salida": "itm_fin", "inventario_max": 5, "presupuesto_solicitudes": 100}
    llaves = {"llaves": [{"id": "itm_fin", "sala": 2}]}
    for opciones, debe_iniciar in (([], False), (["--forzar"], True)):
        argumentos = leer_argumentos(opciones)
        fuente = _FuenteMemoria(datos, salas, llaves)
        almacen = _AlmacenMemoria(datos, salas, None)
        with _integracion_memoria(fuente, almacen) as (modulo, motor):
            app = modulo.Aplicacion(fuente, PresupuestoRed(100), semilla=7,
                                    registrar_log=False, registrar_puntajes=False)
            try:
                try:
                    app.crear_partida("sintetica", forzar=argumentos.forzar)
                except ErrorCripta:
                    assert not debe_iniciar
                if debe_iniciar:
                    motor.assert_called_once()
                    motor.return_value.iniciar.assert_called_once()
                    assert app.partida is motor.return_value
                else:
                    motor.assert_not_called()
                    assert app.partida is None
                assert isinstance(app.reporte_resolubilidad, ResultadoResolubilidad)
                assert app.reporte_resolubilidad.estado == "NO RESOLUBLE"
            finally:
                app.cerrar()


def test_FR003_endpoint_llaves_cuenta_en_presupuesto_solicitudes():
    cuerpo = {"llaves": [{"id": "itm_fin", "sala": 1}]}
    for codigos in ((200,), (429, 200)):
        presupuesto = PresupuestoRed(4)
        respuestas = [_Respuesta(c, cuerpo if c == 200 else {"reintentar_en": 0}) for c in codigos]
        sesion = _Sesion(respuestas)
        cliente = ClienteHTTP(presupuesto, sesion=sesion, dormir=lambda segundos: None)
        assert cliente.llaves("sintetica") == cuerpo
        assert presupuesto.realizadas == len(codigos)
        assert presupuesto.restantes() == 4 - len(codigos)
        assert sesion.llamadas == [cliente.base_url + "/criptas/sintetica/llaves"] * len(codigos)
    presupuesto = PresupuestoRed(1)
    sesion = _Sesion([_Respuesta(429, {"reintentar_en": 0})])
    cliente = ClienteHTTP(presupuesto, sesion=sesion, dormir=lambda segundos: None)
    try:
        cliente.llaves("sintetica")
    except ErrorPresupuesto:
        pass
    else:
        raise AssertionError("El reintento debe detenerse al agotar el presupuesto")
    assert presupuesto.realizadas == 1 and len(sesion.llamadas) == 1

    # Copia local de la misma versión, a través de la orquestación real.
    salas = [{"id": 1, "salidas": {"E": {"sala": 2, "cerrada": True, "llave": "itm_fin"}}},
             {"id": 2, "salidas": {"O": {"sala": 1}}}]
    datos = {"id": "sintetica", "version": "1", "sala_inicial": 1, "sala_salida": 2,
             "llave_salida": "itm_fin", "inventario_max": 5, "presupuesto_solicitudes": 100}
    fuente = _FuenteMemoria(datos, salas, cuerpo)
    almacen = _AlmacenMemoria(datos, salas, cuerpo)
    with _integracion_memoria(fuente, almacen) as (modulo, motor):
        app = modulo.Aplicacion(fuente, PresupuestoRed(100), semilla=7,
                                registrar_log=False, registrar_puntajes=False)
        try:
            app.crear_partida("sintetica")
            assert fuente.consultas_llaves == 0
            motor.return_value.iniciar.assert_called_once()
        finally:
            app.cerrar()
    local = FuenteAlmacen("sintetica", almacen, "1", None, "1")
    assert local.llaves("sintetica") == cuerpo
    offline = ClienteOffline("paquete-en-memoria")
    # Sustituir únicamente lectura física; el método llaves real resuelve la ruta.
    with patch.object(offline, "_leer", return_value=cuerpo) as lectura, patch(
            "requests.sessions.Session.request", side_effect=AssertionError("Red en offline")):
        assert offline.llaves("sintetica") == cuerpo
        lectura.assert_called_once()
        assert str(lectura.call_args.args[1]).replace("\\", "/").endswith(
            "/criptas/sintetica/llaves.json")
    assert offline.presupuesto.realizadas == 0


def test_FR017_codigos_salida_verificar():
    import main

    salas = [{"id": 1, "salidas": {"E": {"sala": 2, "cerrada": True, "llave": "itm_fin"}}},
             {"id": 2, "salidas": {"O": {"sala": 1}}}]
    datos = {"id": "sintetica", "version": "1", "sala_inicial": 1, "sala_salida": 2,
             "llave_salida": "itm_fin", "inventario_max": 5, "presupuesto_solicitudes": 100}
    casos = [(1, None, 0, "RESOLUBLE"), (2, None, 1, "NO RESOLUBLE"),
             (1, ErrorRed("llaves", "error de red"), 2, "NO VERIFICADA"),
             (1, ErrorPresupuesto("llaves", 0), 2, "NO VERIFICADA"),
             (1, ErrorRed("cripta", "cripta inexistente", 404), 2, "NO VERIFICADA")]
    for sala_llave, error, codigo, estado in casos:
        llaves = {"llaves": [{"id": "itm_fin", "sala": sala_llave}]}
        fuente = _FuenteMemoria(datos, salas, llaves, error)
        almacen = _AlmacenMemoria(datos, salas, None)
        with _integracion_memoria(fuente, almacen) as (_, motor), patch.object(
                main, "crear_fuente_datos", return_value=(fuente, PresupuestoRed(100))), patch.object(
                main, "crear_vista", side_effect=AssertionError("--verificar creó una vista")) as vista:
            salida = StringIO()
            with redirect_stdout(salida):
                obtenido = main.main(["--verificar", "sintetica"])
            assert obtenido == codigo, salida.getvalue()
            assert salida.getvalue().startswith("ESTADO: " + estado + "\n")
            if codigo == 2:
                assert "MOTIVO:" in salida.getvalue()
            vista.assert_not_called()
            motor.assert_not_called()


def test_FR018_plantilla_exacta_reporte():
    reporte = ResultadoResolubilidad("RESOLUBLE", orden_llaves=[(0, ["itm_a", "itm_b"]),
                                                              (1, ["itm_c"])])
    assert reporte.formatear_reporte() == (
        "ESTADO: RESOLUBLE\nORDEN DE LLAVES:\n  etapa 0: itm_a, itm_b\n  etapa 1: itm_c")
    reporte = ResultadoResolubilidad(
        "NO RESOLUBLE", llaves_no_obtenibles=["itm_a", "itm_b"],
        frontera_bloqueada=[(4, "N", 7, "itm_a"), (4, "S", 8, None),
                            (4, "E", 9, "itm_b"), (4, "O", 10, None)],
        ubicacion_llaves=[("itm_a", "sala 12"), ("itm_b", "sala 9 (suelta del enemigo e-prueba)")],
        ciclos=["itm_a -> itm_b [sala 4 (E)] -> itm_a [sala 4 (N)]"])
    assert reporte.formatear_reporte() == (
        "ESTADO: NO RESOLUBLE\n"
        "LLAVES NO OBTENIBLES: itm_a, itm_b\n"
        "FRONTERA BLOQUEADA:\n"
        "  - sala 4 (N) -> sala 7: pide itm_a\n"
        "  - sala 4 (S) -> sala 8: sin llave asociada\n"
        "  - sala 4 (E) -> sala 9: pide itm_b\n"
        "  - sala 4 (O) -> sala 10: sin llave asociada\n"
        "UBICACIÓN DE LLAVES:\n"
        "  - itm_a: sala 12\n"
        "  - itm_b: sala 9 (suelta del enemigo e-prueba)\n"
        "CICLOS DETECTADOS:\n"
        "  - itm_a -> itm_b [sala 4 (E)] -> itm_a [sala 4 (N)]")
    for estado, motivo in (
            ("NO RESOLUBLE", "no existe puerta hacia sala_salida que pida llave_salida"),
            ("NO VERIFICADA", "no se pudo consultar /llaves: presupuesto_solicitudes agotado")):
        assert ResultadoResolubilidad(estado, motivo=motivo).formatear_reporte() == (
            "ESTADO: " + estado + "\nMOTIVO: " + motivo)
    assert ResultadoResolubilidad("NO VERIFICADA").formatear_reporte() == "ESTADO: NO VERIFICADA"


if __name__ == "__main__":
    pruebas = (
        test_FR014_llave_salida_detras_de_su_propia_puerta_con_ciclo,
        test_FR002_llave_en_suelta_de_errante_en_sala_inicial,
        test_FR013_varios_ordenes_validos_mismo_orden_determinista,
        test_FR015_cripta_no_resoluble_sin_forzar_no_inicia,
        test_FR003_endpoint_llaves_cuenta_en_presupuesto_solicitudes,
        test_FR017_codigos_salida_verificar,
        test_FR018_plantilla_exacta_reporte,
    )
    for prueba in pruebas:
        prueba()
        print("OK ", prueba.__name__)
    print("Todas las pruebas pasaron")
