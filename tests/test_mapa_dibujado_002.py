"""Aceptación US5: mapa estable, puertas individuales, privacidad y presentación."""

import importlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from controlador.controlador import Controlador
from controlador.orden import MAPA, Orden
from modelo.datos.bitacora_partida import BitacoraPartida, EncabezadoLog
from modelo.juego.mapa_dibujado import (
    SalaMapa, SalidaMapa, calcular_layout, fotografia_conocimiento,
)
from modelo.juego.resumen_historico import inicializar_historia
from tests.cripta_de_prueba import armar, entrada, esqueleto_linea
from tests.test_linea_tiempo import foto_viva
from vista.controles_gui import orden_para_tecla
from vista.vista_consola import VistaConsola, lineas_mapa_dibujado


class PruebasMapaDibujado(unittest.TestCase):
    def escenario(self, n=5, salas=None, contenido=()):
        esc = armar(esqueleto_linea(n) if salas is None else salas, contenido)
        self.addCleanup(esc.cerrar)
        return esc

    def texto(self, mapa, ancho=80):
        return '\n'.join(lineas_mapa_dibujado(mapa, ancho))

    def foto(self, p):
        h = p.linea_tiempo
        return (foto_viva(p), h.proyeccion.resumir(),
                h.cursor, len(h.grupos), len(h.fronteras), len(h.checkpoints))

    def test_FR025_FR029_01_mapa_dibujado_desde_t0(self):
        p = self.escenario().partida
        textos = []
        self.assertTrue(Controlador(p, VistaConsola(salida=textos.append)).ejecutar(Orden(MAPA)))
        texto = '\n'.join(textos)
        for esperado in ('[@1]', '(?)', '|', 'Leyenda', 'Sala actual', 'Exploradas: 1', 'Avistadas: 1'):
            self.assertIn(esperado, texto)
        self.assertTrue(texto.isascii())

    def test_FR026_02_avistada_sin_id_nombre_ni_salidas(self):
        p = self.escenario().partida
        p.mapa.sala(2).nombre = 'SECRETO'
        mapa = p.mapa_dibujado()
        avistadas = [c for c in mapa.casillas if c.estado == 'avistada']
        self.assertEqual(len(avistadas), 1)
        self.assertIsNone(avistadas[0].id)
        self.assertIsNone(avistadas[0].nombre)
        self.assertEqual(len(mapa.conexiones), 1)
        self.assertNotIn('SECRETO', repr(mapa))
        self.assertIn('-> ?', self.texto(mapa))

    def test_FR025_FR030_03_posicion_del_jugador(self):
        p = self.escenario().partida
        p.mover('N')
        mapa = p.mapa_dibujado()
        self.assertEqual([c.id for c in mapa.casillas if c.es_jugador], [2])
        self.assertIn('[@2]', self.texto(mapa))

    def test_FR027_04_memoria_desactualizada(self):
        p = self.escenario().partida
        p.mover('N')
        p.mover('N')
        p.cambiar_estado_puerta(p.mapa.sala(1).salidas[0], 'cerrada')
        mapa = p.mapa_dibujado()
        self.assertEqual(mapa.conexiones[0].estado, 'abierta')

    def test_FR031_05_desconocidas_no_cambian_layout(self):
        p = self.escenario(n=4).partida
        q = self.escenario(n=35).partida
        self.assertEqual(p.mapa_dibujado(), q.mapa_dibujado())
        # La consulta no puede iterar el directorio completo de la cripta.
        class SinRecorrido(list):
            def __iter__(self):
                raise AssertionError('recorrido de salas desconocidas')
        p.conocimiento.salas_por_indice = SinRecorrido(p.mapa.salas)
        self.assertEqual(p.mapa_dibujado(), q.mapa_dibujado())

    def test_FR031_FR035_ids_ocultos_de_avistadas_no_cambian_layout(self):
        def cripta(a, b):
            return [
                {'id': 10, 'nombre': 'Inicio', 'salidas': {
                    'E': {'sala': 20, 'costo': 3}, 'N': {'sala': a, 'costo': 7}}},
                {'id': 20, 'nombre': 'Este', 'salidas': {
                    'O': {'sala': 10, 'costo': 3}, 'N': {'sala': 30, 'costo': 4}}},
                {'id': 30, 'nombre': 'Noreste', 'salidas': {
                    'S': {'sala': 20, 'costo': 4}, 'O': {'sala': b, 'costo': 8}}},
                {'id': a, 'nombre': 'Oculta A', 'salidas': {'S': {'sala': 10, 'costo': 7}}},
                {'id': b, 'nombre': 'Oculta B', 'salidas': {'E': {'sala': 30, 'costo': 8}}}]
        mapas = []
        for a, b in ((2, 90), (95, 1)):
            esc = armar(cripta(a, b), datos={'sala_inicial': 10, 'sala_salida': 30})
            self.addCleanup(esc.cerrar)
            for id_sala in (20, 30):
                esc.partida._explorar_sala(esc.partida.mapa.sala(id_sala))
            mapas.append(esc.partida.mapa_dibujado())
        self.assertEqual(mapas[0], mapas[1])
        self.assertEqual(self.texto(mapas[0]), self.texto(mapas[1]))
        avistadas = [c for c in mapas[0].casillas if c.estado == 'avistada']
        self.assertEqual((avistadas[0].x, avistadas[0].y), (0, -1))
        self.assertEqual((avistadas[1].x, avistadas[1].y), (0, -2))

    def test_FR033_06_pergamino_restaura_dibujo(self):
        esc = self.escenario(n=6)
        p = esc.partida
        pergamino = esc.dar('itm_pergamino')
        p.usar(esc.dar('itm_antorcha'))
        antes = p.mapa_dibujado()
        self.assertTrue(p.mover('N'))
        self.assertNotEqual(antes, p.mapa_dibujado())
        self.assertTrue(p.usar_pergamino(pergamino))
        self.assertEqual(antes, p.mapa_dibujado())

    def test_FR032_07_consulta_sin_efectos(self):
        p = self.escenario().partida
        inicializar_historia(p, 2)
        p.mover('N')
        antes = self.foto(p)
        c = Controlador(p, VistaConsola(salida=lambda texto: None))
        temporal = tempfile.TemporaryDirectory(prefix='mapa_dibujado_')
        self.addCleanup(temporal.cleanup)
        ruta = Path(temporal.name) / 'partida.log'
        log = BitacoraPartida(str(ruta), EncabezadoLog(p.id_cripta, p.version_cripta, 'prueba', p.semilla))
        self.addCleanup(log.cerrar)
        c.agregar_observador(log.anotar)
        c.agregar_observador_comentarios(log.anotar_comentario)
        contenido = ruta.read_bytes()
        observadas = []
        c.agregar_observador(observadas.append)
        with patch.object(p, '_observar_puertas', side_effect=AssertionError('observar')):
            for _ in range(3):
                self.assertTrue(c.ejecutar(Orden(MAPA)))
            pg, grafica = self.grafica()
            lotes = [[pg.event.Event(pg.KEYDOWN, key=pg.K_LEFT)],
                     [pg.event.Event(pg.MOUSEWHEEL, y=1)],
                     [pg.event.Event(pg.KEYDOWN, key=pg.K_c)],
                     [pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE)]]
            grafica._eventos = lambda: lotes.pop(0)
            grafica._mostrar_cuadro = lambda: None
            c.vista = grafica
            self.assertTrue(c.ejecutar(Orden(MAPA)))
        self.assertEqual(self.foto(p), antes)
        self.assertEqual(observadas, [])
        self.assertEqual(ruta.read_bytes(), contenido)

    def test_FR028_08_antorcha_no_revela_contenido(self):
        esc = self.escenario(n=6, contenido=[entrada(3, enemigos=[('remoto', 'ent_troll', 20)])])
        p = esc.partida
        p.usar(esc.dar('itm_antorcha'))
        p.mover('N')
        mapa = p.mapa_dibujado()
        self.assertIn(3, [c.id for c in mapa.casillas])
        self.assertFalse(p.mapa.sala(3).incorporada)
        self.assertNotIn('remoto', repr(mapa))

    def test_FR034_FR035_09_colision_exploradas_y_anillos(self):
        # Dos caminos conocidos reclaman (1,-1); gana id=2 aunque se descubre después.
        salas = (
            SalaMapa(10, 'actual', (SalidaMapa(1, 'N', 1, 'abierta'), SalidaMapa(2, 'E', 1, 'abierta'))),
            SalaMapa(20, 'norte', (SalidaMapa(3, 'E', 1, 'abierta'),)),
            SalaMapa(30, 'este', (SalidaMapa(4, 'N', 1, 'abierta'),)),
            SalaMapa(50, 'mayor', ()), SalaMapa(2, 'menor', ()))
        mapa = calcular_layout(salas, 0)
        menor = next(c for c in mapa.casillas if c.id == 2)
        mayor = next(c for c in mapa.casillas if c.id == 50)
        self.assertEqual((menor.x, menor.y), (1, -1))
        self.assertEqual((mayor.x, mayor.y), (1, -2))
        self.assertTrue(any(c.fuera_cuadricula for c in mapa.conexiones))
        self.assertIn('Conexiones fuera de la cuadricula', self.texto(mapa))

    def test_FR027_FR029_10_costos_y_tres_estados(self):
        salas = (SalaMapa(1, 'Inicio', (
            SalidaMapa(1, 'N', 7, 'abierta'), SalidaMapa(2, 'S', 8, 'cerrada'),
            SalidaMapa(3, 'E', 9, 'cerrada', 'llave_visible'))),
            SalaMapa(None, None, ()), SalaMapa(None, None, ()), SalaMapa(None, None, ()))
        texto = self.texto(calcular_layout(salas, 0))
        for token in ('X', 'K', 'costo 7', 'costo 8', 'costo 9', 'llave_visible'):
            self.assertIn(token, texto)

    def grafica(self):
        pg = importlib.import_module('pygame')
        pg.display.init()
        pg.font.init()
        self.addCleanup(pg.display.quit)
        modulo = importlib.import_module('vista.vista_pygame')
        v = object.__new__(modulo.VistaPygame)
        v.pantalla = pg.Surface((modulo.ANCHO, modulo.ALTO))
        v.fuente = v.fuente_media = v.fuente_chica = pg.font.Font(None, 20)
        v.cerrada = False
        return pg, v

    def test_FR030_FR036_11_controles_graficos_y_marca(self):
        pg, v = self.grafica()
        p = self.escenario().partida
        mapa = p.mapa_dibujado()
        self.assertEqual(orden_para_tecla('m', False, 0, 0), Orden(MAPA))
        key = lambda k: pg.event.Event(pg.KEYDOWN, key=k)
        lotes = [[], [key(pg.K_RIGHT)], [key(pg.K_PLUS)], [key(pg.K_c)],
                 [pg.event.Event(pg.MOUSEWHEEL, y=-1)],
                 [pg.event.Event(pg.MOUSEBUTTONDOWN, button=1, pos=(300, 200))],
                 [pg.event.Event(pg.MOUSEMOTION, pos=(330, 220), rel=(30, 20), buttons=(1, 0, 0))],
                 [pg.event.Event(pg.MOUSEBUTTONUP, button=1, pos=(330, 220))], [key(pg.K_RETURN)]]
        cuadros = []
        v._eventos = lambda: lotes.pop(0)
        v._mostrar_cuadro = lambda: cuadros.append(v.pantalla.copy())
        with patch.object(v, '_crear_niebla_mapa', wraps=v._crear_niebla_mapa) as generar:
            v.mostrar_mapa(mapa)
        # Apertura y dos cambios de zoom; desplazar y recentrar reutilizan la Surface.
        self.assertEqual(generar.call_count, 3)
        self.assertEqual(len(cuadros), 8)
        self.assertNotEqual(pg.image.tobytes(cuadros[0], 'RGB'), pg.image.tobytes(cuadros[1], 'RGB'))
        colores = sys.modules['vista.vista_pygame']
        self.assertEqual(cuadros[0].get_at((568, 340))[:3], colores.SELECCION)
        self.assertEqual(cuadros[0].get_at((701, 319))[:3], colores.COLOR_JUGADOR)
        # La avistada ahora mezcla capas alfa con la niebla, sin color de muro sólido.
        pixel_avistada = cuadros[0].get_at((580, 215))[:3]
        self.assertNotEqual(pixel_avistada, colores.MURO)
        self.assertTrue(all(canal < 50 for canal in pixel_avistada))

    def test_FR035_explorada_tiene_prioridad_sobre_avistada(self):
        salas = (
            SalaMapa(10, 'inicio', (SalidaMapa(1, 'E', 1, 'abierta'), SalidaMapa(3, 'N', 1, 'abierta'))),
            SalaMapa(20, 'este', (SalidaMapa(2, 'N', 1, 'abierta'),)),
            SalaMapa(30, 'noreste', (SalidaMapa(4, 'O', 1, 'abierta'),)),
            SalaMapa(None, None, ()), SalaMapa(5, 'prioritaria', ()))
        mapa = calcular_layout(salas, 0)
        explorada = next(c for c in mapa.casillas if c.id == 5)
        avistada = next(c for c in mapa.casillas if c.id is None)
        self.assertEqual((explorada.x, explorada.y), (0, -1))
        self.assertEqual((avistada.x, avistada.y), (0, -2))

    def test_FR035_indice_ocupacion_equivale_a_lista_ordenada(self):
        from modelo.estructuras.lista_ordenada import ListaOrdenada
        from modelo.juego.mapa_dibujado import IndiceOcupacion
        indice = IndiceOcupacion()
        referencia = ListaOrdenada()
        for i in range(127):
            clave = ((i * 37) % 127 - 63, (i * 11) % 19)
            indice.insertar(clave, True)
            referencia.insertar(clave, True)
        for x in range(-65, 66):
            for y in range(20):
                self.assertEqual(indice.contiene((x, y)), referencia.contiene((x, y)))
        p = self.escenario().partida
        salas, actual = fotografia_conocimiento(p.conocimiento, p.jugador.sala)
        self.assertEqual(calcular_layout(salas, actual), calcular_layout(salas, actual, ListaOrdenada))

    def test_FR029_12_mapa_ancho_por_bloques(self):
        salas = tuple(SalaMapa(i, 'Sala', (SalidaMapa(i+1, 'E', 1, 'abierta'),)
                                if i < 20 else ()) for i in range(21))
        texto = self.texto(calcular_layout(salas, 0), 40)
        self.assertIn('Bloque', texto)
        for i in range(21):
            self.assertIn('[@0]' if i == 0 else f'[{i}]', texto)

    def test_FR033_13_historia_conserva_mapa_anterior(self):
        p = self.escenario().partida
        inicializar_historia(p, 2)
        antes = p.linea_tiempo.consultar_accion(1)
        p.mover('N')
        p.mapa_dibujado()
        self.assertEqual(antes, p.linea_tiempo.consultar_accion(1))
        self.assertEqual(antes, p.linea_tiempo.consultar_t(0))

    def test_FR031_FR034_14_determinismo(self):
        p = self.escenario().partida
        self.assertEqual(p.mapa_dibujado(), p.mapa_dibujado())

    def test_FR034_exploradas_desconectadas_no_inventan_enlaces(self):
        salas = (SalaMapa(10, 'actual', ()), SalaMapa(2, 'aislada', ()))
        mapa = calcular_layout(salas, 0)
        self.assertEqual(mapa.exploradas, 2)
        self.assertEqual(mapa.conexiones, ())
        self.assertNotEqual((mapa.casillas[0].x, mapa.casillas[0].y),
                            (mapa.casillas[1].x, mapa.casillas[1].y))

    def test_FR027_15_puerta_no_observada(self):
        esc = self.escenario(n=6)
        p = esc.partida
        p.usar(esc.dar('itm_antorcha'))
        p.mover('N')
        remotas = [c for c in p.mapa_dibujado().conexiones if c.estado == 'desconocida']
        self.assertTrue(remotas)
        self.assertTrue(all(c.llave is None for c in remotas))
        self.assertIn('no observada', self.texto(p.mapa_dibujado()))

    def test_FR037_16_layout_una_vez_por_apertura(self):
        pg, v = self.grafica()
        p = self.escenario().partida
        lotes = [[], [], [pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE)]]
        v._eventos = lambda: lotes.pop(0)
        v._mostrar_cuadro = lambda: None
        with patch.object(p, 'mapa_dibujado', wraps=p.mapa_dibujado) as construir:
            Controlador(p, v).ejecutar(Orden(MAPA))
        self.assertEqual(construir.call_count, 1)

    def cuatro_salidas(self):
        # Dos puertas físicas diferentes comparten destino, con sus inversas.
        return (
            SalaMapa(70, 'Inicio', (
                SalidaMapa(1, 'N', 7, 'abierta'), SalidaMapa(2, 'S', 8, 'cerrada'),
                SalidaMapa(1, 'E', 9, 'cerrada', 'llave'), SalidaMapa(3, 'O', 5, 'desconocida'))),
            SalaMapa(20, 'Doble destino', (
                SalidaMapa(0, 'S', 7, 'abierta'), SalidaMapa(0, 'O', 9, 'cerrada', 'llave'))),
            SalaMapa(30, 'Sur', (SalidaMapa(0, 'N', 8, 'cerrada'),)),
            SalaMapa(None, None, ()))

    def posiciones(self, mapa):
        return tuple((c.id, c.nombre, c.estado, c.x, c.y) for c in mapa.casillas)

    def test_FR034_origen_inicial_real_distinto_del_menor_id(self):
        esc = armar(esqueleto_linea(5), datos={'sala_inicial': 3, 'sala_salida': 5})
        self.addCleanup(esc.cerrar)
        p = esc.partida
        for sala in p.mapa.salas:
            p._explorar_sala(sala)
        for sala in p.mapa.salas:
            p.cambiar(p.jugador, 'sala', sala)
            inicio = next(c for c in p.mapa_dibujado().casillas if c.id == p.sala_inicial_id)
            self.assertEqual((inicio.x, inicio.y), (0, 0))

    def test_FR031_FR034_todas_las_posiciones_estables_en_cada_explorada(self):
        p = self.escenario().partida
        for sala in p.mapa.salas:
            p._explorar_sala(sala)
        referencia = self.posiciones(p.mapa_dibujado())
        for sala in p.mapa.salas:
            p.cambiar(p.jugador, 'sala', sala)
            mapa = p.mapa_dibujado()
            self.assertEqual(self.posiciones(mapa), referencia)
            self.assertEqual([c.id for c in mapa.casillas if c.es_jugador], [sala.id])

    def test_FR034_FR035_colisiones_no_cambian_al_mover_jugador(self):
        salas = self.cuatro_salidas() + (SalaMapa(1, 'Componente aislado', ()),)
        mapas = [calcular_layout(salas, actual, id_inicial=70) for actual in (0, 1, 2, 4)]
        for mapa in mapas[1:]:
            self.assertEqual(self.posiciones(mapa), self.posiciones(mapas[0]))
            self.assertEqual(mapa.conexiones, mapas[0].conexiones)

    def test_FR027_cada_salida_produce_una_puerta_sin_fusionar_destinos(self):
        salas = self.cuatro_salidas()
        mapa = calcular_layout(salas, 0)
        self.assertEqual(len(mapa.conexiones), sum(len(s.salidas) for s in salas))
        for sala in salas:
            if sala.id is None:
                continue
            puertas = [c for c in mapa.conexiones if mapa.casillas[c.origen].id == sala.id]
            self.assertEqual(tuple(c.direccion for c in puertas), tuple(s.direccion for s in sala.salidas))
        dobles = [c for c in mapa.conexiones if mapa.casillas[c.origen].id == 70
                  and mapa.casillas[c.destino].id == 20]
        self.assertEqual(len(dobles), 2)
        self.assertTrue(all(c.repetida for c in dobles))
        self.assertTrue(any(c.fuera_cuadricula for c in dobles))

    def test_FR027_FR030_rotulo_unico_por_puerta_reciproca(self):
        mapa = calcular_layout(self.cuatro_salidas(), 0)
        self.assertEqual(sum(c.rotular for c in mapa.conexiones), 4)
        _, v = self.grafica()
        puertas = v._preparar_puertas_mapa(mapa, 1.0)
        rotulos = [texto for _, _, _, texto, _ in puertas if texto is not None]
        self.assertEqual(len(rotulos), 4)
        self.assertEqual(len(rotulos), len(tuple(texto for i, texto in enumerate(rotulos)
                                              if texto not in rotulos[:i])))

    def test_FR027_FR030_marcador_en_cada_lado_y_lineas_separadas(self):
        mapa = calcular_layout(self.cuatro_salidas(), 0)
        _, v = self.grafica()
        puertas = v._preparar_puertas_mapa(mapa, 1.0)
        self.assertEqual(len(puertas), len(mapa.conexiones))
        rutas = []
        for conexion, marcador, puntos, _, _ in puertas:
            sala = mapa.casillas[conexion.origen]
            x, y = sala.x * 190, sala.y * 125
            if conexion.direccion == 'N':
                self.assertLess(marcador.centery, y)
                self.assertEqual(marcador.centerx, x)
            elif conexion.direccion == 'S':
                self.assertGreater(marcador.centery, y)
                self.assertEqual(marcador.centerx, x)
            elif conexion.direccion == 'E':
                self.assertGreater(marcador.centerx, x)
                self.assertEqual(marcador.centery, y)
            else:
                self.assertLess(marcador.centerx, x)
                self.assertEqual(marcador.centery, y)
            if sala.id == 70 and mapa.casillas[conexion.destino].id == 20:
                rutas.append(puntos)
                self.assertGreater(len(puntos), 2)
        self.assertEqual(len(rutas), 2)
        self.assertNotEqual(rutas[0], rutas[1])

    def test_FR027_FR030_rotulos_ascii_sin_superposicion_con_destino(self):
        mapa = calcular_layout(self.cuatro_salidas(), 0)
        _, v = self.grafica()
        for zoom in (0.3, 1.0, 2.5):
            ocupados = []
            for conexion, _, _, texto, rect in v._preparar_puertas_mapa(mapa, zoom):
                if texto is None:
                    continue
                self.assertTrue(texto.isascii(), texto)
                self.assertTrue(all(m is not None for m in v.fuente_chica.metrics(texto)), texto)
                self.assertIn(str(conexion.costo), texto)
                self.assertFalse(any(rect.colliderect(otro) for otro in ocupados))
                ocupados.append(rect)
                if conexion.repetida or conexion.fuera_cuadricula:
                    destino = mapa.casillas[conexion.destino]
                    self.assertIn('>' + ('?' if destino.id is None else str(destino.id)), texto)
                if conexion.llave is not None:
                    self.assertIn(conexion.llave, texto)

    def test_FR026_FR030_puerta_a_avistada_termina_en_niebla(self):
        mapa = calcular_layout(self.cuatro_salidas(), 0)
        _, v = self.grafica()
        for conexion, _, puntos, texto, _ in v._preparar_puertas_mapa(mapa, 1.0):
            destino = mapa.casillas[conexion.destino]
            if destino.estado == 'avistada':
                self.assertIsNone(destino.id)
                self.assertIsNone(destino.nombre)
                x, y = puntos[-1]
                dx, dy = abs(x - destino.x * 190), abs(y - destino.y * 125)
                self.assertTrue((dx == 72 and dy <= 33) or (dy == 33 and dx <= 72))
                self.assertNotIn('None', texto)

    def test_FR027_FR029_tabla_incluye_cuatro_salidas_y_fuera(self):
        mapa = calcular_layout(self.cuatro_salidas(), 0)
        texto = self.texto(mapa)
        for fila in ('N -> 20 (costo 7', 'S -> 30 (costo 8',
                     'E -> 20 (costo 9', 'O -> ? (costo 5'):
            self.assertEqual(texto.count(fila), 1)
        self.assertIn('Conexiones fuera de la cuadricula:', texto)

    def test_FR030_resumen_actual_y_apertura_centrada_fuera_del_origen(self):
        pg, v = self.grafica()
        mapa = calcular_layout(self.cuatro_salidas(), 1)
        lotes = [[], [pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE)]]
        v._eventos = lambda: lotes.pop(0)
        v._mostrar_cuadro = lambda: None
        with patch.object(v, '_texto', wraps=v._texto) as escribir:
            v.mostrar_mapa(mapa)
        textos = [str(llamada.args[1]) for llamada in escribir.call_args_list]
        self.assertTrue(any('S -> 70' in t and '7' in t for t in textos))
        self.assertTrue(any('O -> 70' in t and '9' in t for t in textos))
        colores = sys.modules['vista.vista_pygame']
        # El centro del lado O tiene puerta; comprobar el borde más abajo.
        self.assertEqual(v.pantalla.get_at((568, 355))[:3], colores.SELECCION)

    def test_FR032_consultas_con_puertas_repetidas_sin_efectos(self):
        p = self.escenario().partida
        inicializar_historia(p, 2)
        for sala in p.mapa.salas:
            p._explorar_sala(sala)
        antes = self.foto(p)
        azar = p.azar._rng.getstate()
        with patch.object(p, '_observar_puertas', side_effect=AssertionError('observar')):
            for _ in range(3):
                mapa = p.mapa_dibujado()
                self.texto(mapa)
                _, v = self.grafica()
                v._preparar_puertas_mapa(mapa, 1.0)
        self.assertEqual(self.foto(p), antes)
        self.assertEqual(p.azar._rng.getstate(), azar)

    def test_FR030_cuatro_marcadores_de_colores_visibles(self):
        pg, v = self.grafica()
        mapa = calcular_layout(self.cuatro_salidas(), 0)
        lotes = [[], [pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE)]]
        v._eventos = lambda: lotes.pop(0)
        v._mostrar_cuadro = lambda: None
        v.mostrar_mapa(mapa)
        colores = sys.modules['vista.vista_pygame']
        for punto, color in (((640, 307), colores.ABIERTA), ((640, 373), colores.CERRADA),
                             ((712, 340), colores.DORADO), ((568, 340), colores.TEXTO_TENUE)):
            self.assertEqual(v.pantalla.get_at(punto)[:3], color)

    def test_FR038_17_consola_no_carga_grafica(self):
        codigo = ('import sys; from tests.cripta_de_prueba import armar, esqueleto_linea; '
                  'e=armar(esqueleto_linea(3)); e.partida.mapa_dibujado(); '
                  'assert "pygame" not in sys.modules; e.cerrar()')
        resultado = subprocess.run([sys.executable, '-c', codigo], capture_output=True, text=True)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)


if __name__ == '__main__':
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    unittest.main()
