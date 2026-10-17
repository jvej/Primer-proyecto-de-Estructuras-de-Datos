"""Lista doblemente enlazada con nodos centinela (TDA genérico del Modelo).

No importa nada del resto del proyecto.

Costos:
    agregar_al_final / agregar_al_frente ... O(1)
    quitar(nodo)                          ... O(1)  (se entrega el nodo, no se busca)
    reinsertar(nodo, pista)               ... O(1) con una pista válida; O(n) si no
    anterior_de / siguiente_de            ... O(1)
    recorrer                              ... O(n)

Los centinelas (cabeza y cola) son nodos falsos que nunca se muestran: con ellos
insertar y quitar no tienen casos especiales ("vacía", "primero", "último").

Etiqueta de orden (`clave`): cada nodo recibe al nacer un entero que no vuelve a
cambiar y que nunca se repite. Al final se asignan 1, 2, 3...; al frente, 0, -1, -2...
Así el orden de la lista siempre coincide con el orden de las claves, y un nodo
quitado sabe exactamente dónde le toca volver respecto a los que siguen en la
lista, aunque otros se hayan quitado, movido o añadido mientras tanto.
(Recordar solo "quién iba delante" no basta: ese vecino puede haber sido quitado
y su propio vecino recordado quedar desactualizado. Pasa con el pergamino de
retroceso, que se consume sin registrarse, §2.11, al deshacer varias acciones.)
"""


class NodoDoble:
    __slots__ = ("valor", "anterior", "siguiente", "enlazado", "clave")

    def __init__(self, valor=None, clave=0):
        self.valor = valor
        self.anterior = None
        self.siguiente = None
        self.enlazado = False   # True mientras forma parte de la lista
        self.clave = clave      # etiqueta de orden, fija de por vida


class ListaDoble:
    def __init__(self):
        self._cabeza = NodoDoble()
        self._cola = NodoDoble()
        self._cabeza.siguiente = self._cola
        self._cola.anterior = self._cabeza
        self._cabeza.enlazado = True
        self._cola.enlazado = True
        self._tamano = 0
        self._clave_final = 0     # última clave dada al final
        self._clave_frente = 1    # última clave dada al frente (la próxima será 0)

    # ------------------------------------------------------------ consulta
    def __len__(self):
        return self._tamano

    def primero(self):
        """Primer nodo real, o None si la lista está vacía."""
        nodo = self._cabeza.siguiente
        return None if nodo is self._cola else nodo

    def ultimo(self):
        nodo = self._cola.anterior
        return None if nodo is self._cabeza else nodo

    def anterior_de(self, nodo):
        """Nodo anterior, o None si `nodo` es el primero."""
        self._exigir_enlazado(nodo)
        anterior = nodo.anterior
        return None if anterior is self._cabeza else anterior

    def siguiente_de(self, nodo):
        """Nodo siguiente, o None si `nodo` es el último."""
        self._exigir_enlazado(nodo)
        siguiente = nodo.siguiente
        return None if siguiente is self._cola else siguiente

    def nodos(self):
        """Recorre los nodos de adelante hacia atrás."""
        nodo = self._cabeza.siguiente
        while nodo is not self._cola:
            siguiente = nodo.siguiente
            yield nodo
            nodo = siguiente

    def __iter__(self):
        for nodo in self.nodos():
            yield nodo.valor

    # ------------------------------------------------------- modificación
    def agregar_al_final(self, valor):
        self._clave_final += 1
        nodo = NodoDoble(valor, self._clave_final)
        self._enlazar_entre(nodo, self._cola.anterior, self._cola)
        return nodo

    def agregar_al_frente(self, valor):
        self._clave_frente -= 1
        nodo = NodoDoble(valor, self._clave_frente)
        self._enlazar_entre(nodo, self._cabeza, self._cabeza.siguiente)
        return nodo

    def quitar(self, nodo):
        """Desconecta `nodo` en O(1). El nodo conserva su clave para reinsertar()."""
        self._exigir_enlazado(nodo)
        nodo.anterior.siguiente = nodo.siguiente
        nodo.siguiente.anterior = nodo.anterior
        nodo.enlazado = False
        self._tamano -= 1
        return nodo

    def reinsertar(self, nodo, pista=None):
        """Vuelve a conectar un nodo quitado, en el lugar que le da su clave.

        pista: el nodo que iba delante cuando se quitó (None = iba de primero).
        Si la pista sigue en la lista y sigue siendo el vecino correcto, es O(1).
        Si no (por ejemplo, ese vecino fue quitado), se busca el lugar
        recorriendo la lista: O(n), con n acotado por la capacidad del inventario.
        """
        if nodo.enlazado:
            raise ValueError("el nodo ya está en la lista")
        izquierda = self._izquierda_por_pista(nodo, pista)
        if izquierda is None:
            izquierda = self._izquierda_buscando(nodo)
        self._enlazar_entre(nodo, izquierda, izquierda.siguiente)

    # ------------------------------------------------------------ internos
    def _izquierda_por_pista(self, nodo, pista):
        """El nodo que debe quedar a la izquierda de `nodo`, si la pista lo confirma."""
        if pista is None:
            izquierda = self._cabeza
        elif pista.enlazado and pista.clave < nodo.clave:
            izquierda = pista
        else:
            return None
        derecha = izquierda.siguiente
        if derecha is self._cola or derecha.clave > nodo.clave:
            return izquierda
        return None

    def _izquierda_buscando(self, nodo):
        izquierda = self._cabeza
        actual = self._cabeza.siguiente
        while actual is not self._cola and actual.clave < nodo.clave:
            izquierda = actual
            actual = actual.siguiente
        return izquierda

    def _exigir_enlazado(self, nodo):
        if nodo is None or not nodo.enlazado:
            raise ValueError("el nodo no pertenece a la lista")

    def _enlazar_entre(self, nodo, anterior, siguiente):
        nodo.anterior = anterior
        nodo.siguiente = siguiente
        anterior.siguiente = nodo
        siguiente.anterior = nodo
        nodo.enlazado = True
        self._tamano += 1