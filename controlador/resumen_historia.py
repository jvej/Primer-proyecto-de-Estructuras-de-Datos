"""Formato común para consultas y replay, únicamente a partir del resumen."""


def formatear_resumen(resumen):
    """Presenta valores históricos sin acceder al motor ni a puertas vivas."""
    r = resumen
    lineas = [
        "Historia — reloj %s · acciones %s" % (r.reloj, r.acciones),
        "Resultado: %s" % r.estado,
        "Sala del jugador: %s" % r.sala,
        "Vida: %s/%s · ataque: %s · defensa: %s · velocidad: %s" % (
            r.vida, r.vida_max, r.ataque, r.defensa, r.velocidad),
        "Enemigos derrotados: %s" % r.derrotados,
        "Inventario (orden histórico):",
    ]
    for posicion, objeto in enumerate(r.inventario, 1):
        lineas.append("  %s) %s [%s] · %s · usos: %s" % (
            posicion, objeto.base.nombre, objeto.id_ficha, objeto.base.clase, objeto.usos))
    if not r.inventario:
        lineas.append("  Vacío.")
    lineas.append("Efectos activos: %s" % (", ".join(r.efectos) or "ninguno"))
    lineas.append("Enemigos de la sala:")
    for enemigo in r.enemigos:
        lineas.append("  %s [%s] · vida %s/%s · ataque %s · defensa %s · velocidad %s" % (
            enemigo.base.nombre, enemigo.id_instancia, enemigo.vida, enemigo.vida_max,
            enemigo.ataque, enemigo.defensa, enemigo.velocidad))
    if not r.enemigos:
        lineas.append("  Ninguno vivo.")
    lineas.append("Mapa conocido: %s salas exploradas · %s salas avistadas (sin explorar)" % (
        r.num_exploradas, r.num_avistadas))
    # Las salidas ya vienen filtradas por el conocimiento de ese instante.
    # No se completan los destinos ocultos con ids ni nombres de otra fuente.
    for sala in r.salas:
        lineas.append("Sala %s: %s (explorada)" % (sala.id, sala.nombre or "sin nombre"))
        for direccion, estado, destino, llave, costo in sala.salidas:
            visible = "desconocida" if destino is None else "sala %s" % destino
            detalle = estado + (", llave %s" % llave if llave is not None else "")
            lineas.append("  %s -> %s (costo %s, %s)" % (direccion, visible, costo, detalle))
    return "\n".join(lineas)
