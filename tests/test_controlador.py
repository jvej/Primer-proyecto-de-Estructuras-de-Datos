import os
import re

from controlador.controlador import Controlador
from tests.cripta_de_prueba import armar, entrada, esqueleto_linea
from controlador.orden import (ATACAR, EQUIPAR, ESPERAR, GUARDAR, CARGAR, INV_SIGUIENTE, MOVER, Orden,
                   PERGAMINO, SOLTAR, USAR)
from vista.vista_consola import VistaConsola, interpretar


def vista_guionada(lineas):
    pendientes = iter(lineas)

    def leer(indicacion=""):
        try:
            return next(pendientes)
        except StopIteration:
            raise EOFError

    salida = []
    return VistaConsola(leer, salida.append), salida


def sala_con_objetos(*ids, capacidad=5):
    esc = armar(esqueleto_linea(2), capacidad=capacidad)
    for id_ficha in ids:
        esc.dar(id_ficha)
    return esc


def jugar(esc, lineas):
    vista, salida = vista_guionada(lineas)
    controlador = Controlador(esc.partida, vista)
    controlador.correr_partida()
    return controlador, "\n".join(salida)

def test_interpretar_movimiento_y_acciones():
    esc = armar(esqueleto_linea(2))
    p = esc.partida
    assert interpretar("n", p) == Orden(MOVER, "N")
    assert interpretar("  IR   Sur ", p) == Orden(MOVER, "S")
    assert interpretar("abrir e", p).argumento == "E"
    assert interpretar("x", p) == Orden(ESPERAR)
    assert interpretar("retroceso", p) == Orden(PERGAMINO)
    assert interpretar("usar", p) == Orden("usar", None)
    assert interpretar("soltar 3", p) == Orden(SOLTAR, 2)
    assert interpretar("ordenar peso desc", p) == Orden("inv_ordenar", "peso", True)
    assert interpretar("ordenar valor", p) == Orden("inv_ordenar", "valor", False)
    esc.cerrar()


def test_interpretar_errores_devuelven_texto():
    esc = armar(esqueleto_linea(2))
    p = esc.partida
    for linea in ("", "bailar", "ir", "ir x", "abrir", "soltar abc", "soltar 0", "ordenar color",
                  "ordenar peso mucho", "atacar 1 2"):
        resultado = interpretar(linea, p)
        assert isinstance(resultado, str) and resultado, linea
    esc.cerrar()


def test_atacar_y_recoger_sin_numero():
    esc = armar(esqueleto_linea(2), [entrada(1, enemigos=[("e-1", "ent_esqueleto", 10), ("e-2", "ent_esqueleto", 10)],
                                             objetos=["itm_daga"])])
    p = esc.partida
    assert isinstance(interpretar("atacar", p), str)         
    assert interpretar("atacar 2", p) == Orden(ATACAR, 1)
    assert interpretar("recoger", p) == Orden("recoger", 0)   
    esc.cerrar()

def test_controlador_sin_vista_ejecuta_y_rechaza():
    esc = armar(esqueleto_linea(2))
    c = Controlador(esc.partida)
    assert c.ejecutar(Orden(MOVER, "N")) and esc.partida.reloj.tiempo_actual == 100
    assert not c.ejecutar(Orden(MOVER, "X"))
    assert esc.mensajes()[-1] == "Dirección desconocida."
    assert not c.ejecutar(Orden(SOLTAR, None))
    assert esc.mensajes()[-1] == "El inventario está vacío."
    assert not c.ejecutar(Orden(SOLTAR, 4))
    assert esc.mensajes()[-1] == "No tienes ese objeto."
    assert esc.partida.reloj.tiempo_actual == 100           
    esc.cerrar()


def test_observadores_reciben_ordenes_resueltas_y_solo_las_aceptadas():
    esc = sala_con_objetos("itm_daga", "itm_cota", "itm_pocion")
    c = Controlador(esc.partida)
    vistas = []
    c.agregar_observador(vistas.append)
    c.ejecutar(Orden(INV_SIGUIENTE))                      
    assert c.ejecutar(Orden(SOLTAR, None))                 
    assert not c.ejecutar(Orden(ATACAR, 0))                  
    assert c.ejecutar(Orden(ESPERAR))
    assert vistas == [Orden(SOLTAR, "@2"), Orden(ESPERAR)], vistas
    esc.cerrar()


def test_replay_reproduce_el_mismo_estado():
    def nueva():
        return armar(esqueleto_linea(3), [entrada(2, enemigos=[("e-201", "ent_rata", 12)]),
                                          entrada(1, objetos=["itm_daga", "itm_pergamino"])], capacidad=6)

    esc1 = nueva()
    c1 = Controlador(esc1.partida)
    registro = []
    c1.agregar_observador(registro.append)
    for orden in (Orden("recoger", 0), Orden("recoger", 0), Orden(EQUIPAR, 0), Orden(MOVER, "N"),
                  Orden(PERGAMINO), Orden(ESPERAR)):
        c1.ejecutar(orden)
    esc2 = nueva()
    c2 = Controlador(esc2.partida)
    for orden in registro:
        assert c2.ejecutar(orden)
    p1, p2 = esc1.partida, esc2.partida
    assert (p1.reloj.tiempo_actual, p1.jugador.vida, p1.acciones, p1.jugador.sala.id) == \
           (p2.reloj.tiempo_actual, p2.jugador.vida, p2.acciones, p2.jugador.sala.id)
    assert [o.nombre for o in esc1.inventario.objetos()] == [o.nombre for o in esc2.inventario.objetos()]
    esc1.cerrar()
    esc2.cerrar()


def test_guardar_y_cargar_sin_y_con_persistencia():
    esc = armar(esqueleto_linea(2))
    c = Controlador(esc.partida)
    assert not c.ejecutar(Orden(GUARDAR)) and "no está disponible" in esc.mensajes()[-1]
    assert not c.ejecutar(Orden(CARGAR))

    class Falsa:
        def __init__(self, otra):
            self.otra = otra
            self.guardados = 0

        def guardar(self, partida):
            self.guardados += 1
            return "Partida guardada."

        def cargar(self):
            return self.otra

    otra = armar(esqueleto_linea(2))
    c = Controlador(esc.partida, persistencia=Falsa(otra.partida))
    assert c.ejecutar(Orden(GUARDAR)) and c.persistencia.guardados == 1
    assert c.ejecutar(Orden(CARGAR)) and c.partida is otra.partida
    esc.cerrar()
    otra.cerrar()

def test_partida_completa_hasta_la_victoria():
    salas = esqueleto_linea(4, [(3, 4, {"cerrada": True, "llave": "itm_llave_negra"})])
    esc = armar(salas, [entrada(1, objetos=["itm_llave_negra"])])
    controlador, texto = jugar(esc, ["recoger", "n", "n", "abrir n", "n"])
    assert esc.partida.estado == "victoria"
    assert "¡VICTORIA!" in texto and "Acciones: 5" in texto
    esc.cerrar()


def test_inventario_cursor_equipar_y_vista_ordenada():
    esc = sala_con_objetos("itm_daga", "itm_cota", "itm_pocion")
    controlador, texto = jugar(esc, ["inv", "sig", "equipar", "inv", "ordenar peso desc", "ordenar valor", "salir", "s"])
    assert esc.partida.jugador.armadura.nombre == "Cota"
    assert [o.nombre for o in esc.inventario.objetos()] == ["Cota", "Daga", "Poción menor"]  
    assert "[equipado]" in texto and "ordenado por peso (descendente)" in texto
    bloque = texto.split("ordenado por peso (descendente)")[1].split("Inventario ordenado por valor")[0]
    assert bloque.index("Cota") < bloque.index("Daga") < bloque.index("Poción")
    assert esc.partida.acciones == 1                             
    esc.cerrar()


def test_soltar_sin_numero_actua_sobre_el_cursor():
    esc = sala_con_objetos("itm_daga", "itm_cota")
    controlador, texto = jugar(esc, ["sig", "soltar", "salir", "s"])
    assert [o.nombre for o in esc.inventario.objetos()] == ["Daga"]
    assert [o.nombre for o in esc.partida.objetos_en_sala()] == ["Cota"]
    esc.cerrar()


def test_pergamino_desde_la_consola():
    esc = sala_con_objetos("itm_pergamino")
    controlador, texto = jugar(esc, ["esperar", "retroceso", "salir", "s"])
    assert esc.partida.reloj.tiempo_actual == 0 and esc.partida.acciones == 0
    assert esc.inventario.objetos() == []
    assert "el tiempo vuelve atrás" in texto
    esc.cerrar()


def test_los_comandos_de_consulta_no_cambian_la_partida():
    esc = sala_con_objetos("itm_daga", "itm_cota")
    p = esc.partida
    antes = (p.reloj.tiempo_actual, p.acciones, [o.nombre for o in esc.inventario.objetos()])
    jugar(esc, ["ayuda", "inv", "sig", "ant", "inicio", "ordenar nombre", "ordenar peso desc", "salir", "s"])
    assert (p.reloj.tiempo_actual, p.acciones, [o.nombre for o in esc.inventario.objetos()]) == antes
    esc.cerrar()


def test_salir_pide_confirmacion():
    esc = armar(esqueleto_linea(2))
    controlador, texto = jugar(esc, ["salir", "n", "esperar", "salir", "s"])
    assert controlador.terminado and esc.partida.acciones == 1  
    esc.cerrar()


def test_entrada_cerrada_termina_sin_error():
    esc = armar(esqueleto_linea(2))
    controlador, texto = jugar(esc, [])                          
    assert controlador.terminado
    esc.cerrar()


def test_entrada_no_entendida_no_rompe_y_vuelve_a_preguntar():
    esc = armar(esqueleto_linea(2))
    controlador, texto = jugar(esc, ["bailar", "", "salir", "s"])
    assert "No entiendo 'bailar'" in texto
    esc.cerrar()


def test_sesion_elegir_cripta_jugar_y_no_repetir():
    escenarios = []

    def listar():
        return [{"id": "a", "nombre": "Primera", "salas": 2, "dificultad": 1},
                {"id": "b", "nombre": "Segunda", "salas": 2, "dificultad": 2}]

    def crear(id_cripta):
        assert id_cripta == "b"
        esc = armar(esqueleto_linea(2), [entrada(2, trampas=[("t-1", "trp_mortal")])])
        escenarios.append(esc)
        return esc.partida

    vista, salida = vista_guionada(["9", "2", "n", "n"])           
    controlador = Controlador(vista=vista)
    controlador.correr_sesion(listar, crear)
    texto = "\n".join(salida)
    assert "Opción no válida." in texto and "Segunda" in texto and "DERROTA" in texto
    assert escenarios[0].partida.estado == "derrota"
    escenarios[0].cerrar()


def test_sesion_salir_en_el_menu_de_criptas():
    vista, salida = vista_guionada(["salir"])
    Controlador(vista=vista).correr_sesion(lambda: [{"id": "a", "nombre": "x"}], lambda i: None)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO = ("modelo/juego/partida.py", "modelo/juego/actor.py", "modelo/juego/sala.py", "modelo/juego/mapa.py",
          "modelo/juego/efectos.py", "modelo/juego/registro.py", "modelo/juego/inventario.py",
          "modelo/estructuras/lista_doble.py", "modelo/juego/agenda_eventos.py", "modelo/juego/objetos.py",
          "modelo/juego/combate.py", "modelo/juego/comportamiento.py", "modelo/juego/motor_enemigos.py",
          "modelo/juego/evento.py", "modelo/juego/costos.py", "modelo/juego/azar.py")


def _fuente(nombre):
    ruta = os.path.join(RAIZ, nombre)
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _imports(texto):
    return [m.split(".")[-1] for m in re.findall(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", texto, re.M)]


def test_mvc_el_modelo_no_conoce_vista_ni_controlador():
    for nombre in MODELO:
        texto = _fuente(nombre)
        if texto is None:
            continue
        for modulo in _imports(texto):
            assert modulo not in ("controlador", "vista_base", "vista_consola", "orden"), (nombre, modulo)
        assert "print(" not in texto and "input(" not in texto, nombre


def test_mvc_el_controlador_no_imprime_ni_conoce_vistas_concretas():
    texto = _fuente("controlador/controlador.py")
    assert "print(" not in texto and "input(" not in texto
    for modulo in _imports(texto):
        assert modulo not in ("vista_consola", "vista_base"), modulo


def test_mvc_la_vista_no_modifica_el_modelo_ni_conoce_el_controlador():
    texto = _fuente("vista/vista_consola.py")
    assert "controlador" not in _imports(texto)
    prohibidas = (".mover(", ".abrir(", ".atacar(", ".esperar(", ".recoger(", ".soltar(", ".equipar(",
                  ".usar(", ".usar_pergamino(", ".agregar(", ".quitar(", ".restaurar(", ".siguiente(",
                  ".anterior(", ".ir_al_inicio(", ".cambiar(", ".danar(", ".curar(")
    for llamada in prohibidas:
        assert llamada not in texto, llamada


if __name__ == "__main__":
    pruebas = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for nombre, funcion in pruebas:
        funcion()
        print("ok  ", nombre)
    print("\n%d pruebas correctas" % len(pruebas))