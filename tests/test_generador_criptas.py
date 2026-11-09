r"""Fixtures FR-008; ejecutar con venv\Scripts\python.exe -m tests.test_generador_criptas."""

import unittest

from bench.generador_criptas import generar_cripta
from tests.cripta_de_prueba import ubicar_llaves


def _salas(datos):
    return [sala for pagina in datos["paginas"] for sala in pagina["salas"]]


def _alcanzables(salas, llaves):
    """Oráculo de prueba pequeño: recorrido completo con las llaves indicadas."""
    visitadas = [False] * len(salas)
    pendientes = [0]
    visitadas[0] = True
    while pendientes:
        posicion = pendientes.pop()
        for salida in salas[posicion]["salidas"].values():
            if salida.get("cerrada") and salida.get("llave") not in llaves:
                continue
            destino = salida["sala"] - 1
            if not visitadas[destino]:
                visitadas[destino] = True
                pendientes.append(destino)
    return visitadas


class TestGeneradorCriptas(unittest.TestCase):
    def test_FR008_linea_por_defecto_conserva_la_interfaz(self):
        parametros = (12, 7, (40, 200), 4, 600, 3, 300, 5)
        datos = generar_cripta(*parametros)
        self.assertEqual(datos, generar_cripta(*parametros, topologia="linea"))
        salas = _salas(datos)
        self.assertEqual(len(salas), 12)
        self.assertEqual(len(datos["paginas"]), 3)
        self.assertEqual(salas[0]["salidas"]["N"]["sala"], 2)
        for anterior, siguiente in zip(salas, salas[1:]):
            self.assertEqual(anterior["salidas"]["N"]["costo"], siguiente["salidas"]["S"]["costo"])

    def test_FR008_cuadricula_bidireccional_sin_enlaces_fuera_del_borde(self):
        # Ejemplos explícitos: cuadrado completo y última fila incompleta.
        for cantidad, esperadas in (
                (9, [[("S", 6), ("E", 2)], [("S", 5), ("E", 3), ("O", 1)],
                     [("S", 4), ("O", 2)], [("N", 3), ("S", 9), ("O", 5)],
                     [("N", 2), ("S", 8), ("E", 4), ("O", 6)], [("N", 1), ("S", 7), ("E", 5)],
                     [("N", 6), ("E", 8)], [("N", 5), ("E", 9), ("O", 7)], [("N", 4), ("O", 8)]]),
                (5, [[("E", 2)], [("S", 5), ("E", 3), ("O", 1)], [("S", 4), ("O", 2)],
                     [("N", 3), ("O", 5)], [("N", 2), ("E", 4)]])):
            salas = _salas(generar_cripta(cantidad, topologia="cuadricula"))
            self.assertEqual([[(d, salida["sala"]) for d, salida in s["salidas"].items()]
                              for s in salas], esperadas)
        for cantidad in (2, 3, 4, 5, 9, 10, 17):
            with self.subTest(salas=cantidad):
                datos = generar_cripta(cantidad, topologia="cuadricula")
                salas = _salas(datos)
                self.assertEqual(len(salas), cantidad)
                for sala in salas:
                    self.assertTrue(1 <= len(sala["salidas"]) <= 4)
                    for direccion, opuesta in (("N", "S"), ("S", "N"), ("E", "O"), ("O", "E")):
                        if direccion in sala["salidas"]:
                            destino = sala["salidas"][direccion]["sala"]
                            self.assertTrue(1 <= destino <= cantidad)
                            self.assertEqual(salas[destino - 1]["salidas"][opuesta]["sala"], sala["id"])

    def test_FR008_cuadricula_ofrece_rutas_de_distinto_costo(self):
        for semilla in range(12):
            with self.subTest(semilla=semilla):
                datos = generar_cripta(4, semilla=semilla, rango_costos=(1, 2), topologia="cuadricula")
                salas = _salas(datos)
                este = salas[0]["salidas"]["E"]
                sur = salas[0]["salidas"]["S"]
                este_sur = salas[este["sala"] - 1]["salidas"]["S"]
                sur_este = salas[sur["sala"] - 1]["salidas"]["E"]
                self.assertEqual(este_sur["sala"], sur_este["sala"])
                self.assertNotEqual(este["costo"] + este_sur["costo"], sur["costo"] + sur_este["costo"])
                for sala in salas:
                    for salida in sala["salidas"].values():
                        self.assertIn(salida["costo"], (1, 2))

    def test_FR008_cuadricula_sortea_cada_salida_independientemente(self):
        salas = _salas(generar_cripta(16, semilla=7, rango_costos=(1, 100), topologia="cuadricula"))
        diferencias = []
        for sala in salas:
            for direccion, opuesta in (("N", "S"), ("S", "N"), ("E", "O"), ("O", "E")):
                if direccion in sala["salidas"]:
                    salida = sala["salidas"][direccion]
                    inversa = salas[salida["sala"] - 1]["salidas"][opuesta]
                    self.assertTrue(1 <= salida["costo"] <= 100)
                    diferencias.append(salida["costo"] != inversa["costo"])
        self.assertTrue(any(diferencias))

    def test_FR008_cadena_resoluble_sin_saltarse_llaves_en_ambas_topologias(self):
        for topologia in ("linea", "cuadricula"):
            for cantidad, cadena in ((2, 1), (12, 3), (13, 12)):
                with self.subTest(topologia=topologia, salas=cantidad, cadena=cadena):
                    datos = generar_cripta(cantidad, semilla=7, cadena_llaves=cadena,
                                           cantidad_cazadores=20, cierre_automatico=300,
                                           topologia=topologia)
                    salas = _salas(datos)
                    disponibles = []
                    ubicaciones = datos["llaves"]["llaves"]
                    for llave in ubicaciones:
                        visitadas = _alcanzables(salas, disponibles)
                        nuevas = [u["id"] for u in ubicaciones
                                  if visitadas[u["sala"] - 1] and u["id"] not in disponibles]
                        self.assertEqual(nuevas, [llave["id"]])
                        self.assertFalse(visitadas[datos["general"]["sala_salida"] - 1])
                        disponibles.extend(nuevas)
                    self.assertTrue(all(_alcanzables(salas, disponibles)))
                    ultima = datos["general"]["llave_salida"]
                    for sala in salas:
                        for salida in sala["salidas"].values():
                            if salida["sala"] == datos["general"]["sala_salida"]:
                                self.assertEqual(salida["llave"], ultima)
                            if salida.get("cerrada"):
                                self.assertEqual(salida["cierre_automatico"], 300)
                    reconstruidas = ubicar_llaves(datos["contenido"]["contenido"],
                                                  datos["catalogo"]["entidades"])["llaves"]
                    self.assertEqual(len(reconstruidas), cadena)
                    for llave in ubicaciones:
                        self.assertIn(llave, reconstruidas)

    def test_FR008_misma_semilla_mismos_datos_y_version_distingue_topologia(self):
        for topologia in ("linea", "cuadricula"):
            parametros = {"numero_salas": 12, "semilla": 9, "cadena_llaves": 3,
                          "cantidad_cazadores": 12, "rango_cazadores": (0, 50),
                          "topologia": topologia}
            datos = generar_cripta(**parametros)
            self.assertEqual(datos, generar_cripta(**parametros))
            otro = generar_cripta(**parametros)
            otro["paginas"][0]["salas"][0]["nombre"] = "alterada"
            self.assertNotEqual(datos, otro)
        self.assertNotEqual(generar_cripta(12)["general"]["version"],
                            generar_cripta(12, topologia="cuadricula")["general"]["version"])

    def test_FR008_rango_cazadores_entero_o_intervalo_inclusivo(self):
        for rango in (0, 600, (0, 2), (600, 600)):
            with self.subTest(rango=rango):
                datos = generar_cripta(16, semilla=7, cantidad_cazadores=40, rango_cazadores=rango)
                valores = [f["rango"] for f in datos["catalogo"]["entidades"] if f["clase"] == "enemigo"]
                self.assertEqual(len(valores), 40)
                minimo, maximo = rango if isinstance(rango, tuple) else (rango, rango)
                self.assertTrue(all(type(valor) is int and minimo <= valor <= maximo for valor in valores))
                self.assertIn(minimo, valores)
                self.assertIn(maximo, valores)
                self.assertEqual(datos, generar_cripta(16, semilla=7, cantidad_cazadores=40,
                                                      rango_cazadores=rango))

    def test_FR008_rechaza_rangos_de_cazador_invalidos(self):
        for rango in (-1, True, False, 2.0, "3", None, (), (1,), (1, 2, 3),
                      (-1, 2), (2, 1), (True, 3), (0, 3.0), (0, "3"), [0, 3]):
            with self.subTest(rango=rango):
                with self.assertRaises(ValueError):
                    generar_cripta(rango_cazadores=rango)

    def test_FR008_rechaza_topologias_desconocidas(self):
        for topologia in ("", "arbol", None, 1):
            with self.subTest(topologia=topologia):
                with self.assertRaises(ValueError):
                    generar_cripta(topologia=topologia)


if __name__ == "__main__":
    unittest.main(verbosity=2)
