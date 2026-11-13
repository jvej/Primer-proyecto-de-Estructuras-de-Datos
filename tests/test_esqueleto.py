r"""Validación FR-007; ejecutar con venv\Scripts\python.exe -m tests.test_esqueleto."""

import copy
import unittest

from modelo.datos.esqueleto import Esqueleto, descargar_esqueleto
from modelo.juego.errores import ErrorRed


class TestCostosEsqueleto(unittest.TestCase):
    def test_FR007_costo_ausente_usa_100_sin_mutar_respuesta(self):
        cuerpo = {"salas": [{"id": 23, "salidas": {"E": {"sala": 24, "llave": "k"}}}]}
        original = copy.deepcopy(cuerpo)
        esqueleto = Esqueleto()
        esqueleto.agregar_pagina(cuerpo)
        self.assertEqual(esqueleto.salidas[0]["E"], {"sala": 24, "llave": "k", "costo": 100})
        self.assertEqual(esqueleto.vecinos_de(23), [24])
        self.assertEqual(cuerpo, original)

    def test_FR007_costos_enteros_positivos_se_conservan(self):
        for costo in (1, 100, 8000):
            with self.subTest(costo=costo):
                cuerpo = {"salas": [{"id": 23, "salidas": {"O": {"sala": 24, "costo": costo}}}]}
                esqueleto = Esqueleto()
                esqueleto.agregar_pagina(cuerpo)
                self.assertEqual(esqueleto.salidas[0]["O"]["costo"], costo)

    def test_FR007_costos_invalidos_producen_error_con_contexto(self):
        for costo in (0, -5, True, False, 100.0, 1.5, "100", None, [], {}, (1, 2)):
            with self.subTest(costo=costo):
                cuerpo = {"salas": [{"id": 23, "salidas": {"N": {"sala": 24, "costo": costo}}}]}
                original = copy.deepcopy(cuerpo)
                esqueleto = Esqueleto()
                with self.assertRaises(ErrorRed) as error:
                    esqueleto.agregar_pagina(cuerpo)
                mensaje = str(error.exception)
                self.assertIn("sala 23", mensaje)
                self.assertIn("N", mensaje)
                self.assertIn(repr(costo), mensaje)
                self.assertEqual(cuerpo, original)
                self.assertEqual(esqueleto.cantidad(), 0)

    def test_FR007_descarga_propaga_el_error_de_costo(self):
        class FuenteMemoria:
            def pagina_esqueleto(self, id_cripta, pagina):
                return {"salas": [{"id": 31, "salidas": {"S": {"sala": 32, "costo": "mal"}}}]}

        with self.assertRaises(ErrorRed) as error:
            descargar_esqueleto(FuenteMemoria(), "sintetica")
        self.assertIn("sala 31", str(error.exception))
        self.assertIn("S", str(error.exception))
        self.assertIn("'mal'", str(error.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
