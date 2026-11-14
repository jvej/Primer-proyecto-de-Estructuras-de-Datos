"""Planificador de rutas y comportamiento del cazador (FR-003..FR-007, Contrato C3).

Utiliza la bÃºsqueda compartida dijkstra_acotado desde la posiciÃ³n del jugador,
con arreglos persistentes indexados por Sala.indice y tokens de bÃºsqueda para
reinicio O(1) sin tocar la memoria completa del mapa.
"""

from modelo.estructuras.dijkstra import dijkstra_acotado
from modelo.juego.mapa import normalizar_comportamiento


class PlanificadorCazador:
    def __init__(self, mapa) -> None:
        self.mapa = mapa
        n = len(mapa.salas)
        self._arreglo_dist = [0] * n
        self._arreglo_marca = [0] * n
        self._token_busqueda = 0

    def _asegurar_capacidad(self) -> None:
        n = len(self.mapa.salas)
        if len(self._arreglo_dist) < n:
            delta = n - len(self._arreglo_dist)
            self._arreglo_dist.extend([0] * delta)
            self._arreglo_marca.extend([0] * delta)

    def invalidar_todo(self) -> None:
        """Invalida cualquier cÃ¡lculo previo incrementando el token de bÃºsqueda."""
        self._token_busqueda += 1

    def calcular_campo_compartido(self, origen_jugador, cota_rango: int) -> None:
        """Calcula distancias mÃ­nimas desde el jugador hacia todo el esqueleto acotado al rango."""
        self._asegurar_capacidad()
        self._token_busqueda += 1
        dijkstra_acotado(
            origen=origen_jugador,
            mapa=self.mapa,
            filtro_salida=lambda salida: salida.esta_abierta(),
            cota_rango=cota_rango,
            token_busqueda=self._token_busqueda,
            arreglo_dist=self._arreglo_dist,
            arreglo_marca=self._arreglo_marca,
        )

    def decidir_movimiento(self, cazador, partida):
        """Determina la vecina y salida hacia la que avanza el cazador.

        Retorna (mejor_vecino, mejor_salida) si avanza, o (None, None) si espera.
        """
        # Ataca si comparte sala con el jugador (lo maneja resolver_turno)
        if cazador.sala is partida.jugador.sala:
            return None, None

        if cazador.rango <= 0:
            return None, None

        # Rango mÃ¡ximo entre cazadores activos y vivos
        rango_max = cazador.rango
        for e in partida.mapa.enemigos:
            if e.esta_vivo() and e.activo and normalizar_comportamiento(e.comportamiento) == "cazador":
                if e.rango > rango_max:
                    rango_max = e.rango

        self.calcular_campo_compartido(partida.jugador.sala, cota_rango=rango_max)

        u = cazador.sala
        if self._arreglo_marca[u.indice] != self._token_busqueda:
            return None, None

        distancia_cazador = self._arreglo_dist[u.indice]
        if distancia_cazador > cazador.rango:
            return None, None

        mejor_vecino = None
        mejor_salida = None
        min_costo_total = None

        for salida in u.salidas:
            if salida is None or not salida.esta_abierta():
                continue
            vecino = salida.otro_lado(u)
            if vecino is None:
                continue
            if self._arreglo_marca[vecino.indice] != self._token_busqueda:
                continue

            costo_total = salida.costo + self._arreglo_dist[vecino.indice]
            if min_costo_total is None or costo_total < min_costo_total:
                min_costo_total = costo_total
                mejor_vecino = vecino
                mejor_salida = salida
            elif costo_total == min_costo_total:
                # Desempate determinista por menor ID entero
                if vecino.id < mejor_vecino.id:
                    mejor_vecino = vecino
                    mejor_salida = salida

        if mejor_vecino is not None and min_costo_total == distancia_cazador:
            return mejor_vecino, mejor_salida

        return None, None
