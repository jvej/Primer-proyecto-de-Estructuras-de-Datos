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


def test_z_FR010_salidas_cinco_campos_y_etiqueta_privada():
    # Después de las verificaciones de imports: no abre ventana ni carga assets.
    import pygame
    from vista.vista_pygame import VistaPygame
    esc = armar(esqueleto_linea(3, [(1, 2, {"costo": 173})]))
    try:
        class VistaMinima:
            partida = esc.partida
        assert VistaPygame._salida(VistaMinima(), "N") == "abierta"
        assert VistaPygame._salida(VistaMinima(), "N", con_llave=True) == ("abierta", None)
        textos = []
        class DibujoMinimo:
            destello = None
            fuente_chica = None
            def __init__(self):
                self.zonas = []
                self.pantalla = pygame.Surface((1280, 720))
            def _cuadro_de_puerta(self, direccion, estado):
                return pygame.Surface((20, 20))
            def _texto(self, fuente, texto, *args, **kwargs):
                textos.append(texto)
        VistaPygame._dibujar_puerta(DibujoMinimo(), "N", "abierta", None, None, 173)
        assert "desconocida" in textos[0] and "costo 173" in textos[0]
        assert "None" not in textos[0]
    finally:
        esc.cerrar()


def _vista_dialogo_prueba(lotes):
    import pygame
    from vista.vista_pygame import VistaPygame
    vista = object.__new__(VistaPygame)
    vista.cerrada = False
    vista.fuente = vista.fuente_media = vista.fuente_chica = None
    textos = []
    cuadros = []
    lotes = iter(lotes)
    def eventos():
        lote = next(lotes)
        if any(e.type == pygame.QUIT for e in lote):
            vista.cerrada = True
        return lote
    vista._eventos = eventos
    vista._dibujar_fondo_de_dialogo = lambda: None
    vista._caja_centrada = lambda ancho, alto, centro: pygame.Rect(0, 0, ancho, alto)
    vista._texto = lambda fuente, texto, *args, **kwargs: textos.append(texto)
    vista._mostrar_cuadro = lambda: cuadros.append(len(textos))
    return vista, textos, cuadros


def test_z_mapa_tecla_nueva_no_rompe_controles():
    from controlador.orden import MAPA
    from vista.controles_gui import AYUDA_LINEAS
    assert orden_para_tecla("m", False, 0, 0) == Orden(MAPA)
    assert orden_para_tecla("up", False, 0, 0) == Orden(MOVER, "N")
    assert orden_para_tecla("r", False, 0, 0) == Orden(PERGAMINO)
    assert any("M: mapa conocido" in linea for linea in AYUDA_LINEAS)


def test_z_mapa_grafico_privacidad_y_cierre_sin_tiempo():
    import pygame
    esc = armar(esqueleto_linea(3))
    try:
        p = esc.partida
        p.mapa.sala(2).nombre = "NOMBRE_VECINO_PRIVADO"
        p.mapa.sala(3).nombre = "NOMBRE_REMOTO_PRIVADO"
        antes = (p.acciones, p.reloj.tiempo_actual, list(p.conocimiento.estado_salas))
        vista, textos, cuadros = _vista_dialogo_prueba([
            [], [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]])
        c = Controlador(p, vista)
        from controlador.orden import MAPA
        assert c.ejecutar(Orden(MAPA))
        texto = "\n".join(textos)
        assert "desconocida" in texto and "costo 100" in texto and "abierta" in texto
        assert "NOMBRE_VECINO_PRIVADO" not in texto and "NOMBRE_REMOTO_PRIVADO" not in texto
        assert "sala None" not in texto and len(cuadros) == 1
        assert (p.acciones, p.reloj.tiempo_actual, p.conocimiento.estado_salas) == antes
    finally:
        esc.cerrar()


def test_z_mapa_desplazamiento_y_quit():
    import pygame
    mapa = [(i, "Visible %s" % i, []) for i in range(35)]
    vista, textos, cuadros = _vista_dialogo_prueba([
        [], [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_END)],
        [pygame.event.Event(pygame.QUIT)]])
    vista.mostrar_mapa(mapa)
    assert "Sala 34: Visible 34" in textos
    assert len(cuadros) == 2 and vista.cerrada


def test_z_entrada_ir_a_reutiliza_parser_sin_ejecutar_viaje():
    import pygame
    from controlador.orden import IR_A
    esc = armar(esqueleto_linea(5))
    try:
        p = esc.partida
        p._explorar_sala(p.mapa.sala(4))
        vista, textos, cuadros = _vista_dialogo_prueba([
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_4, unicode="4")],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]])
        assert vista._pedir_ir_a(p) == Orden(IR_A, 4)
        assert (p.acciones, p.reloj.tiempo_actual, p.jugador.sala.id) == (0, 0, 1)
        assert len(cuadros) == 1
    finally:
        esc.cerrar()


def test_z_entrada_ir_a_no_enumera_desconocidas_y_escape_cancela():
    import pygame
    esc = armar(esqueleto_linea(3))
    try:
        p = esc.partida
        p.mapa.sala(2).nombre = "SECRETO_NO_MOSTRAR"
        antes = (p.acciones, p.reloj.tiempo_actual, list(p.conocimiento.estado_salas))
        vista, textos, cuadros = _vista_dialogo_prueba([
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2, unicode="2"),
             pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]])
        assert vista._pedir_ir_a(p) is None
        assert any("no está explorada o no existe" in texto for texto in textos)
        assert "SECRETO_NO_MOSTRAR" not in "\n".join(textos)
        assert (p.acciones, p.reloj.tiempo_actual, p.conocimiento.estado_salas) == antes
        vista, textos, cuadros = _vista_dialogo_prueba([[pygame.event.Event(pygame.QUIT)]])
        assert vista._pedir_ir_a(p) is None and vista.cerrada
    finally:
        esc.cerrar()


if __name__ == "__main__":
    pruebas = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for nombre, funcion in pruebas:
        funcion()
        print("ok  ", nombre)
    print("\n%d pruebas correctas" % len(pruebas))
