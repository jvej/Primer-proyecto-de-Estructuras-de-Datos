"""Aceptación 004 sobre replay/carga reales y comentarios del formato actual."""

import ast
import inspect
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from controlador.controlador import Controlador
from controlador.orden import ABRIR, ESPERAR, IR_A, MOVER, Orden, RECOGER
from controlador.reproductor import reproducir
from modelo.datos.fabrica_fuentes import crear_fuente_datos
from modelo.datos.persistencia_partida import ErrorCarga, PersistenciaPartida
from modelo.juego.conocimiento import PUERTA_ABIERTA, PUERTA_CERRADA
from tests import crear_paquete_prueba
from tests.test_linea_tiempo import BaseHistoria
from tests.test_replay_puntajes import Entorno, JUGADAS


class PruebasHistoriaPersistencia(BaseHistoria):
    def aplicacion(self):
        entorno = Entorno()
        self.addCleanup(entorno.borrar)
        app = entorno.aplicacion(semilla=7, nombre="Historia")
        self.addCleanup(app.cerrar)
        p = app.crear_partida(crear_paquete_prueba.ID)
        self.assertEqual((p.acciones, p.reloj.tiempo_actual), (0, 0))
        c = Controlador(p, persistencia=PersistenciaPartida(app))
        c.agregar_observador(app.registrar_orden)
        c.agregar_observador_comentarios(app.registrar_comentario)
        return entorno, app, c

    def conocer_ruta(self, p):
        for sala in p.mapa.salas[:4]:
            p._explorar_sala(sala)
            for salida in sala.salidas:
                if salida is not None:
                    p._recordar_puerta(salida)

    def test_FR007_replay_hasta_sin_vista_y_mismo_resumen(self):
        entorno, app, c = self.aplicacion()
        self.assertIn("hasta", inspect.signature(reproducir).parameters,
                      "FR-007: reproducir todavía no acepta --hasta")
        with self.capacidad("FR-007"):
            from modelo.juego.resumen_historico import inicializar_historia
            from controlador.resumen_historia import formatear_resumen
        p = c.partida
        inicializar_historia(p, 2)
        for _ in range(3):
            self.assertTrue(c.ejecutar(Orden(ESPERAR)))
        esperado = formatear_resumen(p.linea_tiempo.consultar_t(150))
        ruta = app.cerrar()
        fuente, presupuesto = crear_fuente_datos(True, entorno.paquete)
        with patch("main.crear_vista", side_effect=AssertionError("FR-007: creó una vista")):
            resultado = reproducir(ruta, fuente, presupuesto, entorno.datos,
                                   hasta=150, checkpoint_cada=2)
        self.assertTrue(resultado.reproducido, resultado.texto())
        self.assertIn(esperado, resultado.texto())
        self.assertNotIn("pygame", sys.modules)

    def test_FR008_hasta_posterior_al_final(self):
        entorno, app, c = self.aplicacion()
        self.assertIn("hasta", inspect.signature(reproducir).parameters,
                      "FR-008: falta seleccionar el resumen terminal mediante hasta")
        with self.capacidad("FR-008"):
            from modelo.juego.resumen_historico import inicializar_historia
            from controlador.resumen_historia import formatear_resumen
        p = c.partida
        inicializar_historia(p, 3)
        llegar = JUGADAS[:8] + [Orden(RECOGER, 0)] + [Orden(MOVER, "N")] * 4 + [
            Orden(RECOGER, 0), Orden(MOVER, "N"), Orden(ABRIR, "N"), Orden(MOVER, "N")]
        for orden in llegar:
            self.assertTrue(c.ejecutar(orden), str(orden))
        self.assertEqual(p.estado, "victoria", "La fixture terminal usa la ruta existente")
        esperado = formatear_resumen(p.linea_tiempo.consultar_accion(p.acciones + 1))
        t = p.reloj.tiempo_actual + 500
        ruta = app.cerrar()
        fuente, presupuesto = crear_fuente_datos(True, entorno.paquete)
        resultado = reproducir(ruta, fuente, presupuesto, entorno.datos,
                               hasta=t, checkpoint_cada=3)
        self.assertTrue(resultado.reproducido, resultado.texto())
        self.assertIn(esperado, resultado.texto())
        self.assertRegex(resultado.texto().lower(), r"termin[oó].*antes|antes.*termin[oó]")

    def test_FR010_comentario_ir_a_observa_sin_accion(self):
        esc = self.escenario()
        with self.capacidad("FR-010"):
            from controlador.reproductor import reproducir_observacion_ir_a
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 2)
        self.assertTrue(p.esperar())
        puerta = p.mapa.sala(1).salidas[0]
        p.cambiar_estado_puerta(puerta, "cerrada")
        p.cambiar(p.conocimiento.memoria_puertas, 0, PUERTA_ABIERTA)
        antes = (p.reloj.tiempo_actual, p.acciones, p.jugador.sala.id,
                 p.registro.acciones_deshacibles())
        with patch.object(p, "_observar_puertas", wraps=p._observar_puertas) as observar:
            reproducir_observacion_ir_a(p, 2)
            observar.assert_called_once_with()
        self.assertEqual(p.conocimiento.memoria_puertas[0], PUERTA_CERRADA)
        self.assertEqual((p.reloj.tiempo_actual, p.acciones, p.jugador.sala.id,
                          p.registro.acciones_deshacibles()), antes)
        self.assertIsNone(p.registro.grupo_abierto())
        self.coincide_con_vivo(p.linea_tiempo.consultar_t(p.reloj.tiempo_actual), p)

    def test_FR014_guardar_cargar_historia_completa(self):
        entorno, app, c = self.aplicacion()
        with self.capacidad("FR-014"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = c.partida
        inicializar_historia(p, 2)
        esperados = [self.huella(p.linea_tiempo.consultar_t(0))]
        for _ in range(4):
            self.assertTrue(c.ejecutar(Orden(ESPERAR)))
            esperados.append(self.huella(p.linea_tiempo.consultar_accion(p.acciones + 1)))
        self.assertIn("Partida guardada", c.persistencia.guardar(p))
        app.cerrar()
        otra = entorno.aplicacion(nombre="Carga")
        self.addCleanup(otra.cerrar)
        cargada = PersistenciaPartida(otra).cargar()
        self.assertIsNotNone(cargada)
        for k, esperado in enumerate(esperados, 1):
            self.assertEqual(self.huella(cargada.linea_tiempo.consultar_accion(k)), esperado)
        for t in (0, 25, 100, 250, 400):
            self.assertEqual(self.huella(cargada.linea_tiempo.consultar_t(t)),
                             self.huella(p.linea_tiempo.consultar_t(t)))

    def test_FR014_ir_a_bloqueo_posterior_sin_paso(self):
        """Prueba real del pedido a Kim: una marca inicial no basta."""
        esc = self.escenario()
        p = esc.partida
        self.conocer_ruta(p)
        c = Controlador(p)
        lineas = []
        c.agregar_observador(lambda orden: lineas.append(orden.a_texto()))
        c.agregar_observador_comentarios(lambda texto: lineas.append("# " + texto))
        intentos = []

        def antes_del_paso(partida):
            intentos.append(partida.jugador.sala.id)
            if len(intentos) == 2:
                puerta = partida.mapa.sala(2).salidas[0]
                partida.cambiar_estado_puerta(puerta, "cerrada")
                # Memoria obsoleta controlada; observar corrige ambos extremos.
                for posicion in (4, 9):
                    partida.cambiar(partida.conocimiento.memoria_puertas,
                                    posicion, PUERTA_ABIERTA)
            return True

        c.agregar_observador_viaje(antes_del_paso)
        self.assertTrue(c.ejecutar(Orden(IR_A, 4)))
        self.assertEqual((p.jugador.sala.id, p.acciones, p.reloj.tiempo_actual), (2, 1, 100))
        self.assertEqual(p.conocimiento.memoria_puertas[4], PUERTA_CERRADA)
        self.assertEqual(lineas, ["# ir a 4", "mover N", "# ir a 4"],
                         "FR-014: falta el comentario de la observación exterior sin segundo paso")
        with self.capacidad("FR-014"):
            from controlador.reproductor import iterar_lineas_reconstruccion
        self.assertEqual(list(iterar_lineas_reconstruccion(lineas)), lineas)

    def test_FR014_cancelacion_sin_observacion_fantasma(self):
        esc = self.escenario()
        p = esc.partida
        self.conocer_ruta(p)
        c = Controlador(p)
        comentarios = []
        c.agregar_observador_comentarios(comentarios.append)
        c.agregar_observador_viaje(lambda partida: False)
        self.assertTrue(c.ejecutar(Orden(IR_A, 4)))
        self.assertEqual((p.acciones, p.reloj.tiempo_actual), (0, 0))
        self.assertEqual(comentarios, [],
                         "FR-014: una cancelación previa a observar no debe dejar una marca de observación")

    def test_FR014_cargar_con_K_distinta(self):
        entorno, app, c = self.aplicacion()
        with self.capacidad("FR-014"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = c.partida
        inicializar_historia(p, 2)
        for _ in range(7):
            self.assertTrue(c.ejecutar(Orden(ESPERAR)))
        self.assertIn("Partida guardada", c.persistencia.guardar(p))
        esperados = [self.huella(p.linea_tiempo.consultar_accion(k)) for k in range(1, 9)]
        app.cerrar()
        otra = entorno.aplicacion(nombre="Otra K", checkpoint_cada=3)
        self.addCleanup(otra.cerrar)
        cargada = PersistenciaPartida(otra).cargar()
        self.assertEqual(cargada.linea_tiempo.checkpoint_cada, 3)
        self.assertEqual(len(cargada.linea_tiempo.checkpoints), 1 + 7 // 3)
        for k, esperado in enumerate(esperados, 1):
            self.assertEqual(self.huella(cargada.linea_tiempo.consultar_accion(k)), esperado)

    def test_FR007_replay_no_muestra_rama_revertida(self):
        esc = self.escenario()
        pergamino = esc.dar("itm_pergamino")
        with self.capacidad("FR-007"):
            from controlador.reproductor import aplicar_linea_reconstruccion
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 2)
        c = Controlador(p)
        clave = p.inventario.clave_de(pergamino)
        lineas = ("mover N", "mover N", f"usar @{clave}", "esperar")
        for linea in lineas:
            self.assertTrue(aplicar_linea_reconstruccion(c, linea), linea)
        # El movimiento original a sala 3 se eliminó, aunque el reloj llegue a 200 otra vez.
        r = p.linea_tiempo.consultar_t(200)
        self.assertEqual(r.sala, 2)
        self.assertEqual(list(r.estado_salas), p.conocimiento.estado_salas)
        self.assertEqual(r.estado_salas[2], 1, "Sala 3 vuelve a avistada, no explorada")

    def test_FR014_modelo_datos_sin_imports_controlador(self):
        raiz = Path(__file__).resolve().parents[1]
        prohibidos = []
        for relativo in ("modelo/datos/bitacora_partida.py", "modelo/datos/persistencia_partida.py"):
            arbol = ast.parse((raiz / relativo).read_text(encoding="utf-8-sig"))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.ImportFrom):
                    modulos = [nodo.module or ""]
                elif isinstance(nodo, ast.Import):
                    modulos = [alias.name for alias in nodo.names]
                else:
                    continue
                for modulo in modulos:
                    if modulo == "controlador" or modulo.startswith("controlador."):
                        prohibidos.append((relativo, nodo.lineno, modulo))
        self.assertEqual(prohibidos, [],
                         "FR-014/MVC: datos debe recibir callbacks, no importar controlador")

    def test_FR014_fallo_carga_conserva_sesion(self):
        entorno, app, c = self.aplicacion()
        with self.capacidad("FR-014"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = c.partida
        inicializar_historia(p, 2)
        self.assertTrue(c.ejecutar(Orden(ESPERAR)))
        self.assertIn("Partida guardada", c.persistencia.guardar(p))
        ruta = Path(c.persistencia.ruta)
        ruta.write_bytes(b"archivo de prueba truncado")
        antes = self.huella(p.linea_tiempo.consultar_accion(2))
        with self.assertRaises(ErrorCarga):
            c.persistencia.cargar()
        self.assertIs(app.partida, p)
        self.assertEqual(self.huella(p.linea_tiempo.consultar_accion(2)), antes)
        self.assertTrue(c.ejecutar(Orden(ESPERAR)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
