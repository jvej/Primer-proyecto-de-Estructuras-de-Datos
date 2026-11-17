"""Entrada --bench mapa_conocido; escenarios sinteticos de 002."""

from tests.bench_niebla_ir_a import main


def entrada_layout(n):
    """Cuadrícula sintética: solo conocimiento, sin Partida ni contenido remoto."""
    from math import isqrt
    from modelo.juego.mapa_dibujado import SalaMapa, SalidaMapa
    ancho = max(1, isqrt(n))
    salas = []
    for i in range(n):
        salidas = []
        for destino, direccion in ((i - ancho, 'N'), (i + ancho, 'S'),
                                   (i + 1, 'E'), (i - 1, 'O')):
            if not 0 <= destino < n:
                continue
            if direccion == 'E' and i % ancho == ancho - 1:
                continue
            if direccion == 'O' and i % ancho == 0:
                continue
            salidas.append(SalidaMapa(destino, direccion, 1 + i % 7, 'abierta'))
        salas.append(SalaMapa(i + 1, 'Sala sintetica %s' % (i + 1), tuple(salidas)))
    return tuple(salas)


def medir_layout(tamanos=(10, 100, 1000, 5000), repeticiones=5):
    """Mediana sin trazador y pico independiente; misma entrada para alternativas."""
    import gc
    import platform
    import tracemalloc
    from time import perf_counter_ns
    from modelo.estructuras.lista_ordenada import ListaOrdenada
    from modelo.estructuras.ordenamiento import ordenar_merge
    from modelo.juego.mapa_dibujado import calcular_layout, IndiceOcupacion

    print('\nLAYOUT US5: cuadricula sintetica, actual=primera explorada; no certifica SC-001.')
    print('Python %s | %s | mediana de %s muestras; pico separado con tracemalloc' %
          (platform.python_version(), platform.platform(), repeticiones))
    print('K | E | indice | mediana_ms | pico_KiB | candidatos')
    resultados = []
    for n in tamanos:
        entrada = entrada_layout(n)
        e = sum(len(s.salidas) for s in entrada)
        esperado = calcular_layout(entrada, 0)
        for nombre, tipo in (('AVL', IndiceOcupacion), ('ListaOrdenada', ListaOrdenada)):
            assert calcular_layout(entrada, 0, tipo) == esperado
            tiempos = []
            for _ in range(repeticiones):
                inicio = perf_counter_ns()
                resultado = calcular_layout(entrada, 0, tipo)
                tiempos.append((perf_counter_ns() - inicio) / 1_000_000)
            gc.collect()
            tracemalloc.start()
            resultado = calcular_layout(entrada, 0, tipo)
            _, pico = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            mediana = ordenar_merge(tiempos)[len(tiempos) // 2]
            fila = (n, e, nombre, mediana, pico / 1024, resultado.candidatos)
            resultados.append(fila)
            print('%d | %d | %s | %.3f | %.1f | %d' % fila, flush=True)
    return resultados


if __name__ == "__main__":
    resultados_previos = main([])  # No propagar argumentos de main.py.
    if isinstance(resultados_previos, list):
        medir_layout()
