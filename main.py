"""CRIPTA - punto de entrada del programa.

Uso:
    python main.py                              jugar contra el servicio web
    python main.py --offline paquete/           jugar leyendo el paquete de respuestas
    python main.py --gui                        jugar en ventana (Pygame); también con --offline
    python main.py --replay datos_cripta/partidas/x.log    reproducir sin interacción
    python main.py --bench                      todas las mediciones
    python main.py --bench historial inventario solo esos subsistemas

Opciones:
    --cache-size N    fichas del catálogo en memoria (25 por defecto, §4.4)
    --semilla N       semilla fija (por defecto una nueva en cada partida)
    --nombre TEXTO    nombre del jugador (si no se da, se pregunta)
    --datos CARPETA   dónde se guardan caché, logs, guardados y puntajes (datos_cripta)
    --detalle         con --replay: muestra cada orden reproducida

Arquitectura (§6): aquí solo se ARMAN las piezas. El Modelo (partida.py) no sabe de
red, disco ni interfaz; el Controlador recibe funciones y objetos ya armados; la Vista
de consola o la de Pygame (--gui) solo se crean en el modo interactivo: --replay y
--bench no abren ventana ni importan Pygame.
"""

import argparse
import os
import runpy
import sys
import time

from controlador.aplicacion import CACHE_DEFECTO, CARPETA_DEFECTO, Aplicacion
from controlador.controlador import Controlador
from modelo.juego.errores import ErrorCripta
from modelo.datos.fabrica_fuentes import crear_fuente_datos
from modelo.datos.persistencia_partida import PersistenciaPartida
from controlador.repeticiones import ServicioRepeticiones
from controlador.reproductor import reproducir

CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))

BENCHES = (
    ("agenda", "bench_motor.py"),             
    ("red", "bench_red.py"),              
    ("cache", "bench_cache.py"),              
    ("fichas", "bench_almacen_fichas.py"),    
    ("cripta", "bench_almacen_cripta.py"),     
    ("lista_ordenada", "bench_lista_ordenada.py"),
    ("inventario", "bench_inventario.py"),    
    ("historial", "bench_historial.py"),      
    ("ordenamiento", "bench_ordenamiento.py"),  
    ("guardado", "bench_guardado_binario.py"),  
)


def leer_argumentos(argv):
    parser = argparse.ArgumentParser(prog="main.py", description="Cripta - juego de mazmorra")
    parser.add_argument("--offline", metavar="CARPETA",
                        help="lee las respuestas del paquete en CARPETA en vez de la red")
    parser.add_argument("--replay", metavar="LOG", help="reproduce una partida sin interacción")
    parser.add_argument("--bench", nargs="*", metavar="SUBSISTEMA",
                        help="ejecuta mediciones (todas, o solo las indicadas)")
    parser.add_argument("--cache-size", type=int, default=CACHE_DEFECTO,
                        help="fichas del catálogo en memoria (por defecto %d)" % CACHE_DEFECTO)
    parser.add_argument("--semilla", type=int, help="semilla fija para el azar del juego")
    parser.add_argument("--nombre", help="nombre del jugador")
    parser.add_argument("--datos", default=CARPETA_DEFECTO,
                        help="carpeta de datos generados (por defecto %s)" % CARPETA_DEFECTO)
    parser.add_argument("--gui", action="store_true",
                        help="interfaz gráfica con Pygame en vez de la consola")
    parser.add_argument("--detalle", action="store_true",
                        help="con --replay, muestra cada orden reproducida")
    argumentos = parser.parse_args(argv)
    if argumentos.cache_size < 1:
        parser.error("--cache-size debe ser al menos 1")
    return argumentos

def correr_benches(pedidos):
    nombres = []
    for nombre, _archivo in BENCHES:
        nombres.append(nombre)
    for pedido in pedidos:
        if pedido not in nombres:
            print("Subsistema desconocido: %s. Disponibles: %s" % (pedido, ", ".join(nombres)))
            return 2
    fallidos = 0
    for nombre, archivo in BENCHES:
        if len(pedidos) > 0 and nombre not in pedidos:
            continue
        print("\n" + "#" * 72)
        print("# BENCH %s (%s)" % (nombre, archivo))
        print("#" * 72)
        inicio = time.perf_counter()
        try:
            runpy.run_path(os.path.join(CARPETA_PROYECTO, "bench", archivo), run_name="__main__")
        except Exception as error:        
            fallidos += 1
            print("ERROR en %s: %s: %s" % (archivo, type(error).__name__, error))
        print("[%s: %.1f s]" % (nombre, time.perf_counter() - inicio))
    return 1 if fallidos > 0 else 0

def correr_replay(argumentos):
    try:
        fuente, presupuesto = crear_fuente_datos(argumentos.offline is not None, argumentos.offline)
    except ValueError as error:
        print(error)
        return 2
    resultado = reproducir(argumentos.replay, fuente, presupuesto, argumentos.datos,
                           argumentos.cache_size, argumentos.detalle)
    print(resultado.texto())
    return 0 if resultado.reproducido else 1


def crear_vista(argumentos):
    """Solo el modo interactivo crea una vista. Pygame se importa únicamente con --gui."""
    if argumentos.gui:
        try:
            import pygame  
        except ImportError:
            print("Falta Pygame. Instálalo con:  python -m pip install pygame")
            return None
        try:
            from vista.vista_pygame import VistaPygame
        except ImportError as error:
            print("No se pudo abrir la vista gráfica: %s" % error)
            return None
        return VistaPygame()
    from vista.vista_consola import VistaConsola
    return VistaConsola()


def correr_interactivo(argumentos):
    try:
        fuente, presupuesto = crear_fuente_datos(argumentos.offline is not None, argumentos.offline)
    except ValueError as error:
        print(error)
        return 2
    vista = crear_vista(argumentos)
    if vista is None:
        return 2
    print("CRIPTA. Escribe 'ayuda' durante la partida para ver los comandos.")
    if argumentos.offline:
        print("Modo sin conexión: datos de %s" % argumentos.offline)
    nombre = argumentos.nombre if argumentos.nombre else vista.pedir_nombre()

    aplicacion = Aplicacion(fuente, presupuesto, argumentos.datos, argumentos.cache_size,
                            argumentos.semilla, nombre)
    repeticiones = ServicioRepeticiones(
        aplicacion, lambda: crear_fuente_datos(argumentos.offline is not None, argumentos.offline),
        argumentos.datos, argumentos.cache_size)
    controlador = Controlador(vista=vista, persistencia=PersistenciaPartida(aplicacion),
                              puntajes=aplicacion.puntajes, al_terminar=aplicacion.al_terminar,
                              repeticiones=repeticiones)
    controlador.agregar_observador(aplicacion.registrar_orden)      
    try:
        controlador.correr_sesion(aplicacion.listar_criptas, aplicacion.crear_partida)
    except KeyboardInterrupt:
        print("\nInterrumpido.")
    except ErrorCripta as error:
        print("Error: %s" % error)
    finally:
        partida = aplicacion.partida
        ruta_log = aplicacion.cerrar()
        if partida is not None and partida.estado == "jugando":
            if ruta_log is not None:
                print("La partida quedó registrada en %s (puede reproducirse con --replay)."
                      % ruta_log)
            print(aplicacion.reporte())
        if argumentos.gui:
            vista.cerrar()
    print("Hasta pronto.")
    return 0


def main(argv=None):
    argumentos = leer_argumentos(sys.argv[1:] if argv is None else argv)
    if argumentos.bench is not None:
        return correr_benches(argumentos.bench)
    if argumentos.replay:
        return correr_replay(argumentos)
    return correr_interactivo(argumentos)


if __name__ == "__main__":
    sys.exit(main())