"""Pruebas del módulo puro de T018–T025, sin integración del controlador."""

from copy import deepcopy
import unittest
from unittest.mock import patch

from modelo.datos.esqueleto import Esqueleto
from modelo.juego.resolubilidad import verificar_resolubilidad
from modelo.juego import resolubilidad
from modelo.juego.errores import ErrorRed


def _esqueleto(salas):
    esqueleto = Esqueleto()
    esqueleto.agregar_pagina({"salas": salas})
    return esqueleto


class PruebasResolubilidad(unittest.TestCase):
    def test_FR007_costo_ausente_es_100_y_entero_positivo_se_conserva(self):
        for atributos, esperado in (({}, 100), ({"costo": 1}, 1), ({"costo": 37}, 37)):
            with self.subTest(atributos=atributos):
                salas = [{"id": 1, "salidas": {"N": {"sala": 2, **atributos}}},
                         {"id": 2, "salidas": {}}]
                original = deepcopy(salas)
                esqueleto = _esqueleto(salas)
                self.assertEqual(esqueleto.salidas[0]["N"]["costo"], esperado)
                self.assertEqual(salas, original)

    def test_FR007_rechaza_costo_cero_negativo_decimal_texto_y_booleano(self):
        for costo in (0, -1, 1.5, 1.0, "100", True, None):
            with self.subTest(costo=costo), self.assertRaisesRegex(ErrorRed, "costo inválido"):
                _esqueleto([{"id": 1, "salidas": {"N": {"sala": 2, "costo": costo}}},
                            {"id": 2, "salidas": {}}])

    def test_FR014_puertas_salida_desde_salas_inalcanzables(self):
        salas = [{"id": 1, "salidas": {}}, {"id": 2, "salidas": {}},
                 {"id": 3, "salidas": {"N": {"sala": 2, "llave": "fin", "cerrada": True}}},
                 {"id": 4, "salidas": {"E": {"sala": 2, "llave": "fin", "cerrada": True}}}]
        reporte = verificar_resolubilidad(_esqueleto(salas), [{"id": "fin", "sala": 1}], 1, 2, "fin")
        self.assertEqual(reporte.llaves_no_obtenibles, [])
        self.assertEqual(reporte.frontera_bloqueada, [])
        self.assertEqual(reporte.ciclos, [])
        self.assertEqual(reporte.formatear_reporte(), "ESTADO: NO RESOLUBLE\n"
                         "MOTIVO: ninguna puerta hacia sala_salida que pide llave_salida es alcanzable")

    def test_FR014_prioridad_de_motivos_sin_puerta_y_sin_llave(self):
        for pide, motivo in ((None, "no existe puerta hacia sala_salida que pida llave_salida"),
                             ("fin", "llave_salida no puede obtenerse")):
            with self.subTest(pide=pide):
                salas = [{"id": 1, "salidas": {"N": {"sala": 2, "cerrada": True, "llave": pide}}},
                         {"id": 2, "salidas": {}}]
                reporte = verificar_resolubilidad(_esqueleto(salas), [{"id": "fin", "sala": 2}], 1, 2, "fin")
                self.assertEqual(reporte.motivo, motivo)
                self.assertTrue(reporte.formatear_reporte().endswith("MOTIVO: " + motivo))

    def test_SC003_reporte_no_resoluble_ejecuta_un_solo_recorrido(self):
        salas = [{"id": 1, "salidas": {"N": {"sala": 2, "cerrada": True, "llave": "fin"}}},
                 {"id": 2, "salidas": {}}]
        with patch.object(resolubilidad, "_recorrer", wraps=resolubilidad._recorrer) as recorrer:
            reporte = verificar_resolubilidad(_esqueleto(salas), [{"id": "fin", "sala": 2}], 1, 2, "fin")
            texto = reporte.formatear_reporte()
        recorrer.assert_called_once()
        self.assertEqual(reporte.llaves_no_obtenibles, ["fin"])
        self.assertEqual(reporte.frontera_bloqueada, [(1, "N", 2, "fin")])
        self.assertEqual(reporte.ciclos, ["fin -> fin [sala 1 (N)]"])
        self.assertTrue(texto.endswith("MOTIVO: llave_salida no puede obtenerse"))

    def test_SC004_dos_verificaciones_reproducen_texto_exacto_de_ciclos(self):
        salas = [{"id": 1, "salidas": {
            "N": {"sala": 2, "cerrada": True, "llave": "b"},
            "E": {"sala": 3, "cerrada": True, "llave": "a"}}},
            {"id": 2, "salidas": {}}, {"id": 3, "salidas": {}}]
        esqueleto = _esqueleto(salas)
        llaves = [{"id": "a", "sala": 2}, {"id": "b", "sala": 3}]
        textos = []
        for _ in range(2):
            reporte = verificar_resolubilidad(esqueleto, llaves, 1, 3, "a")
            texto = reporte.formatear_reporte().split("CICLOS DETECTADOS:\n", 1)[1]
            textos.append(texto.split("\nMOTIVO:", 1)[0])
        self.assertEqual(textos, ["  - a -> b [sala 1 (N)] -> a [sala 1 (E)]"] * 2)

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

    def test_FR010_coincidencia_por_id_y_abre_del_registro_de_llaves(self):
        salas = [
            {"id": 1, "salidas": {"E": {"sala": 2, "cerrada": True, "llave": "cerrojo"},
                                    "N": {"sala": 3, "cerrada": True, "llave": "itm_inicio"}}},
            {"id": 2, "salidas": {"E": {"sala": 4, "cerrada": True, "llave": "itm_fin"}}},
            {"id": 3, "salidas": {}}, {"id": 4, "salidas": {}},
        ]
        llaves = [{"id": "itm_inicio", "sala": 1, "abre": "cerrojo"},
                  {"id": "itm_fin", "sala": 2}]
        reporte = verificar_resolubilidad(_esqueleto(salas), llaves, 1, 4, "itm_fin")
        self.assertTrue(reporte.es_resoluble())
        self.assertEqual(reporte.orden_llaves, [(0, ["itm_inicio"]), (1, ["itm_fin"])])
        # El mismo id tambi?n abre la otra puerta de la sala inicial.
        self.assertEqual(reporte.frontera_bloqueada, [])
        sin_alias = [{"id": "itm_inicio", "sala": 1}, {"id": "itm_fin", "sala": 2}]
        reporte = verificar_resolubilidad(_esqueleto(salas), sin_alias, 1, 4, "itm_fin")
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
        self.assertEqual(reporte.motivo,
                         "ninguna puerta hacia sala_salida que pide llave_salida es alcanzable")

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
