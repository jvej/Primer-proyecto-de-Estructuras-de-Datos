# Pruebas de la base del motor (§4.1, §4.7). Se ejecutan con: python test_motor_base.py
import random

from actor import Actor, Enemigo
from activacion import activar_enemigos
from agenda_eventos import AgendaEventos
from bucle_principal import Reloj, correr
from comportamiento import resolver_turno_enemigo
from evento import Evento
from motor_enemigos import agendar_turno, matar_enemigo
from sala import DIRECCIONES, Sala


def nueva_rata(id_instancia="e-1", velocidad=100, sala=None, comportamiento="guardian"):
    return Enemigo("Rata", 12, 5, 1, velocidad, comportamiento, id_instancia, sala)


def escenario():
    """Jugador en una sala, enemigo guardián en otra (sin conexión): el enemigo solo espera."""
    jugador = Actor("Jugador", 30, 6, 2, 100, Sala(1))
    return AgendaEventos(), Reloj(), jugador, random.Random(1), []


def probar_primer_turno_se_puede_cancelar():
    agenda, reloj, jugador, azar, bitacora = escenario()
    rata = nueva_rata(sala=Sala(2))
    activar_enemigos(agenda, [rata], 0, jugador, azar, bitacora)
    assert rata.evento_pendiente is not None and rata.tiempo_siguiente == 100
    matar_enemigo(agenda, rata)               # muere antes de su primer turno
    correr(agenda, reloj, lambda: True)
    assert bitacora == []                     # su turno nunca se ejecutó


def probar_reprogramar_actualiza_el_puntero():
    agenda, reloj, jugador, azar, bitacora = escenario()
    rata = nueva_rata(sala=Sala(2))
    viejo = agendar_turno(agenda, rata, 100, jugador, azar, bitacora)
    nuevo = agenda.reprogramar_por_cambio_velocidad(viejo, 50, 100, 200)
    assert rata.evento_pendiente is nuevo and not viejo.valido
    matar_enemigo(agenda, rata)               # debe cancelar el evento NUEVO
    correr(agenda, reloj, lambda: True)
    assert bitacora == []


def probar_siguiente_turno_sale_del_reloj_actual():
    agenda, reloj, jugador, azar, bitacora = escenario()
    rata = nueva_rata(sala=Sala(2))
    viejo = agendar_turno(agenda, rata, 100, jugador, azar, bitacora)
    rata.velocidad = 200
    agenda.reprogramar_por_cambio_velocidad(viejo, 50, 100, 200)   # restante 50 -> 25: t=75
    correr(agenda, reloj, lambda: len(bitacora) < 1)               # ejecuta solo el turno de t=75
    assert reloj.tiempo_actual == 75
    assert rata.tiempo_siguiente == 125       # 75 + 100*100//200 (con el bug daba 150)


def probar_formula_de_cambio_de_velocidad():
    agenda = AgendaEventos()
    e = Evento(175, agenda.nueva_secuencia(), None, lambda ahora: None)
    assert agenda.reprogramar_por_cambio_velocidad(e, 100, 100, 150).tiempo_siguiente == 150
    e = Evento(175, agenda.nueva_secuencia(), None, lambda ahora: None)
    assert agenda.reprogramar_por_cambio_velocidad(e, 100, 100, 50).tiempo_siguiente == 250
    e = Evento(101, agenda.nueva_secuencia(), None, lambda ahora: None)
    assert agenda.reprogramar_por_cambio_velocidad(e, 100, 100, 1000).tiempo_siguiente == 101  # mínimo 1


def probar_orden_de_agenda_con_empates_y_cancelaciones():
    agenda = AgendaEventos()
    salida = []
    def accion(nombre):
        return lambda ahora: salida.append(nombre)
    e1 = Evento(100, agenda.nueva_secuencia(), None, accion("goblin"))
    e2 = Evento(50, agenda.nueva_secuencia(), None, accion("esqueleto"))
    e3 = Evento(50, agenda.nueva_secuencia(), None, accion("trampa"))
    e4 = Evento(50, agenda.nueva_secuencia(), None, accion("rata"))
    for e in (e1, e2, e3, e4):
        agenda.agendar(e)
    agenda.cancelar(e3)
    correr(agenda, Reloj(), lambda: True)
    assert salida == ["esqueleto", "rata", "goblin"]


def probar_activacion_en_orden_de_id():
    agenda, reloj, jugador, azar, bitacora = escenario()
    r2 = nueva_rata("e-202", 150, Sala(2))
    r1 = nueva_rata("e-201", 150, Sala(3))
    activar_enemigos(agenda, [r2, r1], 0, jugador, azar, bitacora)
    assert r1.tiempo_siguiente == r2.tiempo_siguiente == 66
    assert r1.evento_pendiente.secuencia < r2.evento_pendiente.secuencia


def probar_salida_compartida_y_opuestas():
    for i in range(4):
        a, b = Sala(1), Sala(2)
        salida = a.conectar(DIRECCIONES[i], b, "cerrada", llave="itm_llave", cierre_automatico=500)
        j = DIRECCIONES.index(DIRECCIONES[i])
        assert a.salidas[j] is salida
        assert b.salidas[[1, 0, 3, 2][j]] is salida      # el lado opuesto es el mismo objeto
        assert a.vecino(j) is b and b.vecino([1, 0, 3, 2][j]) is a
        salida.estado = "abierta"                        # abrir desde un lado abre para ambos
        assert b.salidas[[1, 0, 3, 2][j]].esta_abierta()
        assert salida.llave == "itm_llave" and salida.cierre_automatico == 500


def probar_vida_nunca_fuera_de_rango():
    rata = Enemigo("Rata", 5, 5, 1, 100, vida_max=12)    # vida inicial menor que vida_max
    rata.curar(100)
    assert rata.vida == 12
    rata.recibir_dano(100)
    assert rata.vida == 0 and not rata.esta_vivo()


def probar_actores_siguen_al_movimiento():
    a, b = Sala(1), Sala(2)
    a.conectar("N", b)
    rata = nueva_rata(sala=a)
    assert rata in a.actores
    rata.mover_a(b)
    assert rata not in a.actores and rata in b.actores and rata.sala is b


def probar_rastreador_sigue_el_mas_fresco_y_desempata_por_id():
    centro, norte, este, lejos = Sala(5), Sala(9), Sala(3), Sala(20)
    centro.conectar("N", norte)
    centro.conectar("E", este)
    jugador = Actor("Jugador", 30, 6, 2, 100, lejos)
    rata = nueva_rata("e-1", 100, centro, "rastreador")
    norte.marcar_visita_jugador(0)
    este.marcar_visita_jugador(0)
    resolver_turno_enemigo(rata, jugador, random.Random(1), 10)
    assert rata.sala is este                              # empate exacto: menor id (3 < 9)
    rata.mover_a(centro)
    norte.marcar_visita_jugador(5)
    resolver_turno_enemigo(rata, jugador, random.Random(1), 10)
    assert rata.sala is norte                             # ahora norte tiene el rastro más fresco
    rata.mover_a(centro)
    resolver_turno_enemigo(rata, jugador, random.Random(1), 600)
    assert rata.sala is centro                            # rastros de 400 o más ya no sirven


if __name__ == "__main__":
    pruebas = [probar_primer_turno_se_puede_cancelar, probar_reprogramar_actualiza_el_puntero,
               probar_siguiente_turno_sale_del_reloj_actual, probar_formula_de_cambio_de_velocidad,
               probar_orden_de_agenda_con_empates_y_cancelaciones, probar_activacion_en_orden_de_id,
               probar_salida_compartida_y_opuestas, probar_vida_nunca_fuera_de_rango,
               probar_actores_siguen_al_movimiento,
               probar_rastreador_sigue_el_mas_fresco_y_desempata_por_id]
    for prueba in pruebas:
        prueba()
        print("OK ", prueba.__name__)
    print("Todas las pruebas pasaron")