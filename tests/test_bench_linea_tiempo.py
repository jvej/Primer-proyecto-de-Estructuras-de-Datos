"""Contrato del bench; los umbrales temporales se comprueban con datos reales."""

import unittest


class PruebasBenchLineaTiempo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bench import bench_linea_tiempo as bench
        cls.bench = bench
        cls.carga = bench.crear_carga(acciones=5000, salas=8)
        cls.resultados = bench.ejecutar_matriz(cls.carga, repeticiones=1)

    def test_SC005_matriz_K_y_alternativas(self):
        self.assertEqual(self.carga.semilla, 20261113)
        self.assertGreaterEqual(self.carga.aceptadas, 5000)
        self.assertEqual([r.nombre for r in self.resultados],
                         ["K=10", "K=50", "K=200", "sin checkpoints",
                          "desde actual", "foto por accion"])
        for r in self.resultados:
            self.assertTrue(r.equivalente)
            self.assertGreater(r.consultas_validadas, 10)
            self.assertEqual(len(r.muestras), len(self.carga.objetivos))
        # También hay una carga sin cambios de inventario ni efectos.
        segura = self.bench.crear_carga(acciones=25, salas=8, caso="seguro")
        self.assertEqual(segura.aceptadas, 25)
        self.bench.validar_variantes(segura)

    def test_SC002_cuenta_grupos_y_externos(self):
        for r in self.resultados[:3]:
            self.assertLessEqual(r.max_grupos, r.k)
            self.assertGreater(r.max_grupos, 0)
            self.assertGreater(r.max_externos, 0)
        self.assertGreater(self.resultados[3].max_grupos, 200)
        self.assertGreater(self.resultados[4].max_grupos, 200)
        self.assertEqual(self.resultados[5].max_grupos, 0)

    def test_SC001_latencia_total_reportada(self):
        # No reloj simulado, ni aserción de <50 ms en una máquina arbitraria.
        for r in self.resultados:
            self.assertGreater(r.preparacion_ms, 0)
            for m in r.muestras:
                self.assertGreater(m.total_ms, 0)
                self.assertTrue(all(t >= 0 for t in m.fases_ms))
                self.assertGreater(sum(m.fases_ms), 0)
            valores = [m.total_ms for m in r.muestras]
            self.assertEqual(r.maximo_ms, self.bench.estadisticas(valores)[0])
            self.assertEqual(r.mediana_ms, self.bench.estadisticas(valores)[1])
        self.assertEqual(self.bench.estadisticas([4, 1, 3, 2]), (4, 2.5))

    def test_SC003_memoria_por_componentes(self):
        for r in self.resultados:
            self.assertEqual([c.nombre for c in r.memoria],
                             ["bases", "deltas", "directorios", "checkpoints"])
            for c in r.memoria:
                self.assertGreaterEqual(c.retenida, 0)
                self.assertGreaterEqual(c.pico, c.retenida)
            self.assertEqual(r.retenida, sum(c.retenida for c in r.memoria))
            self.assertGreaterEqual(r.pico, r.retenida)
            self.assertGreater(r.reserva, 0)
        for r in self.resultados[:3]:
            self.assertEqual(r.checkpoints, 1 + self.carga.aceptadas // r.k)
        self.assertEqual(self.resultados[3].checkpoints, 1)

    def test_SC004_recorte_sufijo_persistentes_y_liberacion(self):
        filas = self.bench.medir_recortes(longitudes=(200, 400), repeticiones=2)
        self.assertEqual(len(filas), 10)
        for i, fila in enumerate(filas):
            self.assertEqual(fila.prefijo_visitado, 0)
            self.assertEqual(fila.grupos, i % 5 + 1)
            self.assertEqual(fila.checkpoints_liberados, 1)
            self.assertGreater(fila.persistentes, 0)
            self.assertTrue(fila.equivalente)
            self.assertGreater(fila.mediana_ms, 0)
            self.assertEqual(fila.visitados, filas[i % 5].visitados)

    def test_SC005_C1_integrada_mismo_resultado(self):
        filas = self.bench.medir_c1(tamanos=(4, 12), ciclos=30, repeticiones=2)
        self.assertEqual(len(filas), 2)
        for fila in filas:
            self.assertTrue(fila.equivalente)
            self.assertGreater(fila.sin_c1_us, 0)
            self.assertGreater(fila.con_c1_us, 0)
            self.assertGreater(fila.deltas, 0)
            self.assertAlmostEqual(fila.extra_us, fila.con_c1_us - fila.sin_c1_us)

    def test_SC005_peor_caso_D_real_y_equivalente(self):
        for d in (100, 1000):
            carga = self.bench.crear_carga_peor_deltas(d)
            self.assertEqual(carga.aceptadas, 600)
            self.assertEqual(len(carga.deltas), 600 * d)
            self.assertEqual(len(carga.inicial.actores), d - 2)
            self.assertTrue(all(a.activo for a in carga.inicial.actores))
            self.assertEqual(len(carga.esperados), len(carga.objetivos))
            for grupo in carga.grupos:
                self.assertEqual(grupo.cursor_fin - grupo.cursor_inicio, d)
            for k in self.bench.VALORES_K:
                variante = self.bench.preparar_variante(carga, k)
                self.assertGreaterEqual(len(variante.linea.checkpoints), 3)
                self.assertEqual(self.bench._validar(carga, variante), len(carga.objetivos))
                # Medición real de ambas APIs en el extremo del último bloque.
                b = 600 - 1
                esperado = carga.esperados[carga.objetivos.index(b)]
                for por_t in (False, True):
                    muestra = self.bench.medir_consulta(variante, b, esperado, por_t)
                    self.assertEqual(muestra.grupos, k - 1)
                    self.assertEqual(muestra.deltas, (k - 1) * d)
                    self.assertEqual(muestra.externos, 0)
                    self.assertGreater(muestra.total_ms, 0)

    def test_SC003_peor_caso_reutiliza_medicion_y_reporte(self):
        from contextlib import redirect_stdout
        from io import StringIO
        # Menor longitud para verificar el informe/memoria, sin umbral temporal.
        filas = self.bench.medir_peor_caso(acciones=3, repeticiones=1)
        self.assertEqual([(d, r.k) for d, r in filas],
                         [(d, k) for d in (100, 1000) for k in (10, 50, 200)])
        for d, r in filas:
            self.assertTrue(r.equivalente)
            self.assertEqual(r.max_deltas, 3 * d)
            self.assertGreater(r.retenida, 0)
            self.assertGreaterEqual(r.pico, r.retenida)
            self.assertTrue(any(m.selector == 't' for m in r.muestras))
            self.assertTrue(any(m.selector == '#k' for m in r.muestras))
        salida = StringIO()
        with redirect_stdout(salida):
            self.bench.imprimir_peor_caso(filas, acciones=3)
            self.bench.imprimir_resumen_k(self.resultados, filas)
        self.assertIn('max grupos/deltas', salida.getvalue())
        self.assertIn('Resumen por K', salida.getvalue())

    def test_FR011_despacho_bench_headless(self):
        import main
        self.assertIn(("linea_tiempo", "bench_linea_tiempo.py"), main.BENCHES)
        self.assertEqual(main.leer_argumentos(["--bench", "linea_tiempo"]).bench,
                         ["linea_tiempo"])


if __name__ == "__main__":
    unittest.main()
