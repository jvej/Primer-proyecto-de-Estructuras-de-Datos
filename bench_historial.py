"""Bench del historial reversible (§4.6, §5.3): python bench_historial.py

Compara la decisión tomada contra la alternativa descartada, medida directamente:

  A. Registro de inversos (registro.py): cada cambio anota la función que lo deshace.
     El costo depende de CUÁNTO CAMBIA en el ciclo, no del tamaño de la cripta.
  B. Copia completa del estado antes de cada acción (copy.deepcopy de mapa, jugador,
     inventario, agenda, reloj y azar). Prohibida por §4.6, pero se mide para justificar
     con números por qué no sirve. (Además no sería correcta: las acciones de la agenda
     son funciones que siguen apuntando al estado original.)

Carga sintética: cripta en línea de N salas, un enemigo guardián con regeneración por
sala y un objeto en el suelo; TODAS las salas incorporadas (el estado crece con N).
Caso típico: solo están activos los enemigos de las primeras ACTIVAS salas (los que el
jugador ya despertó). Peor caso: todos los enemigos activos a la vez. El jugador hace
"esperar" (un ciclo completo de eventos, §5.2).

Mide por tamaño de cripta:
  - tiempo medio de un ciclo con registro (A)
  - tiempo de deshacer un ciclo (A)
  - memoria que retiene el historial con 5 acciones (A)
  - tiempo de UNA copia completa (B) y la memoria de UNA copia (B, x5 para el historial)
"""

import copy
import gc
import sys
import time
import tracemalloc

from cripta_de_prueba import armar, entrada, esqueleto_linea
from registro import MAX_ACCIONES, PilaAcotada

TAMANOS = (20, 200, 1000)
ACTIVAS = 10
CICLOS = 30


def escenario(n, activas):
    contenido = []
    for i in range(2, n + 1):
        contenido.append(entrada(i, enemigos=[("e-%d" % i, "ent_troll", 20)], objetos=["itm_pocion"]))
    esc = armar(esqueleto_linea(n), contenido, semilla=3, capacidad=10)
    partida = esc.partida
    for sala in partida.mapa.salas:              # todo el mapa en memoria
        partida.precarga.asegurar(sala.id)
        partida._incorporar(sala)
        if sala.id <= activas:
            partida._activar_sala(sala)
    return esc


def medir(n, activas):
    esc = escenario(n, activas)
    p = esc.partida

    # A. tiempo de ciclo con registro
    inicio = time.perf_counter()
    for _ in range(CICLOS):
        p.esperar()
    ciclo_ms = (time.perf_counter() - inicio) * 1000 / CICLOS

    # A. deshacer un ciclo
    inicio = time.perf_counter()
    p.registro.deshacer_ultimo()
    p.esperando = True
    deshacer_ms = (time.perf_counter() - inicio) * 1000

    # A. memoria del historial lleno (5 acciones): con historial - sin historial
    tracemalloc.start()                 # mide solo lo asignado desde aquí
    for _ in range(MAX_ACCIONES):
        p.esperar()
    cambios = p.registro.cambios_registrados()
    gc.collect()
    con_historial = tracemalloc.get_traced_memory()[0]
    p.registro._grupos = PilaAcotada(MAX_ACCIONES)      # se suelta el historial
    gc.collect()
    sin_historial = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    memoria_a_kb = (con_historial - sin_historial) / 1024

    # B. una copia completa del estado. La partida y los adaptadores de red/caché no son
    # estado del juego: se le indican a deepcopy como "ya copiados" (su parámetro memo)
    # para que los comparta en vez de intentar copiarlos (tienen hilos y cerrojos).
    estado = (p.mapa, p.jugador, p.inventario, p.agenda, p.reloj, p.azar)
    compartidos = (p, p.precarga, p.resolutor, p.bitacora, p.registro)

    def copiar():
        memo = {}
        for objeto in compartidos:
            memo[id(objeto)] = objeto
        return copy.deepcopy(estado, memo)

    # deepcopy recorre recursivamente salas -> salidas -> salas...: con criptas grandes
    # supera el límite de recursión de Python (otra razón práctica contra B).
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