import time

from modelo.juego.inventario import Inventario

TAMANOS = (10, 100, 1000, 10000)
REPETICIONES_BASE = 20000
REPETICIONES_MINIMAS = 20
CORRIDAS = 5


class Obj:
    def __init__(self, i):
        self.nombre = "o%d" % i
        self.clase = "llave"
        self.peso = 1
        self.valor = 1


def medir(funcion, repeticiones):
    """Microsegundos por llamada: la mejor de varias corridas."""
    mejor = None
    for _ in range(CORRIDAS):
        inicio = time.perf_counter()
        for _ in range(repeticiones):
            funcion()
        total = time.perf_counter() - inicio
        if mejor is None or total < mejor:
            mejor = total
    return mejor * 1e6 / repeticiones


def repeticiones(n, costo_relativo):
    return max(REPETICIONES_MINIMAS, REPETICIONES_BASE // (1 + n * costo_relativo // 100))


def posiciones(n):
    return (("primero", 0), ("medio", n // 2), ("último", n - 1))

def preparar_lista(n):
    inv = Inventario(n)
    objetos = [Obj(i) for i in range(n)]
    for o in objetos:
        inv.agregar(o)
    return inv, objetos


def lista_soltar(n, indice, con_cursor):
    inv, objetos = preparar_lista(n)
    objetivo = objetos[indice]
    if con_cursor:
        for _ in range(indice):
            inv.siguiente()

    def operacion():
        posicion = inv.quitar(objetivo)
        inv.restaurar(objetivo, posicion)
        if not con_cursor:
            inv.ir_al_inicio()   
    return operacion


def lista_equipar(n, indice, con_cursor):
    inv, objetos = preparar_lista(n)
    objetivo = objetos[indice]
    if con_cursor:
        for _ in range(indice):
            inv.siguiente()

    def operacion():
        posicion = inv.quitar(objetivo)
        inv.agregar_al_frente(objetivo)
        inv.quitar(objetivo)
        inv.restaurar(objetivo, posicion)
        if not con_cursor:
            inv.ir_al_inicio()
    return operacion
def arreglo_soltar(n, indice):
    a = [Obj(i) for i in range(n)]

    def operacion():
        objeto = a[indice]
        del a[indice]
        a.insert(indice, objeto)
    return operacion


def arreglo_equipar(n, indice):
    a = [Obj(i) for i in range(n)]

    def operacion():
        objeto = a.pop(indice)
        a.insert(0, objeto)
        a.pop(0)
        a.insert(indice, objeto)
    return operacion

def _sacar(pila, k):
    """Saca k elementos del tope (el tope es el frente del inventario)."""
    temporal = []
    for _ in range(k):
        temporal.append(pila.pop())
    return temporal


def _devolver(pila, temporal):
    while temporal:
        pila.append(temporal.pop())


def pila_preparar(n):
    return [Obj(i) for i in range(n - 1, -1, -1)]


def pila_soltar(n, indice):
    pila = pila_preparar(n)

    def operacion():
        temporal = _sacar(pila, indice)
        objeto = pila.pop()
        _devolver(pila, temporal)
        temporal = _sacar(pila, indice)
        pila.append(objeto)
        _devolver(pila, temporal)
    return operacion


def pila_equipar(n, indice):
    pila = pila_preparar(n)

    def operacion():
        temporal = _sacar(pila, indice)
        objeto = pila.pop()
        _devolver(pila, temporal)
        pila.append(objeto)                    
        pila.pop()                           
        temporal = _sacar(pila, indice)
        pila.append(objeto)
        _devolver(pila, temporal)
    return operacion

def recorrer_lista(n):
    inv, _ = preparar_lista(n)

    def operacion():
        for _objeto in inv:
            pass
    return operacion


def recorrer_arreglo(n):
    a = [Obj(i) for i in range(n)]

    def operacion():
        for _objeto in a:
            pass
    return operacion


def tabla(titulo, filas):
    print("\n=== %s ===" % titulo)
    print("%-8s %-8s | %-18s | %-18s | %-10s | %-10s" %
          ("n", "pos.", "lista (cursor) us", "lista (sin cursor)", "arreglo us", "pila us"))
    for n, nombre, a, b, c, d in filas:
        print("%-8d %-8s | %18.2f | %18.2f | %10.2f | %10.2f" % (n, nombre, a, b, c, d))


def comparar(titulo, lista_fn, arreglo_fn, pila_fn):
    filas = []
    for n in TAMANOS:
        for nombre, indice in posiciones(n):
            r = repeticiones(n, 1)
            filas.append((
                n, nombre,
                medir(lista_fn(n, indice, True), r),
                medir(lista_fn(n, indice, False), repeticiones(n, 40)),
                medir(arreglo_fn(n, indice), r),
                medir(pila_fn(n, indice), repeticiones(n, 60)),
            ))
    tabla(titulo, filas)


def main():
    print("Medición del inventario: microsegundos por operación (mejor de %d corridas)." % CORRIDAS)
    comparar("Soltar el objeto visto y deshacer", lista_soltar, arreglo_soltar, pila_soltar)
    comparar("Equipar (al frente) y deshacer", lista_equipar, arreglo_equipar, pila_equipar)
    print("\n=== Recorrer todo el inventario hacia adelante (la pila no se puede recorrer sin vaciarla) ===")
    print("%-8s | %-12s | %-12s" % ("n", "lista us", "arreglo us"))
    for n in TAMANOS:
        r = repeticiones(n, 1)
        print("%-8d | %12.2f | %12.2f" % (n, medir(recorrer_lista(n), r), medir(recorrer_arreglo(n), r)))


if __name__ == "__main__":
    main()