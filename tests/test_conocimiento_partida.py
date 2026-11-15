"""Integración de exploración, observación C2 y retroceso real de Partida."""

import unittest

from tests.cripta_de_prueba import armar, entrada, esqueleto_linea
from modelo.juego.conocimiento import PUERTA_ABIERTA, PUERTA_CERRADA


class PruebasConocimientoPartida(unittest.TestCase):
    def escenario(self, salas=None, contenido=()):
        esc = armar(salas if salas is not None else esqueleto_linea(6), contenido,
                    datos={"sala_salida": 6})
        self.addCleanup(esc.cerrar)
        return esc

    def foto(self, p):
        c = p.conocimiento
        return (list(c.estado_salas), list(c.memoria_puertas), c.resumen())

    def test_FR002_inicio_solo_sala_inicial_y_puertas_locales(self):
        p = self.escenario().partida
        self.assertEqual(p.conocimiento.estado_salas, [2, 1, 0, 0, 0, 0])
        self.assertEqual(p.conocimiento.resumen(), (1, 1))
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(1), 0), PUERTA_ABIERTA)
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(2), 1), PUERTA_ABIERTA)
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(2), 0), 0)
        self.assertFalse(p.registro.puede_deshacer())

    def test_FR001_FR004_FR010_exploracion_revisita_y_visibilidad(self):
        p = self.escenario().partida
        self.assertIsNone(p.salidas_visibles()[0][2])
        self.assertTrue(p.mover("N"))
        self.assertEqual(p.conocimiento.estado_salas, [2, 2, 1, 0, 0, 0])
        self.assertEqual(p.conocimiento.resumen(), (2, 1))
        self.assertIsNone(p.salidas_visibles()[0][2])
        self.assertEqual(p.salidas_visibles()[1][2], 1)
        self.assertTrue(p.mover("S"))
        self.assertTrue(p.mover("N"))
        self.assertEqual(p.conocimiento.resumen(), (2, 1))

    def test_FR006_puerta_remota_no_observada_hasta_regresar(self):
        p = self.escenario().partida
        puerta = p.mapa.sala(1).salidas[0]
        self.assertTrue(p.mover("N"))
        self.assertTrue(p.mover("N"))
        p.programar(p.reloj.tiempo_actual + 1,
                    lambda ahora: p.cambiar_estado_puerta(puerta, "cerrada"))
        self.assertTrue(p.esperar())
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(1), 0), PUERTA_ABIERTA)
        self.assertTrue(p.mover("S"))
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(1), 0), PUERTA_CERRADA)
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(2), 1), PUERTA_CERRADA)

    def test_FR006_FR012_abrir_autocierre_y_retroceso(self):
        salas = esqueleto_linea(6, [(1, 2, {"cerrada": True, "llave": "itm_llave_bronce", "cierre_automatico": 50})])
        esc = self.escenario(salas)
        esc.dar("itm_llave_bronce")
        esc.dar("itm_pergamino")
        esc.dar("itm_pergamino")
        p = esc.partida
        antes = self.foto(p)
        self.assertTrue(p.abrir("N"))
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(2), 1), PUERTA_ABIERTA)
        self.assertTrue(p.esperar())
        self.assertEqual(p.mapa.sala(1).salidas[0].estado, "cerrada")
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(2), 1), PUERTA_CERRADA)
        self.assertTrue(p.usar_pergamino())
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(2), 1), PUERTA_ABIERTA)
        self.assertTrue(p.usar_pergamino())
        self.assertEqual(self.foto(p), antes)

    def test_FR006_esperar_sin_cambios_no_duplica_conocimiento(self):
        p = self.escenario().partida
        antes = self.foto(p)
        self.assertTrue(p.esperar())
        self.assertEqual(self.foto(p), antes)

    def test_FR001_multiples_accesos_no_duplican_avistadas(self):
        salas = [
            {"id": 1, "salidas": {"N": {"sala": 2}, "E": {"sala": 3}}},
            {"id": 2, "salidas": {"S": {"sala": 1}, "E": {"sala": 4}}},
            {"id": 3, "salidas": {"O": {"sala": 1}, "N": {"sala": 4}}},
            {"id": 4, "salidas": {"O": {"sala": 2}, "S": {"sala": 3}}},
        ]
        p = self.escenario(salas).partida
        self.assertEqual(p.conocimiento.resumen(), (1, 2))
        for direccion in ("N", "S", "E"):
            self.assertTrue(p.mover(direccion))
        self.assertEqual(p.conocimiento.estado_salas, [2, 2, 2, 1])
        self.assertEqual(p.conocimiento.resumen(), (3, 1))

    def test_FR012_pergamino_revierte_entrada_sin_antorcha(self):
        esc = self.escenario()
        p = esc.partida
        esc.dar("itm_pergamino")
        antes = self.foto(p)
        self.assertTrue(p.mover("N"))
        self.assertTrue(p.usar_pergamino())
        self.assertEqual(self.foto(p), antes)
        self.assertEqual(p.jugador.sala.id, 1)

    def test_FR007_FR008_antorcha_revela_sin_observar_puertas_remotas(self):
        salas = esqueleto_linea(6, [(2, 3, {"cerrada": True})])
        esc = self.escenario(salas, [entrada(3, enemigos=[("r-3", "ent_rata", 12)], trampas=[("t-3", "trp_dardos")])])
        p = esc.partida
        antorcha = esc.dar("itm_antorcha")
        self.assertTrue(p.usar(antorcha))
        self.assertEqual(p.conocimiento.estado_salas, [2, 1, 0, 0, 0, 0])
        self.assertTrue(p.mover("N"))
        self.assertEqual(p.conocimiento.estado_salas, [2, 2, 2, 1, 0, 0])
        self.assertEqual(p.conocimiento.resumen(), (3, 1))
        vecina = p.mapa.sala(3)
        self.assertFalse(vecina.incorporada)
        self.assertEqual(vecina.actores, [])
        self.assertEqual(vecina.trampas, [])
        self.assertEqual(p.conocimiento.puerta_recordada(vecina, 0), 0)
        self.assertEqual(p.conocimiento.puerta_recordada(vecina, 1), PUERTA_CERRADA)

    def test_FR012_pergamino_revierte_exploracion_antorcha_y_contadores(self):
        esc = self.escenario()
        p = esc.partida
        self.assertTrue(p.usar(esc.dar("itm_antorcha")))
        esc.dar("itm_pergamino")
        antes = self.foto(p)
        self.assertTrue(p.mover("N"))
        self.assertTrue(p.usar_pergamino())
        self.assertEqual(p.jugador.sala.id, 1)
        self.assertEqual(self.foto(p), antes)


if __name__ == "__main__":
    unittest.main()
