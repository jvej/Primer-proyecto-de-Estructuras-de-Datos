"""SC-005: etapas frente a reiniciar desde el inicio por cada llave obtenida.

Solo criptas sintéticas deterministas; no se consulta la cripta oficial.
Ambas versiones incluyen el mismo preprocesamiento de índices en sus tiempos.
La alternativa comparte _Indices, ColaFIFO y ordenar, pero su recorrido se
implementa aquí y nunca llama al recorrido incremental ni usa listas de espera.
Solo se comparan estado y orden de llaves; no el diagnóstico de casos fallidos.
"""

import time

from bench.generador_criptas import generar_cripta
from modelo.datos.esqueleto import Esqueleto
from modelo.estructuras.cola_fifo import ColaFIFO
from modelo.estructuras.ordenamiento import ordenar
from modelo.juego.resolubilidad import (
    _Indices, ResultadoResolubilidad, verificar_resolubilidad,
)


SEMILLA = 7
REPETICIONES = 7
CASOS = (("linea", 11, 10), ("linea", 51, 50), ("linea", 101, 100),
         ("linea", 201, 200), ("cuadricula", 1000, 50))


def _recorrido_completo(indices, inicio, salida, disponibles, obtenidas):
    """Reinicia las marcas y recorre toda la región accesible desde el inicio."""
    visitadas = [False] * len(indices.salas)
    cola = ColaFIFO()
    if inicio is not None:
        visitadas[inicio] = True
        cola.agregar(inicio)
    pendientes = []
    entrada_salida = False
    while not cola.vacia():
        origen = cola.sacar()
        for llave in indices.llaves_en_sala[origen]:
            if not obtenidas[llave]:
                obtenidas[llave] = True
                pendientes.append(llave)
        for destino, _direccion, abierta, cerradura in indices.vecinos[origen]:
            if not abierta and (cerradura < 0 or not disponibles[cerradura]):
                continue
            if destino == salida and cerradura >= 0 and cerradura == indices.salida:
                entrada_salida = True
            if not visitadas[destino]:
                visitadas[destino] = True
                cola.agregar(destino)
    return pendientes, entrada_salida


def verificar_repetido(esqueleto, ubicaciones_llaves, sala_inicial,
                       sala_salida, llave_salida, catalogo_llaves=None):
    """Alternativa de medición O(L * (S + E)), además del preprocesamiento.

    Después de activar cada llave se repite un recorrido completo. Si varias
    pertenecen a una etapa, las descubiertas en esos recorridos se acumulan
    para la siguiente: nunca se activan antes de cerrar la etapa actual.
    """
    catalogo = catalogo_llaves if catalogo_llaves is not None else []
    indices = _Indices(esqueleto, ubicaciones_llaves, llave_salida, catalogo)
    inicio = esqueleto.posicion(sala_inicial)
    salida = esqueleto.posicion(sala_salida)
    disponibles = [False] * len(indices.textos)
    obtenidas = [False] * len(indices.textos)
    pendientes, entrada_salida = _recorrido_completo(
        indices, inicio, salida, disponibles, obtenidas)
    orden = []
    etapa = 0
    while pendientes:
        pendientes = ordenar(pendientes, clave=lambda p: indices.textos[p])
        orden.append((etapa, [indices.textos[p] for p in pendientes]))
        siguientes = []
        for llave in pendientes:
            disponibles[llave] = True
            if indices.abre[llave] >= 0:
                disponibles[indices.abre[llave]] = True
            nuevas, entrada = _recorrido_completo(
                indices, inicio, salida, disponibles, obtenidas)
            siguientes.extend(nuevas)
            entrada_salida = entrada_salida or entrada
        pendientes = siguientes
        etapa += 1
    resoluble = indices.salida >= 0 and disponibles[indices.salida] and entrada_salida
    return ResultadoResolubilidad("RESOLUBLE" if resoluble else "NO RESOLUBLE",
                                 orden_llaves=orden if resoluble else [])


def _crear_caso(topologia, numero_salas, cantidad_llaves):
    datos = generar_cripta(numero_salas=numero_salas, semilla=SEMILLA,
                           cadena_llaves=cantidad_llaves, topologia=topologia)
    esqueleto = Esqueleto()
    for pagina in datos["paginas"]:
        esqueleto.agregar_pagina(pagina)
    general = datos["general"]
    return (esqueleto, datos["llaves"]["llaves"], general["sala_inicial"],
            general["sala_salida"], general["llave_salida"], datos["catalogo"]["entidades"])


def _comprobar_equivalencia(esperado, resultado):
    if (esperado.estado != resultado.estado
            or esperado.orden_llaves != resultado.orden_llaves):
        raise AssertionError("Las versiones difieren en estado u orden de llaves")


def _mediana(muestras):
    valores = ordenar(muestras)
    medio = len(valores) // 2
    if len(valores) % 2:
        return valores[medio]
    return (valores[medio - 1] + valores[medio]) / 2


def medir_caso(argumentos, repeticiones=REPETICIONES):
    # Una ejecución de calentamiento por versión, fuera de la medición.
    esperado = verificar_resolubilidad(*argumentos)
    _comprobar_equivalencia(esperado, verificar_repetido(*argumentos))
    if not esperado.es_resoluble():
        raise AssertionError("El caso sintético del bench debe ser resoluble")
    tiempos_etapas = []
    tiempos_repetido = []
    versiones = ((verificar_resolubilidad, tiempos_etapas),
                 (verificar_repetido, tiempos_repetido))
    for repeticion in range(repeticiones):
        # Alternar el orden reduce el sesgo de medir siempre una versión primero.
        for funcion, muestras in versiones if repeticion % 2 == 0 else versiones[::-1]:
            inicio = time.perf_counter()
            resultado = funcion(*argumentos)
            muestras.append((time.perf_counter() - inicio) * 1000)
            _comprobar_equivalencia(esperado, resultado)
    return _mediana(tiempos_etapas), _mediana(tiempos_repetido), esperado


def medir_resolubilidad():
    print("== Resolubilidad: por etapas vs recorrido completo por cada llave ==")
    print("Criptas sintéticas; no se mide la cripta oficial. Semilla fija: %d." % SEMILLA)
    print("Mediana de %d repeticiones con time.perf_counter; calentamiento previo." % REPETICIONES)
    print("Incluye preprocesamiento en ambas versiones; excluye generación y armado del esqueleto.")
    print("Salidas cuenta enlaces dirigidos (cada sentido de una puerta cuenta por separado).")
    print("topologia  | salas | salidas | llaves | etapas (ms) | repetido (ms) | aceleracion | estado igual | orden igual")
    mayor = None
    for topologia, numero_salas, cantidad_llaves in CASOS:
        argumentos = _crear_caso(topologia, numero_salas, cantidad_llaves)
        esqueleto, ubicaciones = argumentos[:2]
        salidas = sum(len(salidas_sala) for salidas_sala in esqueleto.salidas)
        etapas, repetido, resultado = medir_caso(argumentos)
        print("%-10s | %5d | %7d | %6d | %11.3f | %13.3f | %10.2fx | SI (%s) | SI" %
              (topologia, len(esqueleto.ids), salidas, len(ubicaciones), etapas,
               repetido, repetido / etapas, resultado.estado))
        if mayor is None or len(esqueleto.ids) > mayor[1]:
            mayor = (topologia, len(esqueleto.ids), etapas)
    topologia, salas, tiempo = mayor
    print("SC-001, caso sintético mayor (%s, %d salas): %.3f ms < 200 ms: %s." %
          (topologia, salas, tiempo, "SI" if tiempo < 200 else "NO"))
    print("Esta referencia sintética no valida SC-001 sobre la cripta oficial publicada.")


if __name__ == "__main__":
    medir_resolubilidad()
