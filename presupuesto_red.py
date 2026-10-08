"""Presupuesto de solicitudes de red (§5.1)."""
import threading

from errores import ErrorPresupuesto


class PresupuestoRed:

    def __init__(self, limite=None, activo=True):
        self.limite = limite
        self.activo = activo
        self.realizadas = 0
        self.reservadas = 0
        self._credito = 0
        self._cerrojo = threading.Lock()

    def fijar_limite(self, limite):
        with self._cerrojo:
            self.limite = limite

    def restantes(self):
        """Solicitudes que aún se pueden planificar (None si no hay tope conocido)."""
        with self._cerrojo:
            if self.limite is None or not self.activo:
                return None
            return self.limite - self.reservadas

    def reservar(self):
        """Reserva una solicitud futura. False si ya no cabe."""
        with self._cerrojo:
            if not self.activo:
                return True
            if self.limite is not None and self.reservadas >= self.limite:
                return False
            self.reservadas += 1
            self._credito += 1
            return True

    def registrar(self, operacion="solicitud"):
        """Se llama justo antes de cada solicitud HTTP real (también reintentos)."""
        with self._cerrojo:
            if not self.activo:
                return
            if self.limite is not None and self.realizadas >= self.limite:
                raise ErrorPresupuesto(operacion, self.limite)
            self.realizadas += 1
            if self._credito > 0:
                self._credito -= 1
            else:
                self.reservadas += 1

    def reporte(self, cache=None):
        """Texto para mostrar al terminar la partida. cache: objeto con .aciertos y .fallos."""
        limite = "sin dato" if self.limite is None else str(self.limite)
        lineas = ["Solicitudes realizadas: %d" % self.realizadas,
                  "Presupuesto de solicitudes: %s" % limite]
        if cache is not None:
            lineas.append("Aciertos de caché: %d" % cache.aciertos)
            lineas.append("Fallos de caché: %d" % cache.fallos)
        if not self.activo:
            lineas.append("(modo --offline: no se hicieron solicitudes de red)")
        return "\n".join(lineas)