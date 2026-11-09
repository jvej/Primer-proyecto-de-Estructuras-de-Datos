"""Selección de un paso de IR_A; no ejecuta acciones ni escribe en el log.

El futuro controlador compuesto debe invocar siguiente_paso antes de cada
movimiento ordinario. Crear otro planificador al reemplazar mapa/conocimiento.
"""

from dataclasses import dataclass

from modelo.estructuras.dijkstra import dijkstra_acotado
from modelo.juego.sala import DIRECCIONES


@dataclass(frozen=True)
class PasoPlanificado:
    estado: str  # "paso", "destino" o "rechazado"
    direccion: str | None = None
    id_siguiente: int | None = None
    costo_total: int | None = None
    motivo: str = ""


class PlanificadorRutas:
    def __init__(self, mapa, conocimiento) -> None:
        if conocimiento.mapa is not mapa:
            raise ValueError("mapa y conocimiento deben corresponder")
        self.mapa = mapa
        self.conocimiento = conocimiento
        n = len(mapa.salas)
        self._dist_navegacion = [0] * n
        self._marca_navegacion = [0] * n
        self._token_navegacion = 0

    def _transitable(self, salida) -> bool:
        c = self.conocimiento
        return (c.es_explorada(salida.sala_a)
                and c.es_explorada(salida.sala_b)
                and c.puerta_recordada_abierta(salida))

    def siguiente_paso(self, origen, id_destino: int) -> PasoPlanificado:
        """Calcula sobre memoria vigente, sin observar puertas físicas.

        La distancia se obtiene desde el destino porque el mapa es no dirigido.
        Se elige min(costo + distancia_vecina, id_vecina), no el menor ID de
        predecesor de Dijkstra. Solo se modifica la memoria de trabajo propia.
        """
        if type(id_destino) is not int or id_destino <= 0:
            return PasoPlanificado("rechazado", motivo="Identificador de destino inválido.")
        destino = self.mapa.sala(id_destino)
        if destino is None or not self.conocimiento.es_explorada(destino):
            return PasoPlanificado("rechazado", motivo="La sala destino no está explorada o no existe.")
        if not self.conocimiento.es_explorada(origen):
            return PasoPlanificado("rechazado", motivo="La sala de origen no está explorada.")
        if origen is destino:
            return PasoPlanificado("destino", costo_total=0, motivo="Ya te encuentras en esa sala.")

        self._token_navegacion += 1
        token = self._token_navegacion
        dist, marca = dijkstra_acotado(
            origen=destino, mapa=self.mapa, filtro_salida=self._transitable,
            cota_rango=None, token_busqueda=token,
            arreglo_dist=self._dist_navegacion,
            arreglo_marca=self._marca_navegacion,
        )
        if marca[origen.indice] != token:
            return PasoPlanificado("rechazado", motivo="No hay ruta conocida disponible hacia el destino.")

        mejor = None
        for i in range(len(DIRECCIONES)):
            salida = origen.salidas[i]
            if salida is None or not self._transitable(salida):
                continue
            vecina = salida.otro_lado(origen)
            if marca[vecina.indice] != token:
                continue
            candidato = (salida.costo + dist[vecina.indice], vecina.id, i)
            if mejor is None or candidato < mejor:
                mejor = candidato
        if mejor is None:
            return PasoPlanificado("rechazado", motivo="No hay ruta conocida disponible hacia el destino.")
        costo, id_vecina, direccion = mejor
        return PasoPlanificado("paso", DIRECCIONES[direccion], id_vecina, costo)
