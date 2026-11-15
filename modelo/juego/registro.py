MAX_ACCIONES = 5


class PilaAcotada:
    def __init__(self, capacidad):
        if capacidad < 1:
            raise ValueError("la capacidad debe ser al menos 1")
        self._datos = [None] * capacidad
        self._capacidad = capacidad
        self._inicio = 0
        self._cantidad = 0

    def __len__(self):
        return self._cantidad

    def apilar(self, elemento):
        if self._cantidad < self._capacidad:
            posicion = (self._inicio + self._cantidad) % self._capacidad
            self._datos[posicion] = elemento
            self._cantidad += 1
            return None

        descartado = self._datos[self._inicio]
        self._datos[self._inicio] = elemento
        self._inicio = (self._inicio + 1) % self._capacidad
        return descartado

    def desapilar(self):
        if self._cantidad == 0:
            raise IndexError("la pila está vacía")

        self._cantidad -= 1
        posicion = (self._inicio + self._cantidad) % self._capacidad
        elemento = self._datos[posicion]
        self._datos[posicion] = None
        return elemento

    def elementos(self):
        resultado = []
        for i in range(self._cantidad):
            resultado.append(
                self._datos[(self._inicio + i) % self._capacidad]
            )
        return resultado

    def tope(self):
        if self._cantidad == 0:
            return None
        return self._datos[
            (self._inicio + self._cantidad - 1) % self._capacidad
        ]


class GrupoRegistro(list):
    """Los mismos inversos contiguos, con identidad escalar para C1."""

    __slots__ = ("identidad",)

    def __init__(self, identidad):
        super().__init__()
        self.identidad = identidad


class Registro:
    def __init__(self, max_acciones=MAX_ACCIONES) -> None:
        self._grupos = PilaAcotada(max_acciones)
        self._abierto = None
        self._consumidor = None
        self._leer_reloj = None
        self._grupo_identidad = None
        self._origen_tokens = object()
        self._siguiente_token = 0
        self._siguiente_grupo = 0

    def conectar_captura(self, consumidor=None, leer_reloj=None) -> None:
        """Conecta C1; sin consumidor no se leen relojes ni se normalizan datos.

        capturar_cambio recibe referencias transitorias ANTES de la escritura.
        El consumidor debe adoptar/normalizar los valores en esa llamada; no
        debe guardar objetos vivos, nodos ni funciones como datos históricos.
        Pasar None desconecta la captura. No cambia los inversos del juego.
        """
        if consumidor is not None and not callable(leer_reloj):
            raise ValueError("la captura necesita un lector de reloj")
        self._consumidor = consumidor
        self._leer_reloj = leer_reloj

    def captura_activa(self) -> bool:
        return self._consumidor is not None

    def token_de(self, objeto):
        """Identidad de instancia para C1, independiente del id de ficha."""
        if self._consumidor is None:
            return None
        marca = getattr(objeto, "_identidad_c1", None)
        if marca is None or marca[0] is not self._origen_tokens:
            self._siguiente_token += 1
            marca = (self._origen_tokens, self._siguiente_token)
            objeto._identidad_c1 = marca
        return marca[1]

    def capturar_cambio(self, operacion, destino, campo, anterior, nuevo,
                        reversible, elemento=None, posicion_anterior=None,
                        posicion_nueva=None, token=None, usos=None) -> None:
        if self._consumidor is not None:
            self._consumidor.capturar_cambio(
                operacion=operacion, destino=destino, campo=campo,
                anterior=anterior, nuevo=nuevo, reversible=reversible,
                elemento=elemento, posicion_anterior=posicion_anterior,
                posicion_nueva=posicion_nueva, token=token, usos=usos,
                instante=self._leer_reloj(), grupo=self._grupo_identidad)

    def notificar(self, evento, grupo=None, **datos) -> None:
        """Hooks opcionales de grupo/frontera; nunca ejecutan el motor."""
        if self._consumidor is None:
            return
        notificacion = getattr(self._consumidor, evento, None)
        if notificacion is not None:
            notificacion(grupo=grupo, instante=self._leer_reloj(), **datos)

    def abrir_grupo(self):
        self._siguiente_grupo += 1
        self._abierto = GrupoRegistro(self._siguiente_grupo)
        self._grupo_identidad = self._abierto.identidad
        self.notificar("abrir_grupo", grupo=self._grupo_identidad)
        return self._grupo_identidad

    def cerrar_grupo(self):
        if self._abierto is None:
            return
        identidad = self._grupo_identidad
        self._grupos.apilar(self._abierto)
        self._abierto = None
        self._grupo_identidad = None
        self.notificar("cerrar_grupo", grupo=identidad)
        return identidad

    def grupo_abierto(self):
        return self._abierto

    def inverso(self, deshacer) -> None:
        if self._abierto is not None:
            self._abierto.append(deshacer)

    def cambiar(self, objeto, campo: str | int, valor) -> None:
        if isinstance(objeto, list) and isinstance(campo, int):
            anterior = objeto[campo]
            self.capturar_cambio("ASIGNAR", objeto, campo, anterior, valor,
                                self._abierto is not None)
            objeto[campo] = valor

            if self._abierto is not None:
                self._abierto.append(
                    lambda: objeto.__setitem__(campo, anterior)
                )
            return

        anterior = getattr(objeto, campo)
        self.capturar_cambio("ASIGNAR", objeto, campo, anterior, valor,
                            self._abierto is not None)
        setattr(objeto, campo, valor)

        if self._abierto is not None:
            self._abierto.append(
                lambda: setattr(objeto, campo, anterior)
            )

    def puede_deshacer(self) -> bool:
        return len(self._grupos) > 0

    def acciones_deshacibles(self) -> int:
        return len(self._grupos)

    def cambios_registrados(self) -> int:
        total = 0
        for grupo in self._grupos.elementos():
            total += len(grupo)
        return total

    def deshacer_ultimo(self):
        grupo = self._grupos.desapilar()
        for i in range(len(grupo) - 1, -1, -1):
            grupo[i]()
        self.notificar("deshacer_grupo", grupo=grupo.identidad)
        return grupo.identidad
