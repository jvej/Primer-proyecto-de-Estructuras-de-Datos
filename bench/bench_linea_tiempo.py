"""SC-001..005: consultas equivalentes sobre una traza C1 real y determinista.

Adaptadores síncronos en memoria: leen exclusivamente las respuestas del
generador, incluido su catálogo. No hay solicitudes HTTP, hilos ni vista.
Las únicas copias completas son de ProyeccionHistorica, nunca de Partida.
"""

from dataclasses import dataclass, fields, is_dataclass, replace
import gc
import platform
import time
import tracemalloc

from bench.generador_criptas import generar_cripta
from modelo.datos.esqueleto import Esqueleto
from modelo.estructuras.ordenamiento import ordenar, ordenar_merge
from modelo.juego.bitacora_pantalla import BitacoraPantalla
from modelo.juego.inventario import Inventario
from modelo.juego.linea_tiempo import (
    ArregloContiguo, DeltaHistorico, FronteraHistorica, GrupoHistorico,
    LineaTiempo, PuntoControl,
)
from modelo.juego.objetos import Objeto
from modelo.juego.partida import Partida
from modelo.juego.resumen_historico import (
    ActorHistorico, BaseActor, BaseObjeto, BaseSala, ObjetoHistorico,
    SalaHistorica, aplicar_delta, deshacer_delta, inicializar_historia,
)
from modelo.juego.sala import DIRECCIONES


SEMILLA = 20261113
VALORES_K = (10, 50, 200)
REPETICIONES = 3


class ContenidoSintetico:
    def __init__(self, datos):
        self.entradas = datos["contenido"]["contenido"]

    def contenido_de(self, sala):
        for entrada in self.entradas:
            if entrada["sala"] == sala:
                return entrada
        raise ValueError("Sala ausente del contenido generado")

    def asegurar(self, sala):
        self.contenido_de(sala)

    iniciar = asegurar
    al_entrar = asegurar


class CatalogoSintetico:
    def __init__(self, datos):
        self.fichas = datos["catalogo"]["entidades"]

    def obtener(self, identidad):
        for ficha in self.fichas:
            if ficha["id"] == identidad:
                return ficha
        raise ValueError("Ficha ausente del catálogo generado")


def crear_partida(salas=16, capacidad=None):
    datos = generar_cripta(numero_salas=salas, semilla=SEMILLA,
                           cadena_llaves=1, rango_costos=(80, 120))
    esqueleto = Esqueleto()
    for pagina in datos["paginas"]:
        esqueleto.agregar_pagina(pagina)
    inventario = Inventario(datos["general"]["inventario_max"]
                            if capacidad is None else capacidad, ordenar)
    partida = Partida(datos["general"], esqueleto, ContenidoSintetico(datos),
                      CatalogoSintetico(datos), inventario,
                      BitacoraPantalla(20), SEMILLA)
    partida.iniciar()
    return partida


def objetivos_consulta(n):
    candidatos = (0, 1, 2, 9, 10, 11, 49, 50, 51, 199, 200, 201,
                  n // 4, n // 2, 3 * n // 4, n - 1, n)
    objetivos = []
    for b in candidatos:
        if 0 <= b <= n and b not in objetivos:
            objetivos.append(b)
    return tuple(objetivos)


@dataclass
class Carga:
    semilla: int
    aceptadas: int
    salas: int
    caso: str
    inicial: object
    deltas: tuple
    grupos: tuple
    fronteras: tuple
    objetivos: tuple
    esperados: tuple


def crear_carga(acciones=5000, salas=16, caso="mixto"):
    if acciones < 1 or salas < 4 or caso not in ("mixto", "seguro"):
        raise ValueError("Carga inválida")
    p = crear_partida(salas)
    inicializar_historia(p, acciones + 1)
    linea = p.linea_tiempo
    linea.exigir_disponible()
    inicial = linea.proyeccion.copiar()
    objetivos = objetivos_consulta(acciones)
    esperados = [None] * len(objetivos)

    def observar(b):
        if b in objetivos:
            esperados[objetivos.index(b)] = linea.proyeccion.resumir()

    observar(0)
    objeto = p.objetos_en_sala()[0]
    # Las direcciones/ids/costos se descubren del mapa generado.
    origen = p.jugador.sala
    ida = next(i for i, salida in enumerate(origen.salidas)
               if salida is not None and salida.esta_abierta())
    destino = origen.salidas[ida].otro_lado(origen)
    vuelta = next(i for i, salida in enumerate(destino.salidas)
                  if salida is not None and salida.otro_lado(destino) is origen)
    for numero in range(acciones):
        paso = numero % 8
        if caso == "mixto" and paso == 0:
            aceptada = p.recoger(p.objetos_en_sala().index(objeto))
        elif caso == "mixto" and paso == 1:
            aceptada = p.soltar(objeto)
        elif caso == "mixto" and paso == 2:
            aceptada = p.mover(DIRECCIONES[ida])
        elif caso == "mixto" and paso == 4:
            aceptada = p.mover(DIRECCIONES[vuelta])
        else:
            if caso == "mixto" and paso == 3:
                # Evento real dentro de la espera: modifica una estadística.
                p.programar(p.reloj.tiempo_actual + 1,
                            lambda t: p.cambiar(p.jugador, "ataque",
                                               p.jugador.ataque + 1))
            aceptada = p.esperar()
        if not aceptada or p.acciones != numero + 1:
            raise AssertionError("La carga debe contener solo acciones aceptadas")
        if caso == "mixto":
            # C1 exterior, sin grupo: efecto persistente en la frontera actual.
            p.cambiar(p.jugador, "antorcha_encendida", numero % 2 == 0)
        linea.exigir_disponible()
        observar(numero + 1)
    return Carga(SEMILLA, p.acciones, salas, caso, inicial,
                 tuple(linea.deltas), tuple(linea.grupos),
                 tuple(linea.fronteras), objetivos, tuple(esperados))


@dataclass
class Variante:
    nombre: str
    k: int | None
    linea: object
    fotos: object = None


def _directorio(elementos):
    resultado = ArregloContiguo()
    for elemento in elementos:
        resultado.agregar(elemento)
    return resultado


def preparar_variante(carga, k=None, modo="adelante", deltas=None, inicial=None):
    """Preparación independiente del tiempo de consulta; reserva real del modelo.

    Se reproducen datos normalizados de C1, sin ejecutar órdenes ni inversos
    del motor. Los checkpoints caen en cursor_fin, antes de los externos.
    """
    reloj = [0]
    linea = LineaTiempo(carga.aceptadas + 1 if k is None else k,
                         lambda: reloj[0])
    linea.iniciar((carga.inicial if inicial is None else inicial).copiar())
    linea.deltas = _directorio(carga.deltas if deltas is None else deltas)
    linea.grupos = _directorio(replace(g) for g in carga.grupos)
    linea.fronteras = _directorio(replace(f) for f in carga.fronteras)
    fotos = _llenar_proyecciones(linea, carga, k, modo)
    reloj[0] = linea.proyeccion.reloj
    nombre = ("desde actual" if modo == "atras" else
              "foto por accion" if modo == "fotos" else
              "sin checkpoints" if k is None else f"K={k}")
    return Variante(nombre, k, linea, fotos)


def _llenar_proyecciones(linea, carga, k, modo, fotos=None):
    if modo == "fotos":
        if fotos is None:
            fotos = ArregloContiguo()
        fotos.agregar(linea.proyeccion.copiar())
    cursor = 0
    for b in range(1, carga.aceptadas + 1):
        fin = linea.grupos[b - 1].cursor_fin
        while cursor < fin:
            aplicar_delta(linea.proyeccion, linea.deltas[cursor])
            cursor += 1
        linea.proyeccion.reloj = carga.fronteras[b].reloj
        if k is not None and b % k == 0:
            linea.checkpoints.agregar(PuntoControl(
                b, linea.proyeccion.reloj, cursor, linea.proyeccion.copiar()))
        # Externos posteriores al cierre, que pertenecen a la frontera b.
        limite = linea.cursor if b == carga.aceptadas else linea.fronteras[b].cursor
        while cursor < limite:
            aplicar_delta(linea.proyeccion, linea.deltas[cursor])
            cursor += 1
        if fotos is not None:
            fotos.agregar(linea.proyeccion.copiar())
    return fotos


def consultar(variante, b):
    linea = variante.linea
    if variante.nombre == "foto por accion":
        return variante.fotos[b].copiar().resumir()
    if variante.nombre != "desde actual":
        return linea.consultar_accion(b + 1)
    copia = linea.proyeccion.copiar()
    cursor = linea.cursor if b == len(linea.grupos) else linea.fronteras[b].cursor
    for i in range(linea.cursor - 1, cursor - 1, -1):
        deshacer_delta(copia, linea.deltas[i])
    copia.reloj = linea.fronteras[b].reloj
    return copia.resumir()


def _validar(carga, variante):
    for b, esperado in zip(carga.objetivos, carga.esperados):
        if consultar(variante, b) != esperado:
            raise AssertionError(f"Resumen diferente: {variante.nombre}, frontera {b}")
        if variante.nombre not in ("desde actual", "foto por accion"):
            if variante.linea.consultar_t(esperado.reloj) != esperado:
                raise AssertionError(f"Consulta temporal diferente: {variante.nombre}, {b}")
    return len(carga.objetivos)


def validar_variantes(carga):
    for k, modo in ((10, "adelante"), (50, "adelante"), (200, "adelante"),
                    (None, "adelante"), (None, "atras"), (None, "fotos")):
        _validar(carga, preparar_variante(carga, k, modo))


def estadisticas(muestras):
    """Máximo y mediana mediante el ordenamiento propio del proyecto."""
    valores = ordenar(muestras)
    if not valores:
        raise ValueError("Se necesita al menos una muestra")
    medio = len(valores) // 2
    mediana = (valores[medio] if len(valores) % 2 else
               (valores[medio - 1] + valores[medio]) / 2)
    return valores[-1], mediana


@dataclass(frozen=True)
class ComponenteMemoria:
    nombre: str
    retenida: int
    pico: int


def _bases_de(carga):
    bases = []

    def visitar(valor):
        if isinstance(valor, (BaseActor, BaseObjeto, BaseSala)):
            if not any(b is valor for b in bases):
                bases.append(valor)
        elif isinstance(valor, (ActorHistorico, ObjetoHistorico, SalaHistorica)):
            visitar(valor.base)

    visitar(carga.inicial.jugador)
    for valor in (*carga.inicial.objetos, *carga.inicial.actores, *carga.inicial.salas):
        visitar(valor)
    for delta in carga.deltas:
        visitar(delta.anterior)
        visitar(delta.nuevo)
    return bases


def _valor_nuevo(valor):
    # Materialización independiente: también cuenta los escalares retenidos
    # que pertenecían a la traza fuente. Los enteros pequeños son compartidos
    # por Python y, correctamente, no agregan otra asignación.
    if type(valor) is str:
        return valor.encode("utf-8").decode("utf-8")
    if type(valor) is int:
        return int(str(valor))
    if isinstance(valor, tuple):
        return tuple(_valor_nuevo(v) for v in valor)
    return valor


def _materializador_escalares(carga):
    """Conservar el aliasing de enteros/textos del dueño real, sin tabla hash.

    Orden y binaria propios sobre identidades. La tabla de correspondencias
    pertenece al instrumento (se reserva antes de tracemalloc), mientras los
    valores clonados pertenecen a los componentes que los retienen. Evita
    cobrar una cadena ASIGNAR o un mismo número de grupo por cada delta.
    """
    pares = []

    def visitar(valor):
        if type(valor) in (int, str):
            pares.append((id(valor), valor))
        elif is_dataclass(valor):
            for campo in fields(valor):
                visitar(getattr(valor, campo.name))
        elif isinstance(valor, (list, tuple)):
            for dato in valor:
                visitar(dato)

    for valor in (carga.inicial, carga.deltas, carga.grupos, carga.fronteras):
        visitar(valor)
    unicos = []
    for par in ordenar_merge(pares, clave=lambda p: p[0]):
        if not unicos or unicos[-1][0] != par[0]:
            unicos.append(par)
    copias = [None] * len(unicos)

    def copiar(valor):
        if type(valor) not in (int, str):
            if isinstance(valor, tuple):
                return tuple(copiar(v) for v in valor)
            return valor
        identidad = id(valor)
        izquierda, derecha = 0, len(unicos)
        while izquierda < derecha:
            medio = (izquierda + derecha) // 2
            if unicos[medio][0] < identidad:
                izquierda = medio + 1
            else:
                derecha = medio
        if izquierda == len(unicos) or unicos[izquierda][0] != identidad:
            raise AssertionError("Escalar no inventariado")
        if copias[izquierda] is None:
            copias[izquierda] = _valor_nuevo(valor)
        return copias[izquierda]

    return copiar


def medir_memoria(carga, k, modo):
    """Asignaciones reales, sin sumar sizeof ni contar dos veces bases.

    Materializa un dueño independiente en cuatro etapas. El pico de cada
    componente es el incremento máximo durante SU construcción (no es
    aditivo); el pico global es el máximo simultáneo. Directorios incluye
    capacidad ociosa, grupos, fronteras y administración de LineaTiempo.
    Checkpoints incluye checkpoint 0 y la proyección actual de trabajo.
    En la referencia, incluye además las fotos completas por acción.
    """
    originales = _bases_de(carga)
    copiar_escalar = _materializador_escalares(carga)
    gc.collect()
    tracemalloc.start()
    componentes = []
    pico_global = 0

    def etapa(nombre, construir):
        nonlocal pico_global
        gc.collect()
        antes = tracemalloc.get_traced_memory()[0]
        tracemalloc.reset_peak()
        valor = construir()
        gc.collect()
        despues, pico = tracemalloc.get_traced_memory()
        pico_global = max(pico_global, pico)
        componentes.append(ComponenteMemoria(nombre, max(0, despues - antes),
                                              max(0, pico - antes)))
        return valor

    try:
        bases = etapa("bases", lambda: [type(b)(*(copiar_escalar(getattr(b, f.name))
                                                 for f in fields(b)))
                                        for b in originales])

        def rebasar(valor):
            if isinstance(valor, (BaseActor, BaseObjeto, BaseSala)):
                for i, base in enumerate(originales):
                    if base is valor:
                        return bases[i]
                raise AssertionError("Base sin contabilizar")
            if isinstance(valor, (ActorHistorico, ObjetoHistorico, SalaHistorica)):
                return type(valor)(*(rebasar(getattr(valor, f.name)) for f in fields(valor)))
            if isinstance(valor, list):
                return [rebasar(v) for v in valor]
            if isinstance(valor, tuple):
                return tuple(rebasar(v) for v in valor)
            return copiar_escalar(valor)

        # El arreglo propietario de deltas también conserva reserva geométrica.
        def construir_deltas():
            return _directorio(DeltaHistorico(*(rebasar(getattr(d, f.name))
                                                for f in fields(d)))
                               for d in carga.deltas)

        deltas = etapa("deltas", construir_deltas)

        def construir_directorios():
            linea = LineaTiempo(carga.aceptadas + 1 if k is None else k,
                                 lambda: carga.fronteras[-1].reloj)
            linea.deltas = deltas
            linea.grupos = _directorio(GrupoHistorico(*(copiar_escalar(getattr(g, f.name))
                                                         for f in fields(g)))
                                        for g in carga.grupos)
            linea.fronteras = _directorio(FronteraHistorica(*(copiar_escalar(getattr(g, f.name))
                                                               for f in fields(g)))
                                          for g in carga.fronteras)
            # Reservar exactamente como agregar en el modelo, sin conservar
            # una lista auxiliar de referencias ni reducirla al recortar.
            for _ in range(1 + (carga.aceptadas // k if k is not None else 0)):
                linea.checkpoints.agregar(None)
            linea.checkpoints.truncar(0)
            fotos = ArregloContiguo() if modo == "fotos" else None
            if fotos is not None:
                for _ in range(carga.aceptadas + 1):
                    fotos.agregar(None)
                fotos.truncar(0)
            return linea, fotos

        linea, fotos = etapa("directorios", construir_directorios)

        def construir_fotos():
            # Base inicial/current se cuenta aquí; nunca se copia el motor.
            from modelo.juego.resumen_historico import ProyeccionHistorica
            linea.proyeccion = ProyeccionHistorica(*(
                rebasar(getattr(carga.inicial, f.name)) for f in fields(carga.inicial)))
            linea.checkpoints.agregar(PuntoControl(0, 0, 0, linea.proyeccion.copiar()))
            return _llenar_proyecciones(linea, carga, k, modo, fotos)

        fotos = etapa("checkpoints", construir_fotos)
        reserva = (linea.deltas.capacidad + linea.grupos.capacidad
                   + linea.fronteras.capacidad + linea.checkpoints.capacidad
                   + (0 if fotos is None else fotos.capacidad))
        return tuple(componentes), max(pico_global, sum(c.retenida for c in componentes)), reserva
    finally:
        tracemalloc.stop()


@dataclass(frozen=True)
class Muestra:
    total_ms: float
    fases_ms: tuple
    grupos: int
    externos: int
    selector: str


@dataclass
class Resultado:
    nombre: str
    k: int | None
    equivalente: bool
    consultas_validadas: int
    preparacion_ms: float
    muestras: tuple
    memoria: tuple
    pico: int
    reserva: int
    checkpoints: int

    @property
    def retenida(self):
        return sum(c.retenida for c in self.memoria)

    @property
    def maximo_ms(self):
        return estadisticas([m.total_ms for m in self.muestras])[0]

    @property
    def mediana_ms(self):
        return estadisticas([m.total_ms for m in self.muestras])[1]

    @property
    def max_grupos(self):
        return estadisticas([m.grupos for m in self.muestras])[0]

    @property
    def max_externos(self):
        return estadisticas([m.externos for m in self.muestras])[0]


def _seleccionar(variante, b, por_t):
    """Mismos cortes del modelo; instrumentación fuera de la consulta pública."""
    linea = variante.linea
    frontera = linea.fronteras[b]
    reloj = frontera.reloj
    if variante.nombre == "foto por accion":
        return variante.fotos[b], 0, 0, reloj
    limite = linea.cursor if b == len(linea.grupos) else frontera.cursor
    if variante.nombre == "desde actual":
        return linea.proyeccion, limite, linea.cursor, reloj
    if not por_t:
        checkpoint = linea.checkpoints[b // linea.checkpoint_cada]
        return checkpoint.proyeccion, checkpoint.cursor, limite, reloj
    izquierda, derecha = 0, len(linea.checkpoints)
    while izquierda < derecha:
        medio = (izquierda + derecha) // 2
        if linea.checkpoints[medio].reloj <= reloj:
            izquierda = medio + 1
        else:
            derecha = medio
    checkpoint = linea.checkpoints[izquierda - 1]
    limite = linea.cursor
    for numero in range(checkpoint.acciones_completadas,
                        min(len(linea.grupos), checkpoint.acciones_completadas
                            + linea.checkpoint_cada)):
        if linea.fronteras[numero].reloj >= reloj:
            limite = linea.grupos[numero].cursor_inicio
            break
    cursor = checkpoint.cursor
    while cursor < limite and linea.deltas[cursor].instante <= reloj:
        cursor += 1
    return checkpoint.proyeccion, checkpoint.cursor, cursor, reloj


def medir_consulta(variante, b, esperado, por_t):
    inicio = time.perf_counter_ns()
    if por_t and variante.nombre not in ("desde actual", "foto por accion"):
        resumen = variante.linea.consultar_t(esperado.reloj)
    else:
        resumen = consultar(variante, b)
    total = (time.perf_counter_ns() - inicio) / 1e6
    if resumen != esperado:
        raise AssertionError("La consulta medida cambió el resumen")
    # Segunda pasada para fases. No se presentan como partes exactas de la
    # muestra pública anterior: contienen sus propias lecturas del reloj.
    inicio = time.perf_counter_ns()
    base, inicio_delta, fin_delta, reloj = _seleccionar(variante, b, por_t)
    seleccion = time.perf_counter_ns()
    copia = base.copiar()
    copiado = time.perf_counter_ns()
    grupos = externos = 0
    ultimo = None
    atras = variante.nombre == "desde actual"
    indices = (range(fin_delta - 1, inicio_delta - 1, -1) if atras
               else range(inicio_delta, fin_delta))
    for i in indices:
        delta = variante.linea.deltas[i]
        if delta.grupo is None:
            externos += 1
        elif delta.grupo != ultimo:
            grupos += 1
            ultimo = delta.grupo
        if atras:
            deshacer_delta(copia, delta)
        else:
            aplicar_delta(copia, delta)
    copia.reloj = reloj
    aplicado = time.perf_counter_ns()
    resumen_fases = copia.resumir()
    final = time.perf_counter_ns()
    if resumen_fases != esperado:
        raise AssertionError("Las fases instrumentadas no equivalen a la API pública")
    return Muestra(total, ((seleccion - inicio) / 1e6, (copiado - seleccion) / 1e6,
                           (aplicado - copiado) / 1e6, (final - aplicado) / 1e6),
                   grupos, externos, "t" if por_t else "#k")


def ejecutar_matriz(carga, repeticiones=REPETICIONES):
    if repeticiones < 1:
        raise ValueError("Se necesita al menos una repetición")
    variantes = []
    preparaciones = []
    for k, modo in ((10, "adelante"), (50, "adelante"), (200, "adelante"),
                    (None, "adelante"), (None, "atras"), (None, "fotos")):
        inicio = time.perf_counter_ns()
        variantes.append(preparar_variante(carga, k, modo))
        preparaciones.append((time.perf_counter_ns() - inicio) / 1e6)
    # Ninguna muestra se mide antes de validar TODAS las alternativas.
    validadas = [_validar(carga, variante) for variante in variantes]
    muestras = [[] for _ in variantes]
    for repeticion in range(repeticiones):
        indices = (range(len(variantes)) if repeticion % 2 == 0
                   else range(len(variantes) - 1, -1, -1))
        for i in indices:
            for j, (b, esperado) in enumerate(zip(carga.objetivos, carga.esperados)):
                muestras[i].append(medir_consulta(variantes[i], b, esperado, j % 2 == 0))
    resultados = []
    for i, variante in enumerate(variantes):
        modo = ("atras" if variante.nombre == "desde actual" else
                "fotos" if variante.fotos is not None else "adelante")
        componentes, pico, reserva = medir_memoria(carga, variante.k, modo)
        resultados.append(Resultado(variante.nombre, variante.k, True, validadas[i],
                                    preparaciones[i], tuple(muestras[i]), componentes,
                                    pico, reserva, len(variante.linea.checkpoints)))
    return resultados


@dataclass
class Recorte:
    longitud: int
    grupos: int
    muestras_ms: tuple
    prefijo_visitado: int
    visitados: int
    persistentes: int
    checkpoints_liberados: int
    bytes_liberados: int
    reserva_antes: int
    reserva_despues: int
    equivalente: bool

    @property
    def mediana_ms(self):
        return estadisticas(self.muestras_ms)[1]


def _recortar(linea, cantidad):
    visitados = prefijo = 0
    for _ in range(cantidad):
        ultimo = linea.grupos[len(linea.grupos) - 1]
        reloj = linea.fronteras[ultimo.numero - 1].reloj
        linea.recortar(ultimo.identidad, reloj)
        visitados += linea.metricas.cambios_visitados_en_recorte
        prefijo += linea.metricas.prefijo_visitado
    return visitados, prefijo


def _reserva(linea):
    return (linea.deltas.capacidad, linea.grupos.capacidad,
            linea.fronteras.capacidad, linea.checkpoints.capacidad)


def _validar_recorte(carga, linea, cantidad):
    frontera = carga.aceptadas - cantidad
    inicio = carga.grupos[frontera].cursor_inicio
    esperado = carga.inicial.copiar()
    for delta in carga.deltas[:inicio]:
        aplicar_delta(esperado, delta)
    persistentes = 0
    for delta in carga.deltas[inicio:]:
        if not delta.reversible:
            aplicar_delta(esperado, delta)
            persistentes += 1
    esperado.reloj = carga.fronteras[frontera].reloj
    if (linea.proyeccion.resumir() != esperado.resumir()
            or linea.consultar_accion(frontera + 1) != esperado.resumir()):
        raise AssertionError("El recorte perdió reversibles o persistentes")
    for delta in linea.deltas:
        if delta.instante > esperado.reloj:
            raise AssertionError("Persistente sin reubicar")
    for i in range(len(linea.checkpoints), linea.checkpoints.capacidad):
        if linea.checkpoints._datos[i] is not None:
            raise AssertionError("El directorio retiene un checkpoint retirado")
    return persistentes


def medir_recortes(longitudes=(200, 2000, 5000), repeticiones=7):
    """Mismo sufijo de 5 acciones: longitudes múltiplos de 8 y K=50.

    Cada muestra comienza con una historia nueva, fuera del cronómetro.
    Incluye la liberación por referencias de las fotos descartadas. Una
    ejecución adicional con tracemalloc mide la memoria que libera el sufijo;
    no se cronometra. La validación del oráculo puede recorrer el prefijo y
    se hace exclusivamente FUERA del intervalo medido.
    """
    filas = []
    for n in longitudes:
        if n % 8 or n % 50 or n < 200:
            raise ValueError("El prefijo debe preservar sufijo y cruzar checkpoint")
        carga = crear_carga(n, salas=16)
        for cantidad in range(1, 6):
            muestras = []
            for _ in range(repeticiones):
                linea = preparar_variante(carga, 50).linea
                antes = len(linea.checkpoints)
                reserva_antes = _reserva(linea)
                inicio = time.perf_counter_ns()
                visitados, prefijo = _recortar(linea, cantidad)
                muestras.append((time.perf_counter_ns() - inicio) / 1e6)
                liberados = antes - len(linea.checkpoints)
                persistentes = _validar_recorte(carga, linea, cantidad)
                if prefijo != 0 or reserva_antes != _reserva(linea):
                    raise AssertionError("El recorte visitó o copió el prefijo")
            gc.collect()
            tracemalloc.start()
            try:
                medida = preparar_variante(carga, 50).linea
                gc.collect()
                retenida_antes = tracemalloc.get_traced_memory()[0]
                _recortar(medida, cantidad)
                gc.collect()
                memoria_liberada = retenida_antes - tracemalloc.get_traced_memory()[0]
            finally:
                tracemalloc.stop()
            filas.append(Recorte(n, cantidad, tuple(muestras), prefijo, visitados,
                                persistentes, liberados, memoria_liberada,
                                sum(reserva_antes), sum(_reserva(linea)), True))
    # Los contadores deben depender únicamente del sufijo, también con externos.
    for i, fila in enumerate(filas):
        if fila.visitados != filas[i % 5].visitados:
            raise AssertionError("El trabajo de recorte crece con el prefijo")
    return filas


@dataclass
class SobrecostoC1:
    tamano: int
    sin_muestras_us: tuple
    con_muestras_us: tuple
    deltas: int
    equivalente: bool

    @property
    def sin_c1_us(self):
        return estadisticas(self.sin_muestras_us)[1]

    @property
    def con_c1_us(self):
        return estadisticas(self.con_muestras_us)[1]

    @property
    def extra_us(self):
        return self.con_c1_us - self.sin_c1_us


def _inventario_integrado(n, captura, ciclos):
    p = crear_partida(capacidad=n)
    ficha = p.resolutor.obtener(p.objetos_en_sala()[0].id)
    objetos = [Objeto(ficha) for _ in range(n)]
    for objeto in objetos:
        p._inv_agregar(objeto)
    if captura:
        # No hay checkpoints periódicos durante la muestra: aislar captura C1
        # integrada, incluido el ensamblado de grupos de una acción real.
        inicializar_historia(p, ciclos + 1)
        p.linea_tiempo.exigir_disponible()
    return p, objetos


def _ciclo_inv(p, objeto):
    def efecto():
        p._inv_al_frente(objeto)
        p._inv_quitar(objeto)
        p._inv_agregar(objeto)
    p._accion(100, efecto)


def _firma_inv(p, objetos):
    return (p.acciones, p.reloj.tiempo_actual, p.estado,
            tuple(objetos.index(o) for o in p.inventario.objetos()),
            tuple(o.usos for o in p.inventario.objetos()),
            p.registro.cambios_registrados(), tuple(p.bitacora.ultimos()))


def medir_c1(tamanos=(10, 100, 1000), ciclos=100, repeticiones=5):
    filas = []
    for n in tamanos:
        # Comprobar equivalencia antes de medir cualquiera de las dos variantes.
        sin, a = _inventario_integrado(n, False, ciclos)
        con, b = _inventario_integrado(n, True, ciclos)
        _ciclo_inv(sin, a[-1])
        _ciclo_inv(con, b[-1])
        if _firma_inv(sin, a) != _firma_inv(con, b):
            raise AssertionError("C1 altera las operaciones integradas")
        muestras = [[], []]
        for repeticion in range(repeticiones):
            for indice in ((0, 1) if repeticion % 2 == 0 else (1, 0)):
                p, objetos = _inventario_integrado(n, bool(indice), ciclos)
                gc.collect()
                inicio = time.perf_counter_ns()
                for _ in range(ciclos):
                    _ciclo_inv(p, objetos[-1])
                muestras[indice].append((time.perf_counter_ns() - inicio) / 1000 / ciclos)
                firma = _firma_inv(p, objetos)
                if indice == 0:
                    firma_sin = firma
                else:
                    firma_con = firma
                    p.linea_tiempo.exigir_disponible()
                    deltas = len(p.linea_tiempo.deltas)
                    resumen = p.linea_tiempo.consultar_accion(p.acciones + 1)
                    tokens = tuple(p.registro.token_de(o) for o in p.inventario.objetos())
                    if tuple(o.token for o in resumen.inventario) != tokens:
                        raise AssertionError("C1 no refleja el inventario vivo")
            if firma_sin != firma_con:
                raise AssertionError("C1 cambia el resultado medido")
        filas.append(SobrecostoC1(n, tuple(muestras[0]), tuple(muestras[1]), deltas, True))
    return filas


def _texto_muestras(muestras):
    return ",".join(f"{valor:.4f}" for valor in muestras)


def imprimir_resultados(carga, resultados):
    print(f"Carga {carga.caso}: salas={carga.salas}; aceptadas={carga.aceptadas}; "
          f"deltas={len(carga.deltas)}; externos="
          f"{sum(d.grupo is None for d in carga.deltas)}; "
          f"bases={len(_bases_de(carga))}")
    print("Objetivos (acciones completadas): " + ",".join(str(b) for b in carga.objetivos))
    print("variante | max/med ms | retenida/pico KiB | checkpoints | max grupos/externos | prep ms | reserva slots")
    for r in resultados:
        print(f"{r.nombre} | {r.maximo_ms:.4f}/{r.mediana_ms:.4f} | "
              f"{r.retenida / 1024:.1f}/{r.pico / 1024:.1f} | {r.checkpoints} | "
              f"{r.max_grupos}/{r.max_externos} | {r.preparacion_ms:.2f} | {r.reserva}")
        print(f"  equivalencia=SI ({r.consultas_validadas} objetivos por #k y t); "
              f"muestras={len(r.muestras)}; total_ms=["
              + _texto_muestras([m.total_ms for m in r.muestras]) + "]")
        fases = []
        for indice, nombre in enumerate(("seleccion", "copia", "aplicacion", "resumen")):
            maximo, mediana = estadisticas([m.fases_ms[indice] for m in r.muestras])
            fases.append(f"{nombre}={maximo:.4f}/{mediana:.4f}")
        print("  fases max/med ms (segunda pasada, igual numero de muestras): " + "; ".join(fases))
        print("  memoria retenida/pico incremental KiB: " + "; ".join(
            f"{c.nombre}={c.retenida / 1024:.1f}/{c.pico / 1024:.1f}" for c in r.memoria))


def main():
    print("Linea de tiempo: semilla=20261113; sin HTTP ni vista.")
    print(f"Equipo: {platform.processor()}; {platform.platform()}; Python {platform.python_version()}.")
    print("Consulta publica completa: #k y t alternados; 3 repeticiones, orden de variantes alternado.")
    print("Preparacion excluida; sin tracemalloc durante tiempos. Fases en segunda pasada.")
    print("Memoria: propietario materializado con aliasing de escalares/bases conservado; incluye reserva.")
    print("Picos por componente incrementales, no sumables; pico global simultaneo.")
    print("Checkpoints incluye foto 0 y proyeccion actual. Referencia por accion conserva tambien la traza comun.")
    inicio = time.perf_counter_ns()
    carga = crear_carga()
    print(f"Generacion/captura de carga (excluida): {(time.perf_counter_ns() - inicio) / 1e6:.2f} ms.")
    segura = crear_carga(5000, caso="seguro")
    validar_variantes(segura)
    print(f"Carga segura adicional: {segura.aceptadas} aceptadas, {len(segura.deltas)} deltas; "
          "seis variantes equivalentes antes de medir la carga mixta.")
    resultados = ejecutar_matriz(carga)
    imprimir_resultados(carga, resultados)
    print("Crecimiento de memoria con K=50 (misma carga mixta, variando A o S):")
    print("acciones | salas | deltas | retenida/pico KiB | bases;deltas;directorios;checkpoints KiB | reserva slots")
    for acciones, salas in ((2500, 16), (5000, 64)):
        otra = crear_carga(acciones, salas)
        componentes, pico, reserva = medir_memoria(otra, 50, "adelante")
        print(f"{acciones} | {salas} | {len(otra.deltas)} | "
              f"{sum(c.retenida for c in componentes) / 1024:.1f}/{pico / 1024:.1f} | "
              + ";".join(f"{c.retenida / 1024:.1f}" for c in componentes)
              + f" | {reserva}")
    print("Recorte K=50: sufijo fijo, persistentes y liberacion de checkpoints incluidos.")
    print("N | grupos | max/med ms | visitados/prefijo | persistentes | cp liberados | bytes liberados | reserva antes/despues | muestras ms")
    for fila in medir_recortes():
        maximo, mediana = estadisticas(fila.muestras_ms)
        print(f"{fila.longitud} | {fila.grupos} | {maximo:.4f}/{mediana:.4f} | "
              f"{fila.visitados}/{fila.prefijo_visitado} | {fila.persistentes} | "
              f"{fila.checkpoints_liberados} | {fila.bytes_liberados} | "
              f"{fila.reserva_antes}/{fila.reserva_despues} | [{_texto_muestras(fila.muestras_ms)}]")
    print("C1 integrada: 100 ciclos de _inv_al_frente/_inv_quitar/_inv_agregar dentro de _accion.")
    print("Incluye normalizacion y fronteras; excluye inicializacion y checkpoints periodicos.")
    print("n | sin/con C1 med us | extra us (%) | max sin/con us | deltas | muestras sin;con us")
    for fila in medir_c1():
        print(f"{fila.tamano} | {fila.sin_c1_us:.3f}/{fila.con_c1_us:.3f} | "
              f"{fila.extra_us:.3f} ({fila.extra_us / fila.sin_c1_us * 100:.1f}%) | "
              f"{estadisticas(fila.sin_muestras_us)[0]:.3f}/"
              f"{estadisticas(fila.con_muestras_us)[0]:.3f} | {fila.deltas} | "
              f"[{_texto_muestras(fila.sin_muestras_us)}];[{_texto_muestras(fila.con_muestras_us)}]")
    print("C1: resultados vivos e inventario historico equivalentes. No atribuir este costo a los benches directos.")
    print("Maximos observados sobre las muestras indicadas; K por defecto no modificado.")


if __name__ == "__main__":
    main()
