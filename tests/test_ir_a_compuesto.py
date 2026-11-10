"""IR_A: §3.4 y casos aplicables del Apéndice B, sin conexión de aplicación."""

import os
import tempfile
import unittest

from controlador.controlador import Controlador
from controlador.orden import IR_A, MOVER, PERGAMINO, CARGAR, Orden, interpretar_ir_a
from modelo.datos.bitacora_partida import BitacoraPartida, EncabezadoLog, leer_log
from modelo.juego.conocimiento import PUERTA_ABIERTA, PUERTA_CERRADA
from modelo.juego import efectos
from tests.cripta_de_prueba import armar, entrada, esqueleto_linea


class PruebasViaje(unittest.TestCase):
    def escenario(self, contenido=(), salas=None, conocidas=True):
        esc = armar(salas if salas is not None else esqueleto_linea(5), contenido,
                    datos={"sala_salida": 5}, capacidad=6)
        self.addCleanup(esc.cerrar)
        p = esc.partida
        if conocidas:
            # Conocimiento previo sintético: no activa contenido remoto.
            for sala in p.mapa.salas:
                p._explorar_sala(sala)
                for salida in sala.salidas:
                    if salida is not None:
                        p._recordar_puerta(salida)
        return esc

    def mensaje(self, esc):
        return esc.mensajes()[-1]

    def test_FR014_parser_clasificacion_y_log_atomico(self):
        self.assertEqual(interpretar_ir_a("  IR A 27  "), Orden(IR_A, 27))
        self.assertFalse(Orden(IR_A, 27).es_de_partida())
        with self.assertRaises(ValueError):
            Orden(IR_A, 27).a_texto()
        with self.assertRaises(ValueError):
            Orden.desde_texto("ir_a 27")
        for texto in ("ir a", "ir a -2", "ir a 0", "ir a x", "ir a 2 extra", "ir n"):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                interpretar_ir_a(texto)

    def test_B_FR014_no_explorada_rechazada_sin_tiempo(self):
        esc = self.escenario(conocidas=False)
        p = esc.partida
        c = Controlador(p)
        for destino in (2, 3, 999, -1, True):
            self.assertFalse(c.ejecutar(Orden(IR_A, destino)))
            self.assertEqual((p.acciones, p.reloj.tiempo_actual, p.registro.acciones_deshacibles()), (0, 0, 0))

    def test_FR014_destino_actual_y_parser_publico(self):
        esc = self.escenario()
        c = Controlador(esc.partida)
        self.assertTrue(c.ejecutar("ir a 1"))
        self.assertEqual(esc.partida.acciones, 0)
        self.assertIn("Ya te encuentras", self.mensaje(esc))
        self.assertFalse(c.ejecutar("ir a x"))

    def test_FR017_FR018_pasos_ordinarios_costos_y_recalculo(self):
        salas = esqueleto_linea(5, [(1, 2, {"costo": 37}), (2, 3, {"costo": 210})])
        esc = self.escenario(salas=salas)
        p = esc.partida
        c = Controlador(p)
        movimientos = []
        c.agregar_observador(lambda orden: movimientos.append((orden, p.reloj.tiempo_actual)))
        self.assertTrue(c.ejecutar("ir a 3"))
        self.assertEqual(movimientos, [(Orden(MOVER, "N"), 37), (Orden(MOVER, "N"), 247)])
        self.assertGreaterEqual(c._planificador._token_navegacion, 3)
        self.assertEqual(p.registro.acciones_deshacibles(), 2)
        self.assertIn("llegado", self.mensaje(esc))

    def test_B_FR019_puerta_recordada_abierta_se_observa_y_detiene(self):
        esc = self.escenario()
        p = esc.partida
        p.mapa.sala(2).salidas[0].estado = "cerrada"
        c = Controlador(p)
        self.assertTrue(c.ejecutar("ir a 4"))
        self.assertEqual((p.jugador.sala.id, p.reloj.tiempo_actual, p.acciones), (2, 100, 1))
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(2), 0), PUERTA_CERRADA)
        self.assertIn("ruta bloqueada", self.mensaje(esc))

    def test_B_FR019_puerta_adyacente_cerrada_no_gasta_tiempo(self):
        esc = self.escenario()
        p = esc.partida
        p.mapa.sala(1).salidas[0].estado = "cerrada"
        self.assertTrue(Controlador(p).ejecutar("ir a 3"))
        self.assertEqual((p.reloj.tiempo_actual, p.acciones), (0, 0))
        self.assertEqual(p.conocimiento.puerta_recordada(p.mapa.sala(1), 0), PUERTA_CERRADA)

    def test_B_FR019_dormidos_se_activan_y_detienen_viaje(self):
        esc = self.escenario([entrada(2, enemigos=[("e-2", "ent_esqueleto", 10)])])
        p = esc.partida
        self.assertTrue(Controlador(p).ejecutar("ir a 4"))
        self.assertEqual(p.jugador.sala.id, 2)
        self.assertTrue(p.enemigos_en_sala()[0].activo)
        self.assertEqual(p.acciones, 1)
        self.assertIn("enemigos vivos", self.mensaje(esc))

    def test_FR019_dano_trampa_cancela(self):
        esc = self.escenario([entrada(2, trampas=[("t-2", "trp_dardos")])])
        self.assertTrue(Controlador(esc.partida).ejecutar("ir a 4"))
        self.assertEqual(esc.partida.jugador.sala.id, 2)
        self.assertIn("daño", self.mensaje(esc))

    def test_FR019_veneno_y_dano_curado_tambien_cancelan(self):
        for curar in (False, True):
            with self.subTest(curar=curar):
                esc = self.escenario()
                p = esc.partida
                if curar:
                    p.programar(20, lambda ahora: p.danar(p.jugador, 1))
                    p.programar(30, lambda ahora: p.curar(p.jugador, 1))
                else:
                    efectos.aplicar_veneno(p, p.jugador, 1)
                self.assertTrue(Controlador(p).ejecutar("ir a 4"))
                self.assertEqual(p.jugador.sala.id, 2)
                self.assertIn("daño", self.mensaje(esc))
                self.assertIs(p.cambiar.__func__, type(p).cambiar)

    def test_FR019_enemigos_muertos_no_detienen(self):
        esc = self.escenario([entrada(2, enemigos=[("e-2", "ent_esqueleto", 0)])])
        self.assertTrue(Controlador(esc.partida).ejecutar("ir a 3"))
        self.assertEqual(esc.partida.jugador.sala.id, 3)
        self.assertIn("llegado", self.mensaje(esc))

    def test_FR021_nunca_abre_puertas_ni_usa_llaves(self):
        salas = esqueleto_linea(5, [(1, 2, {"cerrada": True, "llave": "itm_llave_bronce"})])
        esc = self.escenario(salas=salas)
        llave = esc.dar("itm_llave_bronce")
        self.assertFalse(Controlador(esc.partida).ejecutar("ir a 3"))
        self.assertTrue(esc.inventario.contiene(llave))
        self.assertEqual(esc.partida.mapa.sala(1).salidas[0].estado, "cerrada")
        self.assertEqual(esc.partida.acciones, 0)

    def test_B_FR023_pergamino_posterior_revierte_solo_ultimo_paso(self):
        esc = self.escenario()
        p = esc.partida
        c = Controlador(p)
        esc.dar("itm_pergamino")
        c.ejecutar("ir a 4")
        self.assertTrue(c.ejecutar(Orden(PERGAMINO)))
        self.assertEqual((p.jugador.sala.id, p.reloj.tiempo_actual, p.acciones), (3, 200, 2))
        self.assertFalse(c._viaje_activo)

    def test_B_FR023_pergamino_durante_viaje_cancela_resto(self):
        esc = self.escenario()
        p = esc.partida
        c = Controlador(p)
        esc.dar("itm_pergamino")
        def revertir(orden):
            if orden.tipo == MOVER:
                c.ejecutar(Orden(PERGAMINO))
        c.agregar_observador(revertir)
        self.assertTrue(c.ejecutar("ir a 4"))
        self.assertEqual((p.jugador.sala.id, p.reloj.tiempo_actual, p.acciones), (1, 0, 0))
        self.assertIn("cancelado", self.mensaje(esc))

    def test_FR018_evento_cierra_puerta_y_se_recalcula(self):
        esc = self.escenario()
        p = esc.partida
        p.programar(25, lambda ahora: p.cambiar_estado_puerta(p.mapa.sala(2).salidas[0], "cerrada"))
        c = Controlador(p)
        self.assertTrue(c.ejecutar("ir a 4"))
        self.assertEqual((p.jugador.sala.id, p.acciones), (2, 1))
        self.assertGreaterEqual(c._planificador._token_navegacion, 3)

    def test_B_FR018_puerta_cerrada_se_evade_por_ruta_alternativa(self):
        salas = [
            {"id": 1, "salidas": {"N": {"sala": 2, "costo": 100}, "E": {"sala": 3, "costo": 300}}},
            {"id": 2, "salidas": {"S": {"sala": 1, "costo": 100}, "E": {"sala": 4, "costo": 100}}},
            {"id": 3, "salidas": {"O": {"sala": 1, "costo": 300}, "N": {"sala": 4, "costo": 100}}},
            {"id": 4, "salidas": {"O": {"sala": 2, "costo": 100}, "S": {"sala": 3, "costo": 100}}},
            {"id": 5, "salidas": {}},
        ]
        esc = self.escenario(salas=salas)
        p = esc.partida
        p.programar(25, lambda ahora: p.cambiar_estado_puerta(p.mapa.sala(2).salidas[2], "cerrada"))
        c = Controlador(p)
        pasos = []
        c.agregar_observador(lambda orden: pasos.append(orden.argumento))
        self.assertTrue(c.ejecutar("ir a 4"))
        self.assertEqual(pasos, ["N", "S", "E", "N"])
        self.assertEqual((p.jugador.sala.id, p.reloj.tiempo_actual), (4, 600))

    def test_FR019_dano_letal_detiene_viaje(self):
        esc = self.escenario([entrada(2, trampas=[("t-2", "trp_mortal")])])
        p = esc.partida
        self.assertTrue(Controlador(p).ejecutar("ir a 4"))
        self.assertEqual((p.estado, p.jugador.sala.id, p.acciones), ("derrota", 2, 1))
        self.assertIn("daño", self.mensaje(esc))

    def test_FR022_log_comentario_pasos_y_replay_sin_ir_a(self):
        esc = self.escenario(conocidas=False)
        p = esc.partida
        c = Controlador(p)
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "partida.log")
            log = BitacoraPartida(ruta, EncabezadoLog("test", "1", "1", 1))
            try:
                c.agregar_observador(log.anotar)
                c.agregar_observador_comentarios(log.anotar_comentario)
                # Explorar y regresar con movimientos reales, todos en el log.
                for direccion in ("N", "N", "N", "S", "S", "S"):
                    self.assertTrue(c.ejecutar(Orden(MOVER, direccion)))
                self.assertTrue(c.ejecutar("ir a 4"))
                self.assertEqual(log.lineas, 9)
            finally:
                log.cerrar()
            with open(ruta, encoding="utf-8") as archivo:
                texto = archivo.read()
            self.assertIn("# ir a 4\n", texto)
            _, ordenes = leer_log(ruta)
            otra = self.escenario(conocidas=False).partida
            replay = Controlador(otra)
            while not ordenes.vacia():
                self.assertTrue(replay.ejecutar(ordenes.sacar()))
            self.assertEqual((otra.jugador.sala.id, otra.reloj.tiempo_actual, otra.acciones),
                             (p.jugador.sala.id, p.reloj.tiempo_actual, p.acciones))
            self.assertEqual(otra.conocimiento.estado_salas, p.conocimiento.estado_salas)
            self.assertEqual(otra.conocimiento.memoria_puertas, p.conocimiento.memoria_puertas)
            log.anotar_comentario("cerrado sin error")

    def test_FR014_planificador_se_recrea_en_carga_y_sustitucion(self):
        primera = self.escenario().partida
        segunda = self.escenario().partida
        class PersistenciaFalsa:
            def cargar(self):
                return segunda
        c = Controlador(primera, persistencia=PersistenciaFalsa())
        anterior = c._planificador
        self.assertTrue(c.ejecutar(Orden(CARGAR)))
        self.assertIs(c._planificador.mapa, segunda.mapa)
        self.assertIsNot(c._planificador, anterior)
        self.assertTrue(c.ejecutar("ir a 3"))
        self.assertEqual(primera.acciones, 0)
        c.partida = primera
        self.assertIs(c._planificador.mapa, primera.mapa)

    def test_FR019_excepcion_restaura_adaptador_y_cancela_viaje(self):
        esc = self.escenario()
        p = esc.partida
        c = Controlador(p)
        def fallar(orden):
            raise RuntimeError("observador de prueba")
        c.agregar_observador(fallar)
        with self.assertRaises(RuntimeError):
            c.ejecutar("ir a 3")
        self.assertFalse(c._viaje_activo)
        self.assertIs(p.cambiar.__func__, type(p).cambiar)

    def test_C4_observador_cancela_antes_de_observar_recalcular_y_mover(self):
        esc = self.escenario()
        p = esc.partida
        c = Controlador(p)
        observaciones = []
        p._observar_puertas = lambda: observaciones.append(True)
        movimientos = []
        comentarios = []
        c.agregar_observador(movimientos.append)
        c.agregar_observador_comentarios(comentarios.append)
        estado_antes = (list(p.conocimiento.estado_salas), list(p.conocimiento.memoria_puertas), p.conocimiento.resumen())
        def cancelar(actual):
            self.assertIs(actual, p)
            self.assertIsNone(p.registro.grupo_abierto())
            self.assertIs(p.cambiar.__func__, type(p).cambiar)
            return False
        c.agregar_observador_viaje(cancelar)
        self.assertTrue(c.ejecutar("ir a 4"))
        self.assertEqual((p.acciones, p.reloj.tiempo_actual, p.jugador.sala.id), (0, 0, 1))
        self.assertEqual((observaciones, movimientos), ([], []))
        self.assertEqual(p.registro.acciones_deshacibles(), 0)
        self.assertEqual(c._planificador._token_navegacion, 1)  # Solo validación preliminar C4.
        self.assertEqual((p.conocimiento.estado_salas, p.conocimiento.memoria_puertas, p.conocimiento.resumen()), estado_antes)
        self.assertEqual(comentarios, ["ir a 4"])
        self.assertFalse(c._viaje_activo)

    def test_C4_cancelacion_despues_de_varios_pasos_y_retroceso_individual(self):
        esc = self.escenario()
        p = esc.partida
        esc.dar("itm_pergamino")
        c = Controlador(p)
        visitas = []
        movimientos = []
        c.agregar_observador(movimientos.append)
        def continuar(actual):
            visitas.append(actual.jugador.sala.id)
            self.assertIsNone(actual.registro.grupo_abierto())
            return actual.acciones < 2
        c.agregar_observador_viaje(continuar)
        self.assertTrue(c.ejecutar("ir a 4"))
        self.assertEqual(visitas, [1, 2, 3])
        self.assertEqual(movimientos, [Orden(MOVER, "N"), Orden(MOVER, "N")])
        self.assertEqual((p.jugador.sala.id, p.acciones, p.reloj.tiempo_actual), (3, 2, 200))
        self.assertEqual(p.registro.acciones_deshacibles(), 2)
        self.assertTrue(c.ejecutar(Orden(PERGAMINO)))
        self.assertEqual((p.jugador.sala.id, p.acciones, p.reloj.tiempo_actual), (2, 1, 100))
        self.assertEqual(visitas, [1, 2, 3])  # El pergamino no reinicia el viaje.

    def test_C4_cancelacion_conserva_log_de_movimientos_ejecutados(self):
        esc = self.escenario()
        p = esc.partida
        c = Controlador(p)
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "cancelado.log")
            log = BitacoraPartida(ruta, EncabezadoLog("test", "1", "1", 1))
            try:
                c.agregar_observador(log.anotar)
                c.agregar_observador_comentarios(log.anotar_comentario)
                c.agregar_observador_viaje(lambda actual: actual.acciones < 2)
                c.ejecutar("ir a 4")
                self.assertEqual(log.lineas, 2)
            finally:
                log.cerrar()
            _, ordenes = leer_log(ruta)
            registradas = []
            while not ordenes.vacia():
                registradas.append(ordenes.sacar())
            self.assertEqual(registradas, [Orden(MOVER, "N"), Orden(MOVER, "N")])

    def test_C4_cambio_partida_en_callback_no_mueve_ninguna(self):
        p = self.escenario().partida
        otra = self.escenario().partida
        c = Controlador(p)
        posteriores = []
        def sustituir(actual):
            self.assertIs(actual, p)
            c.partida = otra
            return True
        c.agregar_observador_viaje(sustituir)
        c.agregar_observador_viaje(lambda actual: posteriores.append(True) or True)
        self.assertTrue(c.ejecutar("ir a 4"))
        for partida in (p, otra):
            self.assertEqual((partida.acciones, partida.reloj.tiempo_actual, partida.jugador.sala.id), (0, 0, 1))
        self.assertIs(c._planificador.mapa, otra.mapa)
        self.assertEqual(posteriores, [])
        self.assertFalse(c._viaje_activo)

    def test_C4_token_se_verifica_despues_de_cada_callback(self):
        p = self.escenario().partida
        c = Controlador(p)
        posteriores = []
        def cancelar_token(actual):
            c._token_viaje += 1
            return True
        c.agregar_observador_viaje(cancelar_token)
        c.agregar_observador_viaje(lambda actual: posteriores.append(True) or True)
        self.assertTrue(c.ejecutar("ir a 4"))
        self.assertEqual((p.acciones, p.reloj.tiempo_actual, posteriores), (0, 0, []))

    def test_C4_sin_observadores_conserva_viaje(self):
        p = self.escenario().partida
        c = Controlador(p)
        self.assertTrue(c.ejecutar("ir a 4"))
        self.assertEqual((p.jugador.sala.id, p.acciones, p.reloj.tiempo_actual), (4, 3, 300))

    def test_C4_excepcion_callback_se_propaga_sin_movimientos_posteriores(self):
        for pasos in (0, 2):
            with self.subTest(pasos=pasos):
                p = self.escenario().partida
                c = Controlador(p)
                registrados = []
                c.agregar_observador(registrados.append)
                def fallar(actual):
                    if actual.acciones == pasos:
                        raise RuntimeError("fallo de observador de viaje")
                    return True
                c.agregar_observador_viaje(fallar)
                with self.assertRaisesRegex(RuntimeError, "fallo de observador de viaje"):
                    c.ejecutar("ir a 4")
                self.assertEqual((p.acciones, p.reloj.tiempo_actual, len(registrados)), (pasos, pasos * 100, pasos))
                self.assertFalse(c._viaje_activo)
                self.assertIsNone(p.registro.grupo_abierto())
                self.assertIs(p.cambiar.__func__, type(p).cambiar)

    def test_C4_bool_estricto_y_cancelacion_no_llama_otro_observador(self):
        p = self.escenario().partida
        c = Controlador(p)
        c.agregar_observador_viaje(lambda actual: None)
        with self.assertRaisesRegex(TypeError, "devolver bool"):
            c.ejecutar("ir a 4")
        self.assertEqual(p.acciones, 0)
        self.assertFalse(c._viaje_activo)
        c = Controlador(p)
        posteriores = []
        c.agregar_observador_viaje(lambda actual: False)
        c.agregar_observador_viaje(lambda actual: posteriores.append(True) or True)
        self.assertTrue(c.ejecutar("ir a 4"))
        self.assertEqual(posteriores, [])


if __name__ == "__main__":
    unittest.main()
