"""Agenda de eventos (§4.1): un heap binario propio sobre una lista.

list sí se permite como almacenamiento contiguo (§7); lo que no se permite
es heapq ni dict. La cancelación es perezosa: marcar un evento inválido es
O(1), y el descarte real pasa cuando ese evento llega a la cima del heap.

Si recibe un Registro, anota cómo deshacer cada cambio de la agenda (§4.6).
"""

from typing import List, Optional

from evento import Evento


class AgendaEventos:
    def __init__(self, registro=None) -> None:
        self._heap: List[Evento] = []
        self._siguiente_secuencia = 0
        self.registro = registro

    def __len__(self) -> int:
        return len(self._heap)

    def _inverso(self, deshacer) -> None:
        if self.registro is not None:
            self.registro.inverso(deshacer)

    def nueva_secuencia(self) -> int:
        """Números de secuencia crecientes para desempatar; nunca retroceden."""
        self._siguiente_secuencia += 1
        return self._siguiente_secuencia

    def agendar(self, evento: Evento) -> None:
        self._heap.append(evento)
        self._subir(len(self._heap) - 1)
        self._inverso(lambda: setattr(evento, "valido", False))   # deshacer = invalidarlo

    def cancelar(self, evento: Evento) -> None:
        """O(1): no hay que recorrer la agenda para cancelar un evento futuro."""
        if evento.valido:
            evento.valido = False
            self._inverso(lambda: setattr(evento, "valido", True))

    def reprogramar_por_cambio_velocidad(
        self,
        evento: Evento,
        tiempo_actual: int,
        velocidad_anterior: int,
        velocidad_nueva: int,
    ) -> Evento:
        """Reescala el tiempo restante de una acción ya programada (§2.3).

        restante_nuevo = max(1, (tiempo_siguiente - t) * velocidad_anterior // velocidad_nueva)
        tiempo_siguiente = t + restante_nuevo

        Cancela el evento viejo y agenda uno nuevo con número de secuencia nuevo.
        Si el evento viejo era el turno pendiente de su actor, el actor pasa a
        apuntar al nuevo, para que una cancelación posterior (muerte) lo alcance.
        """
        restante = evento.tiempo_siguiente - tiempo_actual
        restante_nuevo = max(1, restante * velocidad_anterior // velocidad_nueva)

        self.cancelar(evento)
        reagendado = Evento(
            tiempo_siguiente=tiempo_actual + restante_nuevo,
            secuencia=self.nueva_secuencia(),
            actor=evento.actor,
            accion=evento.accion,   # seguro: la acción lee el reloj al ejecutarse
            descripcion=evento.descripcion,
        )
        self.agendar(reagendado)

        actor = evento.actor
        if actor is not None and getattr(actor, "evento_pendiente", None) is evento:
            if self.registro is not None:
                self.registro.cambiar(actor, "evento_pendiente", reagendado)
            else:
                actor.evento_pendiente = reagendado
        return reagendado

    def siguiente(self) -> Optional[Evento]:
        """Extrae y devuelve el próximo evento válido, o None si no queda ninguno."""
        while self._heap:
            evento = self._extraer_minimo()
            self._inverso(lambda e=evento: self.agendar(e))       # deshacer = volver a meterlo
            if evento.valido:
                return evento
        return None

    # --- operaciones internas del heap ---

    def _extraer_minimo(self) -> Evento:
        raiz = self._heap[0]
        ultimo = self._heap.pop()
        if self._heap:
            self._heap[0] = ultimo
            self._bajar(0)
        return raiz

    def _subir(self, i: int) -> None:
        while i > 0:
            padre = (i - 1) // 2
            if self._heap[i] < self._heap[padre]:
                self._heap[i], self._heap[padre] = self._heap[padre], self._heap[i]
                i = padre
            else:
                break

    def _bajar(self, i: int) -> None:
        n = len(self._heap)
        while True:
            izq, der = 2 * i + 1, 2 * i + 2
            menor = i
            if izq < n and self._heap[izq] < self._heap[menor]:
                menor = izq
            if der < n and self._heap[der] < self._heap[menor]:
                menor = der
            if menor == i:
                break
            self._heap[i], self._heap[menor] = self._heap[menor], self._heap[i]
            i = menor