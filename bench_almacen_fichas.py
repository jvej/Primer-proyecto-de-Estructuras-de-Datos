import json
import os
import shutil
import time
from ordenamiento import ordenar
from almacen_fichas import AlmacenFichas

RUTA = "bench_catalogo.dat"
CARPETA = "bench_fichas"


def ficha_de_prueba(i):
    return {"id": "id_" + str(i), "nombre": "Ficha numero " + str(i),
            "vida_max": 10 + i % 50, "ataque": 3, "defensa": 1, "velocidad": 100,
            "comportamiento": "errante", "suelta": ["itm_pocion_menor"]}


def limpiar():
    if os.path.exists(RUTA):
        os.remove(RUTA)
    if os.path.exists(CARPETA):
        shutil.rmtree(CARPETA)


def comparar_lecturas():
    print("n      | indice+seek (us) | un archivo por ficha (us) | por ficha / indice")
    for n in [25, 100, 1000, 5000]:
        limpiar()
        almacen = AlmacenFichas(RUTA, "bench")
        os.makedirs(CARPETA)
        for i in range(n):
            ficha = ficha_de_prueba(i)
            almacen.guardar("id_" + str(i), ficha)
            with open(CARPETA + "/id_" + str(i) + ".json", "w") as f:
                json.dump(ficha, f)

        rep = 2000
        inicio = time.perf_counter()
        for i in range(rep):
            almacen.leer("id_" + str((i * 7) % n))
        t_indice = (time.perf_counter() - inicio) / rep * 1000000

        inicio = time.perf_counter()
        for i in range(rep):
            with open(CARPETA + "/id_" + str((i * 7) % n) + ".json") as f:
                json.load(f)
        t_archivos = (time.perf_counter() - inicio) / rep * 1000000

        print(f"{n:<6} | {t_indice:16.1f} | {t_archivos:25.1f} | {t_archivos / t_indice:18.2f}")
    limpiar()


def medir_arranque():
    print("\nn      | arrancar (reconstruir indice, ms) | guardar una ficha (us)")
    for n in [25, 100, 1000, 5000]:
        limpiar()
        almacen = AlmacenFichas(RUTA, "bench")
        for i in range(n):
            almacen.guardar("id_" + str(i), ficha_de_prueba(i))

        tiempos = []
        for i in range(7):
            inicio = time.perf_counter()
            AlmacenFichas(RUTA, "bench")
            tiempos.append((time.perf_counter() - inicio) * 1000)
        tiempos = ordenar(tiempos)
        t_arranque = tiempos[3]

        inicio = time.perf_counter()
        for i in range(200):
            almacen.guardar("extra_" + str(i), ficha_de_prueba(i))
        t_guardar = (time.perf_counter() - inicio) / 200 * 1000000

        print(f"{n:<6} | {t_arranque:33.3f} | {t_guardar:22.1f}")
    limpiar()

if __name__ == "__main__":
    comparar_lecturas()
    medir_arranque()