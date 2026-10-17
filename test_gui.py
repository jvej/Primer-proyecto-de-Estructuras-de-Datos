"""Pruebas de la interfaz gráfica que NO necesitan Pygame ni ventana.
Ejecutar: python test_gui.py

  - cada tecla produce la misma Orden que el comando equivalente de la consola;
  - elegir enemigo u objeto no es una orden (no consume tiempo ni va al log);
  - el Modelo y el Controlador no importan Pygame (MVC, §6);
  - --replay y --bench no cargan Pygame.
"""
import os
import sys

from controles_gui import (SIG_ENEMIGO, SIG_SUELO, ajustar_posicion, orden_para_tecla,
                           siguiente_posicion)
from cripta_de_prueba import armar, esqueleto_linea
from orden import ABRIR, INV_ORDENAR, MOVER, Orden, SALIR
from vista_consola import interpretar

CARPETA = os.path.dirname(os.path.abspath(__file__))


def test_teclas_igual_que_la_consola():
    esc = armar(esqueleto_linea(2))
    partida = esc.partida
    pares = (("up", "n"), ("down", "s"), ("right", "e"), ("left", "o"), ("space", "atacar 1"),
             ("g", "recoger 1"), ("x", "esperar"), ("r", "retroceso"), ("w", "ant"),
             ("s", "sig"), ("home", "inicio"), ("u", "usar"), ("q", "equipar"),
             ("t", "soltar"), ("i", "inv"), ("p", "puntajes"), ("f5", "guardar"),
             ("f9", "cargar"), ("h", "ayuda"), ("escape", "salir"), ("1", "ordenar peso"),
             ("3", "ordenar nombre"))
    for tecla, comando in pares:
        assert orden_para_tecla(tecla, False, 0, 0) == interpretar(comando, partida), (tecla, comando)
    esc.cerrar()


def test_shift_flecha_abre_y_shift_numero_ordena_descendente():
    assert orden_para_tecla("up", True, 0, 0) == Orden(ABRIR, "N")
    assert orden_para_tecla("left", False, 0, 0) == Orden(MOVER, "O")
    assert orden_para_tecla("2", True, 0, 0) == Orden(INV_ORDENAR, "valor", True)


def test_seleccion_no_es_una_orden():
    assert orden_para_tecla("tab", False, 0, 0) == SIG_ENEMIGO
    assert orden_para_tecla("f", False, 0, 0) == SIG_SUELO
    assert orden_para_tecla("space", False, 2, 0).argumento == 2      # ataca al elegido
    assert orden_para_tecla("g", False, 0, 3).argumento == 3          # recoge el elegido
    assert orden_para_tecla("zzz", False, 0, 0) is None
    assert orden_para_tecla("escape", False, 0, 0) == Orden(SALIR)


def test_seleccion_circular_y_ajuste():
    assert siguiente_posicion(0, 3) == 1 and siguiente_posicion(2, 3) == 0
    assert siguiente_posicion(5, 0) == 0
    assert ajustar_posicion(4, 2) == 1          # murió un enemigo: la selección sigue válida
    assert ajustar_posicion(0, 0) == 0


def test_modelo_y_controlador_no_importan_pygame():
    for nombre in os.listdir(CARPETA):
        if not nombre.endswith(".py") or nombre in ("vista_pygame.py", "test_gui.py", "main.py"):
            continue
        with open(os.path.join(CARPETA, nombre), encoding="utf-8") as archivo:
            assert "import pygame" not in archivo.read(), nombre


def test_replay_y_bench_no_cargan_pygame():
    import main
    argumentos = main.leer_argumentos(["--replay", "x.log"])
    assert not argumentos.gui
    assert "pygame" not in sys.modules


if __name__ == "__main__":
    pruebas = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for nombre, funcion in pruebas:
        funcion()
        print("ok  ", nombre)
    print("\n%d pruebas correctas" % len(pruebas))