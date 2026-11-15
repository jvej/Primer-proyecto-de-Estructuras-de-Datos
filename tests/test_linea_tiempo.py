r"""Aceptación 004: ejecutar con venv\Scripts\python.exe -m tests.test_linea_tiempo.

Se usan partidas reales de cripta_de_prueba. Los imports futuros son locales a
cada caso. Las métricas de SC son contadores observables de trabajo real, no
una implementación del algoritmo ni una medición de los 50 ms del bench.
metricas.acciones_aplicadas corresponde a la última consulta; copias_completas
cuenta checkpoints creados; prefijo_visitado/cambios_visitados_en_recorte
corresponden al último recorte. No se exige un método interno de búsqueda.
"""

from contextlib import contextmanager
import unittest

from controlador.controlador import Controlador
from controlador.orden import AYUDA, INVENTARIO, IR_A, MAPA, MOVER, Orden
from modelo.juego import efectos
from modelo.juego.conocimiento import PUERTA_CERRADA
from tests.cripta_de_prueba import armar, entrada, esqueleto_linea


def foto_viva(p):
    """Oráculo independiente: lee campos reales, sin reconstruir historia."""
    j = p.jugador
    inventario = tuple((id(o), o.id, o.usos) for o in p.inventario.objetos())
    enemigos = tuple((e.id_instancia, e.vida, e.sala.id, e.activo)
                     for e in p.mapa.enemigos)
    agenda = tuple((id(e), e.tiempo_siguiente, e.secuencia, e.valido)
                   for e in p.agenda._heap)
    return (p.reloj.tiempo_actual, p.acciones, p.estado, p.derrotados,
            j.sala.id, j.vida, j.vida_max, j.ataque_efectivo(),
            j.defensa_efectivo(), j.velocidad, inventario, enemigos,
            tuple(p.conocimiento.estado_salas),
            tuple(p.conocimiento.memoria_puertas), p.conocimiento.resumen(),
            tuple(p.efectos_activos()), agenda, p.azar._rng.getstate(),
            tuple(p.bitacora.ultimos()), p.registro.acciones_deshacibles(),
            p.registro.cambios_registrados(), p.esperando)


class BaseHistoria(unittest.TestCase):
    def escenario(self, salas=None, contenido=(), capacidad=12):
        esc = armar(salas if salas is not None else esqueleto_linea(6),
                    contenido, datos={"sala_salida": 6}, capacidad=capacidad)
        self.addCleanup(esc.cerrar)
        self.assertTrue(esc.partida.esperando, "La fixture debe iniciar en una decisión")
        self.assertEqual(esc.partida.reloj.tiempo_actual, 0)
        return esc

    @contextmanager
    def capacidad(self, requisito):
        """Convierte solo APIs ausentes conocidas en un fallo por caso."""
        try:
            yield
        except ImportError as error:
            previstos = ("modelo.juego.linea_tiempo", "modelo.juego.resumen_historico",
                         "controlador.resumen_historia", "controlador.reproductor",
                         "controlador.orden")
            if error.name not in previstos:
                raise
            raise self.failureException(
                f"{requisito}: falta la capacidad prevista en {error.name}: {error}"
            ) from None

    def campo(self, objeto, nombre):
        self.assertTrue(hasattr(objeto, nombre),
                        f"Falta el dato/contador de contrato {nombre!r}")
        return getattr(objeto, nombre)

    def huella(self, r):
        """Datos de la salida filtrada definida en data-model, sin callbacks."""
        return (r.reloj, r.acciones, r.estado, r.sala, r.vida, r.vida_max,
                r.ataque, r.defensa, r.velocidad,
                tuple((o.token, o.id_ficha, o.usos) for o in r.inventario),
                tuple(r.efectos), tuple((e.id_instancia, e.vida) for e in r.enemigos),
                tuple(r.estado_salas), tuple(r.memoria_puertas))

    def coincide_con_vivo(self, r, p):
        self.assertEqual((r.reloj, r.acciones, r.estado, r.sala, r.vida, r.vida_max,
                          r.ataque, r.defensa, r.velocidad),
                         (p.reloj.tiempo_actual, p.acciones, p.estado,
                          p.jugador.sala.id, p.jugador.vida, p.jugador.vida_max,
                          p.jugador.ataque_efectivo(), p.jugador.defensa_efectivo(),
                          p.jugador.velocidad))
        self.assertEqual([o.id_ficha for o in r.inventario],
                         [o.id for o in p.inventario.objetos()])
        self.assertEqual(list(r.efectos), p.efectos_activos())
        self.assertEqual([(e.id_instancia, e.vida) for e in r.enemigos],
                         [(e.id_instancia, e.vida) for e in p.enemigos_en_sala()])
        self.assertEqual(list(r.estado_salas), p.conocimiento.estado_salas)
        self.assertEqual(list(r.memoria_puertas), p.conocimiento.memoria_puertas)


class PruebasLineaTiempo(BaseHistoria):
    def test_FR001_historia_desde_inicio(self):
        esc = self.escenario()
        with self.capacidad("FR-001"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 3)
        for _ in range(8):
            self.assertTrue(p.esperar())
        self.assertEqual(p.registro.acciones_deshacibles(), 5)
        self.assertEqual(p.linea_tiempo.consultar_t(0).vida, 30)
        self.assertEqual(p.linea_tiempo.consultar_accion(1).acciones, 0)

    def test_FR003_primera_actual_y_fuera_rango(self):
        esc = self.escenario()
        with self.capacidad("FR-003"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 2)
        inicial = self.huella(p.linea_tiempo.consultar_accion(1))
        for _ in range(3):
            self.assertTrue(p.esperar())
        self.assertEqual(self.huella(p.linea_tiempo.consultar_accion(1)), inicial)
        self.coincide_con_vivo(p.linea_tiempo.consultar_accion(4), p)
        antes = foto_viva(p)
        for k in (0, -1, 5):
            with self.subTest(k=k), self.assertRaises(ValueError) as error:
                p.linea_tiempo.consultar_accion(k)
            self.assertTrue(str(error.exception), "El rechazo debe explicar su motivo")
        self.assertEqual(foto_viva(p), antes)

    def test_FR006_tiempo_cero_negativo_no_entero_y_futuro(self):
        esc = self.escenario()
        with self.capacidad("FR-006"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 2)
        self.assertEqual(p.linea_tiempo.consultar_t(0).reloj, 0)
        antes = foto_viva(p)
        for t in (-1, 0.5, "abc", 1):
            with self.subTest(t=t), self.assertRaises(ValueError) as error:
                p.linea_tiempo.consultar_t(t)
            self.assertTrue(str(error.exception))
        self.assertEqual(foto_viva(p), antes)

    def test_FR002_eventos_simultaneos_y_predecision(self):
        esc = self.escenario()
        with self.capacidad("FR-002"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 3)
        p.programar(40, lambda ahora: p.danar(p.jugador, 2))
        p.programar(40, lambda ahora: p.cambiar(p.jugador, "defensa", 7))
        # Se agenda después del turno de jugador de t=100: caso real para Mariano.
        p.programar(50, lambda ahora: p.programar(100, lambda t: p.danar(p.jugador, 1)))
        self.assertTrue(p.esperar())
        r = p.linea_tiempo.consultar_t(40)
        self.assertEqual((r.vida, r.defensa, r.reloj), (28, 7, 40))
        self.assertEqual(p.linea_tiempo.consultar_t(100).vida, 27,
                         "FR-002: incluir también eventos simultáneos posteriores al turno")
        antes = self.huella(p.linea_tiempo.consultar_t(100))
        self.assertTrue(p.esperar())
        self.assertEqual(self.huella(p.linea_tiempo.consultar_t(100)), antes,
                         "t de decisión debe excluir la acción iniciada allí")
        self.assertEqual(self.huella(p.linea_tiempo.consultar_accion(2)), antes)

    def test_FR002_tiempo_interior_accion(self):
        esc = self.escenario()
        with self.capacidad("FR-002"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 3)
        p.programar(20, lambda ahora: p.danar(p.jugador, 3))
        p.programar(60, lambda ahora: p.curar(p.jugador, 1))
        self.assertTrue(p.esperar())
        self.assertEqual(p.linea_tiempo.consultar_t(19).vida, 30)
        self.assertEqual(p.linea_tiempo.consultar_t(20).vida, 27)
        self.assertEqual(p.linea_tiempo.consultar_t(59).vida, 27)
        self.assertEqual(p.linea_tiempo.consultar_t(60).vida, 28)
        self.assertEqual(p.linea_tiempo.consultar_t(55).reloj, 55)

    def test_FR004_resumen_completo_e_independiente(self):
        esc = self.escenario(contenido=[entrada(1, enemigos=[("e-1", "ent_troll", 20)])])
        daga = esc.dar("itm_daga")
        esc.dar("itm_pocion")
        esc.dar("itm_pocion")
        with self.capacidad("FR-004"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 3)
        self.assertTrue(p.equipar(daga))
        efectos.aplicar_veneno(p, p.jugador, 1)
        r = p.linea_tiempo.consultar_accion(p.acciones + 1)
        self.coincide_con_vivo(r, p)
        self.assertNotEqual(r.inventario[1].token, r.inventario[2].token)
        congelada = self.huella(r)
        self.assertTrue(p.esperar())
        self.assertEqual(self.huella(r), congelada, "El resumen no debe retener datos vivos")

    def test_FR004_resultado_terminal_historico(self):
        derrota = self.escenario(contenido=[entrada(2, trampas=[("t-1", "trp_mortal")])])
        victoria = self.escenario(esqueleto_linea(6, [(5, 6, {
            "cerrada": True, "llave": "itm_llave_negra"})]))
        victoria.dar("itm_llave_negra")
        with self.capacidad("FR-004"):
            from modelo.juego.resumen_historico import inicializar_historia
        for esc, estado in ((derrota, "derrota"), (victoria, "victoria")):
            with self.subTest(estado=estado):
                p = esc.partida
                inicializar_historia(p, 2)
                pasos = 1 if estado == "derrota" else 4
                for _ in range(pasos):
                    self.assertTrue(p.mover("N"))
                if estado == "victoria":
                    self.assertTrue(p.abrir("N"))
                    self.assertTrue(p.mover("N"))
                self.assertEqual(p.estado, estado)
                self.coincide_con_vivo(p.linea_tiempo.consultar_t(p.reloj.tiempo_actual), p)
                self.assertEqual(p.linea_tiempo.consultar_accion(p.acciones + 1).estado, estado)

    def test_FR005_consulta_sin_mutaciones(self):
        esc = self.escenario()
        esc.dar("itm_pergamino")
        with self.capacidad("FR-005"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 2)
        self.assertTrue(p.esperar())
        antes = foto_viva(p)
        p.linea_tiempo.consultar_t(25)
        p.linea_tiempo.consultar_accion(1)
        self.assertEqual(foto_viva(p), antes)
        self.assertTrue(p.usar_pergamino(), "Consultar debe conservar el retroceso disponible")
        self.assertEqual((p.acciones, p.reloj.tiempo_actual), (0, 0))
        self.coincide_con_vivo(p.linea_tiempo.consultar_t(0), p)
        self.assertEqual(self.huella(p.linea_tiempo.consultar_t(0)),
                         self.huella(p.linea_tiempo.consultar_accion(1)))

    def test_FR009_acciones_revertidas_desaparecen(self):
        esc = self.escenario()
        esc.dar("itm_pergamino")
        with self.capacidad("FR-009"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 2)
        self.assertTrue(p.mover("N"))
        self.assertTrue(p.mover("N"))
        self.assertTrue(p.usar_pergamino())
        r = p.linea_tiempo.consultar_t(p.reloj.tiempo_actual)
        self.assertEqual((r.sala, r.acciones), (2, 1))
        self.assertEqual(list(r.estado_salas), p.conocimiento.estado_salas)
        with self.assertRaises(ValueError):
            p.linea_tiempo.consultar_t(200)

    def test_FR009_antorcha_revertida_no_revela(self):
        esc = self.escenario()
        antorcha, pergamino = esc.dar("itm_antorcha"), esc.dar("itm_pergamino")
        with self.capacidad("FR-009"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 2)
        self.assertTrue(p.usar(antorcha))
        antes = tuple(p.conocimiento.estado_salas)
        self.assertTrue(p.mover("N"))
        self.assertNotEqual(tuple(p.conocimiento.estado_salas), antes)
        self.assertTrue(p.usar_pergamino(pergamino))
        r = p.linea_tiempo.consultar_accion(p.acciones + 1)
        self.assertEqual(tuple(r.estado_salas), antes)
        self.coincide_con_vivo(r, p)

    def test_FR010_no_reversibles_reubicados_y_estado_actual(self):
        esc = self.escenario()
        pergamino = esc.dar("itm_pergamino")
        with self.capacidad("FR-010"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 4)
        puerta = p.mapa.sala(1).salidas[0]
        p.cambiar_estado_puerta(puerta, "cerrada")  # Exterior en t=0.
        self.assertTrue(p.esperar())
        estado_en_cero = tuple(p.linea_tiempo.consultar_t(0).memoria_puertas)
        self.assertTrue(p.esperar())
        p.cambiar_estado_puerta(puerta, "abierta")  # Exterior en t=200.
        p._observar_puertas()  # Mismo método exterior que IR_A, sin grupo.
        self.assertTrue(p.usar_pergamino(pergamino))
        self.assertEqual(p.reloj.tiempo_actual, 100)
        actual = p.linea_tiempo.consultar_t(100)
        self.coincide_con_vivo(actual, p)
        self.assertEqual(self.huella(actual),
                         self.huella(p.linea_tiempo.consultar_accion(p.acciones + 1)))
        self.assertEqual(tuple(p.linea_tiempo.consultar_t(0).memoria_puertas), estado_en_cero)
        self.assertFalse(any(o.id_ficha == "itm_pergamino" for o in actual.inventario))

    def test_FR010_destino_compartido_inverso_y_persistente(self):
        """Colisión observable: puerta de la sala recién visitada y luego revertida."""
        esc = self.escenario()
        pergamino = esc.dar("itm_pergamino")
        with self.capacidad("FR-010"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 3)
        self.assertTrue(p.mover("N"))  # Recuerda 2->3 dentro del grupo.
        puerta = p.mapa.sala(2).salidas[0]
        p.cambiar_estado_puerta(puerta, "cerrada")  # Persiste fuera de acción.
        self.assertEqual(p.conocimiento.memoria_puertas[4], PUERTA_CERRADA)
        self.assertTrue(p.usar_pergamino(pergamino))
        r = p.linea_tiempo.consultar_t(p.reloj.tiempo_actual)
        self.assertEqual(r.memoria_puertas[4], PUERTA_CERRADA,
                         "FR-010: el inverso no debe borrar la observación exterior")
        self.coincide_con_vivo(r, p)

    def test_FR003_renumeracion_y_acciones_aceptadas(self):
        esc = self.escenario()
        esc.dar("itm_pergamino")
        with self.capacidad("FR-003"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 2)
        c = Controlador(p)
        for tipo in (AYUDA, INVENTARIO, MAPA):
            self.assertTrue(c.ejecutar(Orden(tipo)))
        self.assertFalse(c.ejecutar(Orden(MOVER, "O")))
        self.assertEqual(p.acciones, 0)
        for sala in p.mapa.salas[:4]:
            p._explorar_sala(sala)
            for salida in sala.salidas:
                if salida is not None:
                    p._recordar_puerta(salida)
        self.assertTrue(c.ejecutar(Orden(IR_A, 3)))
        self.assertEqual(p.acciones, 2)
        self.assertTrue(p.usar_pergamino())
        self.assertEqual(p.acciones, 1)
        self.assertTrue(p.esperar())
        self.assertEqual(p.acciones, 2)
        self.assertEqual(p.linea_tiempo.consultar_accion(2).sala, 2)
        with self.assertRaises(ValueError):
            p.linea_tiempo.consultar_accion(4)

    def test_FR011_K_entero_positivo_sin_persistir(self):
        esc = self.escenario()
        with self.capacidad("FR-011"):
            from modelo.juego.linea_tiempo import LineaTiempo
        for k in (0, -1, 1.5):
            with self.subTest(k=k), self.assertRaises(ValueError) as error:
                LineaTiempo(k, lambda: esc.partida.reloj.tiempo_actual)
            self.assertTrue(str(error.exception))

    def test_FR012_checkpoint_cero_despues_inicio_y_cada_K(self):
        esc = self.escenario()
        with self.capacidad("FR-012"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 3)
        self.coincide_con_vivo(p.linea_tiempo.consultar_accion(1), p)
        for n in range(1, 9):
            self.assertTrue(p.esperar())
            cps = self.campo(p.linea_tiempo, "checkpoints")
            self.assertEqual([cp.acciones_completadas for cp in cps],
                             list(range(0, n + 1, 3)))
        antes = len(cps)
        p.linea_tiempo.consultar_t(5)
        self.assertEqual(len(p.linea_tiempo.checkpoints), antes)

    def test_FR013_solo_cambios_entre_checkpoints(self):
        esc = self.escenario()
        with self.capacidad("FR-013"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 10)
        cps = self.campo(p.linea_tiempo, "checkpoints")
        inicial = cps[0]
        for _ in range(9):
            self.assertTrue(p.esperar())
        self.assertEqual(len(cps), 1)
        self.assertIs(cps[0], inicial)
        grupos = self.campo(p.linea_tiempo, "grupos")
        self.assertEqual(len(grupos), 9)
        for grupo in grupos:
            self.assertFalse(hasattr(grupo, "proyeccion"),
                             "Entre checkpoints no se guarda una foto por acción")
        self.assertEqual(p.linea_tiempo.consultar_accion(5).acciones, 4)

    def test_SC002_maximo_K_acciones(self):
        esc = self.escenario()
        with self.capacidad("SC-002"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 3)
        for _ in range(17):
            self.assertTrue(p.esperar())
        for k in range(1, 19):
            p.linea_tiempo.consultar_accion(k)
            metricas = self.campo(p.linea_tiempo, "metricas")
            self.assertLessEqual(metricas.acciones_aplicadas, 3)
        for t in (0, 1, 100, 355, 999, 1700):
            p.linea_tiempo.consultar_t(t)
            self.assertLessEqual(p.linea_tiempo.metricas.acciones_aplicadas, 3)

    def test_SC003_sin_copia_completa_por_accion(self):
        esc = self.escenario()
        with self.capacidad("SC-003"):
            from modelo.juego.resumen_historico import inicializar_historia
        p = esc.partida
        inicializar_historia(p, 5)
        for n in range(1, 24):
            self.assertTrue(p.esperar())
            metricas = self.campo(p.linea_tiempo, "metricas")
            self.assertEqual(metricas.copias_completas, 1 + n // 5,
                             "Contar copias retenidas/creadas como checkpoints, no resultados de consulta")
        self.assertEqual(len(p.linea_tiempo.checkpoints), 5)

    def test_SC004_recorte_sin_visitar_prefijo(self):
        corto, largo = self.escenario(), self.escenario()
        corto.dar("itm_pergamino")
        largo.dar("itm_pergamino")
        with self.capacidad("SC-004"):
            from modelo.juego.resumen_historico import inicializar_historia
        visitas = []
        for esc, acciones in ((corto, 23), (largo, 203)):
            p = esc.partida
            inicializar_historia(p, 10)
            for _ in range(acciones):
                self.assertTrue(p.esperar())
            self.assertTrue(p.usar_pergamino())
            m = self.campo(p.linea_tiempo, "metricas")
            self.assertEqual(m.prefijo_visitado, 0)
            visitas.append(m.cambios_visitados_en_recorte)
        self.assertGreater(visitas[0], 0)
        self.assertEqual(visitas[0], visitas[1], "Mismo sufijo no debe visitar un prefijo mayor")


if __name__ == "__main__":
    unittest.main(verbosity=2)
