"""Planificador de rutas y comportamiento del cazador (FR-003..FR-008, Contrato C3).

Utiliza la búsqueda compartida dijkstra_acotado desde la posición del jugador,
con arreglos persistentes indexados por Sala.indice, tokens de búsqueda para
reinicio O(1) y reutilización selectiva con invalidación reactiva (Contrato C2).
"""

from typing import Optional
from modelo.estructuras.dijkstra import dijkstra_acotado
from modelo.juego.mapa import normalizar_comportamiento


class PlanificadorCazador:
    def __init__(self, mapa) -> None:
        self.mapa = mapa
        n = len(mapa.salas)
        self._arreglo_dist = [0] * n
        self._arreglo_marca = [0] * n
        self._token_busqueda = 0
        self._valido = False
        self._sala_jugador_id: Optional[int] = None
        self._rango_utilizado: Optional[int] = None
        self._calculos_realizados = 0
        self._reutilizaciones = 0

    def _asegurar_capacidad(self) -> None:
        n = len(self.mapa.salas)
        if len(self._arreglo_dist) < n:
            delta = n - len(self._arreglo_dist)
            self._arreglo_dist.extend([0] * delta)
            self._arreglo_marca.extend([0] * delta)

    def invalidar_todo(self) -> None:
        """Invalida cualquier cálculo previo incrementando el token de búsqueda."""
        self._valido = False
        self._token_busqueda += 1
        self._sala_jugador_id = None
        self._rango_utilizado = None

    def notificar_cambio_puerta(self, salida, estado_anterior: str, nuevo_estado: str) -> None:
        """Observador del Contrato C2.

        Invalida el campo únicamente si al menos un extremo de la puerta modificada
        pertenece a la región calculada (alcanzada con marca vigente y dist <= _rango_utilizado).
        Si ambos extremos están fuera de la región calculada, el campo se conserva válido.
        """
        if not self._valido or self._rango_utilizado is None:
            return

        a = salida.sala_a
        b = salida.sala_b

        extremo_afectado = False
        for s in (a, b):
            if s is not None and s.indice < len(self._arreglo_marca):
                if (self._arreglo_marca[s.indice] == self._token_busqueda
                        and self._arreglo_dist[s.indice] <= self._rango_utilizado):
                    extremo_afectado = True
                    break

        if extremo_afectado:
            self.invalidar_todo()

    def es_valido(self, partida, rango_requerido: int) -> bool:
        """Comprueba si el campo compartido vigente es reutilizable para el rango requerido."""
        if not self._valido:
            return False
        if partida.jugador.sala is None or self._sala_jugador_id != partida.jugador.sala.id:
            return False
        if self._rango_utilizado is None or rango_requerido > self._rango_utilizado:
            return False
        return True

    def calcular_campo_compartido(self, origen_jugador, cota_rango: int) -> None:
        """Calcula distancias mínimas desde el jugador hacia todo el esqueleto acotado al rango."""
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
        self._sala_jugador_id = origen_jugador.id
        self._rango_utilizado = cota_rango
        self._valido = True
        self._calculos_realizados += 1

    def decidir_movimiento(self, cazador, partida):
        """Determina la vecina y salida hacia la que avanza el cazador.

        Retorna (mejor_vecino, mejor_salida) si avanza, o (None, None) si espera.
        Reutiliza selectivamente el cálculo compartido si sigue siendo válido.
        """
        # Ataca si comparte sala con el jugador (lo maneja resolver_turno)
        if cazador.sala is partida.jugador.sala:
            return None, None

        if cazador.rango <= 0:
            return None, None

        # Rango máximo entre cazadores activos y vivos
        rango_max = cazador.rango
        for e in partida.mapa.enemigos:
            if e.esta_vivo() and e.activo and normalizar_comportamiento(e.comportamiento) == "cazador":
                if e.rango > rango_max:
                    rango_max = e.rango

        if not self.es_valido(partida, rango_max):
            self.calcular_campo_compartido(partida.jugador.sala, cota_rango=rango_max)
        else:
            self._reutilizaciones += 1

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
