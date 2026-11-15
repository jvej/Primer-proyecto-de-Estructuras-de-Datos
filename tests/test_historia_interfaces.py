"""Aceptación 004 de consola/controles; Pygame solo en casos gráficos locales."""

from pathlib import Path
from importlib import import_module
import tempfile
import unittest
from unittest.mock import Mock, patch

from controlador.controlador import Controlador
from controlador.orden import AYUDA, Orden
from modelo.datos.bitacora_partida import BitacoraPartida, EncabezadoLog
from modelo.juego.resolubilidad import ResultadoResolubilidad
from tests.cripta_de_prueba import entrada, esqueleto_linea
from tests.test_controlador import vista_guionada
from tests.test_linea_tiempo import BaseHistoria, foto_viva
from vista.controles_gui import orden_para_tecla
from vista.vista_consola import VistaConsola, interpretar


class PruebasHistoriaInterfaces(BaseHistoria):
    def test_FR003_selectores_consola(self):
        esc = self.escenario()
        for texto in ("historia 0", "historia #1"):
            orden = interpretar(texto, esc.partida)
            self.assertIsInstance(orden, Orden,
                                  f"FR-003: falta interpretar {texto!r} como HISTORIA: {orden}")
            self.assertEqual(orden.tipo, "historia")
            self.assertFalse(orden.es_de_partida())
            with self.assertRaises(ValueError):
                orden.a_texto()
        for texto in ("historia", "historia -1", "historia 0.5", "historia abc",
                      "historia #0", "historia #2"):
            mensaje = interpretar(texto, esc.partida)
            self.assertIsInstance(mensaje, str)
            self.assertTrue(mensaje)

    def test_FR004_formato_compartido(self):
        esc = self.escenario()
        with self.capacidad("FR-004/FR-007"):
            from controlador.resumen_historia import formatear_resumen
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 2)
        resumen = p.linea_tiempo.consultar_t(0)
        texto = formatear_resumen(resumen)
        self.assertIsInstance(texto, str)
        self.assertTrue(texto.strip())
        salida = []
        vista = VistaConsola(lambda pregunta="": "", salida.append)
        mostrar = self.campo(vista, "mostrar_historia")
        mostrar(texto)
        self.assertIn(texto, "\n".join(salida), "La consola debe presentar el formato compartido")
        antes = foto_viva(p)
        self.assertEqual(formatear_resumen(resumen), texto)
        self.assertEqual(foto_viva(p), antes)

    def test_FR005_historia_fuera_log_grupo_y_cancelacion_ir_a(self):
        esc = self.escenario()
        orden = interpretar("historia #1", esc.partida)
        self.assertIsInstance(orden, Orden, "FR-005: falta la orden HISTORIA de interfaz")
        with self.capacidad("FR-005"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 2)
        vista, _ = vista_guionada([])
        c = Controlador(p, vista)
        temporal = tempfile.TemporaryDirectory(prefix="historia_interfaz_")
        self.addCleanup(temporal.cleanup)
        ruta = Path(temporal.name) / "partida.log"
        encabezado = EncabezadoLog(p.id_cripta, p.version_cripta, "prueba", p.semilla)
        log = BitacoraPartida(str(ruta), encabezado)
        self.addCleanup(log.cerrar)
        c.agregar_observador(log.anotar)
        c.agregar_observador_comentarios(log.anotar_comentario)
        contenido = ruta.read_bytes()
        c._viaje_activo = True
        token = c._token_viaje
        antes = foto_viva(p)
        self.assertTrue(c.ejecutar(orden))
        self.assertTrue(c._viaje_activo)
        self.assertEqual(c._token_viaje, token)
        self.assertEqual(foto_viva(p), antes)
        self.assertEqual(ruta.read_bytes(), contenido, "HISTORIA no escribe ni comentario al log")

    def test_FR019_consulta_durante_y_pantalla_final(self):
        esc = self.escenario(contenido=[entrada(2, trampas=[("t-1", "trp_mortal")])])
        with self.capacidad("FR-019"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 2)
        vista, _ = vista_guionada(["historia #1", "salir", "s"])
        presentar = self.campo(vista, "mostrar_historia")
        terminaciones = []

        def al_terminar(partida):
            terminaciones.append(partida.estado)
            return "Fin anotado"

        c = Controlador(p, vista, al_terminar=al_terminar)
        self.assertTrue(c.ejecutar(interpretar("historia #1", p)))
        self.assertTrue(p.mover("N"))
        self.assertEqual(p.estado, "derrota")
        antes = foto_viva(p)
        with patch.object(vista, "mostrar_historia", wraps=presentar) as visto:
            c.correr_partida()
            self.assertGreater(visto.call_count, 0, "FR-019: la pantalla final debe atender HISTORIA")
        self.assertEqual(terminaciones, ["derrota"])
        self.assertEqual(foto_viva(p), antes)

    def test_FR020_L_Escape_H_F1(self):
        """Control puro: no importa Pygame ni crea ventana."""
        historia = orden_para_tecla("l", False, 0, 0)
        self.assertIsInstance(historia, Orden, "FR-020: L todavía no produce HISTORIA")
        self.assertEqual(historia.tipo, "historia")
        self.assertEqual(orden_para_tecla("h", False, 0, 0), Orden(AYUDA))
        self.assertEqual(orden_para_tecla("f1", False, 0, 0), Orden(AYUDA))

    def test_FR020_panel_largo_Escape_sin_cambiar_partida(self):
        esc = self.escenario()
        from vista.vista_base import Vista
        self.assertTrue(callable(getattr(Vista, "mostrar_historia", None)),
                        "FR-020: falta el adaptador de panel histórico en Vista")
        # El doble existente evita abrir ventana o cargar sprites/sonidos.
        pygame = import_module("pygame")
        from tests.test_gui import _vista_dialogo_prueba
        p = esc.partida
        lotes = [[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)],
                 [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_PAGEDOWN)],
                 [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]]
        vista, textos, cuadros = _vista_dialogo_prueba(lotes)
        vista.partida = p
        vista.fin = "resultado conservado"
        antes = foto_viva(p)
        largo = "\n".join(f"Sala histórica {i}" for i in range(60))
        vista.mostrar_historia(largo)
        self.assertGreaterEqual(len(cuadros), 2, "H no debe cerrar el panel como Escape")
        self.assertTrue(textos)
        self.assertFalse(vista.cerrada)
        self.assertEqual(vista.fin, "resultado conservado")
        self.assertEqual(foto_viva(p), antes)

    def test_FR015_reporte_inicio_y_no_resoluble(self):
        self.escenario()  # Misma preparación real que el resto de interfaz.
        salida = []
        vista = VistaConsola(lambda pregunta="": "", salida.append)
        presentar = getattr(vista, "mostrar_reporte_resolubilidad", None)
        self.assertTrue(callable(presentar),
                        "FR-015: falta presentar el reporte canónico en la interfaz")
        reportes = (ResultadoResolubilidad("RESOLUBLE", orden_llaves=[(0, ["itm_a"])]),
                    ResultadoResolubilidad("NO RESOLUBLE", llaves_no_obtenibles=["itm_b"],
                                            motivo="frontera bloqueada"))
        for reporte in reportes:
            with self.subTest(estado=reporte.estado):
                salida.clear()
                presentar(reporte)
                self.assertEqual("\n".join(salida).strip(), reporte.formatear_reporte())
                self.assertTrue(salida[0].startswith("ESTADO:"))

    def test_FR016_costos_existentes_y_destinos_ocultos(self):
        """FR-016 y FR-004: preservar salida actual y su consulta histórica."""
        esc = self.escenario(esqueleto_linea(6, [(1, 2, {"costo": 173})]))
        salida = []
        vista = VistaConsola(lambda pregunta="": "", salida.append)
        texto_actual = vista._texto_salidas(esc.partida)
        self.assertIn("costo 173", texto_actual)
        self.assertIn("desconocida", texto_actual)
        self.assertNotIn("Sala 2", texto_actual)
        with self.capacidad("FR-016/FR-004"):
            from modelo.juego.resumen_historico import inicializar_historia
            from controlador.resumen_historia import formatear_resumen
        inicializar_historia(esc.partida, 2)
        texto = formatear_resumen(esc.partida.linea_tiempo.consultar_t(0))
        self.assertIn("173", texto)
        self.assertNotIn("Sala 2", texto, "No filtrar el nombre de una sala solo avistada")

    def test_FR017_cazador_distinguible(self):
        esc = self.escenario(contenido=[entrada(1, enemigos=[("c-1", "ent_cazador", 10),
                                                            ("g-1", "ent_esqueleto", 10)])])
        vista = VistaConsola(lambda pregunta="": "", lambda texto: None)
        cazador = next(e for e in esc.partida.enemigos_en_sala() if e.comportamiento == "cazador")
        self.assertIn("[CAZADOR]", vista._texto_enemigo(cazador),
                      "FR-017: falta una marca explícita, independiente del nombre del enemigo")
        pygame = import_module("pygame")
        from tests.test_gui import _vista_dialogo_prueba
        grafica, _, _ = _vista_dialogo_prueba([])
        grafica.enemigo_elegido = -1
        grafica.zonas = []
        grafica._dibujar_actor = Mock(return_value=pygame.Rect(0, 0, 10, 10))
        grafica._dibujar_enemigos([cazador])
        etiquetas = [llamada.args[4] for llamada in grafica._dibujar_actor.call_args_list]
        self.assertTrue(any("[CAZADOR]" in etiqueta for etiqueta in etiquetas))


if __name__ == "__main__":
    unittest.main(verbosity=2)
