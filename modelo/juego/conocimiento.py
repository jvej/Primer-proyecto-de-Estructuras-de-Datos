"""Conocimiento del jugador (T003, C6).

Las mutaciones posteriores a la construcción corresponden a Partida y deben
pasar por partida.cambiar, incluidos los contadores. Este contenedor no observa
el mundo, no descubre salas y no notifica eventos por su cuenta.
"""

from modelo.juego.sala import Sala, Salida

ESTADO_DESCONOCIDA = 0
ESTADO_AVISTADA = 1
ESTADO_EXPLORADA = 2

PUERTA_DESCONOCIDA = 0
PUERTA_ABIERTA = 1
PUERTA_CERRADA = 2


class ConocimientoMapa:
    def __init__(self, n: int, salas_por_indice: list[Sala], mapa) -> None:
        if type(n) is not int or n < 0:
            raise ValueError("n debe ser un entero no negativo")
        if salas_por_indice is not mapa.salas or len(salas_por_indice) != n:
            raise ValueError("se requiere la referencia mapa.salas con tamaño n")
        for i in range(n):
            if type(salas_por_indice[i].indice) is not int or salas_por_indice[i].indice != i:
                raise ValueError("los índices de las salas deben ser contiguos")
        self.total_salas = n
        self.salas_por_indice = salas_por_indice
        self.mapa = mapa
        self.estado_salas = [ESTADO_DESCONOCIDA] * n
        self.memoria_puertas = [PUERTA_DESCONOCIDA] * (4 * n)
        self.num_exploradas = 0
        self.num_avistadas = 0

    def _indice(self, sala: Sala) -> int:
        i = sala.indice
        if (type(i) is not int or not 0 <= i < self.total_salas
                or self.salas_por_indice[i] is not sala):
            raise ValueError("la sala no pertenece a este mapa")
        return i

    def estado_sala(self, sala: Sala) -> int:
        return self.estado_salas[self._indice(sala)]

    def es_explorada(self, sala: Sala) -> bool:
        return self.estado_sala(sala) == ESTADO_EXPLORADA

    def es_avistada(self, sala: Sala) -> bool:
        return self.estado_sala(sala) == ESTADO_AVISTADA

    def estado_por_id(self, id_sala: int) -> int:
        """Consulta O(log N), mediante el índice binario existente de Mapa."""
        sala = self.mapa.sala(id_sala)
        return ESTADO_DESCONOCIDA if sala is None else self.estado_sala(sala)

    def puerta_recordada(self, sala: Sala, dir_idx: int) -> int:
        if type(dir_idx) is not int or not 0 <= dir_idx < 4:
            raise ValueError("la dirección debe ser un índice entre 0 y 3")
        return self.memoria_puertas[self._indice(sala) * 4 + dir_idx]

    def puerta_recordada_abierta(self, salida: Salida) -> bool:
        """Consulta solo memoria; extremos desconocidos o discrepantes bloquean.

        El consumidor debe comprobar además que ambas salas estén exploradas.
        Partida sincronizará ambas posiciones al observar esta misma puerta.
        """
        for sala in (salida.sala_a, salida.sala_b):
            self._indice(sala)
            for direccion in range(4):
                if sala.salidas[direccion] is salida:
                    if self.puerta_recordada(sala, direccion) != PUERTA_ABIERTA:
                        return False
                    break
            else:
                return False
        return True

    def resumen(self) -> tuple[int, int]:
        """O(1): los contadores se mantienen mediante partida.cambiar."""
        return self.num_exploradas, self.num_avistadas
