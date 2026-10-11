"""Mediciones del motor (§5.3, §8): agenda de eventos y ciclo completo entre decisiones.

Uso: python bench_motor.py
La alternativa descartada para la agenda se mide con la misma carga que el heap.
"""

import random
import time

import cripta_de_prueba
from agenda_eventos import AgendaEventos
from cripta_de_prueba import armar, entrada, esqueleto_linea
from evento import Evento


class AgendaListaOrdenada:
    """Alternativa descartada 1: lista ordenada de mayor a menor; el mínimo sale por el final.
    Extraer es O(1), pero cada inserción desplaza elementos: O(n)."""

    def __init__(self):
        self._lista = []
        self._secuencia = 0

    def nueva_secuencia(self):
        self._secuencia += 1
        return self._secuencia

    def agendar(self, evento):
        lo, hi = 0, len(self._lista)
        while lo < hi:                      # búsqueda binaria de la posición
            medio = (lo + hi) // 2
            if evento < self._lista[medio]:
                lo = medio + 1
            else:
                hi = medio
        self._lista.insert(lo, evento)

    def siguiente(self):
        return self._lista.pop() if self._lista else None


class AgendaSinOrden:
    """Alternativa descartada 2: lista sin orden; cada extracción busca el mínimo: O(n)."""

    def __init__(self):
        self._lista = []
        self._secuencia = 0

    def nueva_secuencia(self):
        self._secuencia += 1
        return self._secuencia

    def agendar(self, evento):
        self._lista.append(evento)

    def siguiente(self):
        if not self._lista:
            return None
        menor = 0
        for i in range(1, len(self._lista)):
            if self._lista[i] < self._lista[menor]:
                menor = i
        self._lista[menor], self._lista[-1] = self._lista[-1], self._lista[menor]
        return self._lista.pop()


def medir_agenda(clase, pendientes, pasos):
    """Carga que imita al juego: cada actor tiene UN evento pendiente y, al ejecutarlo, agenda el
    siguiente unas 100 unidades después. Los pendientes quedan repartidos en una ventana corta
    alrededor del reloj, así que cada inserción cae hacia el medio de la agenda."""
    azar = random.Random(1)
    agenda = clase()
    nada = lambda ahora: None
    for _ in range(pendientes):
        agenda.agendar(Evento(azar.randint(0, 200), agenda.nueva_secuencia(), None, nada))
    inicio = time.perf_counter()
    for _ in range(pasos):
        e = agenda.siguiente()
        agenda.agendar(Evento(e.tiempo_siguiente + azar.randint(50, 150), agenda.nueva_secuencia(), None, nada))
    return (time.perf_counter() - inicio) * 1000


def bench_agenda():
    print("Agenda de eventos: 20.000 pasos (extraer el siguiente + agendar su sucesor), en ms")
    print("%-12s %12s %18s %18s" % ("pendientes", "heap (elegido)", "lista ordenada", "lista sin orden"))
    for pendientes in (100, 300, 1000, 3000, 10000, 30000):
        clases = (AgendaEventos, AgendaListaOrdenada) if pendientes > 3000 else (AgendaEventos, AgendaListaOrdenada, AgendaSinOrden)
        fila = [medir_agenda(c, pendientes, 20000) for c in clases] + [float('nan')] * (3 - len(clases))
        print("%-12d %12.1f %18.1f %18.1f" % (pendientes, fila[0], fila[1], fila[2]))


def medir_ciclos(enemigos, ficha, ciclos):
    cripta_de_prueba.CATALOGO.append(ficha)
    contenido = [entrada(1, enemigos=[("e-%04d" % i, ficha["id"], 10) for i in range(enemigos)])]
    datos = {"jugador": {"vida_max": 10 ** 9, "ataque": 6, "defensa": 2, "velocidad": 100}}
    esc = armar(esqueleto_linea(2), contenido, datos=datos, capacidad_bitacora=20)
    p = esc.partida
    tiempos = []
    for _ in range(ciclos):
        inicio = time.perf_counter()
        p.esperar()
        tiempos.append((time.perf_counter() - inicio) * 1000)
    acciones = len(p.agenda)
    esc.cerrar()
    return sum(tiempos) / len(tiempos), max(tiempos), acciones


def bench_ciclo():
    print("\nCiclo entre dos decisiones del jugador (§5.2: debe ser < 20 ms), en ms")
    print("%-52s %8s %8s" % ("carga", "medio", "máximo"))
    rapido = {"id": "ent_bench_rapido", "clase": "enemigo", "nombre": "Esqueleto", "vida_max": 10,
              "ataque": 4, "defensa": 2, "velocidad": 100, "comportamiento": "guardian", "suelta": []}
    lento = dict(rapido, id="ent_bench_lento", velocidad=5)
    for enemigos, ficha, texto in ((300, lento, "300 eventos pendientes, ~15 actúan por ciclo"),
                                   (300, rapido, "300 enemigos atacando a la vez (peor caso)")):
        medio, maximo, _ = medir_ciclos(enemigos, ficha, 50)
        print("%-52s %8.2f %8.2f" % (texto, medio, maximo))


if __name__ == "__main__":
    bench_agenda()
    bench_ciclo()