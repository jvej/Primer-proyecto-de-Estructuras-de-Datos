"""Benchmarks independientes de 002, sin archivos de salida ni servicios.

Ejecutar desde la raíz con Python 3.13:
    python -B -m tests.bench_niebla_ir_a

Escenarios deterministas: cuadrículas ponderadas de 10/100/1000 salas, según
el plan interno de 002; no son la cripta oficial de referencia. El extracto
§6.1 fija 5 ms por paso de IR_A, pero no fija aquí un número de salas. Comparar
con 5 ms en estos datos NO certifica cumplimiento del requisito oficial.

Se usan ConocimientoMapa, Registro, Dijkstra y PlanificadorRutas reales. Para
aislar actualización/reversión se prepara un objeto Partida mínimo en memoria
y se invocan sus helpers reales de exploración/observación, sin simular motor,
enemigos ni precarga. El viaje usa una Partida completa con FuenteSimulada de
las pruebas y un planificador instrumentado que delega sin cambiar resultados.

Construcción, reinicios, calentamiento y aserciones quedan fuera del intervalo
medido. Las consultas se cronometran por lotes: su máximo es máximo de LOTE,
no latencia máxima individual. Los otros máximos son de llamadas individuales.
Se conserva GC normal; se incluye sobrecosto de llamadas/bucles Python.
"""

import argparse
import math
import platform
import random
import sys
from time import perf_counter_ns

from controlador.controlador import Controlador
from controlador.orden import IR_A, Orden
from controlador.planificador_rutas import PlanificadorRutas
from modelo.estructuras.dijkstra import dijkstra_acotado
from modelo.juego.conocimiento import ConocimientoMapa, ESTADO_EXPLORADA, PUERTA_ABIERTA
from modelo.juego.partida import Partida
from modelo.juego.registro import Registro
from modelo.juego.sala import Sala
from tests.cripta_de_prueba import armar, esqueleto_linea

LIMITE_PASO_NS = 5_000_000  # Extracto oficial §6.1, solo para cripta de referencia.


class MapaSintetico:
    """Interfaz de Mapa: salas contiguas y búsqueda binaria por ID numérico."""

    def __init__(self, n, semilla):
        self.salas = []
        self.aristas = 0
        self.huella = 0
        for i in range(n):
            sala = Sala(3 * i + 1, "Sala sintética %d" % i)
            sala.indice = i
            self.salas.append(sala)
        ancho = max(1, math.isqrt(n))
        azar = random.Random(semilla)
        for i in range(n):
            if i % ancho != ancho - 1 and i + 1 < n:
                self._conectar(i, "E", i + 1, azar.randint(20, 100))
            if i + ancho < n:
                self._conectar(i, "S", i + ancho, azar.randint(20, 100))

    def _conectar(self, i, direccion, j, costo):
        self.salas[i].conectar(direccion, self.salas[j], costo=costo)
        self.aristas += 1
        self.huella = (self.huella * 131 + i * 17 + j * 7 + costo) % 2_147_483_647

    def sala(self, id_sala):
        bajo, alto = 0, len(self.salas)
        while bajo < alto:
            medio = (bajo + alto) // 2
            if self.salas[medio].id < id_sala:
                bajo = medio + 1
            else:
                alto = medio
        if bajo < len(self.salas) and self.salas[bajo].id == id_sala:
            return self.salas[bajo]
        return None


def conocimiento_completo(mapa):
    c = ConocimientoMapa(len(mapa.salas), mapa.salas, mapa)
    r = Registro()
    for sala in mapa.salas:
        r.cambiar(c.estado_salas, sala.indice, ESTADO_EXPLORADA)
        for direccion, salida in enumerate(sala.salidas):
            if salida is not None:
                r.cambiar(c.memoria_puertas, sala.indice * 4 + direccion, PUERTA_ABIERTA)
    r.cambiar(c, "num_exploradas", len(mapa.salas))
    return c


def transitable_conocida(conocimiento):
    def filtro(salida):
        return (conocimiento.es_explorada(salida.sala_a)
                and conocimiento.es_explorada(salida.sala_b)
                and conocimiento.puerta_recordada_abierta(salida))
    return filtro


def reportar(nombre, n, aristas, tiempos, por_muestra=1, limite=False, detalle=""):
    media = sum(tiempos) / len(tiempos)
    maximo = max(tiempos)
    unidad = "ms/lote" if por_muestra != 1 else "ms/llamada"
    print("%-23s N=%4d E=%4d muestras=%4d ejec/muestra=%7d media=%10.6f max=%10.6f %s %s"
          % (nombre, n, aristas, len(tiempos), por_muestra,
             media / 1_000_000, maximo / 1_000_000, unidad, detalle))
    if por_muestra != 1:
        print("  Amortizado: media %.2f ns/op; máximo promedio de lote %.2f ns/op."
              % (media / por_muestra, maximo / por_muestra))
    if limite:
        print("  Comparación orientativa: máximo %s 5 ms. Referencia oficial NO VALIDADA."
              % ("<" if maximo < LIMITE_PASO_NS else ">="))
    return media, maximo


def medir_consultas(mapa, c, repeticiones, consultas):
    sala = mapa.salas[len(mapa.salas) // 2]
    for nombre, operacion in (("consulta_estado", lambda: c.estado_sala(sala)),
                              ("consulta_puerta", lambda: c.puerta_recordada(sala, 0)),
                              ("consulta_resumen", c.resumen)):
        for _ in range(100):
            operacion()
        tiempos = []
        for _ in range(repeticiones):
            inicio = perf_counter_ns()
            for _ in range(consultas):
                operacion()
            tiempos.append(perf_counter_ns() - inicio)
        reportar(nombre, len(mapa.salas), mapa.aristas, tiempos, consultas)


def medir_actualizacion(mapa, repeticiones, ejecuciones):
    # Solo los tres campos que utilizan los helpers reales de Partida.
    p = object.__new__(Partida)
    p.mapa = mapa
    p.conocimiento = ConocimientoMapa(len(mapa.salas), mapa.salas, mapa)
    p.registro = Registro()
    sala = mapa.salas[len(mapa.salas) // 2]
    grado = sum(1 for salida in sala.salidas if salida is not None)
    actualizar, revertir = [], []
    for vuelta in range(repeticiones * ejecuciones + 1):
        p.registro.abrir_grupo()
        inicio = perf_counter_ns()
        p._explorar_sala(sala)
        for salida in sala.salidas:
            if salida is not None:
                p._recordar_puerta(salida)
        duracion = perf_counter_ns() - inicio
        p.registro.cerrar_grupo()
        assert p.conocimiento.resumen() == (1, grado)
        cambios = p.registro.cambios_registrados()
        inicio = perf_counter_ns()
        p.registro.deshacer_ultimo()
        duracion_reversa = perf_counter_ns() - inicio
        assert p.conocimiento.resumen() == (0, 0)
        assert all(estado == 0 for estado in p.conocimiento.estado_salas)
        assert all(estado == 0 for estado in p.conocimiento.memoria_puertas)
        if vuelta:  # La primera iteración es calentamiento, no una muestra.
            actualizar.append(duracion)
            revertir.append(duracion_reversa)
    detalle = "grado=%d cambios_C1=%d; helpers, no acción completa" % (grado, cambios)
    reportar("explorar_y_observar", len(mapa.salas), mapa.aristas, actualizar, detalle=detalle)
    reportar("revertir_conocimiento", len(mapa.salas), mapa.aristas, revertir, detalle=detalle)


def medir_rutas(mapa, c, repeticiones, ejecuciones):
    n = len(mapa.salas)
    dist, marca = [0] * n, [0] * n
    filtro = transitable_conocida(c)
    origen, destino = mapa.salas[0], mapa.salas[-1]
    token = 0
    for cota in (200, None):
        tiempos = []
        for vuelta in range(repeticiones * ejecuciones + 1):
            token += 1
            inicio = perf_counter_ns()
            dijkstra_acotado(destino, mapa, filtro, cota_rango=cota,
                             token_busqueda=token, arreglo_dist=dist, arreglo_marca=marca)
            duracion = perf_counter_ns() - inicio
            assert marca[destino.indice] == token and dist[destino.indice] == 0
            if vuelta:
                tiempos.append(duracion)
        alcanzadas = sum(1 for m in marca if m == token)
        reportar("dijkstra_acotado" if cota is not None else "dijkstra_completo", n,
                 mapa.aristas, tiempos, detalle="cota=%s alcanzadas=%d" % (cota, alcanzadas))
    planificador = PlanificadorRutas(mapa, c)
    tiempos = []
    for vuelta in range(repeticiones * ejecuciones + 1):
        inicio = perf_counter_ns()
        paso = planificador.siguiente_paso(origen, destino.id)
        duracion = perf_counter_ns() - inicio
        assert paso.estado == "paso" and paso.costo_total == dist[origen.indice]
        if vuelta:
            tiempos.append(duracion)
    return reportar("planificar_IR_A", n, mapa.aristas, tiempos, limite=True)


class PlanificadorMedido(PlanificadorRutas):
    """Instrumentación local: misma implementación, resultados y tokens de C3."""

    def __init__(self, mapa, conocimiento):
        super().__init__(mapa, conocimiento)
        self.tiempos = []

    def siguiente_paso(self, origen, id_destino):
        inicio = perf_counter_ns()
        resultado = super().siguiente_paso(origen, id_destino)
        duracion = perf_counter_ns() - inicio
        self.tiempos.append(duracion)
        return resultado


def medir_recalculo_viaje(n, repeticiones, pasos):
    tiempos = []
    pasos = min(pasos, n - 2)  # Cancelar antes del destino evita el caso llegada.
    for vuelta in range(repeticiones + 1):
        # API simulada en memoria; toda preparación y precarga queda fuera del
        # reloj del planificador. No se mide el viaje completo ni latencia de IO.
        esc = armar(esqueleto_linea(n), semilla=17)
        try:
            p = esc.partida
            for sala in p.mapa.salas:
                p._explorar_sala(sala)
                for salida in sala.salidas:
                    if salida is not None:
                        p._recordar_puerta(salida)
            controlador = Controlador(p)
            medido = PlanificadorMedido(p.mapa, p.conocimiento)
            controlador._planificador = medido  # Solo esta instancia sintética.
            controlador.agregar_observador_viaje(lambda actual: actual.acciones < pasos)
            assert controlador.ejecutar(Orden(IR_A, n))
            assert p.acciones == pasos and p.reloj.tiempo_actual == pasos * 100
            assert len(medido.tiempos) == pasos + 1
            if vuelta:
                tiempos.extend(medido.tiempos[1:])  # Excluir validación preliminar.
        finally:
            esc.cerrar()
    return reportar("recalculo_en_viaje", n, n - 1, tiempos, limite=True,
                    detalle="línea, %d viajes x %d pasos; solo planificación" % (repeticiones, pasos))


def argumentos(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tamanos", nargs="+", type=int, default=[10, 100, 1000])
    parser.add_argument("--semilla", type=int, default=20261110)
    parser.add_argument("--repeticiones", type=int, default=7)
    parser.add_argument("--consultas", type=int, default=1_000_000)
    parser.add_argument("--ejecuciones", type=int, default=20)
    parser.add_argument("--pasos-viaje", type=int, default=8)
    opciones = parser.parse_args(argv)
    if (any(n < 3 for n in opciones.tamanos) or opciones.repeticiones < 2
            or min(opciones.consultas, opciones.ejecuciones, opciones.pasos_viaje) < 1):
        parser.error("tamaños >= 3; repeticiones >= 2; los demás conteos deben ser positivos")
    return opciones


def main(argv=None):
    opciones = argumentos(argv)
    print("CRIPTA 002: escenarios SINTÉTICOS; no certifican la cripta oficial.")
    print("Python %s | %s | semilla=%d repeticiones=%d ejecuciones=%d consultas/lote=%d"
          % (platform.python_version(), platform.platform(), opciones.semilla,
             opciones.repeticiones, opciones.ejecuciones, opciones.consultas))
    print("Tamaños 10/100/1000 del plan interno; límite oficial 5 ms SOLO en referencia.")
    print("Preparación y validaciones excluidas. GC normal; máximo individual salvo lotes de consultas.")
    print("El límite de ciclo de 20 ms con cazadores NO se evalúa en este módulo.")
    resultados = []
    for n in opciones.tamanos:
        mapa = MapaSintetico(n, opciones.semilla)
        copia = MapaSintetico(n, opciones.semilla)
        assert mapa.huella == copia.huella and mapa.aristas == copia.aristas
        del copia
        print("\nEscenario: N=%d E=%d huella=%d" % (n, mapa.aristas, mapa.huella))
        c = conocimiento_completo(mapa)
        medir_consultas(mapa, c, opciones.repeticiones, opciones.consultas)
        medir_actualizacion(mapa, opciones.repeticiones, opciones.ejecuciones)
        resultados.append(medir_rutas(mapa, c, opciones.repeticiones, opciones.ejecuciones))
        medir_recalculo_viaje(n, opciones.repeticiones, opciones.pasos_viaje)
    print("\nFinalizado. Comparaciones sintéticas orientativas; referencia oficial pendiente.")
    print("Integración en main.py --bench pendiente: se conserva intacto por alcance autorizado.")
    return resultados


if __name__ == "__main__":
    main(sys.argv[1:])
