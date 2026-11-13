"""Datos sintéticos compartidos por los benches, sin red, disco ni vista.

Ejemplo mínimo (todas las respuestas quedan en memoria)::

    from bench.generador_criptas import generar_cripta
    from modelo.datos.esqueleto import Esqueleto

    datos = generar_cripta(numero_salas=12, semilla=7, cadena_llaves=3,
                          rango_costos=(40, 200), cantidad_cazadores=4,
                          rango_cazadores=600, cierre_automatico=300)
    esqueleto = Esqueleto()
    for pagina in datos["paginas"]:
        esqueleto.agregar_pagina(pagina)
    ubicaciones = datos["llaves"]["llaves"]

Ejemplo de cuadrícula con rangos de cazador variables::

    cuadricula = generar_cripta(numero_salas=36, semilla=7,
                                topologia="cuadricula", rango_costos=(40, 200),
                                cadena_llaves=5, cantidad_cazadores=12,
                                rango_cazadores=(200, 800))

El resultado es un registro con respuestas del mismo formato que la API:
``general``, ``paginas`` (lista de respuestas de salas), ``contenido``
({"contenido": [...]}), ``catalogo`` ({"entidades": [...]}), ``llaves``
({"llaves": [...]}) y ``version_catalogo`` ({"version": ...}). Los diccionarios
son registros de salida, no índices ni cachés; las posiciones usan listas.

``topologia`` admite "linea" (por defecto) o "cuadricula", ambas bidireccionales.
La cuadrícula tiene ancho ceil(sqrt(numero_salas)) y numera en serpiente: cada
fila alterna el sentido y la última puede quedar incompleta. Cada salida sortea
su costo independientemente, incluso respecto de su inversa. Con al menos cuatro
salas y un rango de costos no constante se garantiza un par de rutas alternativas
de distinto costo. Con menos salas no hay espacio para un circuito; un rango
constante conserva ese costo en todas las salidas.

``cadena_llaves`` cuenta todas las
llaves, incluida la de salida: debe estar entre 1 y numero_salas - 1. Cada llave
aparece después de la etapa anterior y antes de la suya. En cuadrícula, todos
los enlaces que entran a una etapa posterior piden la llave de esa etapa, para
conservar la cadena aun con caminos alternativos. Los cazadores pueden portarlas
en su ``suelta``. ``rango_cazadores`` admite un entero >= 0 o una tupla inclusiva
(mínimo, máximo) de enteros >= 0; cada cazador sortea su rango en ese intervalo,
medido en unidades de costo. Un entero asigna el mismo rango a todos.
``cierre_automatico`` es el tiempo de cierre de las puertas de la cadena (0 lo
omite). ``rango_costos`` incluye ambos extremos; ``salas_por_pagina`` controla
la paginación. Cantidades inválidas producen ValueError, sin ajustes silenciosos.

Con los mismos parámetros y semilla se obtienen respuestas idénticas y nuevas
en cada llamada. El Random local solo genera fixtures; no altera el azar de
ninguna partida. La versión incluye los parámetros para distinguir los datos.
"""

from math import isqrt
from random import Random


def _crear_salas(numero_salas, topologia, minimo, maximo, azar):
    salas = []
    # La línea mantiene los costos compartidos entre las dos caras de cada puerta.
    costos = ([azar.randint(minimo, maximo) for _ in range(numero_salas - 1)]
              if topologia == "linea" else [])
    ancho = isqrt(numero_salas - 1) + 1
    for posicion in range(numero_salas):
        salidas = {}
        if topologia == "linea":
            if posicion + 1 < numero_salas:
                salidas["N"] = {"sala": posicion + 2, "costo": costos[posicion]}
            if posicion > 0:
                salidas["S"] = {"sala": posicion, "costo": costos[posicion - 1]}
        else:
            fila, columna = divmod(posicion, ancho)
            if fila % 2:
                columna = ancho - 1 - columna
            for direccion, df, dc in (("N", -1, 0), ("S", 1, 0), ("E", 0, 1), ("O", 0, -1)):
                fila_vecina, columna_vecina = fila + df, columna + dc
                if fila_vecina < 0 or not 0 <= columna_vecina < ancho:
                    continue
                desplazamiento = (columna_vecina if fila_vecina % 2 == 0
                                  else ancho - 1 - columna_vecina)
                destino = fila_vecina * ancho + desplazamiento
                if destino < numero_salas:
                    salidas[direccion] = {"sala": destino + 1, "costo": azar.randint(minimo, maximo)}
        salas.append({"id": posicion + 1, "nombre": "Sala sintética %d" % (posicion + 1),
                      "salidas": salidas})
    return salas


def _distinguir_rutas(salas, minimo, maximo, azar):
    """Evita un empate casual de costos en el primer circuito de cuatro salas."""
    if minimo == maximo:
        return
    for sala in salas:
        salidas = sala["salidas"]
        if "E" not in salidas or "S" not in salidas:
            continue
        este, sur = salidas["E"], salidas["S"]
        desde_este = salas[este["sala"] - 1]["salidas"]
        desde_sur = salas[sur["sala"] - 1]["salidas"]
        if "S" not in desde_este or "E" not in desde_sur:
            continue
        if este["costo"] + desde_este["S"]["costo"] == sur["costo"] + desde_sur["E"]["costo"]:
            # Sorteo uniforme entre los costos permitidos salvo el que empata.
            nuevo = azar.randint(minimo, maximo - 1)
            este["costo"] = nuevo + (nuevo >= este["costo"])
        return


def generar_cripta(numero_salas=10, semilla=0, rango_costos=(100, 100),
                   cantidad_cazadores=0, rango_cazadores=500, cadena_llaves=1,
                   cierre_automatico=0, salas_por_pagina=50, topologia="linea"):
    """Construye una cripta sintética resoluble con una cadena de llaves."""
    enteros = (numero_salas, semilla, cantidad_cazadores,
               cadena_llaves, cierre_automatico, salas_por_pagina)
    if any(type(valor) is not int for valor in enteros):
        raise ValueError("Los tamaños, la semilla, el rango y el cierre deben ser enteros")
    if numero_salas < 2 or not 1 <= cadena_llaves < numero_salas:
        raise ValueError("Se requieren al menos dos salas y entre 1 y salas - 1 llaves")
    if cantidad_cazadores < 0 or cierre_automatico < 0:
        raise ValueError("Cazadores y cierre no pueden ser negativos")
    if type(rango_cazadores) is int:
        rango_minimo = rango_maximo = rango_cazadores
    elif (isinstance(rango_cazadores, tuple) and len(rango_cazadores) == 2
          and all(type(valor) is int for valor in rango_cazadores)):
        rango_minimo, rango_maximo = rango_cazadores
    else:
        raise ValueError("rango_cazadores debe ser un entero o una tupla de dos enteros")
    if not 0 <= rango_minimo <= rango_maximo:
        raise ValueError("Los rangos de cazador deben cumplir 0 <= mínimo <= máximo")
    if topologia not in ("linea", "cuadricula"):
        raise ValueError("topologia debe ser 'linea' o 'cuadricula'")
    if salas_por_pagina < 1:
        raise ValueError("salas_por_pagina debe ser positivo")
    if (not isinstance(rango_costos, (tuple, list)) or len(rango_costos) != 2
            or any(type(valor) is not int for valor in rango_costos)):
        raise ValueError("rango_costos debe contener dos enteros")
    minimo, maximo = rango_costos
    if minimo < 1 or maximo < minimo:
        raise ValueError("Los costos deben cumplir 1 <= mínimo <= máximo")

    azar = Random(semilla)
    salas = _crear_salas(numero_salas, topologia, minimo, maximo, azar)
    if topologia == "cuadricula":
        _distinguir_rutas(salas, minimo, maximo, azar)
    contenido = [{"sala": sala["id"], "enemigos": [], "objetos": [], "trampas": []} for sala in salas]

    fichas = []
    llaves = []
    # Arreglo por posición de sala, sin búsquedas por ID en tablas de Python.
    llaves_por_sala = [[] for _ in range(numero_salas)]
    etapas = [cadena_llaves] * numero_salas
    sala_llave = 1
    for indice in range(cadena_llaves):
        id_llave = "itm_sintetica_%04d" % (indice + 1)
        origen = (indice + 1) * (numero_salas - 1) // cadena_llaves
        for posicion in range(sala_llave - 1, origen):
            etapas[posicion] = indice
        ubicacion = {"id": id_llave, "sala": sala_llave}
        llaves.append(ubicacion)
        llaves_por_sala[sala_llave - 1].append(ubicacion)
        contenido[sala_llave - 1]["objetos"].append(id_llave)
        fichas.append({"id": id_llave, "clase": "llave", "nombre": "Llave %d" % (indice + 1),
                       "peso": 1, "valor": 1, "abre": id_llave})
        sala_llave = origen + 1

    for posicion, sala in enumerate(salas):
        for salida in sala["salidas"].values():
            etapa_destino = etapas[salida["sala"] - 1]
            if etapas[posicion] != etapa_destino:
                etapa_puerta = max(etapas[posicion], etapa_destino)
                salida["cerrada"] = True
                salida["llave"] = llaves[etapa_puerta - 1]["id"]
                if cierre_automatico > 0:
                    salida["cierre_automatico"] = cierre_automatico

    for indice in range(cantidad_cazadores):
        posicion = azar.randrange(numero_salas - 1)
        instancia = "e-sintetico-%d" % (indice + 1)
        tipo = "ent_cazador_sintetico_%d" % (indice + 1)
        suelta = []
        for ubicacion in llaves_por_sala[posicion]:
            if "enemigo" not in ubicacion:
                ubicacion["enemigo"] = instancia
                suelta.append(ubicacion["id"])
        if suelta:
            contenido[posicion]["objetos"] = []
        contenido[posicion]["enemigos"].append({"instancia": instancia, "tipo": tipo, "vida": 10})
        rango = (rango_minimo if rango_minimo == rango_maximo
                 else azar.randint(rango_minimo, rango_maximo))
        fichas.append({"id": tipo, "clase": "enemigo", "nombre": "Cazador %d" % (indice + 1),
                       "vida_max": 10, "ataque": 4, "defensa": 1, "velocidad": 100,
                       "comportamiento": "cazador", "rango": rango, "suelta": suelta})

    total_paginas = (numero_salas + salas_por_pagina - 1) // salas_por_pagina
    paginas = []
    for indice in range(total_paginas):
        inicio = indice * salas_por_pagina
        paginas.append({"pagina": indice + 1, "total_paginas": total_paginas,
                        "salas": salas[inicio:inicio + salas_por_pagina]})
    version = "g2-%s-%d-%d-%d-%d-%d-%d-%d-%d-%d-%d" % (
        topologia, semilla, numero_salas, minimo, maximo, cantidad_cazadores, rango_minimo, rango_maximo,
        cadena_llaves, cierre_automatico, salas_por_pagina)
    general = {"id": "sintetica-%d" % semilla, "version": version, "salas_total": numero_salas,
               "paginas": total_paginas, "salas_por_pagina": salas_por_pagina,
               "sala_inicial": 1, "sala_salida": numero_salas, "llave_salida": llaves[-1]["id"],
               "presupuesto_solicitudes": 10 + numero_salas + cantidad_cazadores + cadena_llaves,
               "inventario_max": cadena_llaves,
               "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}}
    return {"general": general, "paginas": paginas, "contenido": {"contenido": contenido},
            "catalogo": {"entidades": fichas}, "llaves": {"llaves": llaves},
            "version_catalogo": {"version": version}}
