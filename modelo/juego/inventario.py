from modelo.estructuras.lista_doble import ListaDoble


class InventarioError(Exception):
    """Rechazos del inventario (no consumen tiempo virtual)"""


class InventarioLleno(InventarioError):
    pass


class ObjetoNoEstaEnInventario(InventarioError):
    pass


CRITERIOS = ("peso", "valor", "nombre")


class PosicionInventario:

    __slots__ = ("nodo", "anterior")

    def __init__(self, nodo, anterior):
        self.nodo = nodo            # el nodo que se quitó
        self.anterior = anterior    # el nodo que iba delante (None = iba de primero)


class Inventario:
    def __init__(self, capacidad, ordenador=None):
        if capacidad < 0:
            raise ValueError("la capacidad no puede ser negativa")
        self._capacidad = capacidad
        self._ordenador = ordenador
        self._lista = ListaDoble()
        self._cursor = None   # nodo que el jugador está viendo

    # ---------------------------------------------------- contrato de Partida
    @property
    def capacidad(self):
        return self._capacidad

    def __len__(self):
        return len(self._lista)

    def lleno(self):
        return len(self._lista) >= self._capacidad

    def objetos(self):
        resultado = []
        for objeto in self._lista:
            resultado.append(objeto)
        return resultado

    def agregar(self, objeto):
        if self.lleno():
            raise InventarioLleno("inventario lleno (%d)" % self._capacidad)
        nodo = self._lista.agregar_al_final(objeto)
        if self._cursor is None:
            self._cursor = nodo

    def agregar_al_frente(self, objeto):
        if self.lleno():
            raise InventarioLleno("inventario lleno (%d)" % self._capacidad)
        self._cursor = self._lista.agregar_al_frente(objeto)

    def quitar(self, objeto):
        """Saca el objeto y devuelve su posición (para restaurar())."""
        nodo = self._nodo_de(objeto)
        if nodo is None:
            raise ObjetoNoEstaEnInventario("el objeto no está en el inventario")
        anterior = self._lista.anterior_de(nodo)
        if self._cursor is nodo:
            vecino = self._lista.siguiente_de(nodo)
            self._cursor = vecino if vecino is not None else anterior
        self._lista.quitar(nodo)
        return PosicionInventario(nodo, anterior)

    def restaurar(self, objeto, posicion):
        if posicion.nodo.valor is not objeto:
            raise ValueError("la posición no corresponde a ese objeto")
        self._lista.reinsertar(posicion.nodo, posicion.anterior)
        self._cursor = posicion.nodo

    def esta_vacio(self):
        return len(self._lista) == 0

    def __iter__(self):
        return iter(self._lista)

    def contiene(self, objeto):
        return self._nodo_de(objeto) is not None

    def objeto_en(self, indice):
        if indice < 0 or indice >= len(self._lista):
            raise IndexError("no hay objeto en la posición %d" % indice)
        i = 0
        for objeto in self._lista:
            if i == indice:
                return objeto
            i += 1

    def indice_de(self, objeto):
        i = 0
        for actual in self._lista:
            if actual is objeto:
                return i
            i += 1
        raise ObjetoNoEstaEnInventario("el objeto no está en el inventario")

    def clave_de(self, objeto):
        nodo = self._nodo_de(objeto)
        if nodo is None:
            raise ObjetoNoEstaEnInventario("el objeto no está en el inventario")
        return nodo.clave

    def objeto_por_clave(self, clave):
        if self._cursor is not None and self._cursor.clave == clave:
            return self._cursor.valor
        for nodo in self._lista.nodos():
            if nodo.clave == clave:
                return nodo.valor
        return None

    def contar_clase(self, clase):
        total = 0
        for objeto in self._lista:
            if objeto.clase == clase:
                total += 1
        return total
    
    def objeto_actual(self):
        return None if self._cursor is None else self._cursor.valor

    def ir_al_inicio(self):
        self._cursor = self._lista.primero()

    def siguiente(self):
        if self._cursor is None:
            return False
        nodo = self._lista.siguiente_de(self._cursor)
        if nodo is None:
            return False
        self._cursor = nodo
        return True

    def anterior(self):
        if self._cursor is None:
            return False
        nodo = self._lista.anterior_de(self._cursor)
        if nodo is None:
            return False
        self._cursor = nodo
        return True

    # --------------------------------------------------------- vista ordenada
    def vista_ordenada(self, criterio, descendente=False):
        if self._ordenador is None:
            raise ValueError("el inventario no recibió un ordenador")
        if criterio == "peso":
            clave = _clave_peso
        elif criterio == "valor":
            clave = _clave_valor
        elif criterio == "nombre":
            clave = _clave_nombre
        else:
            raise ValueError("criterio desconocido: %r (use %s)" % (criterio, CRITERIOS))
        return self._ordenador(
            self.objetos(),
            clave=clave,
            descendente=descendente,
            comparacion_costosa=(criterio == "nombre"),   
        )

    def _nodo_de(self, objeto):
        if self._cursor is not None and self._cursor.valor is objeto:
            return self._cursor
        for nodo in self._lista.nodos():
            if nodo.valor is objeto:
                return nodo
        return None


def _clave_peso(objeto):
    return objeto.peso


def _clave_valor(objeto):
    return objeto.valor


def _clave_nombre(objeto):
    return objeto.nombre.lower()