"""Partida de demostración del motor, sobre una cripta simulada (sin red): python demo_motor.py"""

from cripta_de_prueba import armar, entrada, esqueleto_linea


def main():
    salas = esqueleto_linea(4, [(1, 2, {"cerrada": True, "llave": "itm_llave_bronce", "cierre_automatico": 300}),
                                (3, 4, {"cerrada": True, "llave": "itm_llave_negra"})])
    contenido = [entrada(1, objetos=["itm_llave_bronce", "itm_daga"]),
                 entrada(2, enemigos=[("e-201", "ent_rata", 12)], objetos=["itm_llave_negra"]),
                 entrada(3, trampas=[("t-31", "trp_dardos")])]
    esc = armar(salas, contenido, semilla=42)
    p = esc.partida

    p.recoger(0)                 # llave de bronce
    p.recoger(0)                 # daga
    p.equipar(esc.inventario.objetos()[1])
    p.abrir("N")
    p.mover("N")                 # entra a la sala 2: se activa la rata
    while p.enemigos_en_sala() and p.estado == "jugando":
        p.atacar(0)
    p.recoger(0)                 # llave negra
    p.mover("N")
    p.abrir("N")
    p.mover("N")                 # sala de salida

    for mensaje in esc.mensajes():
        print(mensaje)
    print("\nEstado: %s | acciones: %d | derrotados: %d | tiempo final: %d | vida: %d/%d"
          % (p.estado, p.acciones, p.derrotados, p.reloj.tiempo_actual, p.jugador.vida, p.jugador.vida_max))
    esc.cerrar()


if __name__ == "__main__":
    main()