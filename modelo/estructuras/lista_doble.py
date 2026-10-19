class NodoDoble:
    __slots__ = ("valor", "anterior", "siguiente", "enlazado", "clave")

    def __init__(self, valor=None, clave=0):
        self.valor = valor
        self.anterior = None
        self.siguiente = None
        self.enlazado = False  
        self.clave = clave    


class ListaDoble:
    def __init__(self):
        self._cabeza = NodoDoble()
        self._cola = NodoDoble()
        self._cabeza.siguiente = self._cola
        self._cola.anterior = self._cabeza
        self._cabeza.enlazado = True
        self._cola.enlazado = True
        self._tamano = 0
        self._clave_final = 0    
        self._clave_frente = 1    

    def __len__(self):
        return self._tamano

    def primero(self):
        nodo = self._cabeza.siguiente
        return None if nodo is self._cola else nodo

    def ultimo(self):
        nodo = self._cola.anterior
        return None if nodo is self._cabeza else nodo

    def anterior_de(self, nodo):
        self._exigir_enlazado(nodo)
        anterior = nodo.anterior
        return None if anterior is self._cabeza else anterior

    def siguiente_de(self, nodo):
        self._exigir_enlazado(nodo)
        siguiente = nodo.siguiente
        return None if siguiente is self._cola else siguiente

    def nodos(self):
        nodo = self._cabeza.siguiente
        while nodo is not self._cola:
            siguiente = nodo.siguiente
            yield nodo
            nodo = siguiente

    def __iter__(self):
        for nodo in self.nodos():
            yield nodo.valor

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
        self._exigir_enlazado(nodo)
        nodo.anterior.siguiente = nodo.siguiente
        nodo.siguiente.anterior = nodo.anterior
        nodo.enlazado = False
        self._tamano -= 1
        return nodo

    def reinsertar(self, nodo, pista=None):
        if nodo.enlazado:
            raise ValueError("el nodo ya está en la lista")
        izquierda = self._izquierda_por_pista(nodo, pista)
        if izquierda is None:
            izquierda = self._izquierda_buscando(nodo)
        self._enlazar_entre(nodo, izquierda, izquierda.siguiente)

    def _izquierda_por_pista(self, nodo, pista):
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