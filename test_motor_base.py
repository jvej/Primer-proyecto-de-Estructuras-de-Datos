# Pruebas de las piezas básicas del motor (§4.1, §4.6, §4.7). Se ejecutan con: python test_motor_base.py
from actor import Actor, Enemigo
from agenda_eventos import AgendaEventos
from evento import Evento
from registro import Registro, MAX_ACCIONES
from sala import DIRECCIONES, OPUESTAS, Sala


def ejecutar_todo(agenda):
    """Saca eventos de la agenda en orden y devuelve sus descripciones."""
    salida = []
    while len(agenda) > 0:
        evento = agenda.siguiente()
        if evento is not None:
            salida.append(evento.descripcion)
    return salida


def probar_orden_de_agenda_con_empates_y_cancelaciones():
    agenda = AgendaEventos()
    nombres = ["goblin", "esqueleto", "trampa", "rata"]
    tiempos = [100, 50, 50, 50]
    eventos = []
    for nombre, tiempo in zip(nombres, tiempos):
        eventos.append(Evento(tiempo, agenda.nueva_secuencia(), None, lambda ahora: None, nombre))
        agenda.agendar(eventos[-1])
    agenda.cancelar(eventos[2])                       # "trampa" se cancela antes de activarse
    assert ejecutar_todo(agenda) == ["esqueleto", "rata", "goblin"]


def probar_formula_de_cambio_de_velocidad():
    agenda = AgendaEventos()
    for velocidad_nueva, esperado in ((150, 150), (50, 250)):
        e = Evento(175, agenda.nueva_secuencia(), None, lambda ahora: None)
        assert agenda.reprogramar_por_cambio_velocidad(e, 100, 100, velocidad_nueva).tiempo_siguiente == esperado
    e = Evento(101, agenda.nueva_secuencia(), None, lambda ahora: None)
    assert agenda.reprogramar_por_cambio_velocidad(e, 100, 100, 1000).tiempo_siguiente == 101   # mínimo 1


def probar_reprogramar_da_secuencia_nueva_y_actualiza_el_actor():
    agenda = AgendaEventos()
    actor = Actor("A", 10, 1, 1, 100)
    e = Evento(100, agenda.nueva_secuencia(), actor, lambda ahora: None)
    actor.evento_pendiente = e
    agenda.agendar(e)
    nuevo = agenda.reprogramar_por_cambio_velocidad(e, 50, 100, 200)
    assert nuevo.secuencia > e.secuencia and not e.valido
    assert actor.evento_pendiente is nuevo and actor.tiempo_siguiente == 75


def probar_deshacer_agenda_con_registro():
    registro = Registro()
    agenda = AgendaEventos(registro)
    a = Evento(10, agenda.nueva_secuencia(), None, lambda ahora: None, "a")
    b = Evento(20, agenda.nueva_secuencia(), None, lambda ahora: None, "b")
    agenda.agendar(a)
    agenda.agendar(b)
    registro.abrir_grupo()
    assert agenda.siguiente() is a            # se ejecuta a
    agenda.cancelar(b)                         # se cancela b
    c = Evento(5, agenda.nueva_secuencia(), None, lambda ahora: None, "c")
    agenda.agendar(c)                          # se agenda c
    agenda.siguiente()                         # sale c (t=5 < 20; b ya estaba cancelado)
    agenda.siguiente()                         # descarta b y queda vacía
    registro.cerrar_grupo()
    registro.deshacer_ultimo()
    assert ejecutar_todo(agenda) == ["a", "b"]  # a y b vuelven; c desaparece


def probar_registro_limita_a_cinco_acciones():
    registro = Registro()
    caja = Actor("caja", 0, 0, 0, 100)
    for i in range(1, 8):
        registro.abrir_grupo()
        registro.cambiar(caja, "vida", i)
        registro.cerrar_grupo()
    assert registro.acciones_deshacibles() == MAX_ACCIONES == 5
    for _ in range(5):
        registro.deshacer_ultimo()
    assert not registro.puede_deshacer() and caja.vida == 2   # solo se deshicieron las últimas 5


def probar_salida_compartida_y_opuestas():
    assert OPUESTAS == (1, 0, 3, 2)
    for i in range(4):
        a, b = Sala(1), Sala(2)
        salida = a.conectar(DIRECCIONES[i], b, "cerrada", llave="itm_llave", cierre_automatico=500)
        assert a.salidas[i] is salida and b.salidas[OPUESTAS[i]] is salida
        assert a.vecino(i) is b and b.vecino(OPUESTAS[i]) is a
        salida.estado = "abierta"                        # abrir desde un lado abre para ambos
        assert b.salidas[OPUESTAS[i]].esta_abierta()
        assert salida.llave == "itm_llave" and salida.cierre_automatico == 500


def probar_actores_siguen_al_movimiento():
    a, b = Sala(1), Sala(2)
    rata = Enemigo("Rata", 12, 5, 1, 100, "guardian", "e-1", a)
    assert rata in a.actores
    rata.mover_a(b)
    assert rata not in a.actores and rata in b.actores and rata.sala is b


def probar_rastro_caduca_a_las_400():
    sala = Sala(1)
    assert not sala.rastro_fresco(0)
    sala.marcar_visita_jugador(100)
    assert sala.rastro_fresco(499) and not sala.rastro_fresco(500)


if __name__ == "__main__":
    pruebas = [probar_orden_de_agenda_con_empates_y_cancelaciones, probar_formula_de_cambio_de_velocidad,
               probar_reprogramar_da_secuencia_nueva_y_actualiza_el_actor, probar_deshacer_agenda_con_registro,
               probar_registro_limita_a_cinco_acciones, probar_salida_compartida_y_opuestas,
               probar_actores_siguen_al_movimiento, probar_rastro_caduca_a_las_400]
    for prueba in pruebas:
        prueba()
        print("OK ", prueba.__name__)
    print("Todas las pruebas pasaron")