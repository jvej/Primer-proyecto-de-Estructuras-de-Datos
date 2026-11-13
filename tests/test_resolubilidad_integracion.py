"""Regresiones de orquestación T026–T029, sin red ni interfaz gráfica real."""

from contextlib import redirect_stdout
from io import StringIO
import os
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import main
import controlador.aplicacion as modulo
from controlador.controlador import Controlador
from modelo.datos.presupuesto_red import PresupuestoRed
from modelo.juego.errores import ErrorCripta, ErrorPresupuesto, ErrorRed
from tests import crear_paquete_prueba
from tests.test_resolubilidad import _AlmacenMemoria, _FuenteMemoria, _integracion_memoria


def _entradas(sala_llave=1):
    datos = {"id": "sintetica", "version": "1", "sala_inicial": 1, "sala_salida": 2,
             "llave_salida": "itm_fin", "inventario_max": 5, "presupuesto_solicitudes": 100}
    salas = [{"id": 1, "salidas": {"E": {
        "sala": 2, "cerrada": True, "llave": "itm_fin"}}}, {"id": 2, "salidas": {}}]
    llaves = {"llaves": [{"id": "itm_fin", "sala": sala_llave}]}
    return datos, salas, llaves


class PruebasIntegracionResolubilidad(unittest.TestCase):
    def test_FR009_verificar_no_inicializa_motor_red_precarga_log_ni_puntajes(self):
        datos, salas, llaves = _entradas()
        fuente = _FuenteMemoria(datos, salas, llaves)
        almacen = _AlmacenMemoria(datos, salas, None)
        with _integracion_memoria(fuente, almacen) as (_, motor), patch.object(
                modulo, "BitacoraPartida") as log:
            app = modulo.Aplicacion(fuente, PresupuestoRed(100))
            with redirect_stdout(StringIO()) as salida:
                reporte = app.verificar("sintetica")
            self.assertIs(reporte, app.reporte_resolubilidad)
            self.assertEqual(reporte.estado, "RESOLUBLE")
            self.assertEqual(salida.getvalue(), "")
            self.assertEqual(app.partidas_creadas, 0)
            self.assertIsNone(app.partida)
            self.assertIsNone(app.precarga)
            self.assertIsNone(app.ejecutor)
            self.assertIsNone(app.log)
            self.assertIs(almacen.llaves, llaves)
            motor.assert_not_called()
            modulo.EjecutorRed.assert_not_called()
            modulo.PrecargaContenido.assert_not_called()
            log.assert_not_called()

    def test_FR015_error_transporta_reporte_y_sesion_vuelve_a_seleccionar(self):
        datos, salas, llaves = _entradas(sala_llave=2)
        fuente = _FuenteMemoria(datos, salas, llaves)
        almacen = _AlmacenMemoria(datos, salas, None)
        with _integracion_memoria(fuente, almacen) as (_, motor):
            app = modulo.Aplicacion(fuente, PresupuestoRed(100))
            with self.assertRaises(modulo.ErrorNoResoluble) as rechazo:
                app.crear_partida("sintetica")
            self.assertIs(rechazo.exception.reporte, app.reporte_resolubilidad)
            self.assertEqual(str(rechazo.exception), app.reporte_resolubilidad.formatear_reporte())
            self.assertIsNone(app.partida)
            vista = Mock()
            vista.elegir_cripta.side_effect = ["sintetica", None]
            controlador = Controlador(vista=vista)
            controlador.correr_sesion(lambda: [], app.crear_partida)
            self.assertEqual(vista.elegir_cripta.call_count, 2)
            vista.mostrar_aviso.assert_called_once_with(app.reporte_resolubilidad.formatear_reporte())
            motor.assert_not_called()

    def test_FR016_forzar_del_constructor_y_sobrescritura_por_partida(self):
        for valor_constructor, valor_partida, permitido in (
                (False, None, False), (True, None, True), (True, False, False), (False, True, True)):
            with self.subTest(constructor=valor_constructor, partida=valor_partida):
                datos, salas, llaves = _entradas(sala_llave=2)
                fuente = _FuenteMemoria(datos, salas, llaves)
                almacen = _AlmacenMemoria(datos, salas, None)
                with _integracion_memoria(fuente, almacen) as (_, motor):
                    app = modulo.Aplicacion(fuente, PresupuestoRed(100), registrar_log=False,
                                            forzar=valor_constructor)
                    if permitido:
                        self.assertIs(app.crear_partida("sintetica", forzar=valor_partida),
                                      motor.return_value)
                    else:
                        with self.assertRaises(modulo.ErrorNoResoluble):
                            app.crear_partida("sintetica", forzar=valor_partida)
                        motor.assert_not_called()
                    self.assertEqual(fuente.consultas_llaves, 1)
                    self.assertEqual(app.reporte_resolubilidad.estado, "NO RESOLUBLE")
                    app.cerrar()

    def test_FR009_reconstruccion_guardado_y_replay_no_consultan_ni_verifican(self):
        for opciones in ({"ordenes_previas": []}, {"partida_nueva": False},
                         {"exigir_versiones": ("1", "sintetica")}):
            with self.subTest(opciones=opciones):
                datos, salas, llaves = _entradas(sala_llave=2)
                fuente = _FuenteMemoria(datos, salas, llaves,
                                        ErrorRed("llaves", "no debe consultarse"))
                almacen = _AlmacenMemoria(datos, salas, None)
                with _integracion_memoria(fuente, almacen) as (_, motor), patch.object(
                        modulo, "verificar_resolubilidad", side_effect=AssertionError("verificación")):
                    app = modulo.Aplicacion(fuente, PresupuestoRed(100), registrar_log=False)
                    self.assertIs(app.crear_partida("sintetica", **opciones), motor.return_value)
                    self.assertEqual(fuente.consultas_llaves, 0)
                    self.assertIsNone(app.reporte_resolubilidad)
                    app.cerrar()

    def test_FR004_contingencia_red_y_presupuesto_bloquea_salvo_forzar(self):
        for error in (ErrorRed("llaves", "conexión interrumpida"), ErrorPresupuesto("llaves", 0)):
            for forzar in (False, True):
                with self.subTest(error=type(error).__name__, forzar=forzar):
                    datos, salas, llaves = _entradas()
                    fuente = _FuenteMemoria(datos, salas, llaves, error)
                    almacen = _AlmacenMemoria(datos, salas, None)
                    with _integracion_memoria(fuente, almacen) as (_, motor):
                        app = modulo.Aplicacion(fuente, PresupuestoRed(100), registrar_log=False,
                                                forzar=forzar)
                        if forzar:
                            app.crear_partida("sintetica")
                            motor.assert_called_once()
                        else:
                            with self.assertRaises(modulo.ErrorNoResoluble):
                                app.crear_partida("sintetica")
                            motor.assert_not_called()
                            self.assertIsNone(app.partida)
                        self.assertEqual(app.reporte_resolubilidad.estado, "NO VERIFICADA")
                        self.assertIn(str(error), app.reporte_resolubilidad.motivo)
                        self.assertIsNone(almacen.llaves)
                        app.cerrar()

    def test_FR004_copia_local_evade_consulta_aunque_fuente_falle(self):
        datos, salas, llaves = _entradas()
        fuente = _FuenteMemoria(datos, salas, llaves, ErrorPresupuesto("llaves", 0))
        almacen = _AlmacenMemoria(datos, salas, llaves)
        with _integracion_memoria(fuente, almacen):
            app = modulo.Aplicacion(fuente, PresupuestoRed(100))
            self.assertEqual(app.verificar("sintetica").estado, "RESOLUBLE")
            self.assertEqual(fuente.consultas_llaves, 0)

    def test_FR005_cambio_version_no_reutiliza_llaves_anteriores(self):
        datos, salas, llaves = _entradas()
        fuente = _FuenteMemoria(datos, salas, llaves)
        with TemporaryDirectory() as carpeta:
            app = modulo.Aplicacion(fuente, PresupuestoRed(100), carpeta)
            self.assertEqual(app.verificar("sintetica").estado, "RESOLUBLE")
            self.assertEqual(app.verificar("sintetica").estado, "RESOLUBLE")
            self.assertEqual(fuente.consultas_llaves, 1)
            fuente.datos = {**datos, "version": "2"}
            fuente.ubicaciones = {"llaves": [{"id": "itm_fin", "sala": 2}]}
            self.assertEqual(app.verificar("sintetica").estado, "NO RESOLUBLE")
            self.assertEqual(fuente.consultas_llaves, 2)

    def test_FR012_abre_solo_se_lee_de_fichas_locales_sin_pedir_catalogo(self):
        datos, salas, llaves = _entradas()
        llaves = {"llaves": [{"id": "itm_maestra", "sala": 1}]}
        fuente = _FuenteMemoria(datos, salas, llaves)
        with TemporaryDirectory() as carpeta, patch.object(
                fuente, "catalogo", create=True, side_effect=AssertionError("Solicitud de catálogo")):
            app = modulo.Aplicacion(fuente, PresupuestoRed(100), carpeta)
            self.assertEqual(app.verificar("sintetica").estado, "NO RESOLUBLE")
            app.local.guardar("itm_maestra", {"id": "itm_maestra", "abre": "itm_fin"})
            # Una aplicación nueva recupera también la ficha del disco, sin red.
            otra = modulo.Aplicacion(fuente, PresupuestoRed(100), carpeta)
            self.assertEqual(otra.verificar("sintetica").estado, "RESOLUBLE")
            self.assertEqual(fuente.consultas_llaves, 1)

    def test_FR015_rechazo_despues_de_partida_anterior_deja_partida_en_none(self):
        datos, salas, llaves = _entradas(sala_llave=2)
        fuente = _FuenteMemoria(datos, salas, llaves)
        almacen = _AlmacenMemoria(datos, salas, None)
        with _integracion_memoria(fuente, almacen):
            app = modulo.Aplicacion(fuente, PresupuestoRed(100), registrar_log=False)
            app.crear_partida("sintetica", forzar=True)
            ejecutor = app.ejecutor
            with self.assertRaises(modulo.ErrorNoResoluble):
                app.crear_partida("sintetica")
            self.assertIsNone(app.partida)
            self.assertIsNone(app.precarga)
            self.assertIsNone(app.ejecutor)
            ejecutor.cerrar.assert_called_once()

    def test_FR017_errores_en_datos_catalogo_y_esqueleto_solo_imprimen_reporte(self):
        for metodo in ("datos_cripta", "version_catalogo", "pagina_esqueleto"):
            with self.subTest(metodo=metodo):
                datos, salas, llaves = _entradas()
                fuente = _FuenteMemoria(datos, salas, llaves)
                almacen = _AlmacenMemoria(datos, salas, None)
                with _integracion_memoria(fuente, almacen) as (_, motor), patch.object(
                        almacen, "tiene_pagina", return_value=False), patch.object(
                        fuente, metodo, side_effect=ErrorCripta("causa sintética")), patch.object(
                        main, "crear_fuente_datos", return_value=(fuente, PresupuestoRed(100))), patch.object(
                        main, "crear_vista", side_effect=AssertionError("Vista creada")):
                    with redirect_stdout(StringIO()) as salida:
                        codigo = main.main(["--verificar", "sintetica", "--gui"])
                    self.assertEqual(codigo, 2)
                    self.assertEqual(salida.getvalue(),
                                     "ESTADO: NO VERIFICADA\nMOTIVO: causa sintética\n")
                    motor.assert_not_called()

    def test_FR017_cli_offline_real_no_crea_vista_log_precarga_ni_puntajes(self):
        with TemporaryDirectory() as carpeta:
            paquete = crear_paquete_prueba.crear(os.path.join(carpeta, "paquete"))
            datos = os.path.join(carpeta, "datos")
            with patch.object(main, "crear_vista", side_effect=AssertionError("Vista creada")), patch.object(
                    modulo, "Partida", side_effect=AssertionError("Partida creada")), patch.object(
                    modulo, "PrecargaContenido", side_effect=AssertionError("Precarga creada")), patch.object(
                    modulo, "BitacoraPartida", side_effect=AssertionError("Log creado")), patch(
                    "requests.sessions.Session.request", side_effect=AssertionError("Red en offline")):
                for id_cripta, esperado, estado in (
                        (crear_paquete_prueba.ID, 0, "RESOLUBLE"),
                        (crear_paquete_prueba.ID_CICLO, 1, "NO RESOLUBLE"),
                        ("inexistente", 2, "NO VERIFICADA")):
                    with self.subTest(cripta=id_cripta), redirect_stdout(StringIO()) as salida:
                        codigo = main.main(["--offline", paquete, "--datos", datos,
                                            "--verificar", id_cripta, "--forzar", "--gui"])
                    self.assertEqual(codigo, esperado)
                    self.assertTrue(salida.getvalue().startswith("ESTADO: " + estado + "\n"))
                self.assertFalse(os.path.exists(os.path.join(datos, "puntajes.txt")))
                self.assertFalse(os.path.exists(os.path.join(datos, "partidas")))

    def test_FR016_cli_interactivo_propaga_forzar(self):
        vista = Mock()
        argumentos = main.leer_argumentos(["--forzar", "--nombre", "Prueba"])
        with patch.object(main, "crear_fuente_datos", return_value=(Mock(), Mock())), patch.object(
                main, "crear_vista", return_value=vista), patch.object(main, "Aplicacion") as aplicacion, patch.object(
                main, "Controlador"), redirect_stdout(StringIO()):
            aplicacion.return_value.partida = None
            self.assertEqual(main.correr_interactivo(argumentos), 0)
        self.assertTrue(aplicacion.call_args.kwargs["forzar"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
