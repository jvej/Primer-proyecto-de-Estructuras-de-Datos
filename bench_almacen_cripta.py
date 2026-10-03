import os
import time
from almacen_cripta import AlmacenCripta
from ordenamiento import ordenar

RUTA = "bench_cripta.dat"


def contenido_de_prueba(i):
    return {"sala": i,
            "enemigos": [{"instancia": "e-" + str(i), "tipo": "ent_rata_gigante", "vida": 12}],
            "objetos": ["itm_daga_oxidada"],
            "trampas": []}

def limpiar():
    if os.path.exists(RUTA):
        os.remove(RUTA)

def mediana(valores):
    valores = ordenar(valores)
    return valores[len(valores) // 2]

def medir():
    print("salas  | leer una sala (us) | arrancar con todo guardado (ms)")
    for n in [20, 200, 1000, 5000]:
        limpiar()
        a = AlmacenCripta(RUTA, "bench")
        for i in range(n):
            a.guardar_sala(i, contenido_de_prueba(i))

        lecturas = []
        for rep in range(7):
            inicio = time.perf_counter()
            for i in range(200):
                a.leer_sala((i * 7) % n)
            lecturas.append((time.perf_counter() - inicio) / 200 * 1000000)

        arranques = []
        for rep in range(7):
            inicio = time.perf_counter()
            AlmacenCripta(RUTA, "bench")
            arranques.append((time.perf_counter() - inicio) * 1000)

        print(f"{n:<6} | {mediana(lecturas):18.1f} | {mediana(arranques):30.3f}")
    limpiar()

if __name__ == "__main__":
    medir()
    print("\nReferencia del enunciado: cada solicitud de red tarda ~400 ms (400000 us).")