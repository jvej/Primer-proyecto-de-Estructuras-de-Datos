"""
Pruebas de cierre del instante t en el motor (Integración Historia <t>).

Garantiza que, mientras la partida continúe jugando, antes de devolver
el control al jugador (esperando = True) se procesen todos los eventos válidos
del mismo instante t en que recupera el turno.
"""

from tests.cripta_de_prueba import armar, esqueleto_linea


def test_eventos_empatados_mismo_t_ejecutan_antes_de_devolver_control():
    """Eventos A, turno y B en mismo t con secuencias crecientes se ejecutan antes de devolver control."""
    esc = armar(esqueleto_linea(3))
    p = esc.partida

    orden = []

    def accion_a(ahora):
        orden.append(("A", ahora, p.esperando))

    def accion_b(ahora):
        orden.append(("B", ahora, p.esperando))

    t_obj = 100
    p.esperando = False
    p.reloj.tiempo_actual = 0

    # 1. Evento A (secuencia 1)
    p.programar(t_obj, accion_a, None, "A")
    # 2. Turno del jugador (secuencia 2)
    ev_turno = p.programar(t_obj, p._turno_jugador, p.jugador, "turno")
    p.jugador.evento_pendiente = ev_turno
    # 3. Evento B (secuencia 3)
    p.programar(t_obj, accion_b, None, "B")

    p._avanzar()

    assert p.esperando is True
    assert p.reloj.tiempo_actual == t_obj
    nombres = [item[0] for item in orden]
    assert nombres == ["A", "B"], f"Se esperaba ['A', 'B'], obtenido {nombres}"
    # B debió ejecutarse después de que el turno despertó esperando=True
    assert orden[1][2] is True, "B debió ejecutarse cuando esperando ya era True (cierre del instante)"
    esc.cerrar()


def test_evento_en_t_programa_otro_evento_para_mismo_t():
    """Un evento ejecutado en t que programa otro evento para ese mismo t se ejecuta antes de ceder control."""
    esc = armar(esqueleto_linea(3))
    p = esc.partida

    ejecutados = []

    def segundo_evento(ahora):
        ejecutados.append(("segundo", ahora))

    def primer_evento(ahora):
        ejecutados.append(("primer", ahora))
        p.programar(ahora, segundo_evento, None, "segundo en mismo t")

    p.esperando = False
    p.reloj.tiempo_actual = 0
    t_obj = 100
    p.programar(t_obj, p._turno_jugador, p.jugador, "turno")
    p.programar(t_obj, primer_evento, None, "primero")

    p._avanzar()

    assert p.esperando is True
    assert p.reloj.tiempo_actual == t_obj
    nombres = [item[0] for item in ejecutados]
    assert nombres == ["primer", "segundo"], f"Se esperaba ['primer', 'segundo'], obtenido {nombres}"
    esc.cerrar()


def test_evento_cancelado_en_t_no_se_ejecuta():
    """Eventos cancelados con tiempo t no se ejecutan durante el cierre del instante."""
    esc = armar(esqueleto_linea(3))
    p = esc.partida

    ejecutados = []

    def accion_cancelada(ahora):
        ejecutados.append("cancelado")

    p.esperando = False
    p.reloj.tiempo_actual = 0
    t_obj = 100
    ev = p.programar(t_obj, accion_cancelada, None, "cancelado")
    p.cancelar(ev)
    p.programar(t_obj, p._turno_jugador, p.jugador, "turno")

    p._avanzar()

    assert p.esperando is True
    assert ejecutados == [], f"El evento cancelado no debió ejecutarse: {ejecutados}"
    esc.cerrar()


def test_eventos_posteriores_a_t_permanecen_pendientes():
    """Eventos con tiempo > t no se extraen ni se ejecutan al cerrar el instante t."""
    esc = armar(esqueleto_linea(3))
    p = esc.partida

    ejecutados = []

    def accion_futura(ahora):
        ejecutados.append("futura")

    p.esperando = False
    p.reloj.tiempo_actual = 0
    t_obj = 100
    p.programar(t_obj, p._turno_jugador, p.jugador, "turno")
    ev_futuro = p.programar(t_obj + 50, accion_futura, None, "futuro")

    p._avanzar()

    assert p.esperando is True
    assert p.reloj.tiempo_actual == t_obj
    assert ejecutados == [], "Evento futuro no debió ejecutarse"
    assert ev_futuro.valido is True
    assert len(p.agenda) > 0
    esc.cerrar()


def test_derrota_durante_procesamiento_en_t_corta_control():
    """Si un evento empatado en t mata al jugador, la partida pasa a derrota y no acepta acciones."""
    esc = armar(esqueleto_linea(3))
    p = esc.partida

    def trampa_letal(ahora):
        p.danar(p.jugador, p.jugador.vida)

    p.esperando = False
    p.reloj.tiempo_actual = 0
    t_obj = 100
    p.programar(t_obj, p._turno_jugador, p.jugador, "turno")
    p.programar(t_obj, trampa_letal, None, "trampa letal")

    p._avanzar()

    assert p.jugador.vida == 0
    assert p.estado == "derrota"
    assert not p._puede_actuar()
    esc.cerrar()


def test_retroceso_restaura_cambios_del_ciclo_completo():
    """El retroceso con pergamino restaura correctamente los cambios de eventos empatados en t."""
    esc = armar(esqueleto_linea(3))
    p = esc.partida
    esc.dar("itm_pergamino")

    vida_inicial = p.jugador.vida

    # Programamos un evento en t=100 que daña levemente al jugador
    def golpe(ahora):
        p.danar(p.jugador, 5)

    p.programar(100, golpe, None, "golpe")
    p.esperar()

    assert p.reloj.tiempo_actual == 100
    assert p.jugador.vida == vida_inicial - 5

    # Ahora el jugador retrocede
    ok = p.usar_pergamino()
    assert ok is True
    assert p.reloj.tiempo_actual == 0
    assert p.jugador.vida == vida_inicial
    esc.cerrar()


if __name__ == "__main__":
    pruebas = [
        test_eventos_empatados_mismo_t_ejecutan_antes_de_devolver_control,
        test_evento_en_t_programa_otro_evento_para_mismo_t,
        test_evento_cancelado_en_t_no_se_ejecuta,
        test_eventos_posteriores_a_t_permanecen_pendientes,
        test_derrota_durante_procesamiento_en_t_corta_control,
        test_retroceso_restaura_cambios_del_ciclo_completo,
    ]
    for prueba in pruebas:
        prueba()
        print("OK", prueba.__name__)
    print("Todas las pruebas de cierre del instante t pasaron")
