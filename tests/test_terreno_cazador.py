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
        except ValueError:
            pass
        else:
            raise AssertionError(f"Salida debió rechazar costo inválido: {invalido!r}")

        try:
            s1.conectar("O", s2, costo=invalido)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Sala.conectar debió rechazar costo inválido: {invalido!r}")


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


def test_FR002_movimiento_rastreador_consume_costo_salida():
    """FR-002: El rastreador sigue el rastro a través de una salida con costo variable
    y programa su próximo turno según max(1, costo*100//velocidad)."""
    puertas = [(1, 2, {"costo": 200})]
    salas = esqueleto_linea(3, puertas)
    esc = armar(salas)
    p = esc.partida

    # Rastreador con velocidad 150 en sala 1
    rastreador = Enemigo("Rata", 10, 2, 0, 150, "rastreador", "e-101", None, 10, [], 0, "tipo_rata")
    rastreador.mover_a(p.mapa.sala(1))
    p.mapa.enemigos.append(rastreador)

    # El jugador se mueve de 1 a 2 consumiendo la salida de costo 200 (reloj pasa a t=200)
    assert p.mover("N")
    assert p.reloj.tiempo_actual == 200
    assert p.sala_actual().id == 2

    # Agendamos el turno del rastreador para que actúe en t=200
    agendar_turno(p, rastreador, p.reloj.tiempo_actual)
    assert rastreador.evento_pendiente is not None
    assert rastreador.evento_pendiente.tiempo_siguiente == 200

    # Ejecutamos el turno del rastreador
    evento = p.agenda.siguiente()
    assert evento is not None
    assert evento.actor is rastreador
    evento.ejecutar(evento.tiempo_siguiente)

    # El rastreador sigue el rastro hacia sala 2 por la salida de costo 200
    assert rastreador.sala.id == 2, f"Rastreador debió moverse a sala 2, está en {rastreador.sala.id}"
    # Su siguiente turno: 200 + max(1, 200 * 100 // 150) = 200 + 133 = 333
    assert rastreador.evento_pendiente is not None
    assert rastreador.evento_pendiente.tiempo_siguiente == 333, (
        f"Siguiente turno del rastreador debió ser 333, obtenido {rastreador.evento_pendiente.tiempo_siguiente}"
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


# ==============================================================================
# BLOQUE 3: CAZADOR Y CONTRATO C3 (FR-003, FR-004, FR-005, FR-006, FR-007)
# ==============================================================================


def test_FR003_cazador_ataca_al_compartir_sala():
    """FR-003: El cazador ataca en su turno si comparte sala con el jugador."""
    salas = esqueleto_linea(2)
    esc = armar(salas)
    p = esc.partida

    cazador = Enemigo("Cazador", 10, 4, 1, 100, "cazador", "c-1", None, 10, [], 0, "ent_cazador", rango=300)
    cazador.mover_a(p.sala_actual())  # Sala 1
    p.mapa.enemigos.append(cazador)

    vida_previa = p.jugador.vida
    agendar_turno(p, cazador, p.reloj.tiempo_actual)

    # Cazador actúa en t=0
    evento = p.agenda.siguiente()
    assert evento is not None
    assert evento.actor is cazador
    evento.ejecutar(evento.tiempo_siguiente)

    # Debe haber atacado al jugador
    assert p.jugador.vida < vida_previa, "El cazador debió atacar al jugador"
    assert cazador.sala is p.sala_actual(), "El cazador debe permanecer en la sala"
    # Siguiente turno agendado con COSTO_ATACAR (100) -> t=100
    assert cazador.evento_pendiente is not None
    assert cazador.evento_pendiente.tiempo_siguiente == 100
    esc.cerrar()


def test_FR004_cazador_espera_sin_ruta_o_costo_mayor_a_rango():
    """FR-004: Si falta ruta abierta o el costo mínimo excede el rango, espera con costo base 100."""
    # Caso 1: Puerta cerrada sin ruta abierta
    puertas_cerradas = [(1, 2, {"cerrada": True, "llave": "itm_llave_oro"})]
    salas1 = esqueleto_linea(2, puertas_cerradas)
    esc1 = armar(salas1)
    p1 = esc1.partida

    c1 = Enemigo("Cazador1", 10, 4, 1, 100, "cazador", "c-1", None, 10, [], 0, "ent_cazador", rango=500)
    c1.mover_a(p1.mapa.sala(2))
    p1.mapa.enemigos.append(c1)

    agendar_turno(p1, c1, p1.reloj.tiempo_actual)
    evento1 = p1.agenda.siguiente()
    assert evento1 is not None
    evento1.ejecutar(evento1.tiempo_siguiente)

    assert c1.sala.id == 2, "Sin ruta, cazador debe permanecer en sala 2"
    assert c1.evento_pendiente is not None
    assert c1.evento_pendiente.tiempo_siguiente == 100, "Debe esperar con costo base 100"
    esc1.cerrar()

    # Caso 2: Ruta abierta pero costo (300) supera rango (200)
    puertas_caras = [(1, 2, {"costo": 300})]
    salas2 = esqueleto_linea(2, puertas_caras)
    esc2 = armar(salas2)
    p2 = esc2.partida

    c2 = Enemigo("Cazador2", 10, 4, 1, 100, "cazador", "c-2", None, 10, [], 0, "ent_cazador", rango=200)
    c2.mover_a(p2.mapa.sala(2))
    p2.mapa.enemigos.append(c2)

    agendar_turno(p2, c2, p2.reloj.tiempo_actual)
    evento2 = p2.agenda.siguiente()
    assert evento2 is not None
    evento2.ejecutar(evento2.tiempo_siguiente)

    assert c2.sala.id == 2, "Costo > rango: cazador debe esperar"
    assert c2.evento_pendiente is not None
    assert c2.evento_pendiente.tiempo_siguiente == 100
    esc2.cerrar()


def test_FR004_cazador_avanza_en_limite_exacto_de_rango():
    """FR-004: Si el costo mínimo iguala exactamente el rango (d == rango), avanza."""
    puertas = [(1, 2, {"costo": 200})]
    salas = esqueleto_linea(2, puertas)
    esc = armar(salas)
    p = esc.partida

    # Cazador en sala 2 con rango 200 exacto
    c = Enemigo("Cazador", 10, 4, 1, 100, "cazador", "c-1", None, 10, [], 0, "ent_cazador", rango=200)
    c.mover_a(p.mapa.sala(2))
    p.mapa.enemigos.append(c)

    agendar_turno(p, c, p.reloj.tiempo_actual)
    evento = p.agenda.siguiente()
    assert evento is not None
    evento.ejecutar(evento.tiempo_siguiente)

    # d == rango: debe avanzar a la sala 1
    assert c.sala.id == 1, "En límite exacto d == rango, el cazador debe avanzar"
    assert c.evento_pendiente is not None
    assert c.evento_pendiente.tiempo_siguiente == 200, "Siguiente turno debe reflejar salida.costo=200"
    esc.cerrar()


def test_FR005_cazador_elige_ruta_menor_costo_con_mas_pasos():
    """FR-005: Prefiere ruta de menor costo con más pasos frente a otra con menos pasos y mayor costo."""
    # Grafo cuadrado:
    # Sala 1 (0,0): N a 2 (costo 50), E a 4 (costo 300)
    # Sala 2 (0,1): S a 1 (costo 50), E a 3 (costo 50)
    # Sala 3 (1,1): O a 2 (costo 50), S a 4 (costo 50)
    # Sala 4 (1,0): O a 1 (costo 300), N a 3 (costo 50)
    # Cazador en Sala 1 con rango 400. Jugador en Sala 4.
    # Ruta directa 1 -> 4: costo 300 (1 paso).
    # Ruta alterna 1 -> 2 -> 3 -> 4: costo 50 + 50 + 50 = 150 (3 pasos).
    salas = [
        {"id": 1, "nombre": "Sala 1", "salidas": {"N": {"sala": 2, "costo": 50}, "E": {"sala": 4, "costo": 300}}},
        {"id": 2, "nombre": "Sala 2", "salidas": {"S": {"sala": 1, "costo": 50}, "E": {"sala": 3, "costo": 50}}},
        {"id": 3, "nombre": "Sala 3", "salidas": {"O": {"sala": 2, "costo": 50}, "S": {"sala": 4, "costo": 50}}},
        {"id": 4, "nombre": "Sala 4", "salidas": {"O": {"sala": 1, "costo": 300}, "N": {"sala": 3, "costo": 50}}},
    ]
    esc = armar(salas)
    p = esc.partida

    p.jugador.mover_a(p.mapa.sala(4))
    cazador = Enemigo("Cazador", 10, 4, 1, 100, "cazador", "c-1", None, 10, [], 0, "ent_cazador", rango=400)
    cazador.mover_a(p.mapa.sala(1))
    p.mapa.enemigos.append(cazador)

    agendar_turno(p, cazador, p.reloj.tiempo_actual)
    evento = p.agenda.siguiente()
    assert evento is not None
    evento.ejecutar(evento.tiempo_siguiente)

    # Debe haber elegido sala 2 (ruta barata de 150) en lugar de sala 4 directa (300)
    assert cazador.sala.id == 2, f"Cazador debió elegir sala 2 (ruta barata), está en {cazador.sala.id}"
    assert cazador.evento_pendiente is not None
    assert cazador.evento_pendiente.tiempo_siguiente == 50
    esc.cerrar()


def test_FR006_cazador_desempate_por_menor_id_primera_vecina():
    """FR-006: Cuando varias primeras vecinas permiten el mismo costo mínimo, elige menor ID."""
    # Cazador en sala 1, Jugador en sala 4.
    # Vecinas de sala 1: sala 5 (costo 100) y sala 2 (costo 100).
    # Desde ambas se llega a sala 4 con costo adicional 100 (total 200).
    # Vecina de menor ID: 2 < 5.
    salas = [
        {"id": 1, "nombre": "Sala 1", "salidas": {"N": {"sala": 5, "costo": 100}, "S": {"sala": 2, "costo": 100}}},
        {"id": 2, "nombre": "Sala 2", "salidas": {"N": {"sala": 1, "costo": 100}, "E": {"sala": 4, "costo": 100}}},
        {"id": 4, "nombre": "Sala 4", "salidas": {"O": {"sala": 2, "costo": 100}, "S": {"sala": 5, "costo": 100}}},
        {"id": 5, "nombre": "Sala 5", "salidas": {"S": {"sala": 1, "costo": 100}, "N": {"sala": 4, "costo": 100}}},
    ]
    esc = armar(salas)
    p = esc.partida

    p.jugador.mover_a(p.mapa.sala(4))
    cazador = Enemigo("Cazador", 10, 4, 1, 100, "cazador", "c-1", None, 10, [], 0, "ent_cazador", rango=300)
    cazador.mover_a(p.mapa.sala(1))
    p.mapa.enemigos.append(cazador)

    agendar_turno(p, cazador, p.reloj.tiempo_actual)
    evento = p.agenda.siguiente()
    assert evento is not None
    evento.ejecutar(evento.tiempo_siguiente)

    # Ante empate de costo total (200), debe desempatar por menor ID: sala 2 < sala 5
    assert cazador.sala.id == 2, f"Debió elegir sala 2 (menor id frente a 5), está en {cazador.sala.id}"
    esc.cerrar()


def test_FR007_cazador_omnisciencia_y_no_abre_puertas():
    """FR-007: Conoce el esqueleto completo y puertas reales; no abre puertas cerradas
    y la niebla o falta de descarga de contenido no condicionan su decisión."""
    # 4 salas en anillo:
    # 1 <-> 2: cerrada con llave (costo 50)
    # 2 <-> 3: abierta (costo 50)
    # 1 <-> 4: abierta (costo 100)
    # 4 <-> 3: abierta (costo 100)
    # Cazador en 3, Jugador en 1.
    # Ruta directa 3 -> 2 -> 1 bloqueada por puerta cerrada en (1,2).
    # Ruta abierta 3 -> 4 -> 1 disponible (costo 200).
    salas = [
        {"id": 1, "nombre": "Sala 1", "salidas": {
            "N": {"sala": 2, "cerrada": True, "llave": "itm_llave_oro", "costo": 50},
            "E": {"sala": 4, "costo": 100}
        }},
        {"id": 2, "nombre": "Sala 2", "salidas": {
            "S": {"sala": 1, "cerrada": True, "llave": "itm_llave_oro", "costo": 50},
            "N": {"sala": 3, "costo": 50}
        }},
        {"id": 3, "nombre": "Sala 3", "salidas": {
            "S": {"sala": 2, "costo": 50},
            "O": {"sala": 4, "costo": 100}
        }},
        {"id": 4, "nombre": "Sala 4", "salidas": {
            "O": {"sala": 1, "costo": 100},
            "E": {"sala": 3, "costo": 100}
        }},
    ]
    esc = armar(salas)
    p = esc.partida

    # Simular que sala 4 no ha descargado contenido (incorporada == False)
    p.mapa.sala(4).incorporada = False

    p.jugador.mover_a(p.mapa.sala(1))
    cazador = Enemigo("Cazador", 10, 4, 1, 100, "cazador", "c-1", None, 10, [], 0, "ent_cazador", rango=300)
    cazador.mover_a(p.mapa.sala(3))
    p.mapa.enemigos.append(cazador)

    agendar_turno(p, cazador, p.reloj.tiempo_actual)
    evento = p.agenda.siguiente()
    assert evento is not None
    evento.ejecutar(evento.tiempo_siguiente)

    # El cazador debe avanzar hacia sala 4 (única ruta abierta) y NO hacia sala 2 (puerta cerrada)
    assert cazador.sala.id == 4, f"Cazador no debe abrir puertas cerradas; debió ir a sala 4, está en {cazador.sala.id}"
    puerta_cerrada = p.mapa.sala(1).salidas[DIRECCIONES.index("N")]
    assert not puerta_cerrada.esta_abierta(), "La puerta cerrada debió permanecer cerrada"
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
        test_FR002_movimiento_rastreador_consume_costo_salida,
        test_FR008_apertura_y_cierre_pasan_por_cambiar_estado_puerta,
        test_FR008_cada_cambio_efectivo_emite_unico_aviso,
        test_FR008_solicitar_mismo_estado_no_genera_cambio_ni_aviso,
        test_FR008_pergamino_restaura_puerta_y_cierre_existente,
        test_FR008_retroceso_comunica_invalidacion_de_rutas,
        test_FR008_restauracion_no_duplica_registros_ni_emite_avisos_durante_retroceso,
        test_FR003_cazador_ataca_al_compartir_sala,
        test_FR004_cazador_espera_sin_ruta_o_costo_mayor_a_rango,
        test_FR004_cazador_avanza_en_limite_exacto_de_rango,
        test_FR005_cazador_elige_ruta_menor_costo_con_mas_pasos,
        test_FR006_cazador_desempate_por_menor_id_primera_vecina,
        test_FR007_cazador_omnisciencia_y_no_abre_puertas,
    ]
    for p in pruebas:
        p()
        print("OK", p.__name__)
    print("Todas las pruebas pasaron")
