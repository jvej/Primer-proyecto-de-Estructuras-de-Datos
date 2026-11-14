"""Regresiones de integracion del benchmark 002, sin medir en las pruebas CLI."""

import runpy
from pathlib import Path
import unittest
from unittest.mock import patch

import main
from tests import bench_niebla_ir_a as bench


class PruebasBenchMapa(unittest.TestCase):
    def test_SC002_registro_y_despacho(self):
        registros = [r for r in main.BENCHES if r[0] == "mapa_conocido"]
        self.assertEqual(registros, [("mapa_conocido", "bench_mapa_conocido.py")])
        with patch("main.runpy.run_path") as ejecutar, patch("main.crear_vista", side_effect=AssertionError("vista")):
            self.assertEqual(main.main(["--bench", "mapa_conocido"]), 0)
        ejecutar.assert_called_once_with(str(Path(main.CARPETA_PROYECTO) / "bench" / "bench_mapa_conocido.py"), run_name="__main__")

    def test_SC002_adaptador_aisla_argumentos(self):
        with patch.object(bench, "main") as ejecutar, patch("sys.argv", ["main.py", "--bench", "mapa_conocido"]):
            runpy.run_path(str(Path(main.CARPETA_PROYECTO) / "bench" / "bench_mapa_conocido.py"), run_name="__main__")
        ejecutar.assert_called_once_with([])

    def test_SC003_SC004_escenarios_reales_y_reversion(self):
        mapa = bench.MapaSintetico(10, 20261110)
        with patch("builtins.print"):
            bench.medir_actualizacion(mapa, 2, 1)
            bench.medir_actualizacion(mapa, 2, 1, antorcha=True)
            bench.medir_registro(mapa, 2, 1)
            bench.medir_pergamino(10, 2)

    def test_SC002_error_de_subsistema_y_benchmark(self):
        with patch("builtins.print"):
            self.assertEqual(main.main(["--bench", "no_existe"]), 2)
            with patch("main.runpy.run_path", side_effect=ValueError("fallo")):
                self.assertEqual(main.main(["--bench", "mapa_conocido"]), 1)


if __name__ == "__main__":
    unittest.main()
