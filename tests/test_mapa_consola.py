"""Bloque 6: mapa filtrado, costos e IR_A desde consola."""

import unittest

from controlador.controlador import Controlador
from controlador.orden import MAPA, IR_A, MOVER, Orden
from modelo.juego.conocimiento import PUERTA_ABIERTA
from tests.cripta_de_prueba import armar, esqueleto_linea
from vista.vista_consola import VistaConsola, interpretar, AYUDA_TEXTO


class PruebasMapaConsola(unittest.TestCase):
    def escenario(self, salas=None):
        if salas is None:
            salas = esqueleto_linea(5, [(1, 2, {"costo": 173})])
        for sala in salas:
            sala["nombre"] = "Nombre secreto %s" % sala["id"]
        esc = armar(salas, datos={"sala_salida": 5})
        self.addCleanup(esc.cerrar)
        return esc

    def foto(self, p):
        return (p.jugador.sala, p.reloj.tiempo_actual, p.acciones,
                list(p.conocimiento.estado_salas), list(p.conocimiento.memoria_puertas),
                p.conocimiento.resumen(), p.registro.acciones_deshacibles(),
                p.registro.cambios_registrados(), list(p.bitacora.ultimos()), len(p.agenda))

    def test_FR004_FR005_mapa_no_filtra_ids_nombres_ni_contenido(self):
        p = self.escenario().partida
        mapa = p.mapa_conocido()
        self.assertEqual(mapa, [(1, "Nombre secreto 1", [("N", "abierta", None, None, 173)])])
        salida = []
        vista = VistaConsola(salida=salida.append)
        vista.mostrar_mapa(mapa)
        texto = "\n".join(salida)
        for secreto in ("Nombre secreto 2", "Nombre secreto 3", "Sala 2:", "Sala 3:", "sala None"):
            self.assertNotIn(secreto, texto)
        self.assertIn("desconocida", texto)
        self.assertIn("costo 173", texto)
        mapa[0][2].clear()
        self.assertEqual(len(p.salidas_visibles()), 1)

    def test_FR003_FR006_mapa_usa_memoria_no_estado_fisico(self):
        p = self.escenario().partida
        self.assertTrue(p.mover("N"))
        self.assertTrue(p.mover("N"))
        puerta = p.mapa.sala(1).salidas[0]
        p.cambiar_estado_puerta(puerta, "cerrada")
        antes = self.foto(p)
        fila = p.mapa_conocido()[0]
        self.assertEqual(fila[2][0], ("N", "abierta", 2, None, 173))
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(1), 0), PUERTA_ABIERTA)
        self.assertEqual(self.foto(p), antes)

    def test_FR007_FR010_puertas_no_observadas_ocultan_estado_y_llave(self):
        salas = esqueleto_linea(5, [(3, 4, {"cerrada": True, "llave": "llave_no_observada", "costo": 201})])
        esc = self.escenario(salas)
        p = esc.partida
        self.assertTrue(p.usar(esc.dar("itm_antorcha")))
        self.assertTrue(p.mover("N"))
        mapa = p.mapa_conocido()
        self.assertEqual([fila[0] for fila in mapa], [1, 2, 3])
        salida_remota = mapa[2][2][0]
        self.assertEqual(salida_remota, ("N", "desconocida", None, None, 201))
        self.assertNotIn("llave_no_observada", str(mapa))
        self.assertFalse(p.mapa.sala(3).incorporada)

    def test_FR009_mapa_es_consulta_sin_tiempo_historial_ni_log(self):
        p = self.escenario().partida
        salida = []
        c = Controlador(p, VistaConsola(salida=salida.append))
        registradas = []
        c.agregar_observador(registradas.append)
        antes = self.foto(p)
        self.assertFalse(Orden(MAPA).es_de_partida())
        self.assertTrue(c.ejecutar(interpretar("mapa", p)))
        self.assertTrue(salida)
        self.assertEqual(self.foto(p), antes)
        self.assertEqual(registradas, [])
        self.assertTrue(Controlador(p).ejecutar(Orden(MAPA)))
        self.assertEqual(self.foto(p), antes)

    def test_FR014_ir_a_desde_pedir_orden_conserva_ids_y_movimientos(self):
        p = self.escenario().partida
        self.assertEqual(interpretar("ir a 4", p), Orden(IR_A, 4))
        self.assertEqual(interpretar("ir n", p), Orden(MOVER, "N"))
        self.assertEqual(interpretar("n", p), Orden(MOVER, "N"))
        self.assertEqual(interpretar("mover norte", p), Orden(MOVER, "N"))
        vista = VistaConsola(entrada=lambda indicacion: "ir a 4", salida=lambda texto: None)
        c = Controlador(p, vista)
        antes = self.foto(p)
        self.assertFalse(c.ejecutar(vista.pedir_orden(p)))
        self.assertEqual(self.foto(p), antes)
        for sala in p.mapa.salas:
            p._explorar_sala(sala)
            for salida in sala.salidas:
                if salida is not None:
                    p._recordar_puerta(salida)
        self.assertTrue(c.ejecutar(vista.pedir_orden(p)))
        self.assertEqual((p.jugador.sala.id, p.acciones), (4, 3))

    def test_FR014_parser_errores_y_ayuda(self):
        p = self.escenario().partida
        for texto in ("ir a", "ir a cero", "ir a -1", "ir a 0", "ir a 4 extra", "mapa extra"):
            self.assertIsInstance(interpretar(texto, p), str)
        self.assertIn("ir a <sala>", AYUDA_TEXTO)
        self.assertIn("mapa", AYUDA_TEXTO)

    def test_FR003_FR010_salidas_cinco_campos_sin_sala_none(self):
        p = self.escenario().partida
        self.assertEqual(p.salidas_visibles(), [("N", "abierta", None, None, 173)])
        texto = VistaConsola()._texto_salidas(p)
        self.assertIn("desconocida", texto)
        self.assertIn("costo 173", texto)
        self.assertNotIn("sala None", texto)

if __name__ == "__main__":
    unittest.main()
