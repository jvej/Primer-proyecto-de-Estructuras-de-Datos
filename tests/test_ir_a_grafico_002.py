"""IR_A gráfico: eventos simulados, cancelación y pergamino diferido."""

import contextlib
import importlib
import io
import unittest
from unittest.mock import Mock, patch

import main
from controlador.controlador import Controlador
from controlador.orden import ESPERAR, IR_A, MOVER, PERGAMINO, SALIR, Orden
from tests.cripta_de_prueba import armar, esqueleto_linea
from tests.test_gui import _vista_dialogo_prueba
from tests.test_replay_puntajes import Entorno
from vista.animaciones_gui import Animador, CORRER


class PruebasViajeGrafico(unittest.TestCase):
    def setUp(self):
        self.pg = importlib.import_module("pygame")
        self.pg.display.init()
        self.addCleanup(self.pg.display.quit)
        self.pg.event.clear()
        self.esc = armar(esqueleto_linea(5), datos={"sala_salida": 5})
        self.addCleanup(self.esc.cerrar)
        self.p = self.esc.partida

    def tecla(self, key, unicode=""):
        return self.pg.event.Event(self.pg.KEYDOWN, key=key, unicode=unicode, mod=0)

    def vista(self, lotes):
        v, textos, cuadros = _vista_dialogo_prueba(lotes)
        v.partida = self.p
        v.animador = Animador()
        v.animador.reiniciar(self.p)
        v.ultima_orden = None
        v.centros = []
        v.entrando_por = v.volver_de = None
        v.entrando_ms = 600
        v.enemigo_elegido = v.objeto_elegido = 0
        v.sonidos = Mock()
        v._sonar_mensajes = Mock()
        v._dibujar_partida = Mock()
        v.mostrar_aviso = Mock()
        return v, textos

    def conocer(self):
        for sala in self.p.mapa.salas:
            self.p._explorar_sala(sala)
            for salida in sala.salidas:
                if salida is not None:
                    self.p._recordar_puerta(salida)

    def viajar(self, v):
        self.conocer()
        c = Controlador(self.p, v)
        c.agregar_observador_viaje(v.atender_viaje)
        c.ejecutar(v._entregar(Orden(IR_A, 4)))
        return c

    def test_A_V_abre_dialogo_y_devuelve_orden_sin_mover(self):
        self.p._explorar_sala(self.p.mapa.sala(4))
        v, _ = self.vista([[self.tecla(self.pg.K_v)],
                           [self.tecla(self.pg.K_4, "4"), self.tecla(self.pg.K_RETURN)]])
        self.assertEqual(v.pedir_orden(self.p), Orden(IR_A, 4))
        self.assertEqual((self.p.acciones, self.p.reloj.tiempo_actual), (0, 0))

    def test_B_cancelar_dialogo_vuelve_a_entrada_normal(self):
        v, _ = self.vista([[self.tecla(self.pg.K_v)], [self.tecla(self.pg.K_ESCAPE)],
                           [self.tecla(self.pg.K_x)]])
        self.assertEqual(v.pedir_orden(self.p), Orden(ESPERAR))
        self.assertEqual(self.p.acciones, 0)

    def test_C_escape_antes_del_primer_paso(self):
        v, _ = self.vista([[self.tecla(self.pg.K_ESCAPE)]])
        c = self.viajar(v)
        self.assertFalse(c.terminado)
        self.assertFalse(v.cerrada)
        self.assertEqual((self.p.acciones, self.p.reloj.tiempo_actual), (0, 0))

    def test_D_escape_despues_de_dos_pasos(self):
        v, _ = self.vista([[], [], [self.tecla(self.pg.K_ESCAPE)]])
        c = self.viajar(v)
        self.assertEqual((self.p.jugador.sala.id, self.p.acciones,
                          self.p.reloj.tiempo_actual), (3, 2, 200))
        self.assertFalse(c._viaje_activo)
        self.assertFalse(c.terminado)

    def test_E_F_R_diferida_unica_revierte_ultimo_paso(self):
        self.esc.dar("itm_pergamino")
        v, _ = self.vista([[], [], [self.tecla(self.pg.K_r), self.tecla(self.pg.K_r)],
                           [self.tecla(self.pg.K_x)]])
        c = self.viajar(v)
        self.assertEqual((self.p.jugador.sala.id, self.p.acciones), (3, 2))
        orden = v.pedir_orden(self.p)
        self.assertEqual(orden, Orden(PERGAMINO))
        self.assertIsNone(v._orden_pendiente)
        self.assertTrue(c.ejecutar(orden))
        self.assertEqual((self.p.jugador.sala.id, self.p.acciones,
                          self.p.reloj.tiempo_actual), (2, 1, 100))
        self.assertEqual(v.pedir_orden(self.p), Orden(ESPERAR))

    def test_G_cambio_partida_descarta_pendiente(self):
        v, _ = self.vista([[self.tecla(self.pg.K_r)], [self.tecla(self.pg.K_x)]])
        self.assertFalse(v.atender_viaje(self.p))
        otro = armar(esqueleto_linea(2))
        self.addCleanup(otro.cerrar)
        self.assertEqual(v.pedir_orden(otro.partida), Orden(ESPERAR))
        self.assertIsNone(v._orden_pendiente)

    def test_H_QUIT_descarta_pendiente(self):
        v, _ = self.vista([[self.tecla(self.pg.K_r)],
                           [self.pg.event.Event(self.pg.QUIT)]])
        v.atender_viaje(self.p)
        self.assertIsNotNone(v._orden_pendiente)
        self.assertFalse(v.atender_viaje(self.p))
        self.assertTrue(v.cerrada)
        self.assertIsNone(v._orden_pendiente)

    def test_H_R_QUIT_pedir_prioriza_cierre_y_conserva_otros_eventos(self):
        v, _ = self.vista([[self.tecla(self.pg.K_r)]])
        self.assertFalse(v.atender_viaje(self.p))
        self.assertEqual(v._orden_pendiente, Orden(PERGAMINO))
        antes = (self.p.acciones, self.p.reloj.tiempo_actual)
        primero = self.tecla(self.pg.K_x)
        ultimo = self.tecla(self.pg.K_m)
        self.pg.event.post(primero)
        self.pg.event.post(self.pg.event.Event(self.pg.QUIT))
        self.pg.event.post(ultimo)
        with patch.object(self.p, "usar_pergamino", side_effect=AssertionError("acción")):
            self.assertEqual(v.pedir_orden(self.p), Orden(SALIR))
        self.assertTrue(v.cerrada)
        self.assertIsNone(v._orden_pendiente)
        self.assertIsNone(v._partida_orden_pendiente)
        self.assertEqual(self.pg.event.get(), [primero, ultimo])
        self.assertEqual((self.p.acciones, self.p.reloj.tiempo_actual), antes)

    def test_H_R_sin_QUIT_entrega_pergamino_y_conserva_eventos(self):
        v, _ = self.vista([[self.tecla(self.pg.K_r)]])
        self.assertFalse(v.atender_viaje(self.p))
        otro = self.tecla(self.pg.K_x)
        self.pg.event.post(otro)
        self.assertEqual(v.pedir_orden(self.p), Orden(PERGAMINO))
        self.assertFalse(v.cerrada)
        self.assertIsNone(v._orden_pendiente)
        self.assertEqual(self.pg.event.get(), [otro])

    def test_I_callback_no_ejecuta_acciones(self):
        v, _ = self.vista([[self.tecla(self.pg.K_r)]])
        with patch.object(Controlador, "ejecutar", side_effect=AssertionError("reentrada")):
            with patch.object(self.p, "usar_pergamino", side_effect=AssertionError("acción")):
                with patch.object(self.p, "mover", side_effect=AssertionError("acción")):
                    self.assertFalse(v.atender_viaje(self.p))
        self.assertEqual((self.p.acciones, self.p.reloj.tiempo_actual), (0, 0))

    def test_J_animaciones_inicio_paso_y_retroceso(self):
        self.conocer()
        v, _ = self.vista([[], []])
        v._entregar(Orden(IR_A, 4))
        v.atender_viaje(self.p)
        self.assertFalse(any(a.tipo == CORRER for a in v.animador.activas))
        self.p.mover("N")
        v.atender_viaje(self.p)
        self.assertEqual(sum(a.tipo == CORRER for a in v.animador.activas), 1)
        v.animador.activas = []
        self.esc.dar("itm_pergamino")
        orden = v._entregar(Orden(PERGAMINO))
        Controlador(self.p).ejecutar(orden)
        v.mostrar_partida(self.p)
        self.assertFalse(any(a.tipo == CORRER for a in v.animador.activas))

    def test_K_main_suscripcion_gui_unica_y_consola_ninguna(self):
        entorno = Entorno()
        self.addCleanup(entorno.borrar)
        for gui in (False, True):
            v = Mock()

            def inspeccionar(c, listar, crear):
                self.assertEqual(len(c._observadores_viaje), int(gui))
                if gui:
                    self.assertIs(c._observadores_viaje[0], v.atender_viaje)
                self.assertEqual(len(c._observadores), 1)
                self.assertEqual(len(c._observadores_comentarios), 1)

            args = main.leer_argumentos(["--offline", entorno.paquete, "--datos",
                                        entorno.datos, "--nombre", "Prueba"]
                                       + (["--gui"] if gui else []))
            with patch.object(main, "crear_vista", return_value=v):
                with patch.object(Controlador, "correr_sesion", inspeccionar):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(main.correr_interactivo(args), 0)

    def test_L_dialogo_no_revela_destino_avistado(self):
        self.p.mapa.sala(2).nombre = "SECRETO_VECINO"
        v, textos = self.vista([[self.tecla(self.pg.K_v)],
                               [self.tecla(self.pg.K_2, "2"), self.tecla(self.pg.K_RETURN)],
                               [self.tecla(self.pg.K_ESCAPE)], [self.tecla(self.pg.K_x)]])
        memoria = list(self.p.conocimiento.memoria_puertas)
        self.assertEqual(v.pedir_orden(self.p), Orden(ESPERAR))
        self.assertNotIn("SECRETO_VECINO", "\n".join(textos))
        self.assertTrue(any("no está explorada" in t for t in textos))
        self.assertEqual(self.p.conocimiento.memoria_puertas, memoria)


if __name__ == "__main__":
    unittest.main()
