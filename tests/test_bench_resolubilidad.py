"""Validación del comparador de SC-005; no prueba tiempos de la máquina."""

from copy import deepcopy
import unittest
from unittest.mock import patch

from bench import bench_resolubilidad as bench
from modelo.datos.esqueleto import Esqueleto
from modelo.juego.resolubilidad import ResultadoResolubilidad, verificar_resolubilidad


def _esqueleto(salas):
    esqueleto = Esqueleto()
    esqueleto.agregar_pagina({"salas": salas})
    return esqueleto


class PruebasBenchResolubilidad(unittest.TestCase):
    def test_FR013_merge_conserva_resultado_y_orden_de_criptas_existentes(self):
        from modelo.estructuras.ordenamiento import ordenar
        from modelo.juego import resolubilidad
        from tests import test_resolubilidad as aceptacion

        def comparar(*argumentos, **opciones):
            actual = verificar_resolubilidad(*argumentos, **opciones)
            # El verificador anterior solo difiere en la función de ordenación.
            with patch.object(resolubilidad, "ordenar_merge", ordenar):
                anterior = verificar_resolubilidad(*argumentos, **opciones)
            for atributo in ("estado", "orden_llaves", "llaves_no_obtenibles",
                             "frontera_bloqueada", "ubicacion_llaves", "ciclos", "motivo"):
                self.assertEqual(getattr(actual, atributo), getattr(anterior, atributo), atributo)
            self.assertEqual(actual.formatear_reporte(), anterior.formatear_reporte())
            return actual

        # Reutilizar las criptas y permutaciones de aceptación, sin duplicar fixtures:
        # ciclo, llave portada e inalcanzable, y empates lexicográficos por etapa.
        with patch.object(aceptacion, "verificar_resolubilidad", side_effect=comparar):
            for prueba in (
                    aceptacion.test_FR014_llave_salida_detras_de_su_propia_puerta_con_ciclo,
                    aceptacion.test_FR002_llave_en_suelta_de_errante_en_sala_inicial,
                    aceptacion.test_FR013_varios_ordenes_validos_mismo_orden_determinista):
                with self.subTest(cripta=prueba.__name__):
                    prueba()
        for topologia, salas, llaves in bench.CASOS:
            with self.subTest(topologia=topologia, salas=salas, llaves=llaves):
                comparar(*bench._crear_caso(topologia, salas, llaves))

    def test_SC005_casos_del_bench_coinciden_con_el_orden_generado(self):
        for topologia, salas, llaves in bench.CASOS:
            with self.subTest(topologia=topologia, salas=salas, llaves=llaves):
                argumentos = bench._crear_caso(topologia, salas, llaves)
                esperado = [(i, [u["id"]]) for i, u in enumerate(argumentos[1])]
                for funcion in (verificar_resolubilidad, bench.verificar_repetido):
                    resultado = funcion(*argumentos)
                    self.assertEqual(resultado.estado, "RESOLUBLE")
                    self.assertEqual(resultado.orden_llaves, esperado)

    def test_FR013_varias_llaves_por_etapa_no_adelantan_la_siguiente(self):
        salas = [
            {"id": 10, "salidas": {"N": {"sala": 20},
                                   "E": {"sala": 30, "cerrada": True, "llave": "a"},
                                   "O": {"sala": 40, "cerrada": True, "llave": "z"}}},
            {"id": 20, "salidas": {}},
            {"id": 30, "salidas": {"N": {"sala": 50, "cerrada": True, "llave": "b"}}},
            {"id": 40, "salidas": {}}, {"id": 50, "salidas": {}},
        ]
        llaves = [{"id": "z", "sala": 10}, {"id": "a", "sala": 20},
                  {"id": "c", "sala": 40}, {"id": "b", "sala": 30}]
        esperado = [(0, ["a", "z"]), (1, ["b", "c"])]
        for entrada in (salas, salas[::-1]):
            argumentos = (_esqueleto(entrada), llaves, 10, 50, "b")
            for funcion in (verificar_resolubilidad, bench.verificar_repetido):
                resultado = funcion(*argumentos)
                self.assertEqual(resultado.estado, "RESOLUBLE")
                self.assertEqual(resultado.orden_llaves, esperado)

    def test_FR010_alias_de_ubicacion_y_catalogo_y_llave_portada(self):
        salas = [{"id": 3, "salidas": {"N": {"sala": 9, "cerrada": True, "llave": "puerta"}}},
                 {"id": 9, "salidas": {}}]
        for en_catalogo in (False, True):
            llaves = [{"id": "llave", "sala": 3, "enemigo": "instancia-sintetica"}]
            catalogo = [{"id": "llave", "abre": "puerta"}] if en_catalogo else []
            if not en_catalogo:
                llaves[0]["abre"] = "puerta"
            argumentos = (_esqueleto(salas), llaves, 3, 9, "puerta", catalogo)
            for funcion in (verificar_resolubilidad, bench.verificar_repetido):
                resultado = funcion(*argumentos)
                self.assertEqual(resultado.estado, "RESOLUBLE")
                self.assertEqual(resultado.orden_llaves, [(0, ["llave"])])

    def test_FR011_rechaza_salida_sin_llave_o_sin_puerta_correspondiente(self):
        for cerrada, pedido, sala_llave in ((True, "fin", 9), (False, None, 3),
                                           (True, None, 3)):
            salas = [{"id": 3, "salidas": {"N": {"sala": 9, "cerrada": cerrada, "llave": pedido}}},
                     {"id": 9, "salidas": {}}]
            argumentos = (_esqueleto(salas), [{"id": "fin", "sala": sala_llave}], 3, 9, "fin")
            for funcion in (verificar_resolubilidad, bench.verificar_repetido):
                resultado = funcion(*argumentos)
                self.assertEqual(resultado.estado, "NO RESOLUBLE")
                self.assertEqual(resultado.orden_llaves, [])

    def test_SC005_reinicia_por_cada_llave_y_no_modifica_entradas(self):
        argumentos = bench._crear_caso("linea", 11, 10)
        esqueleto = argumentos[0]
        original = deepcopy((esqueleto.ids, esqueleto.salidas, argumentos[1:]))
        with patch.object(bench, "_recorrido_completo", wraps=bench._recorrido_completo) as recorrer:
            resultado = bench.verificar_repetido(*argumentos)
        self.assertTrue(resultado.es_resoluble())
        self.assertEqual(recorrer.call_count, 1 + len(argumentos[1]))
        self.assertTrue(all(llamada.args[1] == esqueleto.posicion(argumentos[2])
                            for llamada in recorrer.call_args_list))
        self.assertEqual((esqueleto.ids, esqueleto.salidas, argumentos[1:]), original)

    def test_SC005_interrumpe_medicion_si_difieren_estado_u_orden(self):
        esperado = ResultadoResolubilidad("RESOLUBLE", [(0, ["a", "b"])])
        for otro in (ResultadoResolubilidad("NO RESOLUBLE"),
                     ResultadoResolubilidad("RESOLUBLE", [(0, ["b", "a"])])):
            with self.assertRaises(AssertionError):
                bench._comprobar_equivalencia(esperado, otro)


if __name__ == "__main__":
    unittest.main(verbosity=2)
