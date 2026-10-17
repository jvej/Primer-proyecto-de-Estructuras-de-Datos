from modelo.estructuras.lista_ordenada import ListaOrdenada

class Nodo:
    def __init__(self, id_ficha, ficha):
        self.id = id_ficha
        self.ficha = ficha
        self.anterior = None
        self.siguiente = None


class Cache:
    def __init__(self, tope=25, en_uso=None, usar_lru=True):
        self.tabla = ListaOrdenada()  
        self.tope = tope
        self.en_uso = en_uso      
        self.usar_lru = usar_lru   
        self.primero = None         
        self.ultimo = None          
        self.aciertos = 0
        self.fallos = 0
        self.desbordes = 0      # veces que hubo que pasar el tope porque todo estaba en uso
        self.rechazadas = 0     # fichas sin uso que no entraron a memoria por estar todo protegido

    def cantidad(self):
        return self.tabla.cantidad()

    def obtener(self, id_ficha):
        """Devuelve la ficha o None. Cuenta acierto o fallo."""
        nodo = self.tabla.buscar(id_ficha)
        if nodo is None:
            self.fallos += 1
            return None
        self.aciertos += 1
        if self.usar_lru:
            self._quitar(nodo)
            self._poner_al_frente(nodo)
        return nodo.ficha

    def poner(self, id_ficha, ficha):
        """Guarda la ficha. Devuelve el id liberado, o None si no se liberó nada.

        Política de saturación (§4.4). Nunca se libera una ficha en uso. Si al llegar al
        tope no se puede liberar ninguna (todas en uso):
          - si la ficha nueva NO está en uso, no entra a memoria: queda solo en disco
            (quien la pidió ya la tiene; volver a necesitarla cuesta una lectura de disco).
            La caché no pasa el tope.
          - si la ficha nueva SÍ está en uso (el juego la necesita en memoria), entra y la
            caché pasa el tope; se cuenta en `desbordes`. Ese exceso es inevitable: hay más
            fichas obligatoriamente protegidas que capacidad. Se corrige en cuanto alguna
            deje de estar en uso (en cualquier poner() posterior, nuevo o de actualización).
        """
        nodo = self.tabla.buscar(id_ficha)
        if nodo is not None:
            nodo.ficha = ficha
            if self.usar_lru:
                self._quitar(nodo)
                self._poner_al_frente(nodo)
            self._volver_al_tope()
            return None

        liberado = None
        while self.cantidad() >= self.tope:
            quitado = self._liberar()
            if quitado is None:
                break
            if liberado is None:
                liberado = quitado

        if self.cantidad() >= self.tope and not self._esta_en_uso(id_ficha):
            self.rechazadas += 1          # desborde evitable: se queda solo en disco
            return liberado

        nodo = Nodo(id_ficha, ficha)
        self._poner_al_frente(nodo)
        self.tabla.insertar(id_ficha, nodo)
        if self.cantidad() > self.tope:
            self.desbordes += 1
        return liberado

    def _volver_al_tope(self):
        """Si quedó por encima del tope, libera fichas que ya no estén en uso."""
        while self.cantidad() > self.tope:
            if self._liberar() is None:
                return

    def contiene(self, id_ficha):
        return self.tabla.contiene(id_ficha)

    def _esta_en_uso(self, id_ficha):
        if self.en_uso is None:
            return False
        return self.en_uso(id_ficha)

    def _liberar(self):
        actual = self.ultimo
        while actual is not None:
            if not self._esta_en_uso(actual.id):
                self._quitar(actual)
                self.tabla.eliminar(actual.id)
                return actual.id
            actual = actual.anterior
        return None   

    def _quitar(self, nodo):
        if nodo.anterior is not None:
            nodo.anterior.siguiente = nodo.siguiente
        else:
            self.primero = nodo.siguiente
        if nodo.siguiente is not None:
            nodo.siguiente.anterior = nodo.anterior
        else:
            self.ultimo = nodo.anterior
        nodo.anterior = None
        nodo.siguiente = None

    def _poner_al_frente(self, nodo):
        nodo.anterior = None
        nodo.siguiente = self.primero
        if self.primero is not None:
            self.primero.anterior = nodo
        self.primero = nodo
        if self.ultimo is None:
            self.ultimo = nodo