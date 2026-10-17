"""Bench del guardado (§4.10): binario de formato propio vs el MISMO estado en JSON.

Usa el formato actual (versión 2): además de las salas, el bloque general trae la
cripta, sus versiones, el jugador y la lista de órdenes jugadas (con eso se reconstruye
la partida al cargar, ver persistencia_partida.py). Se simula una partida en la que el
jugador hizo unas 3 órdenes por sala conocida.
"""
import json
import os
import time
from modelo.datos.guardado_binario import guardar, cargar_todo, leer_sala, PartidaGuardada, SalaGuardada
from modelo.estructuras.ordenamiento import ordenar

RUTA_BIN = "bench_partida.bin"
RUTA_JSON = "bench_partida.json"


def armar_partida(n):
    p = PartidaGuardada(1250, 42, 27, 3, "cripta-bench", "v1", "cat-bench-1", "Jugador")
    p.inventario = ["itm_daga", "itm_llave_negra"]
    p.solicitudes = 7
    tipos = ("mover N", "recoger 0", "atacar 0", "esperar", "equipar 1", "pergamino")
    for i in range(3 * n):
        p.ordenes.append(tipos[i % len(tipos)])
    for i in range(n):
        s = SalaGuardada(i + 1, rastro=i)
        if i % 3 == 0:
            s.enemigos.append(["e-" + str(i), "ent_rata_gigante", 12, 300 + i])
        if i % 2 == 0:
            s.objetos.append("itm_antorcha")
        s.puertas.append(["N", i % 2])
        s.puertas.append(["E", 1])
        p.salas.append(s)
    return p


def a_json(p):
    salas = []
    for s in p.salas:
        salas.append([s.id, s.rastro, s.enemigos, s.objetos, s.puertas])
    return [p.reloj, p.semilla, p.vida, p.sala_actual, p.inventario, p.id_cripta,
            p.version_cripta, p.version_catalogo, p.nombre, p.ordenes, p.solicitudes, salas]


def mediana(valores):
    valores = ordenar(valores)
    return valores[len(valores) // 2]


def medir(funcion, repeticiones=7):
    tiempos = []
    for i in range(repeticiones):
        inicio = time.perf_counter()
        funcion()
        tiempos.append((time.perf_counter() - inicio) * 1000)
    return mediana(tiempos)


def comparar():
    print("Mismo estado en ambos formatos: salas + bloque general con 3 órdenes por sala.")
    print("salas | bin (KB) | json (KB) | cargar bin (ms) | cargar json (ms) | 1 sala bin (ms) | 1 sala json (ms)")
    for n in [20, 200, 1000, 5000]:
        p = armar_partida(n)
        guardar(RUTA_BIN, p)
        with open(RUTA_JSON, "w") as f:
            json.dump(a_json(p), f)

        kb_bin = os.path.getsize(RUTA_BIN) / 1024
        kb_json = os.path.getsize(RUTA_JSON) / 1024

        def cargar_json():
            with open(RUTA_JSON) as f:
                return json.load(f)

        t_bin = medir(lambda: cargar_todo(RUTA_BIN))
        t_json = medir(cargar_json)
        # en binario se busca en el índice, en JSON hay que cargar todo
        t_una_bin = medir(lambda: leer_sala(RUTA_BIN, n // 2))
        t_una_json = medir(cargar_json)

        print(f"{n:<5} | {kb_bin:8.1f} | {kb_json:9.1f} | {t_bin:15.3f} | {t_json:16.3f} | {t_una_bin:15.4f} | {t_una_json:16.3f}")
    os.remove(RUTA_BIN)
    os.remove(RUTA_JSON)


if __name__ == "__main__":
    comparar()
