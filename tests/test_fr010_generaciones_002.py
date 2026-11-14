"""FR-010: barreras permanentes solo para memoria de puertas."""

import unittest
from unittest.mock import patch

from modelo.juego.registro import Registro
from tests.cripta_de_prueba import armar, esqueleto_linea


class PruebasGeneracionesMemoria(unittest.TestCase):
    def registro(self, inicial=0):
        memoria = [inicial] * 4
        r = Registro()
        r._proteger_memoria_puertas(memoria)
        return r, memoria

    def accion(self, r, memoria, valores):
        r.abrir_grupo()
        for valor in valores:
            r.cambiar(memoria, 0, valor)
        r.cerrar_grupo()

    def test_FR010_reversible_y_permanente_posterior(self):
        r, memoria = self.registro()
        self.accion(r, memoria, [1])
        r.cambiar(memoria, 0, 2)
        r.deshacer_ultimo()
        self.assertEqual(memoria[0], 2)

    def test_FR010_reversible_posterior_a_permanente(self):
        r, memoria = self.registro()
        r.cambiar(memoria, 0, 2)
        self.accion(r, memoria, [1])
        r.deshacer_ultimo()
        self.assertEqual(memoria[0], 2)

    def test_FR010_observacion_permanente_mismo_valor(self):
        r, memoria = self.registro()
        self.accion(r, memoria, [1])
        r.cambiar(memoria, 0, 1)
        r.cambiar(memoria, 0, 1)
        r.deshacer_ultimo()
        self.assertEqual(memoria[0], 1)

    def test_FR010_dos_grupos_anteriores_y_dos_pergaminos(self):
        r, memoria = self.registro()
        self.accion(r, memoria, [1])
        self.accion(r, memoria, [2])
        r.cambiar(memoria, 0, 1)
        for _ in range(2):
            r.deshacer_ultimo()
            self.assertEqual(memoria[0], 1)

    def test_FR010_grupo_posterior_se_deshace_y_anterior_no_borra(self):
        r, memoria = self.registro()
        self.accion(r, memoria, [1])
        r.cambiar(memoria, 0, 2)
        self.accion(r, memoria, [1, 2, 1])
        r.deshacer_ultimo()
        self.assertEqual(memoria[0], 2)
        r.deshacer_ultimo()
        self.assertEqual(memoria[0], 2)

    def test_FR010_varios_cambios_y_celdas_independientes(self):
        r, memoria = self.registro()
        r.abrir_grupo()
        for valor in (1, 2, 1):
            r.cambiar(memoria, 0, valor)
        r.cambiar(memoria, 1, 1)
        r.cerrar_grupo()
        r.cambiar(memoria, 0, 2)
        r.deshacer_ultimo()
        self.assertEqual(memoria, [2, 0, 0, 0])

    def test_FR010_sin_permanencia_deshace_todos_los_cambios(self):
        r, memoria = self.registro()
        self.accion(r, memoria, [1, 2, 1])
        r.deshacer_ultimo()
        self.assertEqual(memoria, [0] * 4)

    def test_FR010_otras_listas_y_atributos_conservan_semantica(self):
        r, memoria = self.registro()
        otra = [0]
        class Contador:
            valor = 0
        contador = Contador()
        r.abrir_grupo()
        r.cambiar(otra, 0, 1)
        r.cambiar(contador, 'valor', 1)
        r.cerrar_grupo()
        r.cambiar(otra, 0, 2)
        r.cambiar(contador, 'valor', 2)
        r.deshacer_ultimo()
        self.assertEqual((otra[0], contador.valor), (0, 0))
        self.assertEqual(memoria, [0] * 4)

    def test_FR010_limite_cinco_grupos_e_identidad(self):
        r, memoria = self.registro()
        for _ in range(6):
            self.accion(r, memoria, [1])
        self.assertEqual(r.acciones_deshacibles(), 5)
        for _ in range(5):
            r.deshacer_ultimo()
        self.assertEqual(memoria[0], 1)
        self.assertIs(r._memoria_protegida, memoria)
        r._proteger_memoria_puertas(memoria)
        with self.assertRaises(RuntimeError):
            r._proteger_memoria_puertas([0] * 4)

    def escenario(self):
        esc = armar(esqueleto_linea(4))
        self.addCleanup(esc.cerrar)
        return esc

    def test_FR010_dos_extremos_caso_real_reportado(self):
        esc = self.escenario()
        p = esc.partida
        antes = (list(p.conocimiento.estado_salas), p.conocimiento.resumen())
        pergamino = esc.dar('itm_pergamino')
        memoria = p.conocimiento.memoria_puertas
        self.assertTrue(p.mover('N'))
        puerta = p.mapa.sala(2).salidas[0]
        p.cambiar_estado_puerta(puerta, 'cerrada')
        self.assertTrue(p.usar_pergamino(pergamino))
        self.assertEqual((memoria[4], memoria[9]), (2, 2))
        self.assertEqual(puerta.estado, 'cerrada')
        self.assertIs(p.conocimiento.memoria_puertas, memoria)
        self.assertEqual((p.conocimiento.estado_salas, p.conocimiento.resumen()), antes)
        self.assertEqual((p.jugador.sala.id, p.reloj.tiempo_actual), (1, 0))

    def test_FR010_observar_mismo_valor_no_agrega_tiempo_ni_grupos(self):
        esc = self.escenario()
        p = esc.partida
        pergamino = esc.dar('itm_pergamino')
        p.mover('N')
        antes = (p.acciones, p.reloj.tiempo_actual,
                 p.registro.acciones_deshacibles(), p.registro.cambios_registrados())
        with patch.object(p.registro, 'cambiar', wraps=p.registro.cambiar) as cambios:
            p._observar_puertas()
            self.assertEqual(cambios.call_count, 4)  # Dos puertas, dos extremos.
        self.assertEqual((p.acciones, p.reloj.tiempo_actual,
                          p.registro.acciones_deshacibles(), p.registro.cambios_registrados()), antes)
        p.usar_pergamino(pergamino)
        self.assertEqual((p.conocimiento.memoria_puertas[4],
                          p.conocimiento.memoria_puertas[9]), (1, 1))

    def test_FR010_dos_pergaminos_reales_conservan_observacion(self):
        esc = self.escenario()
        p = esc.partida
        esc.dar('itm_pergamino')
        esc.dar('itm_pergamino')
        p.mover('N')
        p.esperar()
        p.cambiar_estado_puerta(p.mapa.sala(2).salidas[0], 'cerrada')
        for _ in range(2):
            self.assertTrue(p.usar_pergamino())
            self.assertEqual((p.conocimiento.memoria_puertas[4],
                              p.conocimiento.memoria_puertas[9]), (2, 2))


if __name__ == '__main__':
    unittest.main()
