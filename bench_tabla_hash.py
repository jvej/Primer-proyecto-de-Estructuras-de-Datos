import time
from tabla_hash import TablaHash

def buscar_lineal(lista, clave):
    for par in lista:
        if par[0] == clave:
            return par[1]
    return None


def medir(funcion, repeticiones):
    inicio = time.perf_counter()
    for i in range(repeticiones):
        funcion()
    fin = time.perf_counter()
    return (fin - inicio) / repeticiones


def comparar_busquedas():
    print("n      | hash (us) | lineal (us) | lineal/hash | cubeta mas larga")
    for n in [25, 100, 1000, 10000]:
        tabla = TablaHash()
        lista = [] 
        for i in range(n):
            clave = "itm_" + str(i)
            tabla.insertar(clave, i)
            lista.append([clave, i])

        buscadas = []
        for i in range(0, n, max(1, n // 20)):
            buscadas.append("itm_" + str(i))
        buscadas.append("itm_" + str(n - 1))
        buscadas.append("no_existe")

        def con_tabla():
            for c in buscadas:
                tabla.buscar(c)

        def con_lista():
            for c in buscadas:
                buscar_lineal(lista, c)

        rep = 200 if n <= 1000 else 20
        t_hash = medir(con_tabla, rep) / len(buscadas) * 1000000
        t_lin = medir(con_lista, rep) / len(buscadas) * 1000000
        print(f"{n:<6} | {t_hash:9.3f} | {t_lin:11.3f} | {t_lin / t_hash:11.1f} | {tabla.cubeta_mas_larga()}")


def medir_insercion():
    print("\nn      | insertar todo (ms)")
    for n in [25, 100, 1000, 10000]:
        inicio = time.perf_counter()
        tabla = TablaHash() 
        for i in range(n):
            tabla.insertar("itm_" + str(i), i)
        fin = time.perf_counter()
        print(f"{n:<6} | {(fin - inicio) * 1000:.3f}")


if __name__ == "__main__":
    comparar_busquedas()
    medir_insercion()