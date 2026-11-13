"""Pruebas del módulo puro de T018–T025, sin integración del controlador."""

from copy import deepcopy
import unittest
from unittest.mock import patch

from modelo.datos.esqueleto import Esqueleto
from modelo.juego.resolubilidad import verificar_resolubilidad


def _esqueleto(salas):
    esqueleto = Esqueleto()
    esqueleto.agregar_pagina({"salas": salas})
    return esqueleto


class PruebasResolubilidad(unittest.TestCase):
    def test_FR014_ciclo_de_tres_llaves_con_puertas_por_flecha(self):
        salas = [
            {"id": 10, "salidas": {
                "N": {"sala": 20, "cerrada": True, "llave": "itm_b"},
                "S": {"sala": 30, "cerrada": True, "llave": "itm_c"},
                "E": {"sala": 40, "cerrada": True, "llave": "itm_a"}}},
            {"id": 20, "salidas": {}},
            {"id": 30, "salidas": {}},
            {"id": 40, "salidas": {}},
        ]
        llaves = [{"id": "itm_a", "sala": 20}, {"id": "itm_b", "sala": 30},
                  {"id": "itm_c", "sala": 40}]
        esperado = "itm_a -> itm_b [sala 10 (N)] -> itm_c [sala 10 (S)] -> itm_a [sala 10 (E)]"
        for entrada, ubicaciones in ((salas, llaves), (salas[::-1], llaves[::-1])):
            reporte = verificar_resolubilidad(_esqueleto(entrada), ubicaciones, 10, 40, "itm_a")
            self.assertEqual(reporte.estado, "NO RESOLUBLE")
            self.assertEqual(reporte.llaves_no_obtenibles, ["itm_a", "itm_b", "itm_c"])
            self.assertEqual(reporte.ciclos, [esperado])

    def test_FR010_coincidencia_por_abre_en_ubicacion_o_catalogo_en_memoria(self):
        salas = [
            {"id": 1, "salidas": {"E": {"sala": 2, "cerrada": True, "llave": "cerrojo"},
                                    "N": {"sala": 3, "cerrada": True, "llave": "itm_inicio"}}},
            {"id": 2, "salidas": {"E": {"sala": 4, "cerrada": True, "llave": "itm_fin"}}},
            {"id": 3, "salidas": {}}, {"id": 4, "salidas": {}},
        ]
        for en_ubicacion in (True, False):
            llaves = [{"id": "itm_inicio", "sala": 1}, {"id": "itm_fin", "sala": 2}]
            catalogo = None
            if en_ubicacion:
                llaves[0]["abre"] = "cerrojo"
            else:
                catalogo = [{"id": "itm_inicio", "abre": "cerrojo"}]
            reporte = verificar_resolubilidad(_esqueleto(salas), llaves, 1, 4, "itm_fin", catalogo)
            self.assertTrue(reporte.es_resoluble())
            self.assertEqual(reporte.orden_llaves, [(0, ["itm_inicio"]), (1, ["itm_fin"])])
        # Sin ficha ni atributo en la ubicación, el id no abre otra cerradura.
        reporte = verificar_resolubilidad(_esqueleto(salas), llaves, 1, 4, "itm_fin")
        self.assertFalse(reporte.es_resoluble())
        self.assertIn((1, "E", 2, "cerrojo"), reporte.frontera_bloqueada)

    def test_FR011_motivo_sin_puerta_que_pida_llave_salida(self):
        salas = [{"id": 1, "salidas": {"N": {"sala": 2}}}, {"id": 2, "salidas": {}}]
        reporte = verificar_resolubilidad(
            _esqueleto(salas), [{"id": "itm_fin", "sala": 1}], 1, 2, "itm_fin")
        self.assertEqual(reporte.estado, "NO RESOLUBLE")
        self.assertEqual(reporte.formatear_reporte(),
                         "ESTADO: NO RESOLUBLE\n"
                         "MOTIVO: no existe puerta hacia sala_salida que pida llave_salida")

    def test_FR012_etapa_cero_agota_region_sin_activar_llaves_pendientes(self):
        salas = [
            {"id": 1, "salidas": {"N": {"sala": 2},
                                    "E": {"sala": 4, "cerrada": True, "llave": "itm_z"}}},
            {"id": 2, "salidas": {"N": {"sala": 3}}},
            {"id": 3, "salidas": {}},
            {"id": 4, "salidas": {"N": {"sala": 5, "cerrada": True, "llave": "itm_fin"}}},
            {"id": 5, "salidas": {}},
        ]
        llaves = [{"id": "itm_z", "sala": 1}, {"id": "itm_a", "sala": 3},
                  {"id": "itm_fin", "sala": 4}]
        reporte = verificar_resolubilidad(_esqueleto(salas), llaves, 1, 5, "itm_fin")
        self.assertTrue(reporte.es_resoluble())
        self.assertEqual(reporte.orden_llaves, [(0, ["itm_a", "itm_z"]), (1, ["itm_fin"])])

    def test_FR014_frontera_ordenada_excluye_puertas_internas_e_incluye_sin_llave(self):
        salas = [
            {"id": 20, "salidas": {"N": {"sala": 30, "cerrada": True, "llave": "itm_fin"}}},
            {"id": 10, "salidas": {
                "O": {"sala": 40, "cerrada": True},
                "E": {"sala": 30, "cerrada": True},
                "S": {"sala": 20},
                "N": {"sala": 20, "cerrada": True, "llave": "itm_interna"}}},
            {"id": 30, "salidas": {}}, {"id": 40, "salidas": {}},
        ]
        reporte = verificar_resolubilidad(
            _esqueleto(salas), [{"id": "itm_fin", "sala": 30}], 10, 30, "itm_fin")
        self.assertEqual(reporte.frontera_bloqueada,
                         [(10, "E", 30, None), (10, "O", 40, None), (20, "N", 30, "itm_fin")])

    def test_FR014_etiqueta_de_la_puerta_cerrada_mas_cercana(self):
        salas = [
            {"id": 1, "salidas": {"N": {"sala": 2, "cerrada": True, "llave": "itm_a"}}},
            {"id": 2, "salidas": {"E": {"sala": 3, "cerrada": True, "llave": "itm_b"}}},
            {"id": 3, "salidas": {"S": {"sala": 4}}},
            {"id": 4, "salidas": {}},
        ]
        llaves = [{"id": "itm_a", "sala": 2}, {"id": "itm_b", "sala": 4}]
        # itm_a necesita itm_a; itm_b necesita itm_b, no la primera puerta itm_a.
        reporte = verificar_resolubilidad(_esqueleto(salas), llaves, 1, 2, "itm_a")
        self.assertEqual(reporte.ciclos, ["itm_a -> itm_a [sala 1 (N)]"])
        llaves[0]["sala"] = 4
        llaves[1]["sala"] = 2
        reporte = verificar_resolubilidad(_esqueleto(salas), llaves, 1, 2, "itm_a")
        self.assertEqual(reporte.ciclos, ["itm_a -> itm_b [sala 2 (E)] -> itm_a [sala 1 (N)]"])

    def test_FR011_no_basta_otra_entrada_a_la_salida(self):
        salas = [
            {"id": 1, "salidas": {"N": {"sala": 2}}},
            {"id": 2, "salidas": {}},
            {"id": 3, "salidas": {"N": {"sala": 2, "llave": "itm_fin", "cerrada": True}}},
        ]
        reporte = verificar_resolubilidad(
            _esqueleto(salas), [{"id": "itm_fin", "sala": 1}], 1, 2, "itm_fin")
        self.assertFalse(reporte.es_resoluble())
        self.assertIsNone(reporte.motivo)

    def test_FR011_puerta_de_salida_se_cuenta_aunque_destino_ya_este_visitado(self):
        salas = [
            {"id": 1, "salidas": {"N": {"sala": 2}, "E": {"sala": 3}}},
            {"id": 2, "salidas": {}},
            {"id": 3, "salidas": {"N": {"sala": 2, "llave": "itm_fin", "cerrada": True}}},
        ]
        reporte = verificar_resolubilidad(
            _esqueleto(salas), [{"id": "itm_fin", "sala": 1}], 1, 2, "itm_fin")
        self.assertTrue(reporte.es_resoluble())

    def test_FR010_indices_resueltos_una_vez_y_entradas_sin_mutacion(self):
        salas = [{"id": 1, "salidas": {"N": {"sala": 2, "estado": "cerrada", "llave": "itm_fin"}}},
                 {"id": 2, "salidas": {"S": {"sala": 1}}}]
        llaves = [{"id": "itm_fin", "sala": 1}]
        original = deepcopy(llaves)
        esqueleto = _esqueleto(salas)
        salidas = deepcopy(esqueleto.salidas)
        with patch.object(esqueleto, "posicion", wraps=esqueleto.posicion) as posicion:
            reporte = verificar_resolubilidad(esqueleto, llaves, 1, 2, "itm_fin")
        self.assertTrue(reporte.es_resoluble())
        self.assertEqual(posicion.call_count, 2 + len(llaves) + 2)
        self.assertEqual(llaves, original)
        self.assertEqual(esqueleto.salidas, salidas)

    def test_FR014_dfs_iterativa_supera_mil_dependencias(self):
        cantidad = 1200
        salas = [{"id": 0, "salidas": {
            "N": {"sala": 1, "cerrada": True, "llave": "itm_0000"}}}]
        llaves = []
        for i in range(1, cantidad + 1):
            salidas = {}
            if i < cantidad:
                salidas = {"N": {"sala": i + 1, "cerrada": True, "llave": "itm_%04d" % i}}
            salas.append({"id": i, "salidas": salidas})
            # X_i está tras X_(i+1); la última llave cierra un ciclo consigo misma.
            llaves.append({"id": "itm_%04d" % (i - 1), "sala": min(i + 1, cantidad)})
        reporte = verificar_resolubilidad(_esqueleto(salas), llaves, 0, 1, "itm_0000")
        self.assertEqual(reporte.estado, "NO RESOLUBLE")
        self.assertEqual(reporte.ciclos,
                         ["itm_1199 -> itm_1199 [sala 1199 (N)]"])

    def test_FR014_varios_ciclos_eligen_el_menor_id_ciclico(self):
        salas = [
            {"id": 1, "salidas": {
                "N": {"sala": 2, "cerrada": True, "llave": "itm_z"},
                "S": {"sala": 3, "cerrada": True, "llave": "itm_b"}}},
            {"id": 2, "salidas": {}}, {"id": 3, "salidas": {}},
        ]
        # La menor llave, itm_a, lleva al ciclo itm_z. El menor ciclo es itm_b.
        llaves = [{"id": "itm_a", "sala": 2}, {"id": "itm_z", "sala": 2},
                  {"id": "itm_b", "sala": 3}]
        for entrada in (salas, salas[::-1]):
            reporte = verificar_resolubilidad(_esqueleto(entrada), llaves, 1, 2, "itm_z")
            self.assertEqual(reporte.ciclos, ["itm_b -> itm_b [sala 1 (S)]"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
