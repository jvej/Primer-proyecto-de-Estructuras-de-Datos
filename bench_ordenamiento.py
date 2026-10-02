import time
import random
from ordenamiento import ordenar_insercion, ordenar_merge, ordenar

SEMILLA = 42

class Contador:
    comparaciones = 0

    def __init__(self, valor):
        self.valor = valor

    def __gt__(self, otro):
        Contador.comparaciones += 1
        return self.valor > otro.valor

    def __lt__(self, otro):
        Contador.comparaciones += 1
        return self.valor < otro.valor


class Costoso:
    def __init__(self, valor):
        self.valor = valor

    def _trabajo(self):
        total = 0
        for i in range(100):
            total += i

    def __gt__(self, otro):
        self._trabajo()
        return self.valor > otro.valor

    def __lt__(self, otro):
        self._trabajo()
        return self.valor < otro.valor


def datos_aleatorios(n, azar):
    lista = []
    for i in range(n):
        lista.append(azar.randint(0, n * 10))
    return lista


def datos_casi_ordenados(n, azar):
    lista = list(range(n))
    cambios = n // 20      
    for i in range(cambios):
        a = azar.randint(0, n - 1)
        b = azar.randint(0, n - 1)
        lista[a], lista[b] = lista[b], lista[a]
    return lista


def datos_inversos(n, azar):
    lista = []
    for i in range(n, 0, -1):
        lista.append(i)
    return lista


def medir_tiempo(funcion, datos, clave, repeticiones):
    tiempos = []
    for i in range(repeticiones):
        inicio = time.perf_counter()
        funcion(datos, clave=clave)
        fin = time.perf_counter()
        tiempos.append(fin - inicio)
    tiempos = ordenar(tiempos)         
    return tiempos[len(tiempos) // 2]   


def contar_comparaciones(funcion, datos):
    Contador.comparaciones = 0
    funcion(datos, clave=Contador)
    return Contador.comparaciones


def repeticiones_para(n):
    if n >= 5000:
        return 3
    return 7


def comparar_algoritmos():
    azar = random.Random(SEMILLA)
    tamanos = [10, 20, 50, 100, 1000, 5000]
    escenarios = [
        ("aleatorio", datos_aleatorios),
        ("casi ordenado", datos_casi_ordenados),
        ("casi ordenado local", datos_casi_ordenados_local),
        ("inverso", datos_inversos),
    ]

    for nombre, generador in escenarios:
        print("\n=== Escenario:", nombre, "===")
        print("n      | ins (ms) | merge (ms) | auto (ms) | ins comp | merge comp")
        for n in tamanos:
            datos = generador(n, azar)
            rep = repeticiones_para(n)
            t_ins = medir_tiempo(ordenar_insercion, datos, None, rep) * 1000
            t_mer = medir_tiempo(ordenar_merge, datos, None, rep) * 1000
            t_aut = medir_tiempo(ordenar, datos, None, rep) * 1000
            c_ins = contar_comparaciones(ordenar_insercion, datos)
            c_mer = contar_comparaciones(ordenar_merge, datos)
            print(f"{n:<6} | {t_ins:8.3f} | {t_mer:10.3f} | {t_aut:9.3f} | {c_ins:8} | {c_mer:10}")


def comparar_costosas():
    azar = random.Random(SEMILLA)
    print("\n=== Comparaciones costosas (datos aleatorios) ===")
    print("n      | ins (ms) | merge (ms)")
    for n in [50, 100, 500, 1000]:
        datos = datos_aleatorios(n, azar)
        t_ins = medir_tiempo(ordenar_insercion, datos, Costoso, 3) * 1000
        t_mer = medir_tiempo(ordenar_merge, datos, Costoso, 3) * 1000
        print(f"{n:<6} | {t_ins:8.2f} | {t_mer:10.2f}")


def referencia_sorted():
   
    azar = random.Random(SEMILLA)
    print("\n=== Referencia: sorted() de Python (no se usa en el programa) ===")
    for n in [100, 1000, 5000]:
        datos = datos_aleatorios(n, azar)
        tiempos = []
        for i in range(5):
            inicio = time.perf_counter()
            sorted(datos)
            tiempos.append(time.perf_counter() - inicio)
        tiempos = ordenar(tiempos)
        print(f"n={n}: {tiempos[2] * 1000:.3f} ms")

def datos_casi_ordenados_local(n, azar):
    lista = list(range(n))
    for i in range(n // 20):
        a = azar.randint(0, n - 2)
        lista[a], lista[a + 1] = lista[a + 1], lista[a] 
    return lista


if __name__ == "__main__":
    comparar_algoritmos()
    comparar_costosas()
    referencia_sorted()