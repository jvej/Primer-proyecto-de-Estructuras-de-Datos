"""
Pruebas de aceptación y unitarias de la capacidad 002: niebla de guerra, mapa conocido
e "ir a".

Por ahora contiene las pruebas del contrato C3 (MonticuloMin y dijkstra_acotado), tarea
T007. Las pruebas de FR-001..FR-024 se agregan aquí a medida que se escriben T004, T008,
T015, T021 y T023 (primero la prueba, después el código).

Se ejecuta con: python -m tests.test_niebla_ir_a
"""

from modelo.estructuras.dijkstra import dijkstra_acotado
from modelo.estructuras.monticulo_min import MonticuloMin
from modelo.juego.sala import Sala


class MapaFalso:
    """Lo mínimo que usa dijkstra_acotado: la lista de salas indexada por Sala.indice."""

    def __init__(self, salas):
        self.salas = salas


def buscar(salas, id_sala):
    for sala in salas:
        if sala.id == id_sala:
            return sala
    raise ValueError("no existe la sala %r" % (id_sala,))


class SalasPorId:
    """Permite escribir s[3] para obtener la sala de id 3 (solo para las pruebas)."""

    def __init__(self, salas):
        self._salas = salas

    def __getitem__(self, id_sala):
        return buscar(self._salas, id_sala)


def armar_mapa(ids, conexiones):
    """ids: ids de sala en orden de índice. conexiones: (id_a, direccion, id_b, costo, estado)."""
    salas = []
    for posicion in range(len(ids)):
        sala = Sala(ids[posicion], "Sala %d" % ids[posicion])
        sala.indice = posicion
        salas.append(sala)
    for id_a, direccion, id_b, costo, estado in conexiones:
        sala_a = buscar(salas, id_a)
        sala_a.conectar(direccion, buscar(salas, id_b), estado, costo=costo)
    return MapaFalso(salas), SalasPorId(salas)


def abiertas(salida):
    return salida.esta_abierta()


def alcanzada(marcas, sala, token):
    return marcas[sala.indice] == token


# --- MonticuloMin

def test_C3_monticulo_min_insertar_extraer_orden_correcto():
    m = MonticuloMin()
    assert m.es_vacio() and len(m) == 0
    for valor in (50, 10, 40, 20, 30, 10, 60, 5):
        m.insertar((valor, 1))
    assert len(m) == 8
    obtenidos = []
    while not m.es_vacio():
        obtenidos.append(m.extraer_min()[0])
    assert obtenidos == [5, 10, 10, 20, 30, 40, 50, 60], obtenidos
    try:
        m.extraer_min()
        assert False, "extraer de un montículo vacío debe lanzar IndexError"
    except IndexError:
        pass


def test_C3_monticulo_min_desempate_por_menor_id():
    m = MonticuloMin()
    for id_sala in (9, 2, 7, 4):
        m.insertar((100, id_sala))
    m.insertar((50, 8))
    salida = []
    while not m.es_vacio():
        salida.append(m.extraer_min())
    assert salida == [(50, 8), (100, 2), (100, 4), (100, 7), (100, 9)], salida


# ---dijkstra_acotado

def test_C3_dijkstra_acotado_camino_minimo_correcto():
    mapa, s = armar_mapa([1, 2, 3], [
        (1, "E", 2, 100, "abierta"),
        (2, "E", 3, 100, "abierta"),
        (1, "S", 3, 350, "abierta"),
    ])
    dist, marca = dijkstra_acotado(s[1], mapa, abiertas, token_busqueda=1)
    assert dist[s[1].indice] == 0
    assert dist[s[2].indice] == 100
    assert dist[s[3].indice] == 200, "debe preferir la ruta de más salas y menor costo"
    for sala in mapa.salas:
        assert alcanzada(marca, sala, 1)


def test_C3_dijkstra_acotado_cota_rango():
    mapa, s = armar_mapa([1, 2, 3, 4], [
        (1, "E", 2, 100, "abierta"),
        (2, "E", 3, 100, "abierta"),
        (3, "E", 4, 100, "abierta"),
    ])
    dist, marca = dijkstra_acotado(s[1], mapa, abiertas, cota_rango=200, token_busqueda=1)
    assert alcanzada(marca, s[3], 1) and dist[s[3].indice] == 200, "costo igual a la cota se alcanza"
    assert not alcanzada(marca, s[4], 1), "costo mayor a la cota no se alcanza"
    dist2, marca2 = dijkstra_acotado(s[1], mapa, abiertas, cota_rango=None, token_busqueda=1)
    assert alcanzada(marca2, s[4], 1) and dist2[s[4].indice] == 300


def test_C3_dijkstra_acotado_filtro_de_salidas():
    mapa, s = armar_mapa([1, 2, 3], [
        (1, "E", 2, 100, "cerrada"),
        (2, "E", 3, 100, "abierta"),
    ])
    dist, marca = dijkstra_acotado(s[1], mapa, abiertas, token_busqueda=1)
    assert alcanzada(marca, s[1], 1)
    assert not alcanzada(marca, s[2], 1), "una salida cerrada no se atraviesa"
    assert not alcanzada(marca, s[3], 1)


def test_C3_dijkstra_acotado_determinismo_empates():
    conexiones = [
        (1, "E", 2, 100, "abierta"),
        (1, "S", 3, 100, "abierta"),
        (2, "S", 4, 100, "abierta"),
        (3, "E", 4, 100, "abierta"),
    ]
    mapa, s = armar_mapa([1, 2, 3, 4], conexiones)
    dist_a, marca_a = dijkstra_acotado(s[1], mapa, abiertas, token_busqueda=1)
    dist_b, marca_b = dijkstra_acotado(s[1], mapa, abiertas, token_busqueda=1)
    assert dist_a[s[4].indice] == 200
    assert dist_a == dist_b and marca_a == marca_b, "misma entrada, mismo resultado"
    dist_c, _ = dijkstra_acotado(s[4], mapa, abiertas, token_busqueda=1)
    assert dist_c[s[2].indice] == dist_c[s[3].indice] == 100


def test_C3_arreglos_llamadores_independientes_sin_interferencia():
    mapa, s = armar_mapa([1, 2, 3, 4], [
        (1, "E", 2, 100, "abierta"),
        (2, "E", 3, 100, "abierta"),
        (3, "E", 4, 100, "abierta"),
    ])
    n = len(mapa.salas)
    dist_cazador, marca_cazador = [0] * n, [0] * n
    dist_nav, marca_nav = [0] * n, [0] * n
    dijkstra_acotado(s[1], mapa, abiertas, cota_rango=300, token_busqueda=1,
                     arreglo_dist=dist_cazador, arreglo_marca=marca_cazador)
    copia_dist = list(dist_cazador)
    copia_marca = list(marca_cazador)
    dijkstra_acotado(s[4], mapa, abiertas, cota_rango=None, token_busqueda=1,
                     arreglo_dist=dist_nav, arreglo_marca=marca_nav)
    assert dist_cazador == copia_dist and marca_cazador == copia_marca, \
        "la búsqueda de navegación no debe tocar los arreglos del cazador"
    assert dist_nav[s[1].indice] == 300

    dijkstra_acotado(s[1], mapa, abiertas, cota_rango=100, token_busqueda=2,
                     arreglo_dist=dist_cazador, arreglo_marca=marca_cazador)
    assert alcanzada(marca_cazador, s[2], 2) and dist_cazador[s[2].indice] == 100
    assert not alcanzada(marca_cazador, s[3], 2), "la marca vieja (token 1) no vale para el token 2"


def test_C3_arreglos_demasiado_cortos_se_rechazan():
    mapa, s = armar_mapa([1, 2], [(1, "E", 2, 100, "abierta")])
    try:
        dijkstra_acotado(s[1], mapa, abiertas, arreglo_dist=[0], arreglo_marca=[0, 0])
        assert False, "debe lanzar ValueError si un arreglo es más corto que el mapa"
    except ValueError:
        pass


if __name__ == "__main__":
    pruebas = [
        test_C3_monticulo_min_insertar_extraer_orden_correcto,
        test_C3_monticulo_min_desempate_por_menor_id,
        test_C3_dijkstra_acotado_camino_minimo_correcto,
        test_C3_dijkstra_acotado_cota_rango,
        test_C3_dijkstra_acotado_filtro_de_salidas,
        test_C3_dijkstra_acotado_determinismo_empates,
        test_C3_arreglos_llamadores_independientes_sin_interferencia,
        test_C3_arreglos_demasiado_cortos_se_rechazan,
    ]
    for p in pruebas:
        p()
        print("OK", p.__name__)
    print("Todas las pruebas pasaron")