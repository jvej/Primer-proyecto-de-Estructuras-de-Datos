# Pruebas del motor completo (§2, §4.1, §4.6, §4.7) con una cripta simulada.
# sorted() se usa SOLO para comparar resultados en las pruebas; el programa no lo usa.
import efectos
from cripta_de_prueba import armar, entrada, esqueleto_linea


def foto(p):
    """Resumen del estado del juego para comparar antes y después de un retroceso."""
    eventos = []
    for e in p.agenda._heap:
        if e.valido:
            eventos.append((e.tiempo_siguiente, e.secuencia, e.descripcion))
    enemigos = []
    for e in p.mapa.enemigos:
        enemigos.append((e.id_instancia, e.vida, e.sala.id, e.activo, e.velocidad))
    rastros = [(s.id, s.ultimo_instante_jugador) for s in p.mapa.salas]
    puertas = []
    for s in p.mapa.salas:
        for d in s.salidas:
            if d is not None:
                puertas.append((s.id, d.estado))
    trampas = [(t.instancia, t.armada) for s in p.mapa.salas for t in s.trampas]
    suelo = [(s.id, [o.id for o in s.objetos]) for s in p.mapa.salas]
    return (p.reloj.tiempo_actual, p.acciones, p.derrotados, p.estado, p.jugador.vida,
            p.jugador.sala.id, p.jugador.velocidad, p.jugador.evento_pendiente.tiempo_siguiente,
            sorted(eventos), enemigos, rastros, puertas, trampas, suelo)


def probar_inicio():
    esc = armar(esqueleto_linea(3))
    p = esc.partida
    assert p.esperando and p.estado == "jugando" and p.reloj.tiempo_actual == 0
    assert p.sala_actual().id == 1 and p.sala_actual().ultimo_instante_jugador == 0
    assert p.jugador.tiempo_siguiente == 0
    esc.cerrar()


def probar_ejemplo_de_la_seccion_2_13():
    # Rata de velocidad 150 en la sala 2: se activa al entrar, actúa en t=66 y de nuevo en t=132.
    esc = armar(esqueleto_linea(3), [entrada(2, enemigos=[("e-201", "ent_rata", 12)])])
    p = esc.partida
    assert p.mover("N")
    rata = p.mapa.enemigos[0]
    assert p.reloj.tiempo_actual == 100 and p.jugador.tiempo_siguiente == 100
    assert rata.activo and rata.tiempo_siguiente == 132     # actuó en 66 y ya tiene el turno de 132
    assert p.jugador.vida < 30                              # y su acción de 66 fue atacar
    assert p.acciones == 1
    esc.cerrar()


def probar_rechazos_no_consumen_tiempo():
    salas = esqueleto_linea(3, [(1, 2, {"cerrada": True, "llave": "itm_llave_bronce"})])
    esc = armar(salas, [entrada(1, objetos=["itm_daga", "itm_cota"])], capacidad=1)
    p = esc.partida
    assert p.recoger(0)                                     # costo 25
    assert p.reloj.tiempo_actual == 25
    antes = foto(p)
    assert not p.recoger(0)                                 # inventario lleno
    assert not p.abrir("N")                                 # sin la llave
    assert not p.mover("N")                                 # puerta cerrada
    assert not p.mover("S")                                 # no hay salida
    assert not p.atacar(0)                                  # no hay enemigos
    assert foto(p) == antes
    esc.cerrar()


def probar_puerta_con_llave_y_cierre_automatico():
    salas = esqueleto_linea(3, [(1, 2, {"cerrada": True, "llave": "itm_llave_bronce", "cierre_automatico": 200})])
    esc = armar(salas, [entrada(1, objetos=["itm_llave_bronce"])])
    p = esc.partida
    assert p.recoger(0) and p.abrir("N")                    # 25 + 50
    assert p.reloj.tiempo_actual == 75
    puerta = p.sala_actual().salidas[0]
    assert puerta.esta_abierta()
    while p.reloj.tiempo_actual < 225:
        assert p.esperar()
    assert not puerta.esta_abierta()                        # se cerró sola a los 200 de abrirse (t=25+200)
    assert not p.mover("N")
    esc.cerrar()


def probar_combate_botin_y_cancelacion():
    esc = armar(esqueleto_linea(2), [entrada(2, enemigos=[("e-1", "ent_esqueleto", 10)])])
    p = esc.partida
    assert p.mover("N")
    esqueleto = p.mapa.enemigos[0]
    while p.enemigos_en_sala():
        assert p.atacar(0)
    assert not esqueleto.esta_vivo() and p.derrotados == 1
    assert not esqueleto.evento_pendiente.valido            # sus eventos futuros ya no ocurren
    assert [o.id for o in p.objetos_en_sala()] == ["itm_pocion"]    # soltó su botín
    assert esqueleto not in p.sala_actual().actores
    ataques = len([m for m in esc.mensajes() if "te ataca" in m])
    p.esperar(); p.esperar()
    assert len([m for m in esc.mensajes() if "te ataca" in m]) == ataques
    esc.cerrar()


def probar_veneno_antidoto_y_regeneracion():
    esc = armar(esqueleto_linea(2))
    p = esc.partida
    efectos.aplicar_veneno(p, p.jugador, 2)                 # t=0: pulsos en 80,160,240,320,400
    while p.reloj.tiempo_actual < 500:
        p.esperar()
    assert p.jugador.vida == 20 and p.jugador.evento_veneno is None     # exactamente 5 pulsos
    esc.cerrar()

    esc = armar(esqueleto_linea(2))
    p = esc.partida
    antidoto = esc.dar("itm_antidoto")
    efectos.aplicar_veneno(p, p.jugador, 2)
    p.esperar()                                             # t=100: un pulso (80)
    assert p.jugador.vida == 28
    assert p.usar(antidoto)                                 # cancela los pulsos futuros
    while p.reloj.tiempo_actual < 600:
        p.esperar()
    assert p.jugador.vida == 28 and antidoto not in esc.inventario.objetos()
    esc.cerrar()

    esc = armar(esqueleto_linea(2), [entrada(2, enemigos=[("e-1", "ent_troll", 10)])])
    p = esc.partida
    p.mover("N")
    troll = p.mapa.enemigos[0]
    while p.reloj.tiempo_actual < 400:                      # activado en 0: regenera en 200 y 400
        p.esperar()
    assert troll.vida == 14 and troll.vida <= troll.vida_max
    esc.cerrar()


def probar_velocidad_temporal():
    esc = armar(esqueleto_linea(2))
    p = esc.partida
    p.jugador.vida = 10
    pocion = esc.dar("itm_pocion_rapida")
    assert p.usar(pocion)                   # costo 50 -> 50 unidades; con velocidad 150 queda en 33
    assert p.jugador.velocidad == 150 and p.reloj.tiempo_actual == 33
    assert "velocidad 150" in p.efectos_activos()
    while p.reloj.tiempo_actual <= 300:
        p.esperar()
    assert p.jugador.velocidad == 100 and p.efectos_activos() == []
    esc.cerrar()


def probar_trampa_y_rearme():
    esc = armar(esqueleto_linea(2), [entrada(2, trampas=[("t-1", "trp_dardos")])])
    p = esc.partida
    p.mover("N")
    assert p.jugador.vida == 26 and not p.trampas_en_sala()[0].armada       # t=0
    p.mover("S"); p.mover("N")                                              # entra en t=200: desarmada
    assert p.jugador.vida == 26
    p.mover("S"); p.mover("N")                                              # entra en t=400: ya rearmada (300)
    assert p.jugador.vida == 22
    esc.cerrar()


def probar_victoria_y_derrota():
    salas = esqueleto_linea(4, [(3, 4, {"cerrada": True, "llave": "itm_llave_negra"})])
    esc = armar(salas, [entrada(1, objetos=["itm_llave_negra"])])
    p = esc.partida
    assert p.recoger(0) and p.mover("N") and p.mover("N")
    assert p.abrir("N") and p.estado == "jugando"
    assert p.mover("N") and p.estado == "victoria"
    assert not p.esperar()                                  # la partida terminó
    esc.cerrar()

    esc = armar(esqueleto_linea(2), [entrada(2, trampas=[("t-1", "trp_mortal")])])
    p = esc.partida
    assert p.mover("N") and p.estado == "derrota" and p.jugador.vida == 0
    assert not p.mover("S")
    esc.cerrar()


def probar_rastreador_persigue_el_rastro():
    esc = armar(esqueleto_linea(3), [entrada(1, enemigos=[("e-1", "ent_rata", 12)])])
    p = esc.partida
    rata = p.mapa.enemigos[0]
    assert rata.activo and rata.sala.id == 1                # la sala inicial se activa en t=0
    p.mover("N")                                            # el jugador pasa a la 2; la rata (t=66) lo sigue
    assert rata.sala.id == 2
    esc.cerrar()


def probar_activacion_en_orden_de_id():
    esc = armar(esqueleto_linea(2), [entrada(1, enemigos=[("e-202", "ent_esqueleto", 10), ("e-201", "ent_esqueleto", 10)])])
    primero, segundo = None, None
    for e in esc.partida.mapa.enemigos:
        if e.id_instancia == "e-201":
            primero = e
        else:
            segundo = e
    assert primero.evento_pendiente.secuencia < segundo.evento_pendiente.secuencia
    esc.cerrar()


def probar_equipar_soltar_y_usar():
    esc = armar(esqueleto_linea(2), capacidad=5)
    p = esc.partida
    daga, cota, pocion = esc.dar("itm_daga"), esc.dar("itm_cota"), esc.dar("itm_pocion")
    assert p.equipar(cota) and esc.inventario.objetos()[0] is cota and p.jugador.defensa_efectivo() == 4
    assert p.equipar(daga) and esc.inventario.objetos()[0] is daga and p.jugador.ataque_efectivo() == 9
    assert not p.equipar(pocion)
    p.jugador.vida = 5
    assert p.usar(pocion) and p.jugador.vida == 15 and pocion not in esc.inventario.objetos()   # cura 10
    assert p.soltar(daga) and p.jugador.arma is None and daga in p.objetos_en_sala()
    assert p.ficha_en_uso("itm_cota") and p.ficha_en_uso("itm_daga") and not p.ficha_en_uso("ent_rata")
    esc.cerrar()


def probar_retroceso():
    esc = armar(esqueleto_linea(3), [entrada(2, enemigos=[("e-201", "ent_rata", 12)]),
                                     entrada(1, objetos=["itm_daga"])], capacidad=10)
    p = esc.partida
    esc.dar("itm_pergamino"); esc.dar("itm_pergamino"); esc.dar("itm_pergamino")
    p.precarga.asegurar(2)                                  # lo que mover() hace antes de abrir el grupo:
    p._incorporar(p.mapa.sala(2))                           # crear el contenido no es estado reversible
    antes = foto(p)
    assert p.mover("N") and foto(p) != antes                # entra, se activa la rata y ataca
    assert p.usar_pergamino()
    assert foto(p) == antes                                 # reloj, agenda, rastro, vidas, activación...
    assert p.esperando and len([o for o in esc.inventario.objetos() if o.es_pergamino()]) == 2
    assert p.acciones == 0                                  # y usarlo no cuenta como acción

    # Dos pergaminos seguidos retroceden dos acciones (Apéndice B).
    p.esperar(); base = foto(p); p.esperar(); p.esperar()
    assert p.usar_pergamino() and p.usar_pergamino()
    assert foto(p) == base
    assert [o.es_pergamino() for o in esc.inventario.objetos()] == []

    # Nunca más de 5 acciones hacia atrás, y el pergamino no se gasta si no hay nada que deshacer.
    for _ in range(7):
        p.esperar()
    for _ in range(6):
        esc.dar("itm_pergamino")
    usados = 0
    while p.usar_pergamino():
        usados += 1
    assert usados == 5 and len(esc.inventario.objetos()) == 1   # 5 gastados; el sexto no se gasta sin nada que deshacer
    esc.cerrar()


def probar_retroceso_no_toca_los_pergaminos():
    # Si en el intervalo revertido se recogió un pergamino, la reversión no lo devuelve al suelo (§2.11).
    esc = armar(esqueleto_linea(2), [entrada(1, objetos=["itm_pergamino", "itm_daga"])], capacidad=10)
    p = esc.partida
    esc.dar("itm_pergamino")
    assert p.recoger(0) and p.recoger(0)                    # pergamino, luego daga
    assert len([o for o in esc.inventario.objetos() if o.es_pergamino()]) == 2
    assert p.usar_pergamino()                               # deshace la recogida de la daga
    assert [o.id for o in p.objetos_en_sala()] == ["itm_daga"]
    assert len([o for o in esc.inventario.objetos() if o.es_pergamino()]) == 1   # 2 recogidos - 1 usado
    esc.cerrar()


def probar_retroceso_de_equipo_y_orden():
    esc = armar(esqueleto_linea(2), capacidad=5)
    p = esc.partida
    daga, cota = esc.dar("itm_daga"), esc.dar("itm_cota")
    esc.dar("itm_pergamino")
    orden = list(esc.inventario.objetos())
    assert p.equipar(cota)
    assert p.usar_pergamino()
    assert [o.id for o in esc.inventario.objetos() if not o.es_pergamino()] == [o.id for o in orden if not o.es_pergamino()]
    assert p.jugador.armadura is None
    esc.cerrar()


def probar_mismo_resultado_con_misma_semilla():
    def jugar(semilla):
        esc = armar(esqueleto_linea(3), [entrada(2, enemigos=[("e-1", "ent_rata", 12), ("e-2", "ent_errante", 6)])],
                    semilla=semilla)
        p = esc.partida
        p.mover("N")
        for _ in range(4):
            p.esperar()
        resultado = (foto(p), esc.mensajes())
        esc.cerrar()
        return resultado

    assert jugar(7) == jugar(7)


def probar_sin_presupuesto_no_se_cae():
    esc = armar(esqueleto_linea(14), limite=50)
    p = esc.partida
    esc.presupuesto.fijar_limite(esc.presupuesto.realizadas)    # ya no se permiten más solicitudes
    cargadas = 0
    while p.mover("N"):
        cargadas += 1
    assert 1 <= cargadas < 13 and p.reloj.tiempo_actual == cargadas * 100   # se detuvo en una sala sin cargar
    assert p.estado == "jugando" and p.esperando
    assert "presupuesto" in esc.mensajes()[-1].lower() or "No se pudo cargar" in esc.mensajes()[-1]
    esc.cerrar()


if __name__ == "__main__":
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("probar_")]
    for prueba in pruebas:
        prueba()
        print("OK ", prueba.__name__)
    print("Todas las pruebas pasaron")