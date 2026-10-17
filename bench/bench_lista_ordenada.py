import time
from modelo.estructuras.lista_ordenada import ListaOrdenada


def buscar_lineal(lista, clave):
    for par in lista:
        if par[0] == clave:
            return par[1]
    return None


def medir(funcion, repeticiones):
    inicio = time.perf_counter()
    for i in range(repeticiones):
        funcion()
    return (time.perf_counter() - inicio) / repeticiones


def comparar_busquedas():
    print("n      | ordenada (us) | lineal (us) | lineal/ordenada")
    for n in [25, 100, 1000, 10000]:
        ordenada = ListaOrdenada()
        lista = []
        for i in range(n):
            clave = "itm_" + str((i * 37) % n)   
            ordenada.insertar(clave, i)
            lista.append([clave, i])

        buscadas = []
        for i in range(0, n, max(1, n // 20)):
            buscadas.append("itm_" + str(i))
        buscadas.append("itm_" + str(n - 1))
        buscadas.append("no_existe")

        def con_ordenada():
            for c in buscadas:
                ordenada.buscar(c)

        def con_lista():
            for c in buscadas:
                buscar_lineal(lista, c)

        rep = 200 if n <= 1000 else 20
        t_ord = medir(con_ordenada, rep) / len(buscadas) * 1000000
        t_lin = medir(con_lista, rep) / len(buscadas) * 1000000
        print(f"{n:<6} | {t_ord:13.3f} | {t_lin:11.3f} | {t_lin / t_ord:15.1f}")


def comparar_inserciones():
    print("\nn      | uno a uno (ms) | insertar_muchos (ms)")
    for n in [25, 100, 1000, 5000, 10000]:
        pares = []
        for i in range(n):
            pares.append(["itm_" + str((i * 37) % n), i])

        inicio = time.perf_counter()
        a = ListaOrdenada()
        for p in pares:
            a.insertar(p[0], p[1])
        t_uno = (time.perf_counter() - inicio) * 1000

        inicio = time.perf_counter()
        b = ListaOrdenada()
        b.insertar_muchos(pares)
        t_muchos = (time.perf_counter() - inicio) * 1000

        print(f"{n:<6} | {t_uno:14.3f} | {t_muchos:20.3f}")


def medir_eliminar():
    print("\nn      | eliminar y reinsertar una clave (us)")
    for n in [25, 100, 1000, 10000]:
        t = ListaOrdenada()
        for i in range(n):
            t.insertar("itm_" + str((i * 37) % n), i)
        clave = "itm_" + str(n // 2)

        def operacion():
            t.eliminar(clave)
            t.insertar(clave, 0)

        rep = 500 if n <= 1000 else 50
        print(f"{n:<6} | {medir(operacion, rep) * 1000000:.3f}")


if __name__ == "__main__":
    comparar_busquedas()
    comparar_inserciones()
    medir_eliminar()