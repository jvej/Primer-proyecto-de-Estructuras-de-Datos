"""Contrato C7: codec v4 y foto de escritura; no restauración histórica."""

from pathlib import Path
import struct
import tempfile
import unittest

from modelo.datos import guardado_binario as gb
from modelo.datos.persistencia_partida import foto_de
from tests.test_replay_puntajes import Entorno, JUGADAS


class PruebasGuardadoV4(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.ruta = Path(temporal.name) / "partida.bin"

    def foto(self):
        # Mapa explícito de 3 salas; solo un bloque de contenido guardado.
        p = gb.PartidaGuardada(1250, 42, 27, 3, "cripta", "v", "cat", "Jugadora")
        p.n_salas_conocidas = 3
        p.estados_salas = [0, 1, 2]
        p.memoria_puertas = [0] * 12
        p.memoria_puertas[4] = 1
        p.memoria_puertas[9] = 2
        p.inventario = ["poción ñ"]
        p.ordenes = ["mover N", "esperar"]
        p.solicitudes = 7
        sala = gb.SalaGuardada(3, 17)
        sala.enemigos = [["e1", "cazador", 9, 123]]
        sala.objetos = ["antorcha"]
        sala.puertas = [["N", 1]]
        p.salas = [sala]
        return p

    def prefijo(self):
        # Todos los campos generales anteriores a v4, sin conocimiento.
        return struct.pack("<qqiiH", 1, 2, 3, 1, 0) + bytes(8) + struct.pack("<II", 0, 7)

    def bloque(self, estados, entradas):
        return (self.prefijo() + struct.pack("<H", len(estados)) + bytes(estados)
                + struct.pack("<H", len(entradas))
                + b"".join(struct.pack("<HBB", *e) for e in entradas))

    def test_C7_ida_vuelta_todos_los_campos_y_N_independiente(self):
        p = self.foto()
        gb.guardar(self.ruta, p)
        self.assertEqual(struct.unpack_from("<H", self.ruta.read_bytes(), 4)[0], 4)
        g = gb.cargar_general(self.ruta)
        self.assertEqual(g.n_salas_conocidas, 3)
        self.assertEqual(g.salas, [])
        self.assertEqual(g.estados_salas, [0, 1, 2])
        self.assertEqual(g.memoria_puertas, p.memoria_puertas)
        for campo in ("reloj", "semilla", "vida", "sala_actual", "inventario",
                      "id_cripta", "version_cripta", "version_catalogo", "nombre",
                      "ordenes", "solicitudes"):
            self.assertEqual(getattr(g, campo), getattr(p, campo), campo)
        completo = gb.cargar_todo(self.ruta)
        self.assertEqual(len(completo.salas), 1)
        self.assertEqual(completo.salas[0].enemigos, p.salas[0].enemigos)
        self.assertEqual(gb.leer_sala(self.ruta, 3).objetos, ["antorcha"])

    def test_C7_lineas_y_comentarios_intercalados_roundtrip_literal(self):
        p = self.foto()
        # Sintaxis atómica real del proyecto: direcciones N/E/S, no nombres.
        lineas = ["mover N", "# ir a 4", "mover E", "# ir a 4", "mover S"]
        p.ordenes = list(lineas)
        estados = list(p.estados_salas)
        memoria = list(p.memoria_puertas)
        bloque_enemigos = gb._empaquetar_sala(p.salas[0])
        gb.guardar(self.ruta, p)
        datos = self.ruta.read_bytes()
        self.assertEqual(struct.unpack_from("<H", datos, 4)[0], 4)
        for g in (gb.cargar_general(self.ruta), gb.cargar_todo(self.ruta)):
            self.assertEqual(g.ordenes, lineas)
            self.assertEqual(len(g.ordenes), 5)
            self.assertEqual(g.ordenes.count("# ir a 4"), 2)
            self.assertEqual(g.n_salas_conocidas, p.n_salas_conocidas)
            self.assertEqual(g.estados_salas, estados)
            self.assertEqual(g.memoria_puertas, memoria)
            self.assertEqual(gb._empaquetar_general(g), gb._empaquetar_general(p))
        n, pos_general, _ = struct.unpack_from(gb.ENCABEZADO, datos)[2:]
        self.assertEqual(n, 1)
        self.assertEqual(datos[gb.TAM_ENCABEZADO + gb.TAM_ENTRADA:pos_general],
                         bloque_enemigos)
        self.assertEqual(gb._empaquetar_sala(gb.leer_sala(self.ruta, 3)), bloque_enemigos)
        self.assertEqual(p.ordenes, lineas)
        self.assertEqual(p.estados_salas, estados)
        self.assertEqual(p.memoria_puertas, memoria)

    def test_C7_layout_exacto_P_cuenta_posiciones_y_omite_ceros(self):
        p = self.foto()
        p.memoria_puertas = [0] * 12
        # Los dos extremos de una misma puerta son dos entradas, no una.
        p.memoria_puertas[0] = p.memoria_puertas[5] = 1
        bloque = gb._empaquetar_general(p)
        esperado = struct.pack("<H", 3) + bytes([0, 1, 2]) + struct.pack("<H", 2)
        esperado += struct.pack("<HBBHBB", 0, 0, 1, 1, 1, 1)
        self.assertEqual(bloque[-len(esperado):], esperado)
        self.assertEqual(gb._desempaquetar_general(bloque).memoria_puertas,
                         p.memoria_puertas)

    def test_C7_conocimiento_ausente_no_crea_ni_trunca_archivo(self):
        self.ruta.write_bytes(b"archivo anterior")
        with self.assertRaises(gb.ErrorFormato):
            gb.guardar(self.ruta, gb.PartidaGuardada(0, 1, 10, 1))
        self.assertEqual(self.ruta.read_bytes(), b"archivo anterior")

    def test_C7_N_fuera_de_rango_y_longitudes(self):
        for n in (-1, 65536, None, True):
            p = self.foto()
            p.n_salas_conocidas = n
            with self.subTest(n=n), self.assertRaises(gb.ErrorFormato):
                gb._empaquetar_general(p)
        for campo in ("estados_salas", "memoria_puertas"):
            p = self.foto()
            setattr(p, campo, [])
            with self.subTest(campo=campo), self.assertRaises(gb.ErrorFormato):
                gb._empaquetar_general(p)

    def test_C7_P_fuera_de_rango_y_limite_uint16(self):
        p = self.foto()
        p.n_salas_conocidas = 16384
        p.estados_salas = [2] * 16384
        p.memoria_puertas = [1] * 65536
        with self.assertRaisesRegex(gb.ErrorFormato, "P fuera"):
            gb._empaquetar_general(p)
        p.memoria_puertas[-1] = 0
        self.assertEqual(gb._desempaquetar_general(gb._empaquetar_general(p)).memoria_puertas,
                         p.memoria_puertas)
        p.n_salas_conocidas = 65535
        p.estados_salas = [0] * 65535
        p.memoria_puertas = [0] * (4 * 65535)
        self.assertEqual(gb._desempaquetar_general(gb._empaquetar_general(p)).n_salas_conocidas,
                         65535)

    def test_C7_valores_invalidos_al_escribir(self):
        for campo, valor in (("estados_salas", 3), ("memoria_puertas", 3),
                             ("estados_salas", -1), ("memoria_puertas", True)):
            p = self.foto()
            getattr(p, campo)[0] = valor
            with self.subTest(campo=campo, valor=valor), self.assertRaises(gb.ErrorFormato):
                gb._empaquetar_general(p)

    def test_C7_estados_direcciones_indices_y_duplicados_invalidos(self):
        bloques = [self.bloque([3], []), self.bloque([2], [(0, 4, 1)]),
                   self.bloque([2], [(1, 0, 1)]), self.bloque([2], [(0, 0, 0)]),
                   self.bloque([2], [(0, 0, 3)]),
                   self.bloque([2], [(0, 0, 1), (0, 0, 2)])]
        for b in bloques:
            with self.subTest(b=b), self.assertRaises(gb.ErrorFormato):
                gb._desempaquetar_general(b)

    def test_C7_todas_las_truncaciones_del_bloque_general(self):
        bloque = gb._empaquetar_general(self.foto())
        for largo in range(len(bloque)):
            with self.subTest(largo=largo), self.assertRaises(gb.ErrorFormato):
                gb._desempaquetar_general(bloque[:largo])

    def test_C7_truncaciones_archivo_y_datos_sobrantes(self):
        gb.guardar(self.ruta, self.foto())
        original = self.ruta.read_bytes()
        for largo in range(len(original)):
            self.ruta.write_bytes(original[:largo])
            with self.subTest(largo=largo), self.assertRaises(gb.ErrorFormato):
                gb.cargar_todo(self.ruta)
        self.ruta.write_bytes(original + b"extra")
        with self.assertRaises(gb.ErrorFormato):
            gb.cargar_general(self.ruta)
        with self.assertRaises(gb.ErrorFormato):
            gb._desempaquetar_general(gb._empaquetar_general(self.foto()) + b"extra")

    def test_FR024_version_3_rechazada_explicita(self):
        gb.guardar(self.ruta, self.foto())
        datos = bytearray(self.ruta.read_bytes())
        struct.pack_into("<H", datos, 4, 3)
        self.ruta.write_bytes(datos)
        for lector in (gb.cargar_general, gb.cargar_todo, lambda r: gb.leer_sala(r, 3)):
            with self.assertRaisesRegex(gb.ErrorFormato, "3 incompatible.*4.*niebla"):
                lector(self.ruta)

    def test_C7_offsets_invalidos(self):
        gb.guardar(self.ruta, self.foto())
        original = self.ruta.read_bytes()
        for offset, formato, valor in ((10, "<Q", 0), (18, "<I", 0xffffffff),
                                      (gb.TAM_ENCABEZADO + 4, "<Q", 0),
                                      (gb.TAM_ENCABEZADO + 12, "<I", 0xffffffff)):
            datos = bytearray(original)
            struct.pack_into(formato, datos, offset, valor)
            self.ruta.write_bytes(datos)
            with self.subTest(offset=offset), self.assertRaises(gb.ErrorFormato):
                gb.cargar_todo(self.ruta)

    def test_C7_utf8_y_longitudes_texto_invalidas(self):
        p = self.foto()
        p.nombre = "a" * 65536
        with self.assertRaises(gb.ErrorFormato):
            gb._empaquetar_general(p)
        with self.assertRaises(gb.ErrorFormato):
            gb._leer_texto(b"\x01\x00\xff", 0)
        with self.assertRaises(gb.ErrorFormato):
            gb._leer_texto(b"\x02\x00x", 0)

    def test_C7_bloque_enemigos_bytes_anteriores_intactos(self):
        sala = gb.SalaGuardada(3, 17)
        sala.enemigos = [["e1", "cazador", 9, 123]]
        esperado = struct.pack("<iiH", 3, 17, 1)
        esperado += struct.pack("<H", 2) + b"e1" + struct.pack("<H", 7) + b"cazador"
        esperado += struct.pack("<iiHB", 9, 123, 0, 0)
        self.assertEqual(gb._empaquetar_sala(sala), esperado)
        self.assertEqual(gb._desempaquetar_sala(esperado).enemigos, sala.enemigos)
        for largo in range(len(esperado)):
            with self.subTest(largo=largo), self.assertRaises(gb.ErrorFormato):
                gb._desempaquetar_sala(esperado[:largo])
        with self.assertRaises(gb.ErrorFormato):
            gb._desempaquetar_sala(esperado + b"extra")

    def test_FR011_foto_independiente_y_guardado_de_produccion_v4(self):
        entorno = Entorno()
        self.addCleanup(entorno.borrar)
        app, controlador = entorno.jugar(JUGADAS)
        self.addCleanup(app.cerrar)
        partida = controlador.partida
        c = partida.conocimiento
        antes = (list(c.estado_salas), list(c.memoria_puertas), c.resumen(),
                 partida.acciones, partida.reloj.tiempo_actual,
                 partida.registro.acciones_deshacibles(), len(app.ordenes))
        foto = foto_de(partida, app.version_catalogo, app.nombre, app.ordenes)
        self.assertIsNot(foto.estados_salas, c.estado_salas)
        self.assertIsNot(foto.memoria_puertas, c.memoria_puertas)
        foto.estados_salas[0] = 0
        foto.memoria_puertas[0] = 0
        self.assertIn("Partida guardada", controlador.persistencia.guardar(partida))
        g = gb.cargar_general(controlador.persistencia.ruta)
        self.assertEqual(g.n_salas_conocidas, len(partida.mapa.salas))
        self.assertEqual(g.estados_salas, c.estado_salas)
        self.assertEqual(g.memoria_puertas, c.memoria_puertas)
        self.assertEqual(antes, (c.estado_salas, c.memoria_puertas, c.resumen(),
                               partida.acciones, partida.reloj.tiempo_actual,
                               partida.registro.acciones_deshacibles(), len(app.ordenes)))


if __name__ == "__main__":
    unittest.main()
