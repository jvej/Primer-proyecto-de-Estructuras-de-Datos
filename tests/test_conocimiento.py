"""Pruebas unitarias T003/T004; la aceptación con Partida queda pendiente."""

import unittest

from modelo.datos.esqueleto import Esqueleto
from modelo.juego.mapa import Mapa
from modelo.juego.conocimiento import (
    ConocimientoMapa, ESTADO_DESCONOCIDA, ESTADO_AVISTADA, ESTADO_EXPLORADA,
    PUERTA_DESCONOCIDA, PUERTA_ABIERTA, PUERTA_CERRADA,
)
from modelo.juego.registro import Registro
from modelo.juego.sala import Sala


class PruebasConocimiento(unittest.TestCase):
    def setUp(self):
        esqueleto = Esqueleto()
        # IDs distintos de los índices y sin orden numérico.
        esqueleto.agregar_pagina({"salas": [
            {"id": 90, "nombre": "Inicio", "salidas": {"E": {"sala": 12}}},
            {"id": 12, "nombre": "Vecina", "salidas": {"O": {"sala": 90}}},
            {"id": 47, "nombre": "Lejana", "salidas": {}},
        ]})
        self.mapa = Mapa(esqueleto)
        self.c = ConocimientoMapa(3, self.mapa.salas, self.mapa)
        self.registro = Registro()

    def test_FR001_inicializacion_y_referencias_sin_copias(self):
        self.assertIs(self.c.mapa, self.mapa)
        self.assertIs(self.c.salas_por_indice, self.mapa.salas)
        self.assertEqual(self.c.estado_salas, [ESTADO_DESCONOCIDA] * 3)
        self.assertEqual(self.c.memoria_puertas, [PUERTA_DESCONOCIDA] * 12)
        self.assertEqual(self.c.resumen(), (0, 0))
        self.assertEqual(self.c.total_salas, 3)

    def test_FR001_clasificacion_tres_estados_y_consulta_por_id(self):
        self.registro.cambiar(self.c.estado_salas, 0, ESTADO_EXPLORADA)
        self.registro.cambiar(self.c.estado_salas, 1, ESTADO_AVISTADA)
        self.assertTrue(self.c.es_explorada(self.mapa.salas[0]))
        self.assertTrue(self.c.es_avistada(self.mapa.salas[1]))
        self.assertFalse(self.c.es_explorada(self.mapa.salas[1]))
        self.assertFalse(self.c.es_avistada(self.mapa.salas[0]))
        for id_sala, estado in ((90, 2), (12, 1), (47, 0), (999, 0)):
            self.assertEqual(self.c.estado_por_id(id_sala), estado)

    def test_FR004_FR005_memoria_no_explora_ni_lee_estado_real(self):
        salida = self.mapa.salas[0].salidas[2]
        self.assertFalse(self.c.puerta_recordada_abierta(salida))
        self.registro.cambiar(self.c.memoria_puertas, 2, PUERTA_ABIERTA)
        self.assertFalse(self.c.puerta_recordada_abierta(salida))
        self.registro.cambiar(self.c.memoria_puertas, 7, PUERTA_ABIERTA)
        salida.estado = "cerrada"  # Cambio físico remoto: la memoria no observa.
        self.assertTrue(self.c.puerta_recordada_abierta(salida))
        self.assertEqual(self.c.estado_salas, [0, 0, 0])
        self.assertEqual(self.c.resumen(), (0, 0))
        self.assertEqual(self.c.puerta_recordada(self.mapa.salas[1], 3), PUERTA_ABIERTA)
        self.registro.cambiar(self.c.memoria_puertas, 7, PUERTA_CERRADA)
        self.assertFalse(self.c.puerta_recordada_abierta(salida))

    def test_FR012_reversion_estados_memoria_y_contadores(self):
        r, c = self.registro, self.c
        r.cambiar(c.estado_salas, 1, ESTADO_AVISTADA)
        r.cambiar(c, "num_avistadas", 1)
        r.abrir_grupo()
        r.cambiar(c.estado_salas, 1, ESTADO_EXPLORADA)
        r.cambiar(c, "num_avistadas", 0)
        r.cambiar(c, "num_exploradas", 1)
        r.cambiar(c.memoria_puertas, 2, PUERTA_ABIERTA)
        r.cambiar(c.memoria_puertas, 7, PUERTA_ABIERTA)
        r.cambiar(c.memoria_puertas, 2, PUERTA_CERRADA)
        r.cambiar(c.memoria_puertas, 7, PUERTA_CERRADA)
        r.cerrar_grupo()
        self.assertEqual(c.resumen(), (1, 0))
        r.deshacer_ultimo()
        self.assertEqual(c.resumen(), (0, 1))
        self.assertEqual(c.estado_salas, [0, 1, 0])
        self.assertEqual(c.memoria_puertas, [0] * 12)

    def test_SC002_resumen_no_recorre_arreglos(self):
        class SinAcceso:
            def __iter__(self):
                raise AssertionError("resumen no debe recorrer el estado")

            def __getitem__(self, indice):
                raise AssertionError("resumen no debe consultar el estado")

        self.c.estado_salas = SinAcceso()
        self.c.memoria_puertas = SinAcceso()
        self.registro.cambiar(self.c, "num_exploradas", 2)
        self.registro.cambiar(self.c, "num_avistadas", 1)
        self.assertEqual(self.c.resumen(), (2, 1))

    def test_T003_indices_y_referencias_invalidas(self):
        for n in (-1, True, 1.5, 2):
            with self.assertRaises(ValueError):
                ConocimientoMapa(n, self.mapa.salas, self.mapa)
        with self.assertRaises(ValueError):
            ConocimientoMapa(3, list(self.mapa.salas), self.mapa)
        ajena = Sala(90)
        for indice in (None, -1, 0, 3, True):
            ajena.indice = indice
            with self.assertRaises(ValueError):
                self.c.estado_sala(ajena)
        for direccion in (-1, 4, True, "E"):
            with self.assertRaises(ValueError):
                self.c.puerta_recordada(self.mapa.salas[0], direccion)

    def test_T003_mapa_vacio(self):
        mapa = Mapa(Esqueleto())
        c = ConocimientoMapa(0, mapa.salas, mapa)
        self.assertEqual(c.resumen(), (0, 0))
        self.assertEqual(c.estado_por_id(90), ESTADO_DESCONOCIDA)


if __name__ == "__main__":
    unittest.main()
