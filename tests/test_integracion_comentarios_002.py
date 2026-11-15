"""C4/FR-022: conexión de comentarios con Aplicacion y su log activo."""

import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

import main
from controlador.controlador import Controlador
from controlador.orden import CARGAR, IR_A, MOVER, Orden
from modelo.datos.bitacora_partida import leer_log
from tests.test_replay_puntajes import Entorno, JUGADAS


class PruebasComentariosIntegrados(unittest.TestCase):
    def setUp(self):
        self.entorno = Entorno()
        self.addCleanup(self.entorno.borrar)

    def preparar(self):
        app, controlador = self.entorno.jugar(JUGADAS)
        self.addCleanup(app.cerrar)
        controlador.agregar_observador_comentarios(app.registrar_comentario)
        return app, controlador

    def leer(self, ruta):
        return Path(ruta).read_text(encoding="utf-8")

    def test_FR022_un_comentario_movimientos_y_replay(self):
        app, controlador = self.preparar()
        log = app.log
        anteriores = log.lineas
        ordenes_anteriores = len(app.ordenes)
        self.assertTrue(controlador.ejecutar(Orden(IR_A, 1)))
        texto = self.leer(log.ruta)
        self.assertEqual(texto.splitlines().count("# ir a 1"), 1)
        self.assertEqual(app.ordenes[-1], Orden(MOVER, "S"))
        self.assertEqual(len(app.ordenes), ordenes_anteriores + 1)
        self.assertEqual(log.lineas, anteriores + 1)
        self.assertEqual(texto.splitlines()[-2:], ["# ir a 1", "mover S"])
        _, reproducibles = leer_log(log.ruta)
        obtenidas = []
        while not reproducibles.vacia():
            obtenidas.append(reproducibles.sacar())
        self.assertEqual(obtenidas, app.ordenes)

    def test_FR014_rechazado_no_comenta(self):
        app, controlador = self.preparar()
        antes = self.leer(app.log.ruta)
        tiempo = controlador.partida.reloj.tiempo_actual
        self.assertFalse(controlador.ejecutar(Orden(IR_A, 999999)))
        self.assertEqual(self.leer(app.log.ruta), antes)
        self.assertEqual(controlador.partida.reloj.tiempo_actual, tiempo)

    def test_FR022_carga_normal_cambia_log_sin_resuscribir(self):
        app, controlador = self.preparar()
        original = controlador.partida
        controlador.persistencia.guardar(original)
        viejo = app.log
        self.assertTrue(controlador.ejecutar(Orden(IR_A, 1)))
        contenido_viejo = self.leer(viejo.ruta)
        self.assertTrue(controlador.ejecutar(Orden(CARGAR)))
        self.assertIsNot(controlador.partida, original)
        self.assertIs(controlador.partida, app.partida)
        self.assertEqual(controlador.partida.jugador.sala.id, 2)
        self.assertIsNot(app.log, viejo)
        self.assertIsNone(viejo._archivo)
        self.assertNotEqual(app.log.ruta, viejo.ruta)
        self.assertEqual(len(controlador._observadores_comentarios), 1)
        self.assertEqual(len(controlador._observadores), 1)
        self.assertTrue(controlador.ejecutar(Orden(IR_A, 1)))
        self.assertEqual(self.leer(viejo.ruta), contenido_viejo)
        self.assertEqual(self.leer(app.log.ruta).splitlines().count("# ir a 1"), 1)
        self.assertEqual(self.leer(app.log.ruta).splitlines()[-1], "mover S")

    def test_FR022_sin_log_activo_no_falla(self):
        app = self.entorno.aplicacion(registrar_log=False)
        self.addCleanup(app.cerrar)
        self.assertIsNone(app.log)
        app.registrar_comentario("ir a 1")
        self.assertEqual(app.ordenes, [])

    def test_C4_main_suscribe_una_vez_al_mismo_objeto_aplicacion(self):
        inspecciones = []

        def inspeccionar(controlador, listar, crear):
            self.assertEqual(len(controlador._observadores), 1)
            self.assertEqual(len(controlador._observadores_comentarios), 1)
            orden = controlador._observadores[0]
            comentario = controlador._observadores_comentarios[0]
            self.assertEqual(comentario.__name__, "registrar_comentario")
            self.assertIs(comentario.__self__, orden.__self__)
            self.assertIs(comentario.__self__, crear.__self__)
            comentario("ir a 1")  # Sin partida/log todavía.
            inspecciones.append(True)

        argumentos = main.leer_argumentos([
            "--offline", self.entorno.paquete, "--datos", self.entorno.datos,
            "--nombre", "Prueba",
        ])
        with patch.object(Controlador, "correr_sesion", inspeccionar):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main.correr_interactivo(argumentos), 0)
        self.assertEqual(inspecciones, [True])


if __name__ == "__main__":
    unittest.main()
