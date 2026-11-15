"""Dijkstra acotado compartido (contrato C3).

Función sin estado: no guarda nada a nivel de módulo. Los arreglos de distancia y de
marca, y el número de búsqueda, los administra quien llama (el cazador de Mariano y
"ir a" de Kim tienen cada uno los suyos), así dos búsquedas nunca se pisan.

Marcas de búsqueda: una sala cuenta como alcanzada solo si
arreglo_marca[sala.indice] == token_busqueda. Así no hace falta reiniciar los arreglos
entre búsquedas; basta usar un token nuevo en cada llamada. Un token ya usado con los
mismos arreglos mezclaría resultados viejos con los nuevos.
"""

from typing import Callable, List, Optional

from modelo.estructuras.monticulo_min import MonticuloMin


def dijkstra_acotado(
    origen,
    mapa,
    filtro_salida: Callable,
    cota_rango: Optional[int] = None,
    token_busqueda: int = 1,
    arreglo_dist: Optional[List[int]] = None,
    arreglo_marca: Optional[List[int]] = None,
):
    """Distancias mínimas (suma de costos de salida) desde `origen`.

    filtro_salida(salida) -> bool decide qué salidas se pueden atravesar.
    cota_rango: si no es None, no se expande ningún camino de costo mayor a la cota.
    Devuelve (arreglo_dist, arreglo_marca). Para una sala v alcanzada,
    arreglo_marca[v.indice] == token_busqueda y arreglo_dist[v.indice] es su distancia.
    """
    salas = mapa.salas
    n = len(salas)
    if arreglo_dist is None:
        arreglo_dist = [0] * n
    if arreglo_marca is None:
        arreglo_marca = [0] * n
    if len(arreglo_dist) < n or len(arreglo_marca) < n:
        raise ValueError("los arreglos deben tener al menos una posición por sala")

    arreglo_dist[origen.indice] = 0
    arreglo_marca[origen.indice] = token_busqueda

    cola = MonticuloMin()
    cola.insertar((0, origen.id, origen.indice))
    while not cola.es_vacio():
        distancia, _, indice = cola.extraer_min()
        if distancia > arreglo_dist[indice]:
            continue    
        sala = salas[indice]
        for salida in sala.salidas:       
            if salida is None or not filtro_salida(salida):
                continue
            vecina = salida.otro_lado(sala)
            nueva = distancia + salida.costo
            if cota_rango is not None and nueva > cota_rango:
                continue
            j = vecina.indice
            if arreglo_marca[j] != token_busqueda or nueva < arreglo_dist[j]:
                arreglo_marca[j] = token_busqueda
                arreglo_dist[j] = nueva
                cola.insertar((nueva, vecina.id, j))
    return arreglo_dist, arreglo_marca