"""Pruebas de la parte de aplicación de Axel: log y replay (§4.11), puntajes (§2.12),
guardar/cargar (§4.10, camino A), azar reversible y pila acotada del retroceso (§4.6),
y la corrección del combate con arma/armadura. Ejecutar: python -m tests.test_replay_puntajes

Usan el paquete --offline sintético de crear_paquete_prueba.py en una carpeta temporal:
no tocan la red ni la carpeta datos_cripta/ del proyecto.
"""
import os
import shutil
import tempfile

from tests import crear_paquete_prueba
from controlador.aplicacion import Aplicacion
from modelo.datos.bitacora_partida import ErrorLog, leer_log
from controlador.controlador import Controlador
from tests.cripta_de_prueba import armar, entrada, esqueleto_linea
from modelo.datos.fabrica_fuentes import crear_fuente_datos
from modelo.datos.guardado_binario import cargar_general
from main import main as main_programa
from controlador.orden import ATACAR, EQUIPAR, ESPERAR, MOVER, Orden, PERGAMINO, RECOGER
from modelo.datos.persistencia_partida import ErrorCarga, PersistenciaPartida
from modelo.datos.puntajes import TablaPuntajes
from modelo.juego.registro import PilaAcotada, Registro
from controlador.reproductor import reproducir

JUGADAS = [Orden(RECOGER, 0), Orden(RECOGER, 0), Orden(EQUIPAR, 0), Orden(MOVER, "N"),
           Orden(ATACAR, 0), Orden(ATACAR, 0), Orden(PERGAMINO), Orden(ATACAR, 0), Orden(ESPERAR)]


class Entorno:
    """Carpeta temporal con un paquete offline y una carpeta de datos."""

    def __init__(self):
        self.base = tempfile.mkdtemp(prefix="cripta_test_")
        self.paquete = crear_paquete_prueba.crear(os.path.join(self.base, "paquete"))
        self.datos = os.path.join(self.base, "datos")

    def aplicacion(self, **opciones):
        fuente, presupuesto = crear_fuente_datos(True, self.paquete)
        return Aplicacion(fuente, presupuesto, self.datos, **opciones)

    def jugar(self, ordenes, semilla=7):
        app = self.aplicacion(semilla=semilla, nombre="Prueba")
        partida = app.crear_partida(crear_paquete_prueba.ID)
        controlador = Controlador(partida, persistencia=PersistenciaPartida(app),
                                  al_terminar=app.al_terminar)
        controlador.agregar_observador(app.registrar_orden)
        for orden in ordenes:
            controlador.ejecutar(orden)
        return app, controlador

    def cambiar_version_publicada(self, version):
        carpeta = os.path.join(self.paquete, "criptas", crear_paquete_prueba.ID)
        for nombre in ("general.json", "version.json"):
            ruta = os.path.join(carpeta, nombre)
            with open(ruta, encoding="utf-8") as f:
                texto = f.read()
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(texto.replace('"%s"' % crear_paquete_prueba.VERSION, '"%s"' % version))

    def borrar(self):
        shutil.rmtree(self.base, ignore_errors=True)


def foto(partida):
    inventario = []
    for objeto in partida.inventario.objetos():
        inventario.append(objeto.nombre)
    return (partida.reloj.tiempo_actual, partida.jugador.vida, partida.jugador.sala.id,
            partida.acciones, partida.derrotados, partida.estado, inventario,
            partida.bitacora.ultimos())


# ------------------------------------------------------------ correcciones del modelo
def test_combate_suma_arma_y_armadura():
    esc = armar(esqueleto_linea(2), [entrada(1, enemigos=[("e-1", "ent_esqueleto", 10)])], capacidad=6)
    p = esc.partida
    daga = esc.dar("itm_daga")
    p.equipar(daga)
    vida_antes = p.mapa.enemigos[0].vida
    p.atacar(0)
    dano = vida_antes - p.mapa.enemigos[0].vida
    # ataque 6 + daga 3 + randint(0..4) - defensa 2  ->  entre 7 y 11 (sin la daga sería 4..8)
    assert 7 <= dano <= 11, dano
    esc.cerrar()


def test_pila_acotada_descarta_lo_mas_antiguo():
    pila = PilaAcotada(3)
    for i in range(5):
        pila.apilar(i)
    assert len(pila) == 3 and pila.elementos() == [2, 3, 4]
    assert pila.desapilar() == 4 and pila.desapilar() == 3 and pila.desapilar() == 2
    registro = Registro()
    for i in range(7):
        registro.abrir_grupo()
        registro.cerrar_grupo()
    assert registro.acciones_deshacibles() == 5


def test_el_pergamino_restaura_tambien_el_azar():
    esc = armar(esqueleto_linea(2), [entrada(1, enemigos=[("e-1", "ent_troll", 20)],
                                             objetos=["itm_pergamino"])], capacidad=6)
    p = esc.partida
    p.recoger(0)
    vida = p.mapa.enemigos[0].vida
    p.atacar(0)
    primer_golpe = vida - p.mapa.enemigos[0].vida
    vida_jugador = p.jugador.vida
    assert p.usar_pergamino()
    p.atacar(0)
    assert vida - p.mapa.enemigos[0].vida == primer_golpe          # misma tirada
    assert p.jugador.vida == vida_jugador                          # el contraataque también
    esc.cerrar()


# ------------------------------------------------------------------ log y replay
def test_el_log_tiene_encabezado_y_las_ordenes_aceptadas():
    entorno = Entorno()
    app, controlador = entorno.jugar(JUGADAS + [Orden(ATACAR, 5)])     # la última se rechaza
    ruta = app.cerrar()
    encabezado, ordenes = leer_log(ruta)
    assert encabezado.id_cripta == crear_paquete_prueba.ID
    assert encabezado.version_cripta == crear_paquete_prueba.VERSION
    assert encabezado.version_catalogo == crear_paquete_prueba.VERSION_CATALOGO
    assert encabezado.semilla == 7 and encabezado.jugador == "Prueba"
    leidas = []
    while not ordenes.vacia():
        leidas.append(ordenes.sacar())
    assert leidas == JUGADAS, leidas                                # incluye el pergamino
    entorno.borrar()


def test_replay_reproduce_exactamente_la_partida():
    entorno = Entorno()
    app, controlador = entorno.jugar(JUGADAS)
    esperado = foto(controlador.partida)
    ruta = app.cerrar()
    fuente, presupuesto = crear_fuente_datos(True, entorno.paquete)
    resultado = reproducir(ruta, fuente, presupuesto, entorno.datos)
    assert resultado.reproducido and resultado.fiel, resultado.texto()
    assert foto(resultado.partida) == esperado
    entorno.borrar()


def test_replay_con_version_nueva_usa_la_copia_local_o_se_niega():
    entorno = Entorno()
    app, controlador = entorno.jugar(JUGADAS)
    esperado = foto(controlador.partida)
    ruta = app.cerrar()
    entorno.cambiar_version_publicada("otra")
    fuente, presupuesto = crear_fuente_datos(True, entorno.paquete)
    resultado = reproducir(ruta, fuente, presupuesto, entorno.datos)
    assert resultado.reproducido and "copia local" in resultado.texto()
    assert foto(resultado.partida) == esperado
    # sin copia local: no se reproduce
    shutil.rmtree(os.path.join(entorno.datos, "criptas"))
    fuente, presupuesto = crear_fuente_datos(True, entorno.paquete)
    resultado = reproducir(ruta, fuente, presupuesto, entorno.datos)
    assert not resultado.reproducido and resultado.partida is None
    assert "NO SE PUEDE GARANTIZAR" in resultado.texto()
    entorno.borrar()


def test_replay_detecta_divergencia_y_logs_danados():
    entorno = Entorno()
    app, controlador = entorno.jugar(JUGADAS[:4])
    ruta = app.cerrar()
    with open(ruta, "a", encoding="utf-8") as f:
        f.write("atacar 7\n")                       # no hay 8 enemigos: el original no fue así
    fuente, presupuesto = crear_fuente_datos(True, entorno.paquete)
    resultado = reproducir(ruta, fuente, presupuesto, entorno.datos)
    assert not resultado.reproducido and "DIVERGENCIA en la orden 5" in resultado.texto()
    malo = os.path.join(entorno.base, "malo.log")
    with open(malo, "w", encoding="utf-8") as f:
        f.write("hola\n")
    try:
        leer_log(malo)
        assert False, "debió rechazar el log"
    except ErrorLog:
        pass
    entorno.borrar()


# ------------------------------------------------------------------ puntajes
def test_puntajes_se_registran_y_se_ordenan():
    entorno = Entorno()
    tabla = TablaPuntajes(os.path.join(entorno.base, "puntajes.txt"))

    class P:
        def __init__(self, estado, tiempo, acciones):
            self.id_cripta, self.version_cripta = "c", "v"
            self.estado, self.acciones, self.derrotados = estado, acciones, 0

            class R:
                pass
            self.reloj = R()
            self.reloj.tiempo_actual = tiempo

    tabla.registrar(P("derrota", 100, 3), "Ana")
    tabla.registrar(P("victoria", 900, 20), "Beto")
    tabla.registrar(P("victoria", 500, 30), "Cata")
    tabla.registrar(P("victoria", 500, 10), "Dani")
    with open(tabla.ruta, "a", encoding="utf-8") as f:
        f.write("línea\tdañada\n")
    nombres = []
    for r in tabla.listar():
        nombres.append(r.nombre)
    assert nombres == ["Dani", "Cata", "Beto", "Ana"], nombres
    entorno.borrar()


def test_ganar_registra_puntaje_y_cierra_el_log():
    entorno = Entorno()
    # mismas 8 primeras jugadas; luego cota, 4 salas al norte, llave, abrir y salir
    llegar = JUGADAS[:8] + [Orden(RECOGER, 0)] + [Orden(MOVER, "N")] * 4 + \
        [Orden(RECOGER, 0), Orden(MOVER, "N"), Orden("abrir", "N"), Orden(MOVER, "N")]
    app, controlador = entorno.jugar(llegar, semilla=7)
    partida = controlador.partida
    assert partida.estado == "victoria", foto(partida)
    texto = app.al_terminar(partida)
    assert "tabla de puntajes" in texto and app.log is None
    mejor = app.puntajes.listar()[0]
    assert (mejor.resultado, mejor.nombre, mejor.acciones) == ("victoria", "Prueba", partida.acciones)
    app.cerrar()
    entorno.borrar()


# ------------------------------------------------------------------ guardar y cargar
def test_guardar_y_cargar_reconstruye_la_misma_partida():
    entorno = Entorno()
    app, controlador = entorno.jugar(JUGADAS)
    esperado = foto(controlador.partida)
    app_persistencia = PersistenciaPartida(app)
    mensaje = app_persistencia.guardar(controlador.partida)
    assert "Partida guardada" in mensaje
    general = cargar_general(app_persistencia.ruta)
    assert general.id_cripta == crear_paquete_prueba.ID and general.semilla == 7
    assert len(general.ordenes) == len(JUGADAS)
    app.cerrar()

    otra = entorno.aplicacion(nombre="Prueba")
    otra.crear_partida(crear_paquete_prueba.ID)                    # se está jugando otra cosa
    cargada = PersistenciaPartida(otra).cargar()
    obtenido = foto(cargada)
    assert obtenido[:7] == esperado[:7], (obtenido, esperado)
    # se puede seguir jugando y el log nuevo empieza con las órdenes ya jugadas
    Controlador(cargada).ejecutar(Orden(ESPERAR))
    ruta = otra.cerrar()
    _encabezado, ordenes = leer_log(ruta)
    assert len(ordenes) == len(JUGADAS)          # ESPERAR no pasó por el observador aquí
    entorno.borrar()


def test_cargar_con_otra_version_falla_sin_romper_la_partida_actual():
    entorno = Entorno()
    app, controlador = entorno.jugar(JUGADAS[:4])
    PersistenciaPartida(app).guardar(controlador.partida)
    app.cerrar()
    entorno.cambiar_version_publicada("otra")
    otra = entorno.aplicacion()
    actual = otra.crear_partida(crear_paquete_prueba.ID)
    try:
        PersistenciaPartida(otra).cargar()
        assert False, "debió fallar"
    except ErrorCarga as error:
        assert "versión" in str(error)
    assert otra.partida is actual and otra.ejecutor is not None
    assert Controlador(actual).ejecutar(Orden(ESPERAR))           # la partida actual sigue viva
    otra.cerrar()
    entorno.borrar()


def test_cargar_sin_archivo_devuelve_none():
    entorno = Entorno()
    app = entorno.aplicacion()
    assert PersistenciaPartida(app, os.path.join(entorno.base, "no_existe.bin")).cargar() is None
    entorno.borrar()


# ------------------------------------------------------------------ main
def test_main_sin_vista_en_replay_y_bench():
    entorno = Entorno()
    assert main_programa(["--bench", "no_existe"]) == 2
    assert main_programa(["--replay", os.path.join(entorno.base, "nada.log"),
                          "--offline", entorno.paquete, "--datos", entorno.datos]) == 1
    app, controlador = entorno.jugar(JUGADAS)
    ruta = app.cerrar()
    assert main_programa(["--replay", ruta, "--offline", entorno.paquete,
                          "--datos", entorno.datos]) == 0
    entorno.borrar()


if __name__ == "__main__":
    pruebas = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for nombre, funcion in pruebas:
        funcion()
        print("ok  ", nombre)
    print("\n%d pruebas correctas" % len(pruebas))