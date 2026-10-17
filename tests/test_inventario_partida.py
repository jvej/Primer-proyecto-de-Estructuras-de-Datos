"""Prueba de integración: el Inventario real dentro de la Partida de Mariano.

Reemplaza el InventarioDePrueba que arma cripta_de_prueba.armar() por el Inventario
de §4.5, así que sirve tanto con cripta_de_prueba.py original como ya modificado.
Ejecutar: python -m tests.test_inventario_partida
"""
from tests.cripta_de_prueba import armar, entrada, esqueleto_linea
from modelo.juego.inventario import Inventario
from modelo.estructuras.ordenamiento import ordenar


def armar_con_inventario(*args, capacidad=5, **kwargs):
    esc = armar(*args, capacidad=capacidad, **kwargs)
    inventario = Inventario(capacidad, ordenar)
    esc.partida.inventario = inventario
    esc.inventario = inventario
    return esc


def nombres(esc):
    return [o.nombre for o in esc.inventario.objetos()]


def probar_pergamino_antes_del_objeto_equipado():
    esc = armar_con_inventario(esqueleto_linea(2))
    p = esc.partida
    esc.dar("itm_pergamino")
    daga = esc.dar("itm_daga")
    esc.dar("itm_cota")
    assert p.equipar(daga) and nombres(esc) == ["Daga", "Pergamino de retroceso", "Cota"]
    assert p.usar_pergamino()
    assert nombres(esc) == ["Daga", "Cota"] and p.jugador.arma is None
    esc.cerrar()


def probar_pergamino_antes_del_objeto_soltado():
    esc = armar_con_inventario(esqueleto_linea(2))
    p = esc.partida
    esc.dar("itm_pergamino")
    daga = esc.dar("itm_daga")
    esc.dar("itm_cota")
    assert p.soltar(daga) and nombres(esc) == ["Pergamino de retroceso", "Cota"]
    assert p.usar_pergamino()
    assert nombres(esc) == ["Daga", "Cota"] and p.objetos_en_sala() == []
    esc.cerrar()


def probar_equipar_arma_sustituye_y_se_deshace():
    esc = armar_con_inventario(esqueleto_linea(2))
    p = esc.partida
    daga = esc.dar("itm_daga")
    cota = esc.dar("itm_cota")
    esc.dar("itm_pergamino")
    assert p.equipar(cota) and nombres(esc)[0] == "Cota" and p.jugador.defensa_efectivo() == 4
    assert p.equipar(daga) and nombres(esc)[:2] == ["Daga", "Cota"]
    assert p.usar_pergamino()                       # deshace equipar(daga)
    assert nombres(esc) == ["Cota", "Daga"] and p.jugador.arma is None
    assert p.jugador.armadura is cota
    esc.cerrar()


def probar_inventario_lleno_y_cursor_en_la_partida():
    esc = armar_con_inventario(esqueleto_linea(2), [entrada(1, objetos=["itm_daga", "itm_cota"])],
                               capacidad=1)
    p = esc.partida
    assert p.recoger(0) and esc.inventario.lleno()
    assert not p.recoger(0)                         # lleno: rechazado sin consumir tiempo
    assert p.reloj.tiempo_actual == 25
    assert p.soltar(esc.inventario.objeto_actual())  # soltar el que se está viendo
    assert esc.inventario.esta_vacio() and len(p.objetos_en_sala()) == 2
    esc.cerrar()


if __name__ == "__main__":
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("probar_")]
    for prueba in pruebas:
        prueba()
        print("OK ", prueba.__name__)
    print("Todas las pruebas de integración pasaron")