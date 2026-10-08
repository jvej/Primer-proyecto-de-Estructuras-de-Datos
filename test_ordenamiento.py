# sorted() se usa SOLO para verificar resultados. El programa no lo usa.
import random
from ordenamiento import ordenar, ordenar_insercion, ordenar_merge

azar = random.Random(7)


def probar(funcion):
    assert funcion([]) == []
    assert funcion([5]) == [5]
    assert funcion([3, 1, 2]) == [1, 2, 3]
    assert funcion([3, 1, 2], descendente=True) == [3, 2, 1]

    datos = [1, 2, 2, 1, 3, 3, 2, 1]
    assert funcion(datos) == sorted(datos)

    for n in [10, 50, 200, 1000]:
        datos = []
        for i in range(n):
            datos.append(azar.randint(0, 100))
        assert funcion(datos) == sorted(datos)
        assert funcion(datos, descendente=True) == sorted(datos, reverse=True)

    original = [3, 1, 2]
    funcion(original)
    assert original == [3, 1, 2]

    pares = [("b", 1), ("a", 1), ("c", 0), ("d", 1)]
    esperado = [("c", 0), ("b", 1), ("a", 1), ("d", 1)]
    assert funcion(pares, clave=lambda t: t[1]) == esperado

    esperado_desc = [("b", 1), ("a", 1), ("d", 1), ("c", 0)]
    assert funcion(pares, clave=lambda t: t[1], descendente=True) == esperado_desc


for f in (ordenar_insercion, ordenar_merge, ordenar):
    probar(f)
    print(f.__name__, "OK")

datos = list(range(1000))
for i in range(0, 1000, 20):
    datos[i], datos[i + 1] = datos[i + 1], datos[i]
assert ordenar(datos) == sorted(datos)
print("casi ordenado local OK")