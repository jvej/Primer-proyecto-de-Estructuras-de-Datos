"""Almacenamiento histórico independiente de la pila reversible del motor."""

from dataclasses import dataclass

from modelo.juego.resumen_historico import ProyeccionHistorica, copiar_valor


# Candidato inicial; T063 debe respaldarlo o sustituirlo con mediciones.
K_DEFECTO = 50
OPERACIONES = ("ASIGNAR", "INSERTAR", "QUITAR", "MOVER", "ALTA")


class ArregloContiguo:
    """Directorio cuya reducción lógica solo libera elementos del sufijo."""

    def __init__(self):
        self._datos = []
        self.longitud = 0
        self.capacidad = 0

    def __len__(self):
        return self.longitud

    def __iter__(self):
        for i in range(self.longitud):
            yield self._datos[i]

    def __getitem__(self, posicion):
        if type(posicion) is not int or not 0 <= posicion < self.longitud:
            raise IndexError("Posición fuera del directorio histórico")
        return self._datos[posicion]

    def agregar(self, elemento):
        if self.longitud == self.capacidad:
            capacidad = max(4, self.capacidad * 2)
            nuevos = [None] * capacidad
            for i in range(self.longitud):
                nuevos[i] = self._datos[i]
            self._datos = nuevos
            self.capacidad = capacidad
        self._datos[self.longitud] = elemento
        self.longitud += 1

    def truncar(self, longitud):
        if type(longitud) is not int or not 0 <= longitud <= self.longitud:
            raise ValueError("Longitud histórica inválida")
        while self.longitud > longitud:
            self.longitud -= 1
            self._datos[self.longitud] = None


@dataclass(slots=True)
class DeltaHistorico:
    operacion: str
    destino: str
    campo: str | int | None = None
    token: int | None = None
    anterior: object = None
    nuevo: object = None
    reversible: bool = False
    grupo: int | None = None
    frontera: int = 0
    elemento: int | None = None
    posicion_anterior: int | None = None
    posicion_nueva: int | None = None
    ancla_anterior: int | None = None
    ancla_siguiente: int | None = None
    secuencia_origen: int = 0
    instante_origen: int = 0
    instante: int = 0

    def __post_init__(self):
        if self.operacion not in OPERACIONES:
            raise ValueError(f"Operación histórica inválida: {self.operacion}")
        self.anterior = copiar_valor(self.anterior)
        self.nuevo = copiar_valor(self.nuevo)


@dataclass(slots=True)
class GrupoHistorico:
    identidad: int
    numero: int
    cursor_inicio: int
    cursor_fin: int | None = None


@dataclass(slots=True)
class FronteraHistorica:
    acciones_completadas: int
    reloj: int
    cursor: int


@dataclass(slots=True)
class PuntoControl:
    acciones_completadas: int
    reloj: int
    cursor: int
    proyeccion: object


@dataclass(slots=True)
class MetricasHistoria:
    copias_completas: int = 0
    acciones_aplicadas: int = 0
    externos_aplicados: int = 0
    prefijo_visitado: int = 0
    cambios_visitados_en_recorte: int = 0


class LineaTiempo:
    def __init__(self, checkpoint_cada=K_DEFECTO, leer_reloj=None):
        if type(checkpoint_cada) is not int or checkpoint_cada <= 0:
            raise ValueError("checkpoint_cada debe ser un entero positivo")
        if not callable(leer_reloj):
            raise ValueError("La línea de tiempo necesita un lector de reloj")
        self.checkpoint_cada = checkpoint_cada
        self._leer_reloj = leer_reloj
        self.deltas = ArregloContiguo()
        self.grupos = ArregloContiguo()
        self.fronteras = ArregloContiguo()
        self.checkpoints = ArregloContiguo()
        self.metricas = MetricasHistoria()
        self._secuencia = 0
        self.proyeccion = None

    @property
    def cursor(self):
        return len(self.deltas)

    def iniciar(self, proyeccion):
        """Recibe la proyección propia del inicio y conserva una copia en b=0."""
        if self.proyeccion is not None or len(self.checkpoints) or self.cursor:
            raise ValueError("La historia ya fue iniciada o recibió cambios previos")
        if not isinstance(proyeccion, ProyeccionHistorica):
            raise TypeError("El inicio requiere una ProyeccionHistorica")
        if (proyeccion.reloj != 0 or proyeccion.acciones != 0
                or self._leer_reloj() != 0):
            raise ValueError("La historia debe iniciarse en la frontera 0, antes de acciones")
        sala_inicial = None
        for sala in proyeccion.salas:
            if sala.base.id == proyeccion.jugador.sala:
                sala_inicial = sala
                break
        if (sala_inicial is None or not sala_inicial.incorporada
                or sala_inicial.ultimo_instante_jugador is None):
            raise ValueError("La proyección debe tomarse después de Partida.iniciar()")
        checkpoint = PuntoControl(0, 0, 0, proyeccion.copiar())
        self.proyeccion = proyeccion
        self.fronteras.agregar(FronteraHistorica(0, 0, 0))
        self.checkpoints.agregar(checkpoint)
        self.metricas.copias_completas += 1

    def anotar(self, delta):
        """Recibe exclusivamente datos ya normalizados, nunca objetos C1 vivos."""
        if not isinstance(delta, DeltaHistorico):
            raise TypeError("Se requiere un DeltaHistorico normalizado")
        instante = self._leer_reloj()
        self._secuencia += 1
        delta.secuencia_origen = self._secuencia
        delta.instante_origen = instante
        delta.instante = instante
        self.deltas.agregar(delta)
