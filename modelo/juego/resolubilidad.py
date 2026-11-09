"""Alcanzabilidad por etapas y diagnóstico, exclusivamente con datos en memoria.

Los índices se preparan una vez con ordenar() y búsquedas binarias propias.
Después, cada sala y salida se procesa un número constante de veces entre
recorrido y diagnóstico: O(S + E + L), más ordenar las llaves de cada etapa.
El preprocesamiento incluye ordenar identificadores y salas y traducir sus
posiciones. No se consulta ningún almacén: el catálogo opcional debe llegar
como fichas ya materializadas en memoria. Sin ficha ni ``abre`` en la ubicación,
una llave únicamente abre la cerradura que coincide con su id.
"""

from modelo.estructuras.cola_fifo import ColaFIFO
from modelo.estructuras.ordenamiento import ordenar


DIRECCIONES = ("N", "S", "E", "O")


class ResultadoResolubilidad:
    def __init__(self, estado, orden_llaves=None, llaves_no_obtenibles=None,
                 frontera_bloqueada=None, ubicacion_llaves=None, ciclos=None, motivo=None):
        self.estado = estado
        self.orden_llaves = orden_llaves or []
        self.llaves_no_obtenibles = llaves_no_obtenibles or []
        self.frontera_bloqueada = frontera_bloqueada or []
        self.ubicacion_llaves = ubicacion_llaves or []
        self.ciclos = ciclos or []
        self.motivo = motivo

    def es_resoluble(self) -> bool:
        return self.estado == "RESOLUBLE"

    def formatear_reporte(self) -> str:
        """Plantilla FR-018: omite secciones vacías y no agrega salto final."""
        lineas = ["ESTADO: " + self.estado]
        if self.orden_llaves:
            lineas.append("ORDEN DE LLAVES:")
            for etapa, llaves in self.orden_llaves:
                lineas.append("  etapa %s: %s" % (etapa, ", ".join(llaves)))
        if self.llaves_no_obtenibles:
            lineas.append("LLAVES NO OBTENIBLES: " + ", ".join(self.llaves_no_obtenibles))
        if self.frontera_bloqueada:
            lineas.append("FRONTERA BLOQUEADA:")
            for origen, direccion, destino, llave in self.frontera_bloqueada:
                pedido = "sin llave asociada" if llave is None else "pide " + llave
                lineas.append("  - sala %s (%s) -> sala %s: %s" %
                              (origen, direccion, destino, pedido))
        if self.ubicacion_llaves:
            lineas.append("UBICACIÓN DE LLAVES:")
            for llave, ubicacion in self.ubicacion_llaves:
                lineas.append("  - %s: %s" % (llave, ubicacion))
        if self.ciclos:
            lineas.append("CICLOS DETECTADOS:")
            for ciclo in self.ciclos:
                lineas.append("  - " + ciclo)
        if self.motivo:
            lineas.append("MOTIVO: " + self.motivo)
        return "\n".join(lineas)


def _buscar_cerradura(identificadores, id_texto):
    """Devuelve una posición entera o -1; solo se usa al preparar índices."""
    if id_texto is None:
        return -1
    bajo = 0
    alto = len(identificadores)
    while bajo < alto:
        medio = (bajo + alto) // 2
        if identificadores[medio] < id_texto:
            bajo = medio + 1
        else:
            alto = medio
    if bajo < len(identificadores) and identificadores[bajo] == id_texto:
        return bajo
    return -1


class _Indices:
    """Listas contiguas; los registros de entrada solo se leen."""

    def __init__(self, esqueleto, ubicaciones, llave_salida, catalogo):
        self.salas = esqueleto.ids
        cantidad_salas = len(self.salas)
        self.orden_salas = ordenar(range(cantidad_salas), clave=lambda p: self.salas[p])
        textos = [llave_salida] if llave_salida is not None else []
        for salidas in esqueleto.salidas:
            for direccion in DIRECCIONES:
                if direccion in salidas and salidas[direccion].get("llave") is not None:
                    textos.append(salidas[direccion]["llave"])
        for registros in (ubicaciones, catalogo):
            for registro in registros:
                textos.append(registro["id"])
                if registro.get("abre") is not None:
                    textos.append(registro["abre"])
        self.textos = []
        for texto in ordenar(textos):
            if not self.textos or self.textos[-1] != texto:
                self.textos.append(texto)
        cantidad = len(self.textos)
        self.salida = _buscar_cerradura(self.textos, llave_salida)
        self.abre = [-1] * cantidad
        self.es_llave = [False] * cantidad
        self.ubicaciones = [[] for _ in range(cantidad)]
        self.llaves_en_sala = [[] for _ in range(cantidad_salas)]
        for ficha in catalogo:
            indice = _buscar_cerradura(self.textos, ficha["id"])
            self.abre[indice] = _buscar_cerradura(self.textos, ficha.get("abre"))
        for ubicacion in ubicaciones:
            indice = _buscar_cerradura(self.textos, ubicacion["id"])
            if ubicacion.get("abre") is not None:
                self.abre[indice] = _buscar_cerradura(self.textos, ubicacion["abre"])
        # Orden previo para que varias ubicaciones de una llave también sean deterministas.
        ubicaciones = ordenar(ubicaciones, clave=lambda u: (u["id"], u["sala"], u.get("enemigo") or ""))
        for ubicacion in ubicaciones:
            indice = _buscar_cerradura(self.textos, ubicacion["id"])
            posicion = esqueleto.posicion(ubicacion["sala"])
            self.es_llave[indice] = True
            if posicion is not None:
                self.llaves_en_sala[posicion].append(indice)
            lugar = "sala %s" % ubicacion["sala"]
            if ubicacion.get("enemigo") is not None:
                lugar += " (suelta del enemigo %s)" % ubicacion["enemigo"]
            self.ubicaciones[indice].append(lugar)
            alias = self.abre[indice]
            if alias >= 0 and alias != indice:
                self.ubicaciones[alias].append(lugar)
        self.vecinos = [[] for _ in range(cantidad_salas)]
        for origen in range(cantidad_salas):
            for direccion in DIRECCIONES:
                salida = esqueleto.salidas[origen].get(direccion)
                if salida is None:
                    continue
                destino = esqueleto.posicion(salida["sala"])
                if destino is None:
                    continue
                estado = salida.get("estado", "cerrada" if salida.get("cerrada", False) else "abierta")
                cerradura = _buscar_cerradura(self.textos, salida.get("llave"))
                self.vecinos[origen].append((destino, direccion, estado == "abierta", cerradura))


def _recorrer(indices, inicio, salida):
    visitado = [False] * len(indices.salas)
    disponibles = [False] * len(indices.textos)
    obtenidas = [False] * len(indices.textos)
    listas_espera = [[] for _ in indices.textos]
    cola = ColaFIFO()
    if inicio is not None:
        visitado[inicio] = True
        cola.agregar(inicio)
    etapa = 0
    orden_llaves = []
    entrada_salida = False
    while not cola.vacia():
        pendientes = []
        # Agotar la región completa con las llaves de etapas anteriores,
        # incluidas todas las capas de salidas abiertas de esta misma etapa.
        while not cola.vacia():
            origen = cola.sacar()
            for llave in indices.llaves_en_sala[origen]:
                if not obtenidas[llave]:
                    obtenidas[llave] = True
                    pendientes.append(llave)
            for destino, direccion, abierta, cerradura in indices.vecinos[origen]:
                if abierta or (cerradura >= 0 and disponibles[cerradura]):
                    if destino == salida and cerradura >= 0 and cerradura == indices.salida:
                        entrada_salida = True
                    if not visitado[destino]:
                        visitado[destino] = True
                        cola.agregar(destino)
                elif cerradura >= 0:
                    listas_espera[cerradura].append((origen, direccion, destino))
        if pendientes:
            pendientes = ordenar(pendientes, clave=lambda p: indices.textos[p])
            orden_llaves.append((etapa, [indices.textos[p] for p in pendientes]))
            for llave in pendientes:
                for cerradura in (llave, indices.abre[llave]):
                    if cerradura < 0 or disponibles[cerradura]:
                        continue
                    disponibles[cerradura] = True
                    # Cada lista se libera una sola vez, sin repasar otras puertas.
                    for origen, direccion, destino in listas_espera[cerradura]:
                        if destino == salida and cerradura == indices.salida:
                            entrada_salida = True
                        if not visitado[destino]:
                            visitado[destino] = True
                            cola.agregar(destino)
                    listas_espera[cerradura] = []
            etapa += 1
    return visitado, disponibles, obtenidas, orden_llaves, entrada_salida


def _dependencias(indices, visitado, disponibles, obtenidas, frontera):
    """Continúa desde la frontera; cada sala no alcanzada se etiqueta una vez."""
    explorado = visitado[:]
    etiquetas = [None] * len(indices.salas)
    cola = ColaFIFO()
    for origen, direccion, destino, cerradura in frontera:
        if not explorado[destino]:
            explorado[destino] = True
            etiquetas[destino] = (cerradura, origen, direccion)
            cola.agregar(destino)
    while not cola.vacia():
        origen = cola.sacar()
        for destino, direccion, abierta, cerradura in indices.vecinos[origen]:
            if explorado[destino]:
                continue
            explorado[destino] = True
            etiqueta = etiquetas[origen]
            if not abierta and (cerradura < 0 or not disponibles[cerradura]):
                etiqueta = (cerradura, origen, direccion)
            etiquetas[destino] = etiqueta
            cola.agregar(destino)
    # Construir por destino y transponer en orden de id evita ordenar las
    # adyacencias: el grafo queda con vecinos lexicográficos en tiempo lineal.
    inverso = [[] for _ in indices.textos]
    for sala in indices.orden_salas:
        etiqueta = etiquetas[sala]
        if etiqueta is None or etiqueta[0] < 0:
            continue
        cerradura, origen, direccion = etiqueta
        for llave in indices.llaves_en_sala[sala]:
            if obtenidas[llave]:
                continue
            inverso[cerradura].append((llave, origen, direccion))
            alias = indices.abre[llave]
            if alias >= 0 and alias != llave and not disponibles[alias]:
                inverso[cerradura].append((alias, origen, direccion))
    grafo = [[] for _ in indices.textos]
    for destino in range(len(inverso)):
        for origen, sala, direccion in inverso[destino]:
            grafo[origen].append((destino, sala, direccion))
    return grafo


def _menor_nodo_ciclico(grafo):
    """Selecciona el menor id cíclico sin enumerar ciclos ni repetir por llave.

    Dos pasadas DFS iterativas separan componentes fuertemente conexas en
    O(nodos + aristas). Así una cadena que lleva a un ciclo mayor no altera
    el desempate frente a otro ciclo menor de una rama diferente (FR-014).
    """
    colores = [0] * len(grafo)
    finalizados = []
    for raiz in range(len(grafo)):
        if colores[raiz] != 0:
            continue
        pila = [[raiz, 0]]
        colores[raiz] = 1
        while pila:
            nodo, siguiente = pila[-1]
            if siguiente == len(grafo[nodo]):
                colores[nodo] = 2
                finalizados.append(nodo)
                pila.pop()
                continue
            vecino = grafo[nodo][siguiente][0]
            pila[-1][1] += 1
            if colores[vecino] == 0:
                colores[vecino] = 1
                pila.append([vecino, 0])
    inverso = [[] for _ in grafo]
    for nodo in range(len(grafo)):
        for vecino, sala, direccion in grafo[nodo]:
            inverso[vecino].append(nodo)
    asignado = [False] * len(grafo)
    elegido = -1
    for raiz in reversed(finalizados):
        if asignado[raiz]:
            continue
        asignado[raiz] = True
        pila = [raiz]
        cantidad = 0
        menor = raiz
        while pila:
            nodo = pila.pop()
            cantidad += 1
            menor = min(menor, nodo)
            for vecino in inverso[nodo]:
                if not asignado[vecino]:
                    asignado[vecino] = True
                    pila.append(vecino)
        es_ciclica = cantidad > 1 or any(v == raiz for v, _, _ in grafo[raiz])
        if es_ciclica and (elegido < 0 or menor < elegido):
            elegido = menor
    return elegido


def _detectar_ciclo(indices, grafo):
    """DFS de tres colores con pila contigua; devuelve un testigo determinista."""
    raiz = _menor_nodo_ciclico(grafo)
    if raiz < 0:
        return []
    colores = [0] * len(grafo)
    colores[raiz] = 1
    pila = [[raiz, 0, None]]  # nodo, siguiente arista, arista de entrada
    while pila:
        nodo, siguiente, entrada = pila[-1]
        if siguiente == len(grafo[nodo]):
            colores[nodo] = 2
            pila.pop()
            continue
        arista = grafo[nodo][siguiente]
        pila[-1][1] += 1
        vecino = arista[0]
        if colores[vecino] == 0:
            colores[vecino] = 1
            pila.append([vecino, 0, arista])
        elif colores[vecino] == 1 and vecino == raiz:
            # La raíz es el menor id de cualquier ciclo; el camino activo
            # que regresa a ella ya está normalizado empezando por ese id.
            fragmentos = [indices.textos[raiz]]
            for i in range(1, len(pila) + 1):
                destino, sala, direccion = pila[i][2] if i < len(pila) else arista
                fragmentos.append(" -> %s [sala %s (%s)]" %
                                  (indices.textos[destino], indices.salas[sala], direccion))
            return ["".join(fragmentos)]
    return []


def verificar_resolubilidad(esqueleto, ubicaciones_llaves, sala_inicial,
                           sala_salida, llave_salida, catalogo_llaves=None) -> ResultadoResolubilidad:
    """Recibe ubicaciones y, opcionalmente, una lista de fichas en memoria.

    No llama a fuentes de datos ni altera el esqueleto, ubicaciones o fichas.
    Las llaves portadas se obtienen al alcanzar la sala inicial de su enemigo.
    """
    catalogo = catalogo_llaves if catalogo_llaves is not None else []
    indices = _Indices(esqueleto, ubicaciones_llaves, llave_salida, catalogo)
    inicio = esqueleto.posicion(sala_inicial)
    salida = esqueleto.posicion(sala_salida)
    visitado, disponibles, obtenidas, orden, entrada_salida = _recorrer(indices, inicio, salida)
    if indices.salida >= 0 and disponibles[indices.salida] and entrada_salida:
        return ResultadoResolubilidad("RESOLUBLE", orden_llaves=orden)

    frontera = []
    frontera_reporte = []
    faltantes = [indices.es_llave[i] and not obtenidas[i] for i in range(len(indices.textos))]
    existe_puerta_salida = False
    for origen in indices.orden_salas:
        for destino, direccion, abierta, cerradura in indices.vecinos[origen]:
            if destino == salida and cerradura >= 0 and cerradura == indices.salida:
                existe_puerta_salida = True
            if not abierta and visitado[origen] and not visitado[destino]:
                frontera.append((origen, direccion, destino, cerradura))
                llave = indices.textos[cerradura] if cerradura >= 0 else None
                frontera_reporte.append((indices.salas[origen], direccion, indices.salas[destino], llave))
                if cerradura >= 0:
                    faltantes[cerradura] = True
    if indices.salida >= 0 and not disponibles[indices.salida]:
        faltantes[indices.salida] = True
    llaves_no_obtenibles = []
    ubicaciones = []
    for i in range(len(indices.textos)):
        if faltantes[i]:
            llaves_no_obtenibles.append(indices.textos[i])
            for lugar in indices.ubicaciones[i]:
                ubicaciones.append((indices.textos[i], lugar))
    grafo = _dependencias(indices, visitado, disponibles, obtenidas, frontera)
    ciclos = _detectar_ciclo(indices, grafo)
    motivo = None if existe_puerta_salida else "no existe puerta hacia sala_salida que pida llave_salida"
    return ResultadoResolubilidad("NO RESOLUBLE", llaves_no_obtenibles=llaves_no_obtenibles,
                                 frontera_bloqueada=frontera_reporte, ubicacion_llaves=ubicaciones,
                                 ciclos=ciclos, motivo=motivo)
