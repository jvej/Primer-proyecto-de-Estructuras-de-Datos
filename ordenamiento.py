UMBRAL_PEQUENO = 16     
PORCENTAJE_CASI = 0.10   


def _va_despues(a, b, descendente):
    if descendente:
        return a < b
    return a > b


def _armar_pares(datos, clave):
    pares = []
    for x in datos:
        if clave is None:
            pares.append([x, x])
        else:
            pares.append([clave(x), x])
    return pares


def _quitar_claves(pares):
    resultado = []
    for par in pares:
        resultado.append(par[1])
    return resultado

#Inserción

def _insercion_pares(pares, descendente):
    for i in range(1, len(pares)):
        actual = pares[i]
        j = i - 1
        while j >= 0 and _va_despues(pares[j][0], actual[0], descendente):
            pares[j + 1] = pares[j]
            j -= 1
        pares[j + 1] = actual
    return pares


def ordenar_insercion(datos, clave=None, descendente=False):
    pares = _armar_pares(datos, clave)
    pares = _insercion_pares(pares, descendente)
    return _quitar_claves(pares)

#Mergesort

def _mezclar(izq, der, descendente):
    resultado = []
    i = 0
    j = 0
    while i < len(izq) and j < len(der):
        if _va_despues(izq[i][0], der[j][0], descendente):
            resultado.append(der[j])
            j += 1
        else:
            resultado.append(izq[i])
            i += 1
    while i < len(izq):
        resultado.append(izq[i])
        i += 1
    while j < len(der):
        resultado.append(der[j])
        j += 1
    return resultado


def _merge_pares(pares, descendente):
    if len(pares) <= 1:
        return pares
    medio = len(pares) // 2
    izq = _merge_pares(pares[:medio], descendente)
    der = _merge_pares(pares[medio:], descendente)
    return _mezclar(izq, der, descendente)


def ordenar_merge(datos, clave=None, descendente=False):
    pares = _armar_pares(datos, clave)
    pares = _merge_pares(pares, descendente)
    return _quitar_claves(pares)


#Selector automático

def _porcentaje_desordenado(pares, descendente):
    """Fracción de pares vecinos que están fuera de orden. Una sola pasada."""
    if len(pares) < 2:
        return 0.0
    malos = 0
    for i in range(len(pares) - 1):
        if _va_despues(pares[i][0], pares[i + 1][0], descendente):
            malos += 1
    return malos / (len(pares) - 1)


def elegir_algoritmo(pares, descendente, comparacion_costosa=False):
    """Devuelve 'insercion' o 'merge' según propiedades medibles de los datos."""
    n = len(pares)
    if n <= UMBRAL_PEQUENO:
        return "insercion"
    if _porcentaje_desordenado(pares, descendente) <= PORCENTAJE_CASI:
        return "insercion"
    return "merge"   


def ordenar(datos, clave=None, descendente=False, comparacion_costosa=False):
    """Función que usa el resto del programa. Devuelve una lista NUEVA."""
    pares = _armar_pares(datos, clave)
    if elegir_algoritmo(pares, descendente, comparacion_costosa) == "insercion":
        pares = _insercion_pares(pares, descendente)
    else:
        pares = _merge_pares(pares, descendente)
    return _quitar_claves(pares)


if __name__ == "__main__":
    print(ordenar([5, 2, 9, 1, 5, 6]))
    print(ordenar([5, 2, 9, 1, 5, 6], descendente=True))
    print(ordenar(["luna", "sol", "estrella"], clave=len))
    datos = [("b", 1), ("a", 1), ("c", 0), ("d", 1)]
    print(ordenar_merge(datos, clave=lambda t: t[1]))
    print(ordenar_insercion(datos, clave=lambda t: t[1]))