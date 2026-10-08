import random
import time
from cache import Cache

SEMILLA = 42

def generar_accesos(cantidad, azar):
    """80% de los accesos van a 10 ids 'calientes' que van cambiando."""
    accesos = []
    for paso in range(cantidad):
        base = (paso // 500) * 7 % 100
        if azar.random() < 0.8:
            numero = (base + azar.randint(0, 9)) % 100
        else:
            numero = azar.randint(0, 99)
        accesos.append("id_" + str(numero))
    return accesos


def simular(tope, usar_lru, accesos):
    cache = Cache(tope=tope, usar_lru=usar_lru)
    for id_ficha in accesos:
        if cache.obtener(id_ficha) is None:
            cache.poner(id_ficha, id_ficha)  
    return cache.aciertos, cache.fallos


def comparar_politicas():
    azar = random.Random(SEMILLA)
    accesos = generar_accesos(20000, azar)
    print("tope | LRU aciertos % | FIFO aciertos %")
    for tope in [5, 10, 15, 25, 50]:
        a1, f1 = simular(tope, True, accesos)
        a2, f2 = simular(tope, False, accesos)
        print(f"{tope:<4} | {a1 * 100 / (a1 + f1):14.1f} | {a2 * 100 / (a2 + f2):15.1f}")


def medir_tiempos():
    print("\ntope | obtener acierto (us) | obtener fallo (us) | poner con desalojo (us)")
    for tope in [25, 1000, 10000]:
        cache = Cache(tope=tope)
        for i in range(tope):
            cache.poner("id_" + str(i), i)

        rep = 20000
        inicio = time.perf_counter()
        for i in range(rep):
            cache.obtener("id_" + str(i % tope))
        t_acierto = (time.perf_counter() - inicio) / rep * 1000000

        inicio = time.perf_counter()
        for i in range(rep):
            cache.obtener("no_esta_" + str(i))
        t_fallo = (time.perf_counter() - inicio) / rep * 1000000

        inicio = time.perf_counter()
        for i in range(rep):
            cache.poner("nuevo_" + str(i), i)   
        t_poner = (time.perf_counter() - inicio) / rep * 1000000

        print(f"{tope:<4} | {t_acierto:20.3f} | {t_fallo:18.3f} | {t_poner:23.3f}")


if __name__ == "__main__":
    comparar_politicas()
    medir_tiempos()