import copy
import gc
import platform
import sys
import time
import tracemalloc
from dataclasses import dataclass

from tests.cripta_de_prueba import armar, entrada, esqueleto_linea
from controlador.controlador import Controlador
from modelo.juego.mapa_dibujado import IndiceOcupacion
from modelo.juego.objetos import Objeto
from modelo.juego.orden import IR_A, Orden
from modelo.juego.linea_tiempo import K_DEFECTO
from modelo.juego.registro import MAX_ACCIONES, PilaAcotada
from modelo.juego.resumen_historico import inicializar_historia
from modelo.juego.sala import DIRECCIONES
from tests.cripta_de_prueba import CATALOGO

TAMANOS = (20, 200, 1000)
ACTIVAS = 10
CICLOS = 30
SEMILLA = 3
REPETICIONES = 3


class MemoCopias(IndiceOcupacion):
    """Adaptador del AVL propio para la referencia deepcopy, sin tabla hash.

    La referencia B conserva el estado compartido de antes. Sus tiempos ahora
    incluyen este índice O(log n), por lo que no equivalen al memo de biblioteca
    de las mediciones históricas. No interviene en las cargas A de §5.6.
    """

    def get(self, clave, defecto=None):
        i = self._raiz
        while i != -1:
            nodo = self._nodos[i]
            if clave == nodo[0]:
                return nodo[1]
            i = nodo[2 if clave < nodo[0] else 3]
        return defecto

    def __getitem__(self, clave):
        ausente = object()
        valor = self.get(clave, ausente)
        if valor is ausente:
            raise KeyError(clave)
        return valor

    def __setitem__(self, clave, valor):
        self.insertar(clave, valor)


def escenario(n, activas, parte_ii=False):
    contenido = []
    for i in range(2, n + 1):
        tipo = "ent_cazador" if parte_ii else "ent_troll"
        contenido.append(entrada(i, enemigos=[("e-%d" % i, tipo, 20)], objetos=["itm_pocion"]))
    esc = armar(esqueleto_linea(n), contenido, semilla=SEMILLA, capacidad=10)
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
        memo = MemoCopias()
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


def objeto_de_clase(clase):
    for ficha in CATALOGO:
        if ficha["clase"] == clase:
            return Objeto(ficha)
    raise AssertionError("Falta la ficha sintética de " + clase)


def preparar_revision(n, parte_ii):
    esc = escenario(n, ACTIVAS, parte_ii)
    p = esc.partida
    # Preparación sintética fuera del tiempo y anterior al checkpoint cero.
    # Mantiene vivos a los actores durante toda la carga, sin curarlos al medir.
    p.cambiar(p.jugador, "vida_max", 10 ** 9)
    p.cambiar(p.jugador, "vida", p.jugador.vida_max)
    antorcha = objeto_de_clase("antorcha")
    pergamino = objeto_de_clase("pergamino_retroceso")
    p._inv_agregar(antorcha)
    p._inv_agregar(pergamino)
    if parte_ii:
        for sala in p.mapa.salas:
            for salida in sala.salidas:
                if salida is not None and salida.sala_a is sala:
                    p.cambiar(salida, "costo", p.azar.randint(40, 180))
        costos = [s.costo for sala in p.mapa.salas for s in sala.salidas
                  if s is not None]
        if min(costos) == max(costos):
            raise AssertionError("La carga II debe tener costos distintos")
    activos = sum(e.activo for e in p.mapa.enemigos)
    if activos != min(n, ACTIVAS) - 1:
        raise AssertionError("No coincide la cantidad de enemigos activos preparada")
    return esc, Controlador(p), antorcha, pergamino


def huella_revision(p):
    """Datos observables por valor, sin identidades de objetos ni tiempos reales."""
    return (p.acciones, p.reloj.tiempo_actual, p.estado, p.jugador.sala.id,
            p.jugador.vida, p.jugador.antorcha_encendida,
            tuple(p.conocimiento.estado_salas), tuple(p.conocimiento.memoria_puertas),
            p.conocimiento.resumen(),
            tuple((e.id_instancia, e.sala.id, e.vida, e.activo,
                   e.tiempo_siguiente) for e in p.mapa.enemigos),
            tuple((o.id, o.usos) for o in p.inventario),
            p.azar._rng.getstate())


def comprobar_historia(p):
    linea = p.linea_tiempo
    linea.exigir_disponible()
    r = linea.consultar_accion(p.acciones + 1)
    if ((r.acciones, r.reloj, r.sala, r.vida) !=
            (p.acciones, p.reloj.tiempo_actual, p.jugador.sala.id, p.jugador.vida)
            or tuple(r.estado_salas) != tuple(p.conocimiento.estado_salas)
            or tuple(r.memoria_puertas) != tuple(p.conocimiento.memoria_puertas)):
        raise AssertionError("La historia actual no coincide con la partida")


def ejecutar_revision(p, controlador, antorcha, parte_ii, tiempos=None,
                      traza=None):
    pasos_ir_a = 0
    entradas_antorcha = 0
    for numero in range(CICLOS):
        sala = p.jugador.sala
        # Una acción aceptada por muestra: los destinos IR_A son adyacentes,
        # ya explorados por entradas anteriores o por la antorcha real.
        direccion = "N" if numero % 3 != 2 else "S"
        salida = sala.salidas[DIRECCIONES.index(direccion)]
        iluminada = p.jugador.antorcha_encendida
        inicio = time.perf_counter_ns() if tiempos is not None else 0
        if not parte_ii:
            aceptada = p.esperar()  # Carga original de Parte I.
        elif numero == 0:
            aceptada = p.usar(antorcha)
        elif numero % 3 == 1:
            aceptada = p.mover(direccion)
        else:
            if salida is None:
                raise AssertionError("La carga salió del corredor sintético")
            aceptada = controlador.ejecutar(Orden(IR_A, salida.otro_lado(sala).id))
            pasos_ir_a += 1
        if tiempos is not None:
            tiempos.append((time.perf_counter_ns() - inicio) / 1000000)
        if not aceptada or p.acciones != numero + 1 or p.estado != "jugando":
            raise AssertionError("Cada muestra debe completar una acción de juego")
        if parte_ii and iluminada and p.jugador.sala is not sala:
            entradas_antorcha += 1
        if traza is not None:
            traza.append(huella_revision(p))
    return pasos_ir_a, entradas_antorcha


@dataclass(frozen=True)
class ResultadoRevision:
    medio: float
    maximo: float
    deshacer_medio: float
    deshacer_maximo: float
    retenida: float
    pico: float
    inversos: int
    deltas: int
    conocimiento: int
    checkpoints: int
    pasos_ir_a: int
    entradas_antorcha: int


def medir_revision(n, parte_ii, captura):
    tiempos, retrocesos = [], []
    esperada = None
    # Calentamiento y tres repeticiones independientes. Validación fuera del reloj.
    for repeticion in range(REPETICIONES + 1):
        esc, controlador, antorcha, pergamino = preparar_revision(n, parte_ii)
        p = esc.partida
        try:
            if captura:
                inicializar_historia(p, K_DEFECTO)
                p.linea_tiempo.exigir_disponible()
            traza = []
            ejecutar_revision(p, controlador, antorcha, parte_ii,
                              tiempos if repeticion else None, traza)
            if captura:
                comprobar_historia(p)
                traza.append(tuple(p.linea_tiempo.deltas))
            inicio = time.perf_counter_ns()
            if not p.usar_pergamino(pergamino):
                raise AssertionError("El retroceso real debe poder ejecutarse")
            duracion = (time.perf_counter_ns() - inicio) / 1000000
            if repeticion:
                retrocesos.append(duracion)
            if p.acciones != CICLOS - 1:
                raise AssertionError("El pergamino debe retirar una sola acción")
            if captura:
                comprobar_historia(p)
            traza.append(huella_revision(p))
            if esperada is not None and traza != esperada:
                raise AssertionError("Carga no determinista con la misma semilla")
            esperada = traza
        finally:
            esc.cerrar()

    # Memoria en otra partida/pasada; excluye mapa, precarga e inventario inicial.
    # Incluye checkpoint cero, C1, cinco grupos, agenda y demás asignaciones
    # retenidas de la carga; no se presenta como memoria exclusiva de inversos.
    esc, controlador, antorcha, pergamino = preparar_revision(n, parte_ii)
    p = esc.partida
    try:
        gc.collect()
        tracemalloc.start()
        if captura:
            inicializar_historia(p, K_DEFECTO)
            p.linea_tiempo.exigir_disponible()
        pasos, entradas = ejecutar_revision(p, controlador, antorcha, parte_ii)
        gc.collect()
        retenida, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        if huella_revision(p) != esperada[CICLOS - 1]:
            raise AssertionError("La pasada de memoria cambió el resultado cronometrado")
        inversos = p.registro.cambios_registrados()
        deltas = conocimiento = checkpoints = 0
        if captura:
            comprobar_historia(p)
            linea = p.linea_tiempo
            deltas, checkpoints = len(linea.deltas), len(linea.checkpoints)
            conocimiento = sum(d.destino in ("estado_salas", "memoria_puertas")
                               or (d.destino == "partida" and d.campo in
                                   ("num_exploradas", "num_avistadas"))
                               for d in linea.deltas)
            if not conocimiento or not deltas or checkpoints != 1 + CICLOS // K_DEFECTO:
                raise AssertionError("La carga debe capturar conocimiento y checkpoints")
        if parte_ii and (not pasos or not entradas
                         or not p.planificador_cazador._calculos_realizados):
            raise AssertionError("Falta IR_A, exploración iluminada o cálculo del cazador")
        final = huella_revision(p)
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        esc.cerrar()
    return ResultadoRevision(sum(tiempos) / len(tiempos), max(tiempos),
                             sum(retrocesos) / len(retrocesos), max(retrocesos),
                             retenida / 1024, pico / 1024, inversos, deltas,
                             conocimiento, checkpoints, pasos, entradas), final


def bench_revision():
    print("\nRevisión §5.6: misma semilla %d; %d acciones; %d repeticiones; K=%d" %
          (SEMILLA, CICLOS, REPETICIONES, K_DEFECTO))
    print("Parte I = esperas originales; Parte II = cazadores, costos 40..180, antorcha e IR_A.")
    print("Por carga: n-1 enemigos incorporados; %d activos (salas sin jugador)." % (ACTIVAS - 1))
    print("Tiempo: 90 acciones y 3 pergaminos por fila, sin trazador; preparación excluida.")
    print("Memoria: pasada separada, KiB incrementales retenidos/pico de toda la carga;")
    print("incluye historia desde cero en C1, no solo los cinco grupos del pergamino.")
    print("salas | carga       | media ms | max ms | perg media/max ms | retenida/pico KiB"
          " | inversos | deltas/conocim/CP | IR_A/luz")
    for n in TAMANOS:
        sin_captura = None
        for parte_ii, captura, etiqueta in ((False, False, "I original"),
                                           (True, False, "II sin C1"),
                                           (True, True, "II con C1")):
            r, final = medir_revision(n, parte_ii, captura)
            if parte_ii and not captura:
                sin_captura = final
            if captura and final != sin_captura:
                raise AssertionError("Activar C1 cambió el resultado de la carga II")
            print("%5d | %-11s | %8.4f | %7.4f | %8.4f/%8.4f | %10.1f/%10.1f"
                  " | %8d | %6d/%6d/%2d | %3d/%3d" %
                  (n, etiqueta, r.medio, r.maximo, r.deshacer_medio,
                   r.deshacer_maximo, r.retenida, r.pico, r.inversos, r.deltas,
                   r.conocimiento, r.checkpoints, r.pasos_ir_a, r.entradas_antorcha))
    if "pygame" in sys.modules:
        raise AssertionError("El benchmark no debe crear ni importar la vista")
    print("Validado: trazas repetidas idénticas, C1 no altera el resultado, historia actual fiel.")


def main():
    print("Entorno: Python %s | %s" % (platform.python_version(), platform.platform()))
    print("Historial reversible: registro de inversos (A) vs copia completa (B)")
    print("A historial KB = memoria que libera soltar el historial lleno (5 acciones);")
    print("entre paréntesis, cuántos inversos guarda. nan = deepcopy no terminó.")
    print("Referencia B: memo con AVL propio; sus tiempos no equivalen al memo histórico.")
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
    bench_revision()


if __name__ == "__main__":
    main()
