import os
import sys

from vista.animaciones_gui import (ABRIR_PUERTA, ATAQUE, CORRER, CORRER_MS, DANO, MUERTE, REPOSO,
                             TRAMPA, Animador, indice_de_cuadro)
from controlador.controlador import Controlador
from vista.controles_gui import (SIG_ENEMIGO, SIG_SUELO, ajustar_posicion, orden_para_tecla,
                           siguiente_posicion)
from tests.cripta_de_prueba import armar, entrada, esqueleto_linea
from controlador.orden import ABRIR, ATACAR, EQUIPAR, INV_ORDENAR, MOVER, Orden, PERGAMINO, RECOGER, SALIR
from vista.vista_consola import interpretar

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    assert orden_para_tecla("space", False, 2, 0).argumento == 2    
    assert orden_para_tecla("g", False, 0, 3).argumento == 3         
    assert orden_para_tecla("zzz", False, 0, 0) is None
    assert orden_para_tecla("escape", False, 0, 0) == Orden(SALIR)


def test_seleccion_circular_y_ajuste():
    assert siguiente_posicion(0, 3) == 1 and siguiente_posicion(2, 3) == 0
    assert siguiente_posicion(5, 0) == 0
    assert ajustar_posicion(4, 2) == 1         
    assert ajustar_posicion(0, 0) == 0


def test_modelo_y_controlador_no_importan_pygame():
    for carpeta, subcarpetas, archivos in os.walk(RAIZ):
        subcarpetas[:] = [s for s in subcarpetas if not s.startswith(".") and s not in ("venv", "__pycache__")]
        for nombre in archivos:
            if not nombre.endswith(".py") or nombre in ("vista_pygame.py", "test_gui.py", "main.py"):
                continue
            with open(os.path.join(carpeta, nombre), encoding="utf-8") as archivo:
                assert "import pygame" not in archivo.read(), nombre


def test_replay_y_bench_no_cargan_pygame():
    import main
    argumentos = main.leer_argumentos(["--replay", "x.log"])
    assert not argumentos.gui
    assert "pygame" not in sys.modules


def test_animaciones_salen_de_la_partida_sin_cambiarla():
    esc = armar(esqueleto_linea(2), [entrada(1, enemigos=[("e-1", "ent_errante", 6)])])
    partida = esc.partida
    controlador = Controlador(partida)
    enemigo = partida.enemigos_en_sala()[0]
    animador = Animador()
    animador.reiniciar(partida)
    ahora = 1000
    vistos = []
    while enemigo.esta_vivo() and partida.estado == "jugando":
        assert controlador.ejecutar(Orden(ATACAR, 0))
        antes = (partida.reloj.tiempo_actual, partida.jugador.vida, enemigo.vida)
        animador.observar(partida, ahora, ATACAR, [(enemigo, (500, 200))])
        assert antes == (partida.reloj.tiempo_actual, partida.jugador.vida, enemigo.vida)
        vistos.append(animador.estado(partida.jugador, ahora)[0])
        ahora += 2000
    assert ATAQUE in vistos or DANO in vistos
    if not enemigo.esta_vivo():
        caidos = animador.fantasmas(ahora - 2000)
        assert len(caidos) == 1 and caidos[0][0] is enemigo and caidos[0][1] == (500, 200)
        assert animador.estado(enemigo, ahora - 2000)[0] == MUERTE
    esc.cerrar()


def test_retroceso_no_anima():
    esc = armar(esqueleto_linea(2), [entrada(1, enemigos=[("e-1", "ent_troll", 20)])])
    esc.dar("itm_pergamino")
    partida = esc.partida
    controlador = Controlador(partida)
    animador = Animador()
    animador.reiniciar(partida)
    controlador.ejecutar(Orden(ATACAR, 0))
    animador.observar(partida, 0, ATACAR, [])
    animador.activas = []
    controlador.ejecutar(Orden(PERGAMINO))       
    animador.observar(partida, 10, PERGAMINO, [])
    assert animador.activas == []
    assert animador.estado(partida.jugador, 10)[0] == REPOSO
    esc.cerrar()


def test_entrar_a_otra_sala_anima_la_carrera():
    esc = armar(esqueleto_linea(2))
    partida = esc.partida
    animador = Animador()
    animador.reiniciar(partida)
    assert Controlador(partida).ejecutar(Orden(MOVER, "N"))
    animador.observar(partida, 0, MOVER, [])
    assert animador.estado(partida.jugador, 100)[0] == CORRER
    assert animador.estado(partida.jugador, 5000)[0] == REPOSO   
    esc.cerrar()


def test_trampa_al_entrar_anima_el_dano_cuando_termina_de_correr():
    esc = armar(esqueleto_linea(2), [entrada(2, trampas=[("t-1", "trp_dardos")])])
    partida = esc.partida
    animador = Animador()
    animador.reiniciar(partida)
    vida = partida.jugador.vida
    assert Controlador(partida).ejecutar(Orden(MOVER, "N"))
    assert partida.jugador.vida < vida                               
    animador.observar(partida, 0, MOVER, [])
    assert animador.estado(partida.jugador, 100)[0] == CORRER        
    assert animador.estado(partida.jugador, CORRER_MS + 10)[0] == DANO  
    efectos = animador.efectos_trampa(CORRER_MS + 10)
    assert len(efectos) == 1 and efectos[0][1] == "trp_dardos"
    assert animador.efectos_trampa(100) == []                       
    esc.cerrar()


def test_recoger_un_arma_no_la_equipa():
    esc = armar(esqueleto_linea(2), [entrada(1, objetos=["itm_daga"])])
    partida = esc.partida
    controlador = Controlador(partida)
    assert controlador.ejecutar(Orden(RECOGER, 0))
    assert partida.jugador.arma is None               
    assert controlador.ejecutar(Orden(EQUIPAR, None))
    assert partida.jugador.arma is not None            
    esc.cerrar()


def test_cuadros_de_animacion():
    assert indice_de_cuadro(REPOSO, 0, 2) == 0 and indice_de_cuadro(REPOSO, 460, 2) == 1
    assert indice_de_cuadro(REPOSO, 920, 2) == 0               
    assert indice_de_cuadro(MUERTE, 0, 3) == 0 and indice_de_cuadro(MUERTE, 99999, 3) == 2
    assert indice_de_cuadro(ATAQUE, 0, 0) == -1              
    assert indice_de_cuadro(CORRER, 0, 6) == 0 and indice_de_cuadro(CORRER, 80 * 7, 6) == 1  
    assert indice_de_cuadro(ABRIR_PUERTA, 0, 4) == 0 and indice_de_cuadro(ABRIR_PUERTA, 9999, 4) == 3
    assert indice_de_cuadro(TRAMPA, 0, 4) == 0 and indice_de_cuadro(TRAMPA, 9999, 4) == 3


if __name__ == "__main__":
    pruebas = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for nombre, funcion in pruebas:
        funcion()
        print("ok  ", nombre)
    print("\n%d pruebas correctas" % len(pruebas))