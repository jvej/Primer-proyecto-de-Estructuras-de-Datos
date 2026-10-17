"""Efectos temporales y del entorno (§2.10). Cada efecto es un evento en la agenda.

Todo cambio pasa por partida.cambiar / partida.programar, así queda registrado
para el retroceso. Cancelar un efecto es cancelar su evento (§4.1).
"""

INTERVALO_VENENO = 80
DURACION_VENENO = 400
INTERVALO_REGENERACION = 200


def aplicar_veneno(partida, actor, dano):
    """Daño cada 80 unidades durante 400 desde su aplicación (5 pulsos). Reaplicar reinicia."""
    cancelar_veneno(partida, actor)
    inicio = partida.reloj.tiempo_actual

    def programar(tiempo):
        evento = partida.programar(tiempo, pulso, actor, "veneno")
        partida.cambiar(actor, "evento_veneno", evento)

    def pulso(ahora):
        if not actor.esta_vivo():
            return
        if actor is partida.jugador:
            partida.bitacora.agregar(f"El veneno te hace {dano} de daño.")
        partida.danar(actor, dano)
        if actor.esta_vivo() and ahora + INTERVALO_VENENO <= inicio + DURACION_VENENO:
            programar(ahora + INTERVALO_VENENO)
        else:
            partida.cambiar(actor, "evento_veneno", None)

    if actor is partida.jugador:
        partida.bitacora.agregar("Estás envenenado.")
    programar(inicio + INTERVALO_VENENO)


def cancelar_veneno(partida, actor):
    if actor.evento_veneno is not None:
        partida.cancelar(actor.evento_veneno)
        partida.cambiar(actor, "evento_veneno", None)


def iniciar_regeneracion(partida, enemigo):
    """Recupera enemigo.regeneracion de vida cada 200 unidades, sin pasar de vida_max."""

    def programar(tiempo):
        evento = partida.programar(tiempo, pulso, enemigo, "regeneración")
        partida.cambiar(enemigo, "evento_regeneracion", evento)

    def pulso(ahora):
        if not enemigo.esta_vivo():
            return
        if enemigo.vida < enemigo.vida_max:
            partida.curar(enemigo, enemigo.regeneracion)
        programar(ahora + INTERVALO_REGENERACION)

    programar(partida.reloj.tiempo_actual + INTERVALO_REGENERACION)


def cambiar_velocidad(partida, actor, delta):
    """Suma delta a la velocidad y reajusta su próxima acción con la fórmula de §2.3.
    Devuelve el cambio realmente aplicado (la velocidad nunca baja de 1)."""
    anterior = actor.velocidad
    nueva = max(1, anterior + delta)
    partida.cambiar(actor, "velocidad", nueva)
    evento = actor.evento_pendiente
    if evento is not None and evento.valido and nueva != anterior:
        partida.agenda.reprogramar_por_cambio_velocidad(
            evento, partida.reloj.tiempo_actual, anterior, nueva)
    return nueva - anterior


def velocidad_temporal(partida, actor, delta, duracion):
    aplicado = cambiar_velocidad(partida, actor, delta)

    def terminar(ahora):
        cambiar_velocidad(partida, actor, -aplicado)
        if actor is partida.jugador:
            partida.bitacora.agregar("Termina el efecto de velocidad.")

    partida.programar(partida.reloj.tiempo_actual + duracion, terminar, actor, "fin de velocidad")


def encender_antorcha(partida, objeto):
    jugador = partida.jugador
    partida.cambiar(jugador, "antorcha_encendida", True)

    def apagar(ahora):
        partida.cambiar(jugador, "antorcha_encendida", False)
        partida.bitacora.agregar("Tu antorcha se apaga.")

    partida.programar(partida.reloj.tiempo_actual + objeto.duracion, apagar, jugador, "antorcha")


def disparar_trampa(partida, trampa):
    """Se activa al entrar el jugador, se desarma y programa su rearme (§2.10)."""
    partida.bitacora.agregar(f"¡Trampa! {trampa.nombre}.")
    partida.cambiar(trampa, "armada", False)
    partida.programar(partida.reloj.tiempo_actual + trampa.rearme,
                      lambda ahora: partida.cambiar(trampa, "armada", True), None, "rearme de trampa")
    if trampa.dano > 0:
        partida.danar(partida.jugador, trampa.dano)
    if trampa.veneno > 0 and partida.jugador.esta_vivo():
        aplicar_veneno(partida, partida.jugador, trampa.veneno)


def programar_cierre(partida, salida):
    """Una salida con cierre automático se cierra sola tras el tiempo indicado."""

    def cerrar(ahora):
        partida.cambiar(salida, "estado", "cerrada")
        partida.cambiar(salida, "evento_cierre", None)
        if partida.jugador.sala is salida.sala_a or partida.jugador.sala is salida.sala_b:
            partida.bitacora.agregar("Una puerta se cierra.")

    evento = partida.programar(partida.reloj.tiempo_actual + salida.cierre_automatico,
                               cerrar, None, "cierre de puerta")
    partida.cambiar(salida, "evento_cierre", evento)