"""FR-014..016: planificación aislada; aún no hay viaje compuesto."""

import unittest

from controlador.planificador_rutas import PlanificadorRutas
from modelo.datos.esqueleto import Esqueleto
from modelo.juego.conocimiento import ConocimientoMapa, PUERTA_ABIERTA, PUERTA_CERRADA
from modelo.juego.mapa import Mapa
from modelo.juego.registro import Registro
from tests.cripta_de_prueba import armar, esqueleto_linea


class PruebasPlanificador(unittest.TestCase):
    def crear(self, ids, conexiones):
        e = Esqueleto()
        e.agregar_pagina({"salas": [{"id": i, "salidas": {}} for i in ids]})
        mapa = Mapa(e)
        for a, direccion, b, costo in conexiones:
            mapa.sala(a).conectar(direccion, mapa.sala(b), costo=costo)
        c = ConocimientoMapa(len(ids), mapa.salas, mapa)
        r = Registro()
        for sala in mapa.salas:
            r.cambiar(c.estado_salas, sala.indice, 2)
            for i, salida in enumerate(sala.salidas):
                if salida is not None:
                    r.cambiar(c.memoria_puertas, sala.indice * 4 + i, PUERTA_ABIERTA)
        return mapa, c, PlanificadorRutas(mapa, c)

    def test_FR015_prefiere_mas_pasos_con_menor_costo(self):
        m, c, p = self.crear([91, 8, 37], [(91, "E", 8, 2), (8, "E", 37, 3), (91, "N", 37, 20)])
        paso = p.siguiente_paso(m.sala(91), 37)
        self.assertEqual((paso.estado, paso.direccion, paso.id_siguiente, paso.costo_total), ("paso", "E", 8, 5))

    def test_FR016_empate_elige_menor_id_del_primer_vecino(self):
        # El menor ID se inserta después y tiene el mayor costo del primer paso.
        m, c, p = self.crear([80, 40, 3, 99], [
            (80, "N", 40, 1), (40, "E", 99, 9),
            (80, "E", 3, 8), (3, "N", 99, 2),
        ])
        paso = p.siguiente_paso(m.sala(80), 99)
        self.assertEqual((paso.id_siguiente, paso.direccion, paso.costo_total), (3, "E", 10))

    def test_FR014_destinos_invalidos_avistados_y_desconocidos(self):
        m, c, p = self.crear([1, 2, 3], [(1, "E", 2, 5), (2, "E", 3, 5)])
        c.estado_salas[m.sala(2).indice] = 1
        c.estado_salas[m.sala(3).indice] = 0
        for destino in (2, 3, 999, 0, -1, True, "2", None):
            with self.subTest(destino=destino):
                paso = p.siguiente_paso(m.sala(1), destino)
                self.assertEqual(paso.estado, "rechazado")
                self.assertIsNone(paso.direccion)
                self.assertTrue(paso.motivo)

    def test_FR014_destino_actual_no_requiere_movimiento(self):
        m, c, p = self.crear([1], [])
        paso = p.siguiente_paso(m.sala(1), 1)
        self.assertEqual((paso.estado, paso.costo_total, paso.direccion), ("destino", 0, None))

    def test_FR015_no_usa_intermedias_avistadas_o_desconocidas(self):
        m, c, p = self.crear([1, 2, 3], [(1, "N", 2, 2), (2, "N", 3, 2)])
        for estado in (0, 1):
            c.estado_salas[1] = estado
            self.assertEqual(p.siguiente_paso(m.sala(1), 3).estado, "rechazado")

    def test_FR015_ruta_solo_por_puertas_recordadas_abiertas(self):
        m, c, p = self.crear([1, 2, 3], [(1, "N", 2, 2), (2, "N", 3, 2), (1, "E", 3, 15)])
        # Cerrada en la memoria: debe evitarla aunque físicamente está abierta.
        c.memoria_puertas[0] = PUERTA_CERRADA
        self.assertEqual(p.siguiente_paso(m.sala(1), 3).costo_total, 15)
        c.memoria_puertas[0] = 0
        self.assertEqual(p.siguiente_paso(m.sala(1), 3).costo_total, 15)
        c.memoria_puertas[0] = PUERTA_ABIERTA
        # Abierta en memoria y cerrada físicamente: conserva la ruta recordada.
        m.sala(1).salidas[0].estado = "cerrada"
        self.assertEqual(p.siguiente_paso(m.sala(1), 3).costo_total, 4)

    def test_FR018_recalcula_y_no_usa_marcas_viejas(self):
        m, c, p = self.crear([1, 2, 3], [(1, "N", 2, 2), (2, "N", 3, 2)])
        dist, marcas = p._dist_navegacion, p._marca_navegacion
        self.assertEqual(p.siguiente_paso(m.sala(1), 3).estado, "paso")
        c.memoria_puertas[0] = PUERTA_CERRADA
        self.assertEqual(p.siguiente_paso(m.sala(1), 3).estado, "rechazado")
        self.assertIs(p._dist_navegacion, dist)
        self.assertIs(p._marca_navegacion, marcas)
        self.assertEqual(p._token_navegacion, 2)

    def test_C3_planificadores_independientes(self):
        m, c, p = self.crear([1, 2], [(1, "N", 2, 4)])
        otro = PlanificadorRutas(m, c)
        p.siguiente_paso(m.sala(1), 2)
        foto = (list(p._dist_navegacion), list(p._marca_navegacion), p._token_navegacion)
        otro.siguiente_paso(m.sala(2), 1)
        self.assertEqual((p._dist_navegacion, p._marca_navegacion, p._token_navegacion), foto)
        self.assertIsNot(p._dist_navegacion, otro._dist_navegacion)

    def test_FR014_FR015_consulta_no_modifica_partida_ni_tiempo(self):
        esc = armar(esqueleto_linea(3))
        self.addCleanup(esc.cerrar)
        partida = esc.partida
        c = partida.conocimiento
        p = PlanificadorRutas(partida.mapa, c)
        def foto():
            return (partida.jugador.sala, partida.reloj.tiempo_actual, partida.acciones,
                    partida.registro.acciones_deshacibles(), partida.registro.cambios_registrados(),
                    list(c.estado_salas), list(c.memoria_puertas), c.resumen(), len(partida.agenda), esc.mensajes())
        antes = foto()
        self.assertEqual(p.siguiente_paso(partida.jugador.sala, 2).estado, "rechazado")
        self.assertEqual(p.siguiente_paso(partida.jugador.sala, 1).estado, "destino")
        self.assertEqual(foto(), antes)
        self.assertTrue(partida.mover("N"))
        antes = foto()
        self.assertEqual(p.siguiente_paso(partida.jugador.sala, 1).estado, "paso")
        self.assertEqual(foto(), antes)


if __name__ == "__main__":
    unittest.main()
