import threading

from cola_fifo import ColaFIFO


class Tarea:
    def __init__(self, secuencia, funcion, argumentos):
        self.secuencia = secuencia
        self.funcion = funcion
        self.argumentos = argumentos
        self.resultado = None
        self.error = None
        self._listo = threading.Event()

    def terminada(self):
        return self._listo.is_set()

    def esperar_fin(self):
        """Espera (tiempo real) sin lanzar el error; el reloj virtual no se mueve."""
        self._listo.wait()

    def resultado_o_error(self):
        self._listo.wait()
        if self.error is not None:
            raise self.error
        return self.resultado


class EjecutorRed:
    def __init__(self):
        self._cola = ColaFIFO()
        self._condicion = threading.Condition()
        self._secuencia = 0
        self._activo = True
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()

    def enviar(self, funcion, *argumentos):
        with self._condicion:
            if not self._activo:
                raise RuntimeError("el ejecutor de red ya fue cerrado")
            tarea = Tarea(self._secuencia, funcion, argumentos)
            self._secuencia += 1
            self._cola.agregar(tarea)
            self._condicion.notify()
            return tarea

    def _bucle(self):
        while True:
            with self._condicion:
                while self._cola.vacia() and self._activo:
                    self._condicion.wait()
                if self._cola.vacia():
                    return
                tarea = self._cola.sacar()
            try:
                tarea.resultado = tarea.funcion(*tarea.argumentos)
            except Exception as e:           # el error se re-lanza en el hilo principal
                tarea.error = e
            tarea._listo.set()

    def cerrar(self):
        with self._condicion:
            self._activo = False
            self._condicion.notify()
        self._hilo.join(timeout=5)