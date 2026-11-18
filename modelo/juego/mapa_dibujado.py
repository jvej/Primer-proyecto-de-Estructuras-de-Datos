"""Foto conocida y disposición pura de US5; sin acceso a puertas vivas en el layout.

Los índices transitorios identifican casillas anónimas, nunca son ids de salas.
El índice AVL de ocupación usa nodos en almacenamiento contiguo propio.
"""

from dataclasses import dataclass

from modelo.estructuras.lista_ordenada import ListaOrdenada
from modelo.estructuras.ordenamiento import ordenar_merge
from modelo.juego.conocimiento import ESTADO_EXPLORADA, PUERTA_ABIERTA, PUERTA_CERRADA
from modelo.juego.sala import DIRECCIONES

DESPLAZAMIENTOS = ((0, -1), (0, 1), (1, 0), (-1, 0))


@dataclass(frozen=True, slots=True)
class SalidaMapa:
    destino: int
    direccion: str
    costo: int
    estado: str
    llave: str | None = None


@dataclass(frozen=True, slots=True)
class SalaMapa:
    id: int | None
    nombre: str | None
    salidas: tuple


@dataclass(frozen=True, slots=True)
class Casilla:
    x: int
    y: int
    estado: str
    id: int | None
    nombre: str | None
    es_jugador: bool


@dataclass(frozen=True, slots=True)
class Conexion:
    origen: int
    destino: int
    direccion: str
    costo: int
    estado: str
    llave: str | None
    fuera_cuadricula: bool
    repetida: bool = False
    rotular: bool = True


@dataclass(frozen=True, slots=True)
class MapaDibujado:
    casillas: tuple
    conexiones: tuple
    exploradas: int
    avistadas: int
    candidatos: int = 0


class IndiceOcupacion:
    """AVL propio: [clave, valor, izquierda, derecha, altura] por nodo."""

    def __init__(self):
        self._nodos = []
        self._raiz = -1

    def _altura(self, i):
        return 0 if i == -1 else self._nodos[i][4]

    def _actualizar(self, i):
        nodo = self._nodos[i]
        nodo[4] = 1 + max(self._altura(nodo[2]), self._altura(nodo[3]))

    def _rotar(self, i, izquierda):
        lado = 3 if izquierda else 2
        contrario = 2 if izquierda else 3
        j = self._nodos[i][lado]
        self._nodos[i][lado] = self._nodos[j][contrario]
        self._nodos[j][contrario] = i
        self._actualizar(i)
        self._actualizar(j)
        return j

    def _insertar(self, i, clave, valor):
        if i == -1:
            self._nodos.append([clave, valor, -1, -1, 1])
            return len(self._nodos) - 1
        nodo = self._nodos[i]
        if clave == nodo[0]:
            nodo[1] = valor
            return i
        lado = 2 if clave < nodo[0] else 3
        nodo[lado] = self._insertar(nodo[lado], clave, valor)
        self._actualizar(i)
        balance = self._altura(nodo[2]) - self._altura(nodo[3])
        if balance > 1:
            hijo = nodo[2]
            if clave > self._nodos[hijo][0]:
                nodo[2] = self._rotar(hijo, True)
            return self._rotar(i, False)
        if balance < -1:
            hijo = nodo[3]
            if clave < self._nodos[hijo][0]:
                nodo[3] = self._rotar(hijo, False)
            return self._rotar(i, True)
        return i

    def insertar(self, clave, valor):
        self._raiz = self._insertar(self._raiz, clave, valor)

    def contiene(self, clave):
        i = self._raiz
        while i != -1:
            nodo = self._nodos[i]
            if clave == nodo[0]:
                return True
            i = nodo[2 if clave < nodo[0] else 3]
        return False


def fotografia_conocimiento(conocimiento, sala_actual):
    """Solo explora topología de exploradas y consulta memoria, jamás estado real.

    ListaOrdenada se construye en bloque. Sus claves Sala.indice solo deduplican
    extremos; la asignación de referencias sigue ids visibles y luego N,S,E,O.
    Se barre estado_salas una vez por apertura, sin modificar su almacenamiento.
    Solo se accede a los objetos de sala cuyos estados indican EXPLORADA.
    """
    c = conocimiento
    exploradas = []
    for indice, estado in enumerate(c.estado_salas):
        if estado == ESTADO_EXPLORADA:
            exploradas.append(c.salas_por_indice[indice])
    exploradas = ordenar_merge(exploradas, clave=lambda sala: sala.id)
    pares = []
    for sala in exploradas:
        pares.append((sala.indice, [-1]))
        for salida in sala.salidas:
            if salida is not None:
                pares.append((salida.otro_lado(sala).indice, [-1]))
    referencias = ListaOrdenada()
    referencias.insertar_muchos(pares)
    salas = []
    actual = None
    for sala in exploradas:
        posicion = len(salas)
        referencias.buscar(sala.indice)[0] = posicion
        salas.append(SalaMapa(sala.id, sala.nombre, ()))
        if sala is sala_actual:
            actual = posicion
    for i, sala in enumerate(exploradas):
        salidas = []
        for direccion, salida in enumerate(sala.salidas):
            if salida is None:
                continue
            destino = referencias.buscar(salida.otro_lado(sala).indice)
            if destino[0] == -1:
                destino[0] = len(salas)
                salas.append(SalaMapa(None, None, ()))
            memoria = c.puerta_recordada(sala, direccion)
            estado = ('abierta' if memoria == PUERTA_ABIERTA else
                      'cerrada' if memoria == PUERTA_CERRADA else 'desconocida')
            llave = salida.llave if memoria in (PUERTA_ABIERTA, PUERTA_CERRADA) else None
            salidas.append(SalidaMapa(destino[0], DIRECCIONES[direccion], salida.costo, estado, llave))
        salas[i] = SalaMapa(sala.id, sala.nombre, tuple(salidas))
    if actual is None:
        raise ValueError('La sala actual debe estar explorada')
    return tuple(salas), actual


def _anillo(r):
    yield 0, -r
    yield 0, r
    yield r, 0
    yield -r, 0
    for a in range(1, r):
        b = r - a
        yield a, -b
        yield a, b
        yield -a, b
        yield -a, -b


def calcular_layout(conocidas, actual, tipo_indice=IndiceOcupacion, *, id_inicial=None):
    """Función pura sobre una foto compacta, sin ids ni salidas de avistadas.

    BFS O(K+E) más ordenación; índice O(log K) por candidato. Anillos: ver plan.
    tipo_indice permite medir la alternativa con exactamente la misma entrada.
    id_inicial identifica el origen conocido real, independiente del jugador.
    Las fotos sintéticas que lo omiten toman su primera sala como origen.
    """
    n = len(conocidas)
    if not 0 <= actual < n or conocidas[actual].id is None:
        raise ValueError('Se requiere una sala actual explorada')
    exploradas = ordenar_merge([i for i in range(n) if conocidas[i].id is not None],
                                clave=lambda i: conocidas[i].id)
    inicial = 0 if id_inicial is None else next(
        (i for i in exploradas if conocidas[i].id == id_inicial), -1)
    if inicial == -1 or conocidas[inicial].id is None:
        raise ValueError('Se requiere una sala inicial explorada')
    salidas = [ordenar_merge(s.salidas, clave=lambda s: DIRECCIONES.index(s.direccion))
               if s.id is not None else () for s in conocidas]
    propuestas = [None] * n
    propuestas[inicial] = (0, 0)
    raices = [inicial] + [i for i in exploradas if i != inicial]
    max_x = 0
    for raiz in raices:
        if raiz != inicial:
            if propuestas[raiz] is not None:
                continue
            propuestas[raiz] = (max_x + 3, 0)
        nivel = [raiz]
        while nivel:
            siguiente = []
            for origen in ordenar_merge(nivel, clave=lambda i: conocidas[i].id):
                x, y = propuestas[origen]
                max_x = max(max_x, x)
                for salida in salidas[origen]:
                    destino = salida.destino
                    if conocidas[destino].id is None or propuestas[destino] is not None:
                        continue
                    dx, dy = DESPLAZAMIENTOS[DIRECCIONES.index(salida.direccion)]
                    propuestas[destino] = (x + dx, y + dy)
                    siguiente.append(destino)
            nivel = siguiente
    avistadas = []
    reveladoras = [None] * n
    for origen in exploradas:
        for salida in salidas[origen]:
            destino = salida.destino
            if conocidas[destino].id is None and reveladoras[destino] is None:
                reveladoras[destino] = (origen, salida.direccion)
                avistadas.append(destino)
    ocupadas = tipo_indice()
    posiciones = [None] * n
    orden = exploradas + avistadas
    candidatos = 0
    for i in orden:
        if conocidas[i].id is None:
            origen, direccion = reveladoras[i]
            dx, dy = DESPLAZAMIENTOS[DIRECCIONES.index(direccion)]
            x, y = posiciones[origen]
            propuesta = (x + dx, y + dy)
        else:
            propuesta = propuestas[i]
        posicion = propuesta
        candidatos += 1
        if ocupadas.contiene(posicion):
            r = 1
            encontrada = False
            while not encontrada:
                for dx, dy in _anillo(r):
                    posicion = (propuesta[0] + dx, propuesta[1] + dy)
                    candidatos += 1
                    if not ocupadas.contiene(posicion):
                        encontrada = True
                        break
                r += 1
        posiciones[i] = posicion
        ocupadas.insertar(posicion, True)
    casillas = []
    publicos = [-1] * n
    for i in orden:
        sala = conocidas[i]
        x, y = posiciones[i]
        publicos[i] = len(casillas)
        casillas.append(Casilla(x, y, 'explorada' if sala.id is not None else 'avistada',
                               sala.id, sala.nombre if sala.id is not None else None, i == actual))
    conexiones = []
    for origen in exploradas:
        x, y = posiciones[origen]
        for salida in salidas[origen]:
            direccion = DIRECCIONES.index(salida.direccion)
            dx, dy = DESPLAZAMIENTOS[direccion]
            fuera = posiciones[salida.destino] != (x + dx, y + dy)
            repetida = any(otra is not salida and otra.destino == salida.destino
                           for otra in salidas[origen])
            # Una puerta física conserva sus dos salidas. Solo su rótulo se
            # comparte con la inversa exacta; jamás se fusiona por par de salas.
            inversa = next((otra for otra in salidas[salida.destino]
                            if otra.destino == origen
                            and otra.direccion == DIRECCIONES[direccion ^ 1]
                            and otra.costo == salida.costo), None)
            anterior = (publicos[salida.destino] < publicos[origen] or
                        (salida.destino == origen and (direccion ^ 1) < direccion))
            rotular = inversa is None or not anterior
            conexiones.append(Conexion(publicos[origen], publicos[salida.destino],
                                        salida.direccion, salida.costo, salida.estado,
                                        salida.llave, fuera, repetida, rotular))
    return MapaDibujado(tuple(casillas), tuple(conexiones), len(exploradas), len(avistadas), candidatos)
