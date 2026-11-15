"""
Benchmark de la Capacidad 001: Terreno, cazador e invalidación de rutas.

Cubre:
- T025 / SC-004: Medición de ciclos individuales del motor entre decisiones (< 20 ms).
- T026 / SC-005: Comparación sistemática de cálculo individual vs. cálculo compartido (1, 10, 30, 100 cazadores).
- T027 / SC-006: Comparación de reutilización con invalidación vs. recálculo continuo (puertas estables e inestables).
"""

import math
import random
import time
from typing import List, Tuple

from tests import cripta_de_prueba
from tests.cripta_de_prueba import armar, entrada, esqueleto_linea
from modelo.juego.actor import Enemigo
from modelo.juego.cazador import PlanificadorCazador
from modelo.estructuras.dijkstra import dijkstra_acotado
from modelo.juego.mapa import normalizar_comportamiento
from modelo.juego.sala import DIRECCIONES


def generar_cripta_sintetica(n_salas: int, semilla: int = 42):
    """Genera una topología determinista de salas conectadas en red bidireccional con costos variables."""
    azar = random.Random(semilla)
    salas = []
    lado = max(2, int(math.isqrt(n_salas)))

    for i in range(1, n_salas + 1):
        salidas = {}
        fila = (i - 1) // lado
        col = (i - 1) % lado

        # Norte / Sur
        if fila > 0:
            salidas["S"] = {"sala": i - lado, "costo": azar.choice([50, 100, 150, 200])}
        if (fila + 1) * lado + col < n_salas:
            salidas["N"] = {"sala": i + lado, "costo": azar.choice([50, 100, 150, 200])}

        # Este / Oeste
        if col > 0:
            salidas["O"] = {"sala": i - 1, "costo": azar.choice([50, 100, 150, 200])}
        if col + 1 < lado and i < n_salas:
            salidas["E"] = {"sala": i + 1, "costo": azar.choice([50, 100, 150, 200])}

        salas.append({"id": i, "nombre": f"Sala {i}", "salidas": salidas})
    return salas


def bench_sc004_ciclos_individuales():
    """T025 / SC-004: Medición de cada ciclo completo entre decisiones del jugador con cazadores activos."""
    print("=" * 72)
    print("T025 / SC-004: Medición de ciclos entre decisiones del jugador")
    print("Criterio estricto: tiempo de cada ciclo individual < 20 ms")
    print("=" * 72)

    semilla = 101
    n_salas = 100
    n_cazadores = 30
    n_ciclos = 50
    rango = 600

    salas = generar_cripta_sintetica(n_salas, semilla=semilla)
    contenido = []
    for c_id in range(1, n_cazadores + 1):
        sala_dest = 2 + (c_id % (n_salas - 2))
        contenido.append(entrada(sala_dest, enemigos=[(f"caz-{c_id}", "ent_cazador", 10)]))

    datos = {"jugador": {"vida_max": 10**9, "ataque": 0, "defensa": 10**6, "velocidad": 100}}
    esc = armar(salas, contenido, datos=datos, semilla=semilla, capacidad_bitacora=50)
    p = esc.partida

    # Precargar contenidos sintéticos para todas las salas para aislar el motor
    for s in p.mapa.salas:
        clave = str(s.id)
        if not p.precarga._contenidos.contiene(clave):
            ent = entrada(s.id)
            for c in contenido:
                if c["sala"] == s.id:
                    ent = c
            p.precarga._contenidos.insertar(clave, ent)

    # Incorporar y activar salas con cazadores
    for s in p.mapa.salas:
        p._incorporar(s)

    for enemigo in p.mapa.enemigos:
        enemigo.activo = True
        enemigo.rango = rango

    tiempos_ms = []

    # Medir exclusivamente el ciclo del motor entre decisiones (excluyendo setup, red, GUI)
    for _ in range(n_ciclos):
        t0 = time.perf_counter()
        p.esperar()
        t1 = time.perf_counter()
        duracion_ms = (t1 - t0) * 1000.0
        tiempos_ms.append(duracion_ms)

    esc.cerrar()

    tiempo_maximo_ms = max(tiempos_ms)
    tiempo_medio_ms = sum(tiempos_ms) / len(tiempos_ms)
    tiempos_ordenados = sorted(tiempos_ms)
    p50 = tiempos_ordenados[int(len(tiempos_ordenados) * 0.50)]
    p95 = tiempos_ordenados[int(len(tiempos_ordenados) * 0.95)]
    p99 = tiempos_ordenados[int(len(tiempos_ordenados) * 0.99)]
    ciclos_exceden_20ms = sum(1 for t in tiempos_ms if t >= 20.0)

    print(f"Configuración: {n_salas} salas sintéticas, {n_cazadores} cazadores activos, rango={rango}")
    print(f"Semilla: {semilla} | Ciclos medidos: {len(tiempos_ms)}")
    print(f"Tiempo máximo: {tiempo_maximo_ms:.3f} ms")
    print(f"Tiempo medio:  {tiempo_medio_ms:.3f} ms")
    print(f"Percentiles:   p50={p50:.3f} ms | p95={p95:.3f} ms | p99={p99:.3f} ms")
    print(f"Ciclos que exceden 20 ms: {ciclos_exceden_20ms} de {len(tiempos_ms)}")

    cumple_sc004 = tiempo_maximo_ms < 20.0 and ciclos_exceden_20ms == 0
    print(f"Cumplimiento SC-004 (< 20 ms): {'SI (CUMPLE)' if cumple_sc004 else 'NO (INCUMPLE)'}")
    print()
    return cumple_sc004


def _decidir_individual(cazador, partida, cota_rango):
    """Cálculo individual directo (Dijkstra desde cazador hacia jugador)."""
    if cazador.sala is partida.jugador.sala or cazador.rango <= 0:
        return None, None
    mapa = partida.mapa
    n = len(mapa.salas)
    dist = [0] * n
    marca = [0] * n
    dijkstra_acotado(
        origen=cazador.sala,
        mapa=mapa,
        filtro_salida=lambda s: s.esta_abierta(),
        cota_rango=cota_rango,
        token_busqueda=1,
        arreglo_dist=dist,
        arreglo_marca=marca,
    )
    destino = partida.jugador.sala
    if marca[destino.indice] != 1 or dist[destino.indice] > cazador.rango:
        return None, None

    mejor_vecino = None
    mejor_salida = None
    min_costo = None
    u = cazador.sala
    for s in u.salidas:
        if s is None or not s.esta_abierta():
            continue
        v = s.otro_lado(u)
        if v is None:
            continue
        dist_v = [0] * n
        marca_v = [0] * n
        dijkstra_acotado(
            origen=v,
            mapa=mapa,
            filtro_salida=lambda sal: sal.esta_abierta(),
            cota_rango=cota_rango,
            token_busqueda=1,
            arreglo_dist=dist_v,
            arreglo_marca=marca_v,
        )
        if marca_v[destino.indice] == 1:
            costo_total = s.costo + dist_v[destino.indice]
            if min_costo is None or costo_total < min_costo:
                min_costo = costo_total
                mejor_vecino = v
                mejor_salida = s
            elif costo_total == min_costo and v.id < mejor_vecino.id:
                mejor_vecino = v
                mejor_salida = s
    return mejor_vecino, mejor_salida


def bench_sc005_individual_vs_compartido():
    """T026 / SC-005: Comparación sistemática de cálculo individual vs. compartido."""
    print("=" * 72)
    print("T026 / SC-005: Comparación sistemática Individual vs. Compartido")
    print("Densidades: 1, 10, 30 y 100 cazadores | Rangos: Pequeño (250) vs Grande (1500)")
    print("=" * 72)
    print(f"{'Cazadores':>10} | {'Rango':>8} | {'Individual (ms)':>17} | {'Compartido (ms)':>17} | {'Speedup':>10}")
    print("-" * 72)

    n_salas = 120
    semilla = 42
    salas = generar_cripta_sintetica(n_salas, semilla=semilla)

    for rango_nombre, rango_val in (("Pequeño", 250), ("Grande", 1500)):
        for cant_cazadores in (1, 10, 30, 100):
            azar = random.Random(semilla)
            contenido = []
            for c_id in range(1, cant_cazadores + 1):
                s_id = azar.randint(2, n_salas)
                contenido.append(entrada(s_id, enemigos=[(f"c-{c_id}", "ent_cazador", 10)]))

            esc = armar(salas, contenido, semilla=semilla)
            p = esc.partida

            # Precarga sintética de contenidos
            for s in p.mapa.salas:
                clave = str(s.id)
                if not p.precarga._contenidos.contiene(clave):
                    p.precarga._contenidos.insertar(clave, entrada(s.id))

            for s_id in range(2, n_salas + 1):
                p._incorporar(p.mapa.sala(s_id))

            cazadores = [e for e in p.mapa.enemigos if normalizar_comportamiento(e.comportamiento) == "cazador"]
            for c in cazadores:
                c.activo = True
                c.rango = rango_val

            # Medición cálculo compartido
            planificador = PlanificadorCazador(p.mapa)
            t0 = time.perf_counter()
            for c in cazadores:
                planificador.decidir_movimiento(c, p)
            t_compartido = (time.perf_counter() - t0) * 1000.0

            # Medición cálculo individual
            t0 = time.perf_counter()
            for c in cazadores:
                _decidir_individual(c, p, rango_val)
            t_individual = (time.perf_counter() - t0) * 1000.0

            speedup = t_individual / max(0.001, t_compartido)
            print(f"{cant_cazadores:>10} | {rango_nombre:>8} | {t_individual:>17.2f} | {t_compartido:>17.2f} | {speedup:>9.1f}x")
            esc.cerrar()
    print()


def bench_sc006_reutilizacion_vs_recalculo():
    """T027 / SC-006: Comparación de reutilización con invalidación vs. recálculo continuo."""
    print("=" * 72)
    print("T027 / SC-006: Reutilización con Invalidación vs. Recálculo Continuo")
    print("=" * 72)

    n_salas = 100
    n_cazadores = 20
    n_pasos = 30
    semilla = 77
    salas = generar_cripta_sintetica(n_salas, semilla=semilla)

    contenido = []
    for c_id in range(1, n_cazadores + 1):
        contenido.append(entrada(2 + (c_id % (n_salas - 2)), enemigos=[(f"c-{c_id}", "ent_cazador", 10)]))

    for modo in ("Puertas Estables", "Puertas Inestables"):
        esc = armar(salas, contenido, semilla=semilla)
        p = esc.partida
        for s in p.mapa.salas:
            clave = str(s.id)
            if not p.precarga._contenidos.contiene(clave):
                p.precarga._contenidos.insertar(clave, entrada(s.id))
            p._incorporar(s)

        for e in p.mapa.enemigos:
            e.activo = True
            e.rango = 500

        plan_con_reutilizacion = p.planificador_cazador
        plan_recalculo = PlanificadorCazador(p.mapa)

        t_reutil_total = 0.0
        t_recalc_total = 0.0
        equivalencia_estricta = True

        for paso in range(n_pasos):
            # En modo inestable, mutamos una puerta cada 5 pasos
            if modo == "Puertas Inestables" and paso % 5 == 0:
                salida = p.mapa.salas[1].salidas[0]
                if salida is not None:
                    nuevo_est = "cerrada" if salida.esta_abierta() else "abierta"
                    p.cambiar_estado_puerta(salida, nuevo_est)

            # Recálculo continuo: invalidamos siempre antes de cada consulta
            t0 = time.perf_counter()
            decisiones_recalc = []
            for c in p.mapa.enemigos:
                plan_recalculo.invalidar_todo()
                decisiones_recalc.append(plan_recalculo.decidir_movimiento(c, p))
            t_recalc_total += (time.perf_counter() - t0) * 1000.0

            # Reutilización selectiva con invalidación reactiva
            t0 = time.perf_counter()
            decisiones_reutil = []
            for c in p.mapa.enemigos:
                decisiones_reutil.append(plan_con_reutilizacion.decidir_movimiento(c, p))
            t_reutil_total += (time.perf_counter() - t0) * 1000.0

            # Verificación de equivalencia observable estricta paso a paso
            if decisiones_recalc != decisiones_reutil:
                equivalencia_estricta = False

        print(f"Escenario: {modo}")
        print(f"  Tiempo Recálculo Continuo:     {t_recalc_total:.2f} ms")
        print(f"  Tiempo Reutilización con Inv:  {t_reutil_total:.2f} ms")
        speedup = t_recalc_total / max(0.001, t_reutil_total)
        print(f"  Mejora de rendimiento:        {speedup:.2f}x")
        print(f"  Cálculos realizados:          {plan_con_reutilizacion._calculos_realizados}")
        print(f"  Reutilizaciones efectivas:    {plan_con_reutilizacion._reutilizaciones}")
        print(f"  Equivalencia observable:      {'OK (100% IDENTICAS)' if equivalencia_estricta else 'ERROR: DISCREPANCIA'}")
        print()
        esc.cerrar()


def correr_todos():
    bench_sc004_ciclos_individuales()
    bench_sc005_individual_vs_compartido()
    bench_sc006_reutilizacion_vs_recalculo()


if __name__ == "__main__":
    correr_todos()
