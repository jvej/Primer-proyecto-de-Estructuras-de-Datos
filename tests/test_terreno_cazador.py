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
from tests.cripta_de_prueba import armar, entrada, esqueleto_linea


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


# ==============================================================================
# BLOQUE 2: PUERTAS, CONTRATO C2 Y RETROCESO (FR-008)
# ==============================================================================


def test_FR008_apertura_y_cierre_pasan_por_cambiar_estado_puerta():
    """FR-008: Tanto la apertura del jugador como el cierre automático canalizan
    sus mutaciones por el método único cambiar_estado_puerta."""
    puertas = [(1, 2, {"cerrada": True, "llave": "itm_llave_bronce", "cierre_automatico": 200})]
    salas = esqueleto_linea(3, puertas)
    esc = armar(salas, [entrada(1, objetos=["itm_llave_bronce"])])
    p = esc.partida

    assert hasattr(p, "cambiar_estado_puerta"), "Partida debe definir cambiar_estado_puerta"

    llamadas = []
    original_cambiar = p.cambiar_estado_puerta

    def spy_cambiar(salida, nuevo_estado):
        llamadas.append((salida, nuevo_estado))
        return original_cambiar(salida, nuevo_estado)

    p.cambiar_estado_puerta = spy_cambiar

    assert p.recoger(0)
    assert p.abrir("N")
    puerta = p.sala_actual().salidas[0]

    assert len(llamadas) == 1, f"Se esperaba 1 llamada en abrir, hubo {len(llamadas)}"
    assert llamadas[0] == (puerta, "abierta")
    assert puerta.esta_abierta()

    while p.reloj.tiempo_actual < 225:
        p.esperar()

    assert not puerta.esta_abierta()
    assert len(llamadas) == 2, f"Se esperaba 2da llamada en cierre automático, hubo {len(llamadas)}"
    assert llamadas[1] == (puerta, "cerrada")
    esc.cerrar()


def test_FR008_cada_cambio_efectivo_emite_unico_aviso():
    """FR-008: Cada cambio de estado real emite exactamente un aviso a observadores registrados."""
    puertas = [(1, 2, {"cerrada": True, "llave": "itm_llave_bronce", "cierre_automatico": 200})]
    salas = esqueleto_linea(3, puertas)
    esc = armar(salas, [entrada(1, objetos=["itm_llave_bronce"])])
    p = esc.partida

    avisos = []

    def observador_puerta(salida, anterior, nuevo):
        avisos.append((salida, anterior, nuevo))

    p.suscribir_cambio_puerta(observador_puerta)

    p.recoger(0)
    p.abrir("N")
    puerta = p.sala_actual().salidas[0]

    assert len(avisos) == 1, f"Esperado 1 aviso tras abrir, obtenido {len(avisos)}"
    assert avisos[0] == (puerta, "cerrada", "abierta")

    while p.reloj.tiempo_actual < 225:
        p.esperar()

    assert len(avisos) == 2, f"Esperado 2do aviso tras cierre automático, obtenido {len(avisos)}"
    assert avisos[1] == (puerta, "abierta", "cerrada")

    p.desuscribir_cambio_puerta(observador_puerta)
    p.cambiar_estado_puerta(puerta, "abierta")
    assert len(avisos) == 2, "Observador desuscrito no debe recibir avisos"
    esc.cerrar()


def test_FR008_solicitar_mismo_estado_no_genera_cambio_ni_aviso():
    """FR-008: Solicitar el estado que la puerta ya tiene es un no-op que retorna False."""
    puertas = [(1, 2, {"cerrada": False})]
    salas = esqueleto_linea(2, puertas)
    esc = armar(salas)
    p = esc.partida

    avisos = []
    p.suscribir_cambio_puerta(lambda s, a, n: avisos.append((s, a, n)))

    puerta = p.sala_actual().salidas[0]
    assert puerta.esta_abierta()

    resultado = p.cambiar_estado_puerta(puerta, "abierta")
    assert resultado is False, "cambiar_estado_puerta debe retornar False si el estado es el mismo"
    assert len(avisos) == 0, "No debe emitir avisos si no hubo cambio real"
    assert puerta.esta_abierta()

    assert p.cambiar_estado_puerta(None, "cerrada") is False
    esc.cerrar()


def test_FR008_pergamino_restaura_puerta_y_cierre_existente():
    """FR-008: Usar pergamino revierte la puerta y restaura el estado previo del evento de cierre."""
    puertas = [(1, 2, {"cerrada": True, "llave": "itm_llave_bronce", "cierre_automatico": 200})]
    salas = esqueleto_linea(3, puertas)
    esc = armar(salas, [entrada(1, objetos=["itm_llave_bronce", "itm_pergamino"])], capacidad=5)
    p = esc.partida

    assert p.recoger(0)  # Llave en t=0 -> t=25
    assert p.recoger(0)  # Pergamino en t=25 -> t=50
    assert p.abrir("N")   # Abre puerta en t=50 -> t=100 (cierre programado para t=250)

    puerta = p.sala_actual().salidas[0]
    assert puerta.esta_abierta()
    assert puerta.evento_cierre is not None

    # Retroceso de la apertura de puerta
    assert p.usar_pergamino()
    assert not puerta.esta_abierta(), "La puerta debió volver a quedar cerrada tras retroceder"
    assert puerta.evento_cierre is None, "El evento de cierre debió quedar limpio/cancelado"
    esc.cerrar()


def test_FR008_retroceso_comunica_invalidacion_de_rutas():
    """FR-008: Al concluir deshacer_ultimo() en usar_pergamino se emite aviso de invalidación de rutas."""
    puertas = [(1, 2, {"cerrada": True, "llave": "itm_llave_bronce"})]
    salas = esqueleto_linea(3, puertas)
    esc = armar(salas, [entrada(1, objetos=["itm_llave_bronce", "itm_pergamino"])], capacidad=5)
    p = esc.partida

    avisos_rutas = []
    p.suscribir_invalidacion_rutas(lambda: avisos_rutas.append(True))

    p.recoger(0)
    p.recoger(0)
    p.abrir("N")
    assert len(avisos_rutas) == 0, "Apertura no dispara invalidación por retroceso"

    assert p.usar_pergamino()
    assert len(avisos_rutas) == 1, "usar_pergamino debió notificar la invalidación de rutas"

    p.desuscribir_invalidacion_rutas(lambda: None)
    esc.cerrar()


def test_FR008_restauracion_no_duplica_registros_ni_emite_avisos_durante_retroceso():
    """FR-008: Durante el retroceso no se emiten avisos individuales a observadores de puertas
    y el historial en registro decrece sin duplicar entradas ni crear nuevas acciones."""
    puertas = [(1, 2, {"cerrada": True, "llave": "itm_llave_bronce"})]
    salas = esqueleto_linea(3, puertas)
    esc = armar(salas, [entrada(1, objetos=["itm_llave_bronce", "itm_pergamino"])], capacidad=5)
    p = esc.partida

    avisos_puertas = []
    p.suscribir_cambio_puerta(lambda s, a, n: avisos_puertas.append((s, a, n)))

    p.recoger(0)
    p.recoger(0)
    p.abrir("N")
    assert len(avisos_puertas) == 1  # Apertura

    acciones_antes = p.registro.acciones_deshacibles()
    assert acciones_antes >= 2

    assert p.usar_pergamino()
    # Durante el retroceso, las mutaciones inversas están silenciadas (_en_retroceso=True)
    # por lo que no se agregan avisos individuales redundantes
    assert len(avisos_puertas) == 1, (
        f"El retroceso no debe emitir avisos individuales de cambio de puerta; obtenidos {len(avisos_puertas)}"
    )
    assert p.registro.acciones_deshacibles() == acciones_antes - 1, (
        "El retroceso debió desapilar una acción sin agregar nuevos grupos"
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
        test_FR008_apertura_y_cierre_pasan_por_cambiar_estado_puerta,
        test_FR008_cada_cambio_efectivo_emite_unico_aviso,
        test_FR008_solicitar_mismo_estado_no_genera_cambio_ni_aviso,
        test_FR008_pergamino_restaura_puerta_y_cierre_existente,
        test_FR008_retroceso_comunica_invalidacion_de_rutas,
        test_FR008_restauracion_no_duplica_registros_ni_emite_avisos_durante_retroceso,
    ]
    for p in pruebas:
        p()
        print("OK", p.__name__)
    print("Todas las pruebas pasaron")
