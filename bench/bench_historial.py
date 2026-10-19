import copy
import gc
import sys
import time
import tracemalloc

from tests.cripta_de_prueba import armar, entrada, esqueleto_linea
from modelo.juego.registro import MAX_ACCIONES, PilaAcotada

TAMANOS = (20, 200, 1000)
ACTIVAS = 10
CICLOS = 30


def escenario(n, activas):
    contenido = []
    for i in range(2, n + 1):
        contenido.append(entrada(i, enemigos=[("e-%d" % i, "ent_troll", 20)], objetos=["itm_pocion"]))
    esc = armar(esqueleto_linea(n), contenido, semilla=3, capacidad=10)
    partida = esc.partida
    for sala in partida.mapa.salas:             
        partida.precarga.asegurar(sala.id)
        partida._incorporar(sala)
        if sala.id <= activas:
            partida._activar_sala(sala)
    return esc


def medir(n, activas):
    esc = escenario(n, activas)
    p = esc.partida

    inicio = time.perf_counter()
    for _ in range(CICLOS):
        p.esperar()
    ciclo_ms = (time.perf_counter() - inicio) * 1000 / CICLOS

    inicio = time.perf_counter()
    p.registro.deshacer_ultimo()
    p.esperando = True
    deshacer_ms = (time.perf_counter() - inicio) * 1000

    tracemalloc.start()               
    for _ in range(MAX_ACCIONES):
        p.esperar()
    cambios = p.registro.cambios_registrados()
    gc.collect()
    con_historial = tracemalloc.get_traced_memory()[0]
    p.registro._grupos = PilaAcotada(MAX_ACCIONES)      
    gc.collect()
    sin_historial = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    memoria_a_kb = (con_historial - sin_historial) / 1024

    estado = (p.mapa, p.jugador, p.inventario, p.agenda, p.reloj, p.azar)
    compartidos = (p, p.precarga, p.resolutor, p.bitacora, p.registro)

    def copiar():
        memo = {}
        for objeto in compartidos:
            memo[id(objeto)] = objeto
        return copy.deepcopy(estado, memo)

    limite = sys.getrecursionlimit()
    sys.setrecursionlimit(max(limite, 200000))
    try:
        inicio = time.perf_counter()
        copia = copiar()
        copia_ms = (time.perf_counter() - inicio) * 1000
        tracemalloc.start()
        antes = tracemalloc.get_traced_memory()[0]
        copia2 = copiar()
        memoria_b_kb = (tracemalloc.get_traced_memory()[0] - antes) / 1024
        tracemalloc.stop()
        del copia, copia2
    except RecursionError:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        copia_ms = memoria_b_kb = float("nan")
    finally:
        sys.setrecursionlimit(limite)
    eventos = len(p.agenda)
    esc.cerrar()
    return eventos, ciclo_ms, deshacer_ms, memoria_a_kb, cambios, copia_ms, memoria_b_kb


def main():
    print("Historial reversible: registro de inversos (A) vs copia completa (B)")
    print("A historial KB = memoria que libera soltar el historial lleno (5 acciones);")
    print("entre paréntesis, cuántos inversos guarda. nan = deepcopy no terminó.")
    filas = []
    for n in TAMANOS:
        filas.append(("típico", n, ACTIVAS))
    filas.append(("peor caso", 200, 200))
    filas.append(("peor caso", 1000, 1000))
    print("caso      | salas | activos | eventos | A ciclo ms | A deshacer ms | A historial KB (inversos)"
          " | B 1 copia ms | B 1 copia KB | B 5 copias KB")
    for caso, n, activas in filas:
        eventos, ciclo, deshacer, mem_a, cambios, copia_ms, mem_b = medir(n, activas)
        print("%-9s | %5d | %7d | %7d | %10.3f | %13.3f | %14.1f (%5d) | %12.2f | %12.1f | %13.1f" % (
            caso, n, min(n, activas), eventos, ciclo, deshacer, mem_a, cambios, copia_ms, mem_b,
            mem_b * 5))
    print("\nLectura: el costo de A sigue a lo que CAMBIA en el ciclo (enemigos que actúan),")
    print("no al tamaño de la cripta; B sigue a TODO el estado y se pagaría en CADA acción.")


if __name__ == "__main__":
    main()