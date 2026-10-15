"""Inventario del jugador (Modelo, §4.5). Estructura: lista doblemente enlazada.

Cumple el contrato que usa Partida (partida.py):
    lleno(), objetos(), agregar(o), agregar_al_frente(o),
    quitar(o) -> posicion, restaurar(o, posicion)
más lo que necesitan la vista y el controlador: cursor (siguiente/anterior),
vista_ordenada(...), contiene(o), contar_clase(...).

No conoce red, disco, vista ni controlador. Solo importa lista_doble.py. Los
objetos que guarda son cualquier cosa con `clase`, `nombre`, `peso` y `valor`
(en la práctica, Objeto de objetos.py). El equipo (arma/armadura) NO se guarda
aquí: vive en el jugador, que es quien lo cambia a través del registro.

Requisitos de §4.5:
    recorrer adelante y atrás ........ cursor + enlaces, O(1) por paso
    soltar el objeto que se está viendo  quitar() lo encuentra en O(1) vía cursor
    equipar -> al frente ............. quitar() + agregar_al_frente(), O(1)
    vista ordenada sin alterar ....... se ordena una copia de las referencias
    lleno -> no se puede recoger ..... agregar() lanza InventarioLleno

`posicion` (lo que devuelve quitar) es opaca para quien la recibe: es el nodo
que se quitó más el que iba delante de él (una pista). restaurar() devuelve el
nodo a su sitio exacto usando la etiqueta de orden que el nodo conserva (ver
lista_doble.py). Esto importa porque el pergamino consumido se quita SIN
registrarse (§2.11) justo antes de deshacer, y puede ser ese vecino. Un índice
numérico no sirve: ver test_pergamino_antes_del_objeto_equipado y
test_aleatoria_deshacer_intervalos_consumiendo_pergaminos.

Costos: quitar() es O(1) si el objeto es el que el cursor señala (las acciones de
la interfaz actúan sobre el objeto que se está viendo); si no, busca recorriendo
la lista, O(n) con n <= inventario_max (una decena de objetos). restaurar() es
O(1) cuando la pista sigue siendo válida y O(n) en el caso raro en que no.
"""

from lista_doble import ListaDoble


class InventarioError(Exception):
    """Rechazos del inventario (no consumen tiempo virtual, Apéndice B)."""


class InventarioLleno(InventarioError):
    pass


class ObjetoNoEstaEnInventario(InventarioError):
    pass


CRITERIOS = ("peso", "valor", "nombre")


class PosicionInventario:
    """Dato opaco devuelto por quitar() y consumido por restaurar()."""

    __slots__ = ("nodo", "anterior")

    def __init__(self, nodo, anterior):
        self.nodo = nodo            # el nodo que se quitó
        self.anterior = anterior    # el nodo que iba delante (None = iba de primero)


class Inventario:
    def __init__(self, capacidad, ordenador=None):
        """
        capacidad: `inventario_max` de la cripta.
        ordenador: función con la forma de ordenar() de ordenamiento.py:
                   ordenador(datos, clave=, descendente=, comparacion_costosa=).
                   Se entrega desde fuera para que este módulo no dependa de él.
        """
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
        """Lista NUEVA con los objetos en el orden real (frente -> final)."""
        resultado = []
        for objeto in self._lista:
            resultado.append(objeto)
        return resultado

    def agregar(self, objeto):
        """Recoge un objeto: va al final. Lanza InventarioLleno si no cabe."""
        if self.lleno():
            raise InventarioLleno("inventario lleno (%d)" % self._capacidad)
        nodo = self._lista.agregar_al_final(objeto)
        if self._cursor is None:
            self._cursor = nodo

    def agregar_al_frente(self, objeto):
        """Pone un objeto de primero (equipar, §2.7). El cursor lo sigue."""
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
        """Devuelve `objeto` a donde estaba cuando quitar() devolvió `posicion`."""
        if posicion.nodo.valor is not objeto:
            raise ValueError("la posición no corresponde a ese objeto")
        self._lista.reinsertar(posicion.nodo, posicion.anterior)
        self._cursor = posicion.nodo

    # ------------------------------------------------------------- consultas
    def esta_vacio(self):
        return len(self._lista) == 0

    def __iter__(self):
        return iter(self._lista)

    def contiene(self, objeto):
        return self._nodo_de(objeto) is not None

    def objeto_en(self, indice):
        """Objeto en esa posición del orden real (0 = el primero). Para el replay (§4.11):
        los objetos no tienen id de instancia, se identifican por su posición."""
        if indice < 0 or indice >= len(self._lista):
            raise IndexError("no hay objeto en la posición %d" % indice)
        i = 0
        for objeto in self._lista:
            if i == indice:
                return objeto
            i += 1

    def indice_de(self, objeto):
        """Posición (0 = el primero) del objeto en el orden real; la inversa de objeto_en."""
        i = 0
        for actual in self._lista:
            if actual is objeto:
                return i
            i += 1
        raise ObjetoNoEstaEnInventario("el objeto no está en el inventario")

    def contar_clase(self, clase):
        """Cuántos objetos de esa clase hay (ej. 'pergamino_retroceso')."""
        total = 0
        for objeto in self._lista:
            if objeto.clase == clase:
                total += 1
        return total

    # ---------------------------------------------------------------- cursor
    def objeto_actual(self):
        return None if self._cursor is None else self._cursor.valor

    def ir_al_inicio(self):
        self._cursor = self._lista.primero()

    def siguiente(self):
        """Avanza el cursor. False si no hay siguiente (el cursor no se mueve)."""
        if self._cursor is None:
            return False
        nodo = self._lista.siguiente_de(self._cursor)
        if nodo is None:
            return False
        self._cursor = nodo
        return True

    def anterior(self):
        """Retrocede el cursor. False si no hay anterior (el cursor no se mueve)."""
        if self._cursor is None:
            return False
        nodo = self._lista.anterior_de(self._cursor)
        if nodo is None:
            return False
        self._cursor = nodo
        return True

    # --------------------------------------------------------- vista ordenada
    def vista_ordenada(self, criterio, descendente=False):
        """Lista NUEVA ordenada por 'peso', 'valor' o 'nombre'; el orden real no cambia.

        El ordenamiento lo hace la función entregada al crear el inventario
        (los algoritmos propios del proyecto, no sorted()). Los empates quedan
        en el orden real (los dos algoritmos son estables).
        """
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
            comparacion_costosa=(criterio == "nombre"),   # comparar textos
        )

    # ------------------------------------------------------------- internos
    def _nodo_de(self, objeto):
        """Nodo que guarda `objeto`: O(1) si es el que se está viendo, si no O(n)."""
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