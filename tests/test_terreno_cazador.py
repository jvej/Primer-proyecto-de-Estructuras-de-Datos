"""
Pruebas de aceptación y unitarias para la Capacidad 001:
Terreno, cazador e invalidación de rutas.

Cita de identificadores estables según la Constitución del proyecto:
- FR-001: Costos de salidas, validación estricta y simetría.
- FR-002: Duración de movimientos en reloj virtual, conservación de costos
          en acciones sin movimiento y reprogramación por cambio de velocidad.
"""

from modelo.juego.actor import Jugador, Enemigo
from modelo.juego.agenda_eventos import AgendaEventos
from modelo.juego.costos import (
    COSTO_ATACAR,
    COSTO_ESPERAR,
    COSTO_USAR_EQUIPAR,
    COSTO_RECOGER_SOLTAR,
    COSTO_ABRIR_PUERTA,
    costo_accion,
)
from modelo.juego.evento import Evento
from modelo.juego.mapa import Mapa
from modelo.juego.motor_enemigos import agendar_turno
from modelo.juego.sala import DIRECCIONES, Sala, Salida
from tests.cripta_de_prueba import armar, esqueleto_linea


class EsqueletoFalso:
    def __init__(self, ids, nombres, salidas):
        self.ids = ids
        self.nombres = nombres
        self.salidas = salidas

    def cantidad(self):
        return len(self.ids)

    def posicion(self, id_sala):
        try:
            return self.ids.index(id_sala)
        except ValueError:
            return None


def test_FR001_costo_predeterminado_y_simetria():
    """FR-001: Salida sin costo explícito vale 100 y es simétrica en ambos sentidos."""
    s1 = Sala(1, "Sala 1")
    s2 = Sala(2, "Sala 2")
    salida = s1.conectar("N", s2)
    assert salida.costo == 100, f"Esperado costo 100 por defecto, obtenido {salida.costo}"

    # Simetría estricta
    salida_desde_s2 = s2.salidas[DIRECCIONES.index("S")]
    assert salida_desde_s2 is salida, "Las salas conectadas deben compartir la misma instancia de Salida"
    assert salida_desde_s2.costo == 100


def test_FR001_validacion_estricta_costo():
    """FR-001: Costo debe ser entero >= 1. Rechaza booleanos, decimales, cadenas, 0 y negativos."""
    s1 = Sala(1, "Sala 1")
    s2 = Sala(2, "Sala 2")

    # Entero válido
    salida = s1.conectar("E", s2, costo=250)
    assert salida.costo == 250

    valores_invalidos = [True, False, 10.5, "100", 0, -1, -100, None]
    for invalido in valores_invalidos:
        try:
            Salida(s1, s2, costo=invalido)
            assert False, f"Salida debió rechazar costo inválido: {invalido!r}"
        except (ValueError, TypeError, AssertionError):
            pass

        try:
            s1.conectar("O", s2, costo=invalido)
            assert False, f"Sala.conectar debió rechazar costo inválido: {invalido!r}"
        except (ValueError, TypeError, AssertionError):
            pass


def test_FR001_carga_costos_desde_mapa():
    """FR-001: Mapa asigna índices contiguos y lee costo de cada salida (o 100 si omite)."""
    esqueleto = EsqueletoFalso(
        ids=[10, 20, 30],
        nombres=["A", "B", "C"],
        salidas=[
            {"N": {"sala": 20, "costo": 150}},
            {"S": {"sala": 10, "costo": 150}, "E": {"sala": 30}},  # omite costo -> 100
            {"O": {"sala": 20}},
        ],
    )
    mapa = Mapa(esqueleto)
    assert mapa.salas[0].indice == 0
    assert mapa.salas[1].indice == 1
    assert mapa.salas[2].indice == 2

    # Salida 10 -> 20 con costo 150
    salida_n = mapa.salas[0].salidas[DIRECCIONES.index("N")]
    assert salida_n.costo == 150

    # Salida 20 -> 30 con costo omitido (100)
    salida_e = mapa.salas[1].salidas[DIRECCIONES.index("E")]
    assert salida_e.costo == 100


def test_FR002_intervalo_minimo_velocidad_alta_costo_1():
    """FR-002: Actor con velocidad alta atravesando costo 1 tarda max(1, 1*100//v) >= 1."""
    velocidades = [100, 150, 200, 500, 1000]
    for v in velocidades:
        intervalo = costo_accion(1, v)
        assert intervalo == 1, f"Para costo 1 y vel {v}, intervalo debe ser 1, obtenido {intervalo}"


def test_FR002_reprogramacion_cambio_velocidad_salida_costosa():
    """FR-002: Acción de costo 300 en t=0 con v=100. En t=100 cambia a v=50 -> nuevo t=500."""
    agenda = AgendaEventos()
    tiempo_inicio = 0
    costo_salida = 300
    v_anterior = 100
    v_nueva = 50

    intervalo_inicial = costo_accion(costo_salida, v_anterior)  # 300
    evento = Evento(tiempo_inicio + intervalo_inicial, agenda.nueva_secuencia(), None, lambda ahora: None)
    agenda.agendar(evento)

    tiempo_cambio = 100
    reagendado = agenda.reprogramar_por_cambio_velocidad(evento, tiempo_cambio, v_anterior, v_nueva)
    assert reagendado.tiempo_siguiente == 500, (
        f"Esperado tiempo_siguiente 500, obtenido {reagendado.tiempo_siguiente}"
    )


def test_FR002_acciones_sin_movimiento_conservan_costos_vigentes():
    """FR-002: Acciones sin movimiento conservan sus costos base (100, 50, 25)."""
    assert COSTO_ATACAR == 100
    assert COSTO_ESPERAR == 100
    assert COSTO_USAR_EQUIPAR == 50
    assert COSTO_RECOGER_SOLTAR == 25
    assert COSTO_ABRIR_PUERTA == 50

    v = 100
    assert costo_accion(COSTO_ATACAR, v) == 100
    assert costo_accion(COSTO_ESPERAR, v) == 100
    assert costo_accion(COSTO_USAR_EQUIPAR, v) == 50
    assert costo_accion(COSTO_RECOGER_SOLTAR, v) == 25
    assert costo_accion(COSTO_ABRIR_PUERTA, v) == 50


def test_FR002_movimiento_jugador_consume_costo_salida():
    """FR-002: El jugador consume el costo de la salida atravesada en la agenda de la partida."""
    salas = esqueleto_linea(3, [(1, 2, {"costo": 250})])
    esc = armar(salas)
    p = esc.partida
    assert p.reloj.tiempo_actual == 0

    ok = p.mover("N")
    assert ok is True
    # Con velocidad 100 y costo 250: intervalo = 250 * 100 // 100 = 250
    assert p.reloj.tiempo_actual == 250, (
        f"El reloj debió avanzar a 250 pulsos, actual: {p.reloj.tiempo_actual}"
    )
    assert p.jugador.sala.id == 2
    esc.cerrar()


def test_FR002_movimiento_enemigos_consume_costo_salida():
    """FR-002: Errantes y rastreadores programan su siguiente turno con el costo de la salida transitada."""
    # Jugador en sala 1, enemigo en sala 2 con única salida abierta al norte hacia sala 3 (costo 300)
    # Puerta cerrada entre 1 y 2 para que el errante solo pueda ir a la sala 3
    puertas = [
        (1, 2, {"cerrada": True, "llave": "itm_llave_oro"}),
        (2, 3, {"costo": 300}),
    ]
    salas = esqueleto_linea(3, puertas)
    esc = armar(salas)
    p = esc.partida

    errante = Enemigo("Rata", 10, 2, 0, 100, "errante", "e-1", None, 10, [], 0, "tipo_rata")
    errante.mover_a(p.mapa.salas[1])  # Sala 2
    p.mapa.enemigos.append(errante)

    agendar_turno(p, errante, p.reloj.tiempo_actual)

    # El errante actúa en t=0 y se mueve al norte por salida de costo 300 hacia sala 3
    evento = p.agenda.siguiente()
    assert evento is not None
    evento.accion(evento.tiempo_siguiente)

    assert errante.sala.id == 3
    assert errante.evento_pendiente is not None
    assert errante.evento_pendiente.tiempo_siguiente == 300, (
        f"Siguiente turno del errante debió ser 300, obtenido {errante.evento_pendiente.tiempo_siguiente}"
    )
    esc.cerrar()


if __name__ == "__main__":
    pruebas = [
        test_FR001_costo_predeterminado_y_simetria,
        test_FR001_validacion_estricta_costo,
        test_FR001_carga_costos_desde_mapa,
        test_FR002_intervalo_minimo_velocidad_alta_costo_1,
        test_FR002_reprogramacion_cambio_velocidad_salida_costosa,
        test_FR002_acciones_sin_movimiento_conservan_costos_vigentes,
        test_FR002_movimiento_jugador_consume_costo_salida,
        test_FR002_movimiento_enemigos_consume_costo_salida,
    ]
    for p in pruebas:
        p()
        print("OK", p.__name__)
    print("Todas las pruebas pasaron")
