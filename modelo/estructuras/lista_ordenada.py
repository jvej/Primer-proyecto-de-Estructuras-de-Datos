from modelo.estructuras.ordenamiento import ordenar

class ListaOrdenada:
    def __init__(self):
        self.claves_lista = []
        self.valores = []

    def _posicion(self, clave):
        bajo = 0
        alto = len(self.claves_lista)
        while bajo < alto:
            medio = (bajo + alto) // 2
            if self.claves_lista[medio] < clave:
                bajo = medio + 1
            else:
                alto = medio
        return bajo

    def insertar(self, clave, valor):
        pos = self._posicion(clave)
        if pos < len(self.claves_lista) and self.claves_lista[pos] == clave:
            self.valores[pos] = valor        
            return
        self.claves_lista.append(None)         
        self.valores.append(None)
        i = len(self.claves_lista) - 1
        while i > pos:                        
            self.claves_lista[i] = self.claves_lista[i - 1]
            self.valores[i] = self.valores[i - 1]
            i -= 1
        self.claves_lista[pos] = clave
        self.valores[pos] = valor

    def buscar(self, clave):
        pos = self._posicion(clave)
        if pos < len(self.claves_lista) and self.claves_lista[pos] == clave:
            return self.valores[pos]
        return None

    def contiene(self, clave):
        pos = self._posicion(clave)
        return pos < len(self.claves_lista) and self.claves_lista[pos] == clave

    def eliminar(self, clave):
        """Devuelve True si la clave existía."""
        pos = self._posicion(clave)
        if pos >= len(self.claves_lista) or self.claves_lista[pos] != clave:
            return False
        for i in range(pos, len(self.claves_lista) - 1):   
            self.claves_lista[i] = self.claves_lista[i + 1]
            self.valores[i] = self.valores[i + 1]
        self.claves_lista.pop()
        self.valores.pop()
        return True

    def cantidad(self):
        return len(self.claves_lista)

    def claves(self):
        resultado = []
        for c in self.claves_lista:
            resultado.append(c)
        return resultado

    def insertar_muchos(self, pares):
        todos = []
        for i in range(len(self.claves_lista)):
            todos.append([self.claves_lista[i], self.valores[i]])
        for p in pares:
            todos.append([p[0], p[1]])
        todos = ordenar(todos, clave=lambda p: p[0])  
        self.claves_lista = []
        self.valores = []
        for i in range(len(todos)):
            if i + 1 < len(todos) and todos[i + 1][0] == todos[i][0]:
                continue                                
            self.claves_lista.append(todos[i][0])
            self.valores.append(todos[i][1])