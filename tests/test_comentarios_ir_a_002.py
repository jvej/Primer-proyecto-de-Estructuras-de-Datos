"""002/004: una marca por observación exterior efectiva, sin acciones nuevas."""

import unittest
from unittest.mock import patch

from controlador.controlador import Controlador
from controlador.orden import IR_A, Orden
from tests.cripta_de_prueba import armar, esqueleto_linea


class PruebasMarcasObservacion(unittest.TestCase):
    def setUp(self):
        esc = armar(esqueleto_linea(5), datos={"sala_salida": 5})
        self.addCleanup(esc.cerrar)
        self.p = esc.partida
        for sala in self.p.mapa.salas:
            self.p._explorar_sala(sala)
            for salida in sala.salidas:
                if salida is not None:
                    self.p._recordar_puerta(salida)
        self.c = Controlador(self.p)
        self.eventos = []
        self.comentarios = []
        self.exteriores = []
        observar_original = self.p._observar_puertas
        plan_original = self.c._planificador.siguiente_paso

        def observar():
            if self.p.registro.grupo_abierto() is None:
                self.exteriores.append(self.p.jugador.sala.id)
                self.eventos.append(("observar", self.p.jugador.sala.id))
            return observar_original()

        def planificar(*args):
            self.eventos.append(("planificar", self.p.jugador.sala.id))
            return plan_original(*args)

        def comentar(texto):
            self.assertIsNone(self.p.registro.grupo_abierto())
            self.comentarios.append(texto)
            self.eventos.append(("comentario", texto))

        self.c.agregar_observador_comentarios(comentar)
        self.c.agregar_observador(lambda orden: self.eventos.append(("mover", orden.argumento)))
        self.addCleanup(patch.stopall)
        patch.object(self.p, "_observar_puertas", side_effect=observar).start()
        patch.object(self.c._planificador, "siguiente_paso", side_effect=planificar).start()

    def test_A_cancelar_antes_de_observar_no_emite_marca(self):
        self.c.agregar_observador_viaje(lambda p: False)
        self.assertTrue(self.c.ejecutar(Orden(IR_A, 4)))
        self.assertEqual(self.comentarios, [])
        self.assertEqual(self.exteriores, [])
        self.assertEqual((self.p.acciones, self.p.reloj.tiempo_actual), (0, 0))
        self.assertEqual(self.p.registro.acciones_deshacibles(), 0)

    def test_B_D_varios_pasos_marcas_intercaladas_y_orden_exacto(self):
        self.assertTrue(self.c.ejecutar(Orden(IR_A, 4)))
        esperado = [("planificar", 1)]  # Validación preliminar sin observar.
        for sala in (1, 2, 3):
            esperado.extend([("comentario", "ir a 4"), ("observar", sala),
                             ("planificar", sala), ("mover", "N")])
        self.assertEqual(self.eventos, esperado)
        self.assertEqual(self.comentarios, ["ir a 4"] * 3)
        self.assertEqual(self.exteriores, [1, 2, 3])
        self.assertEqual((self.p.acciones, self.p.reloj.tiempo_actual), (3, 300))

    def test_C_bloqueo_observado_conserva_marca_sin_movimiento(self):
        def cerrar(p):
            # Cambio controlado tras la planificación preliminar; la memoria
            # se actualiza exclusivamente al observar, sin una acción nueva.
            p.cambiar(p.jugador.sala.salidas[0], "estado", "cerrada")
            return True
        self.c.agregar_observador_viaje(cerrar)
        self.assertTrue(self.c.ejecutar(Orden(IR_A, 4)))
        self.assertEqual(self.eventos, [("planificar", 1), ("comentario", "ir a 4"),
                                       ("observar", 1), ("planificar", 1)])
        self.assertEqual(self.p.conocimiento.memoria_puertas[0], 2)
        self.assertEqual((self.p.acciones, self.p.reloj.tiempo_actual), (0, 0))

    def test_E_cancelacion_tras_dos_pasos_no_agrega_marca_final(self):
        self.c.agregar_observador_viaje(lambda p: p.acciones < 2)
        self.assertTrue(self.c.ejecutar(Orden(IR_A, 4)))
        self.assertEqual(self.comentarios, ["ir a 4"] * 2)
        self.assertEqual(self.exteriores, [1, 2])
        self.assertEqual(self.eventos[-1], ("mover", "N"))
        self.assertEqual((self.p.jugador.sala.id, self.p.reloj.tiempo_actual), (3, 200))

    def test_F_varios_callbacks_no_duplican_marcas(self):
        callbacks = []
        def continuar(p):
            callbacks.append(p.jugador.sala.id)
            return True
        self.c.agregar_observador_viaje(continuar)
        self.c.agregar_observador_viaje(continuar)
        self.assertTrue(self.c.ejecutar(Orden(IR_A, 4)))
        self.assertEqual(len(callbacks), 6)
        self.assertEqual(len(self.comentarios), 3)
        self.assertEqual(len(self.exteriores), 3)

    def test_G_marcas_no_crean_tiempo_ni_grupos(self):
        fronteras = []
        def capturar(texto):
            fronteras.append((self.p.acciones, self.p.reloj.tiempo_actual,
                              self.p.registro.acciones_deshacibles()))
        self.c.agregar_observador_comentarios(capturar)
        self.assertTrue(self.c.ejecutar(Orden(IR_A, 4)))
        self.assertEqual(fronteras, [(0, 0, 0), (1, 100, 1), (2, 200, 2)])
        self.assertEqual(self.p.registro.acciones_deshacibles(), 3)

    def test_A_cambio_partida_en_callback_no_observa_ni_comenta(self):
        self.c.agregar_observador_viaje(lambda p: self.sustituir(p))
        self.assertTrue(self.c.ejecutar(Orden(IR_A, 4)))
        self.assertEqual(self.comentarios, [])
        self.assertEqual(self.exteriores, [])

    def sustituir(self, p):
        self.c.partida = p  # También invalida el token de viaje.
        return True


if __name__ == "__main__":
    unittest.main()
