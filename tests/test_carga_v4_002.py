"""Carga v4 estricta: replay, transacción y conservación de inversos C1/C2."""

from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from controlador.controlador import Controlador
from controlador.orden import ABRIR, CARGAR, ESPERAR, IR_A, MOVER, PERGAMINO, RECOGER, USAR, Orden
from modelo.datos import guardado_binario as gb
from modelo.datos.persistencia_partida import ErrorCarga, PersistenciaPartida
from tests import crear_paquete_prueba as paquete
from tests.cripta_de_prueba import entrada, esqueleto_linea
from tests.test_replay_puntajes import Entorno


class PruebasCargaV4(unittest.TestCase):
    def escenario(self, pasos=(), puerta=False):
        puertas = [(1, 2, {"cerrada": True, "llave": "itm_llave_bronce",
                           "cierre_automatico": 300})] if puerta else []
        # Salida exigida por 003; su llave es obtenible en la sala 7.
        puertas.append((7, 8, {"cerrada": True, "llave": "itm_llave_negra"}))
        contenido = [entrada(1, objetos=["itm_antorcha", "itm_pergamino",
                                         "itm_pergamino", "itm_llave_bronce"])]
        contenido.append(entrada(7, objetos=["itm_llave_negra"]))
        with patch.object(paquete, "salas_y_contenido",
                          return_value=(esqueleto_linea(8, puertas), contenido)):
            entorno = Entorno()
        self.addCleanup(entorno.borrar)
        app = entorno.aplicacion(semilla=7)
        self.addCleanup(app.cerrar)
        p = app.crear_partida(paquete.ID)
        c = Controlador(p, persistencia=PersistenciaPartida(app))
        c.agregar_observador(app.registrar_orden)
        c.agregar_observador_comentarios(app.registrar_comentario)
        for tipo, argumento in pasos:
            self.assertTrue(c.ejecutar(Orden(tipo, argumento)))
        return app, c

    def foto(self, p):
        c = p.conocimiento
        return (list(c.estado_salas), list(c.memoria_puertas), c.resumen(),
                p.acciones, p.reloj.tiempo_actual, p.registro.acciones_deshacibles())

    def guardar(self, c):
        self.assertIn("Partida guardada", c.persistencia.guardar(c.partida))

    def rechazar(self, app, c, motivo):
        p, log, ejecutor, ordenes = app.partida, app.log, app.ejecutor, app.ordenes
        antes = self.foto(p)
        with self.assertRaisesRegex(ErrorCarga, motivo):
            c.persistencia.cargar()
        self.assertIs(app.partida, p)
        self.assertIs(c.partida, p)
        self.assertIs(app.log, log)
        self.assertIs(app.ejecutor, ejecutor)
        self.assertIs(app.ordenes, ordenes)
        self.assertIsNotNone(log._archivo)
        self.assertEqual(self.foto(p), antes)
        self.assertTrue(c.ejecutar(Orden(ESPERAR)))
        self.assertIs(app.log, log)
        self.assertEqual(Path(log.ruta).read_text(encoding="utf-8").splitlines()[-1], "esperar")

    def test_A_B_E_guardar_cargar_movimiento_antorcha_y_pergamino(self):
        normal = [(RECOGER, 1), (RECOGER, 1), (MOVER, "N"), (MOVER, "N"), (MOVER, "S")]
        casos = [normal,
                 [(RECOGER, 0), (USAR, 0), (RECOGER, 0), (RECOGER, 0), (MOVER, "N")],
                 normal + [(PERGAMINO, None)]]
        for pasos in casos:
            with self.subTest(pasos=pasos):
                app, c = self.escenario(pasos)
                esperado = self.foto(c.partida)
                self.guardar(c)
                self.assertTrue(c.ejecutar(Orden(CARGAR)))
                self.assertEqual(self.foto(c.partida), esperado)
                self.assertIs(c.partida, app.partida)

    def test_C_D_F_IR_A_completo_cancelado_y_dos_pergaminos(self):
        pasos = [(RECOGER, 1), (RECOGER, 1)] + [
            (MOVER, d) for d in ("N", "N", "N", "S", "S", "S")]
        for cancelar in (False, True):
            with self.subTest(cancelar=cancelar):
                app, c = self.escenario(pasos)
                original = c.partida
                if cancelar:
                    limite = original.acciones + 2
                    c.agregar_observador_viaje(lambda p: p.acciones < limite)
                self.assertTrue(c.ejecutar(Orden(IR_A, 4)))
                self.assertEqual(original.jugador.sala.id, 3 if cancelar else 4)
                esperado = self.foto(original)
                self.guardar(c)
                self.assertTrue(c.ejecutar(Orden(CARGAR)))
                self.assertEqual(self.foto(c.partida), esperado)
                for _ in range(2):
                    self.assertTrue(original.usar_pergamino())
                    self.assertTrue(c.ejecutar(Orden(PERGAMINO)))
                    self.assertEqual(self.foto(c.partida), self.foto(original))

    def test_G_memoria_abierta_con_puerta_fisica_cerrada(self):
        app, c = self.escenario([(RECOGER, 3), (ABRIR, "N"), (MOVER, "N"),
                                (MOVER, "N"), (ESPERAR, None)], puerta=True)
        p = c.partida
        self.assertEqual(p.mapa.sala(1).salidas[0].estado, "cerrada")
        self.assertEqual(p.conocimiento.memoria_puertas[0], 1)
        esperado = self.foto(p)
        self.guardar(c)
        self.assertTrue(c.ejecutar(Orden(CARGAR)))
        self.assertEqual(self.foto(c.partida), esperado)
        self.assertEqual(c.partida.mapa.sala(1).salidas[0].estado, "cerrada")

    def test_H_O_discrepancia_C2_sin_orden_conserva_sesion(self):
        app, c = self.escenario()
        p = c.partida
        p.cambiar_estado_puerta(p.jugador.sala.salidas[0], "cerrada")
        self.assertEqual(app.ordenes, [])
        self.guardar(c)
        self.rechazar(app, c, "memoria_puertas distinta del replay")

    def test_I_J_K_L_fotos_semanticamente_invalidas(self):
        for caso, motivo in (("N", "N no coincide"), ("salida", "sin salida"),
                             ("extremos", "incoherente"), ("actual", "no explorada"),
                             ("estados", "estado_salas distinto")):
            with self.subTest(caso=caso):
                app, c = self.escenario()
                self.guardar(c)
                ruta = c.persistencia.ruta
                g = gb.cargar_todo(ruta)
                if caso == "N":
                    g.n_salas_conocidas += 1
                    g.estados_salas.append(0)
                    g.memoria_puertas.extend([0] * 4)
                elif caso == "salida":
                    g.memoria_puertas[2] = 1
                elif caso == "extremos":
                    g.memoria_puertas[0] = 2
                elif caso == "actual":
                    g.estados_salas[0] = 1
                else:
                    g.estados_salas[-1] = 1
                gb.guardar(ruta, g)
                self.rechazar(app, c, motivo)

    def test_M_N_O_v3_y_corrupcion_no_alteran_sesion(self):
        for caso in ("v3", "truncado", "sala"):
            with self.subTest(caso=caso):
                app, c = self.escenario()
                self.guardar(c)
                ruta = Path(c.persistencia.ruta)
                datos = bytearray(ruta.read_bytes())
                if caso == "v3":
                    struct.pack_into("<H", datos, 4, 3)
                elif caso == "truncado":
                    datos = datos[:-1]
                else:
                    # Bloque general válido; fallo al leer la sala en validar.
                    struct.pack_into("<Q", datos, gb.TAM_ENCABEZADO + 4, 0)
                ruta.write_bytes(datos)
                self.rechazar(app, c, "3 incompatible" if caso == "v3" else "inválid")

    def test_P_Q_R_validacion_solo_lectura_mantiene_inversos_y_flags(self):
        app, c = self.escenario([(RECOGER, 1), (MOVER, "N")])
        self.guardar(c)
        crear_original = app.crear_partida
        inspecciones = []

        def crear(*args, **kwargs):
            self.assertIs(kwargs["partida_nueva"], False)
            self.assertEqual(kwargs["ordenes_previas"], app.ordenes)
            self.assertEqual(kwargs["exigir_versiones"],
                             (app.partida.version_cripta, app.version_catalogo))
            validar_original = kwargs["validar"]

            def validar(p):
                conocimiento, registro = p.conocimiento, p.registro
                estados, memoria = conocimiento.estado_salas, conocimiento.memoria_puertas
                grupos = registro._grupos
                elementos = grupos.elementos()
                antes = self.foto(p)
                validar_original(p)
                self.assertEqual(self.foto(p), antes)
                self.assertIs(p.conocimiento, conocimiento)
                self.assertIs(p.registro, registro)
                self.assertIs(registro._grupos, grupos)
                self.assertIs(conocimiento.estado_salas, estados)
                self.assertIs(conocimiento.memoria_puertas, memoria)
                for a, b in zip(elementos, grupos.elementos()):
                    self.assertIs(a, b)
                capturados = []
                for grupo in elementos:
                    for inverso in grupo:
                        for celda in inverso.__closure__ or ():
                            objeto = celda.cell_contents
                            if objeto is estados or objeto is memoria:
                                capturados.append(objeto)
                self.assertTrue(capturados)
                inspecciones.append(True)
            kwargs["validar"] = validar
            return crear_original(*args, **kwargs)

        # La rama local aún no incorpora 003: estos guardas detectan llamadas
        # indebidas a sus puntos de verificación, sin implementar resolubilidad.
        with patch.object(app, "verificar", create=True, side_effect=AssertionError("verificar")) as verificar:
            with patch.object(app, "_verificar_cripta", create=True,
                              side_effect=AssertionError("resolubilidad")) as verificar_cripta:
                with patch.object(app, "crear_partida", side_effect=crear):
                    self.assertTrue(c.ejecutar(Orden(CARGAR)))
                verificar.assert_not_called()
                verificar_cripta.assert_not_called()
        self.assertEqual(inspecciones, [True])

    def test_contadores_e_indices_reconstruidos_invalidos_se_rechazan(self):
        for caso in ("contador", "indice", "estado"):
            with self.subTest(caso=caso):
                app, c = self.escenario()
                self.guardar(c)
                crear_original = app.crear_partida

                def crear(*args, **kwargs):
                    validar_original = kwargs["validar"]
                    def validar(p):
                        if caso == "contador":
                            p.conocimiento.num_exploradas += 1
                        elif caso == "indice":
                            p.mapa.salas[-1].indice = 0
                        else:
                            p.conocimiento.estado_salas[-1] = 9
                        validar_original(p)
                    kwargs["validar"] = validar
                    return crear_original(*args, **kwargs)
                with patch.object(app, "crear_partida", side_effect=crear):
                    self.rechazar(app, c, "contadores|índices|estado de sala")


if __name__ == "__main__":
    unittest.main()
