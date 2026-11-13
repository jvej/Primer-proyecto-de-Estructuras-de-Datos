"""Datos históricos propios: nunca se copia el motor ni sus eventos."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BaseObjeto:
    id_ficha: str
    nombre: str
    clase: str
    ataque_bonus: int = 0
    defensa_bonus: int = 0


@dataclass(slots=True)
class ObjetoHistorico:
    token: int
    base: BaseObjeto
    usos: int

    @property
    def id_ficha(self):
        return self.base.id_ficha

    def copiar(self):
        return ObjetoHistorico(self.token, self.base, self.usos)


@dataclass(frozen=True, slots=True)
class BaseActor:
    id_instancia: str
    nombre: str
    tipo: str = ""
    comportamiento: str = ""


@dataclass(slots=True)
class ActorHistorico:
    token: int
    base: BaseActor
    sala: int | None
    vida: int
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int
    velocidad_base: int
    arma: int | None = None
    armadura: int | None = None
    veneno: bool = False
    antorcha_encendida: bool = False
    abrio_salida: bool = False
    activo: bool = False

    @property
    def id_instancia(self):
        return self.base.id_instancia

    def copiar(self):
        return ActorHistorico(
            self.token, self.base, self.sala, self.vida, self.vida_max,
            self.ataque, self.defensa, self.velocidad, self.velocidad_base,
            self.arma, self.armadura, self.veneno, self.antorcha_encendida,
            self.abrio_salida, self.activo)


@dataclass(frozen=True, slots=True)
class BaseSala:
    indice: int
    id: int
    nombre: str
    # Por dirección: (índice vecino, llave, costo), o None. Sin puerta viva.
    salidas: tuple


@dataclass(slots=True)
class SalaHistorica:
    base: BaseSala
    ultimo_instante_jugador: int | None = None
    incorporada: bool = False
    actores: list = field(default_factory=list)

    def copiar(self):
        return SalaHistorica(self.base, self.ultimo_instante_jugador,
                             self.incorporada, list(self.actores))


@dataclass(frozen=True, slots=True)
class SalaConocida:
    id: int
    nombre: str
    salidas: tuple


def _por_token(elementos, token):
    for elemento in elementos:
        if elemento.token == token:
            return elemento
    raise ValueError(f"No existe el token histórico {token}")


@dataclass(slots=True)
class ProyeccionHistorica:
    reloj: int
    acciones: int
    derrotados: int
    estado: str
    jugador: ActorHistorico
    objetos: list
    inventario: list
    actores: list
    salas: list
    estado_salas: list
    memoria_puertas: list
    num_exploradas: int
    num_avistadas: int

    def copiar(self):
        return ProyeccionHistorica(
            self.reloj, self.acciones, self.derrotados, self.estado,
            self.jugador.copiar(), [o.copiar() for o in self.objetos],
            list(self.inventario), [a.copiar() for a in self.actores],
            [s.copiar() for s in self.salas], list(self.estado_salas),
            list(self.memoria_puertas), self.num_exploradas, self.num_avistadas)

    def actor(self, token):
        if self.jugador.token == token:
            return self.jugador
        return _por_token(self.actores, token)

    def objeto(self, token):
        return _por_token(self.objetos, token)

    def resumir(self):
        from modelo.juego.conocimiento import (
            ESTADO_EXPLORADA, PUERTA_ABIERTA, PUERTA_CERRADA)
        from modelo.juego.sala import DIRECCIONES

        j = self.jugador
        ataque = j.ataque
        defensa = j.defensa
        if j.arma is not None:
            ataque += self.objeto(j.arma).base.ataque_bonus
        if j.armadura is not None:
            defensa += self.objeto(j.armadura).base.defensa_bonus
        efectos = []
        if j.veneno:
            efectos.append("veneno")
        if j.velocidad != j.velocidad_base:
            efectos.append(f"velocidad {j.velocidad}")
        if j.antorcha_encendida:
            efectos.append("antorcha encendida")
        enemigos = []
        for sala in self.salas:
            if sala.base.id == j.sala:
                for token in sala.actores:
                    actor = self.actor(token)
                    if token != j.token and actor.vida > 0:
                        enemigos.append(actor.copiar())
                break
        conocidas = []
        for sala in self.salas:
            indice = sala.base.indice
            if self.estado_salas[indice] != ESTADO_EXPLORADA:
                continue
            salidas = []
            for direccion, salida in enumerate(sala.base.salidas):
                if salida is None:
                    continue
                vecino, llave, costo = salida
                memoria = self.memoria_puertas[indice * 4 + direccion]
                estado = ("abierta" if memoria == PUERTA_ABIERTA else
                          "cerrada" if memoria == PUERTA_CERRADA else "desconocida")
                id_visible = (self.salas[vecino].base.id
                              if self.estado_salas[vecino] == ESTADO_EXPLORADA else None)
                salidas.append((DIRECCIONES[direccion], estado, id_visible,
                                llave if memoria in (PUERTA_ABIERTA, PUERTA_CERRADA)
                                else None, costo))
            conocidas.append(SalaConocida(sala.base.id, sala.base.nombre, tuple(salidas)))
        return ResumenHistorico(
            self.reloj, self.acciones, self.estado, j.sala, j.vida, j.vida_max,
            ataque, defensa, j.velocidad,
            tuple(self.objeto(t).copiar() for t in self.inventario),
            tuple(efectos), tuple(enemigos), tuple(self.estado_salas),
            tuple(self.memoria_puertas), self.derrotados,
            self.num_exploradas, self.num_avistadas,
            tuple(conocidas))


@dataclass(frozen=True, slots=True)
class ResumenHistorico:
    reloj: int
    acciones: int
    estado: str
    sala: int | None
    vida: int
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int
    inventario: tuple
    efectos: tuple
    enemigos: tuple
    estado_salas: tuple
    memoria_puertas: tuple
    derrotados: int
    num_exploradas: int
    num_avistadas: int
    salas: tuple


def copiar_valor(valor):
    """Lista blanca de datos que un delta puede poseer, sin deepcopy."""
    if valor is None or type(valor) in (bool, int, float, str):
        return valor
    if isinstance(valor, (BaseObjeto, BaseActor, BaseSala)):
        return valor  # Bases congeladas compuestas únicamente por valores.
    if isinstance(valor, (ObjetoHistorico, ActorHistorico, SalaHistorica)):
        return valor.copiar()
    if isinstance(valor, tuple):
        return tuple(copiar_valor(v) for v in valor)
    raise TypeError(f"Valor ajeno a la proyección histórica: {type(valor).__name__}")


def aplicar_delta(proyeccion, delta):
    """Aplica datos a una proyección propia; no ejecuta operaciones del juego."""
    destino = delta.destino
    if delta.operacion == "ALTA":
        dato = copiar_valor(delta.nuevo)
        if destino == "actor":
            proyeccion.actores.append(dato)
        elif destino == "objeto":
            proyeccion.objetos.append(dato)
        elif destino == "sala":
            proyeccion.salas[delta.token] = dato
        else:
            raise ValueError(f"Alta histórica desconocida: {destino}")
        return
    if destino == "inventario":
        secuencia = proyeccion.inventario
    elif destino == "actores_sala":
        secuencia = proyeccion.salas[delta.token].actores
    elif destino in ("estado_salas", "memoria_puertas"):
        secuencia = getattr(proyeccion, destino)
    else:
        secuencia = None
    if delta.operacion == "ASIGNAR":
        valor = copiar_valor(delta.nuevo)
        if secuencia is not None:
            secuencia[delta.campo] = valor
        elif destino == "partida":
            setattr(proyeccion, delta.campo, valor)
        elif destino == "actor":
            setattr(proyeccion.actor(delta.token), delta.campo, valor)
        elif destino == "objeto":
            setattr(proyeccion.objeto(delta.token), delta.campo, valor)
        elif destino == "sala":
            setattr(proyeccion.salas[delta.token], delta.campo, valor)
        else:
            raise ValueError(f"Destino histórico desconocido: {destino}")
    elif secuencia is None:
        raise ValueError("La operación requiere una secuencia histórica")
    elif delta.operacion == "INSERTAR":
        secuencia.insert(delta.posicion_nueva, delta.elemento)
    elif delta.operacion in ("QUITAR", "MOVER"):
        posicion = delta.posicion_anterior
        if secuencia[posicion] != delta.elemento:
            raise ValueError("El token no coincide con su posición histórica")
        elemento = secuencia.pop(posicion)
        if delta.operacion == "MOVER":
            secuencia.insert(delta.posicion_nueva, elemento)
    else:
        raise ValueError(f"Operación histórica desconocida: {delta.operacion}")


class NormalizadorHistorico:
    """Adaptador C1. Solo este adaptador de captura conoce la partida viva.

    Las marcas de adopción están en las instancias, sin un directorio global
    de objetos retenidos. Fotos, deltas y resúmenes contienen únicamente datos.
    """

    CAMPOS_ACTOR = (
        "sala", "vida", "vida_max", "ataque", "defensa", "velocidad",
        "velocidad_base", "arma", "armadura", "antorcha_encendida",
        "abrio_salida", "activo", "evento_veneno")

    def __init__(self, partida, linea):
        self._partida = partida
        self.linea = linea
        self._origen = object()

    def _token(self, objeto):
        token = self._partida.registro.token_de(objeto)
        if token is None:
            raise ValueError("La captura C1 debe estar conectada antes de normalizar")
        return token

    def _adoptado(self, objeto):
        return getattr(objeto, "_adopcion_historia", None) is self._origen

    def _marcar(self, objeto):
        objeto._adopcion_historia = self._origen

    def _datos_objeto(self, objeto):
        return ObjetoHistorico(
            self._token(objeto),
            BaseObjeto(objeto.id, objeto.nombre, objeto.clase,
                       objeto.ataque_bonus, objeto.defensa_bonus), objeto.usos)

    def _datos_actor(self, actor):
        return ActorHistorico(
            self._token(actor),
            BaseActor(getattr(actor, "id_instancia", ""), actor.nombre,
                      getattr(actor, "tipo", ""),
                      getattr(actor, "comportamiento", "")),
            None if actor.sala is None else actor.sala.id,
            actor.vida, actor.vida_max, actor.ataque, actor.defensa,
            actor.velocidad, actor.velocidad_base,
            None if getattr(actor, "arma", None) is None else self._token(actor.arma),
            None if getattr(actor, "armadura", None) is None else self._token(actor.armadura),
            actor.evento_veneno is not None,
            getattr(actor, "antorcha_encendida", False),
            getattr(actor, "abrio_salida", False), getattr(actor, "activo", False))

    def crear_proyeccion(self):
        """Único recorrido inicial del mundo ya incorporado, tras iniciar()."""
        p = self._partida
        salas = []
        for sala in p.mapa.salas:
            salidas = []
            for salida in sala.salidas:
                salidas.append(None if salida is None else (
                    salida.otro_lado(sala).indice, salida.llave, salida.costo))
            salas.append(SalaHistorica(
                BaseSala(sala.indice, sala.id, sala.nombre, tuple(salidas)),
                sala.ultimo_instante_jugador, sala.incorporada,
                [self._token(a) for a in sala.actores]))
            if sala.incorporada:
                self._marcar(sala)
        objetos = []
        inventario = []
        for objeto in p.inventario.objetos():
            objetos.append(self._datos_objeto(objeto))
            inventario.append(self._token(objeto))
            self._marcar(objeto)
        for objeto in (p.jugador.arma, p.jugador.armadura):
            if objeto is not None and not self._adoptado(objeto):
                objetos.append(self._datos_objeto(objeto))
                self._marcar(objeto)
        actores = []
        for actor in p.mapa.enemigos:
            actores.append(self._datos_actor(actor))
            self._marcar(actor)
        self._marcar(p.jugador)
        c = p.conocimiento
        return ProyeccionHistorica(
            p.reloj.tiempo_actual, p.acciones, p.derrotados, p.estado,
            self._datos_actor(p.jugador), objetos, inventario, actores, salas,
            list(c.estado_salas), list(c.memoria_puertas),
            c.num_exploradas, c.num_avistadas)

    def _emitir(self, operacion, destino, **datos):
        from modelo.juego.linea_tiempo import DeltaHistorico
        delta = DeltaHistorico(operacion, destino, **datos)
        self.linea.anotar(delta)
        aplicar_delta(self.linea.proyeccion, delta)

    def _adoptar_objeto(self, objeto, grupo):
        if not self._adoptado(objeto):
            self._marcar(objeto)
            self._emitir("ALTA", "objeto", token=self._token(objeto),
                         nuevo=self._datos_objeto(objeto), grupo=grupo)
        return self._token(objeto)

    def _adoptar_actor(self, actor, grupo):
        if not self._adoptado(actor):
            self._marcar(actor)
            self._emitir("ALTA", "actor", token=self._token(actor),
                         nuevo=self._datos_actor(actor), grupo=grupo)
        return self._token(actor)

    def _adoptar_sala(self, sala, grupo):
        if not self._adoptado(sala):
            self._marcar(sala)
            for actor in sala.actores:
                self._adoptar_actor(actor, grupo)
            # La incorporación es anterior a sus cambios C1 y no se deshace.
            dato = SalaHistorica(
                self.linea.proyeccion.salas[sala.indice].base,
                sala.ultimo_instante_jugador, sala.incorporada,
                [self._token(a) for a in sala.actores])
            self._emitir("ALTA", "sala", token=sala.indice, nuevo=dato, grupo=grupo)

    def _valor_actor(self, campo, valor, grupo):
        if campo == "sala":
            if valor is not None:
                self._adoptar_sala(valor, grupo)
                return valor.id
            return None
        if campo in ("arma", "armadura"):
            return None if valor is None else self._adoptar_objeto(valor, grupo)
        if campo == "evento_veneno":
            return valor is not None
        return copiar_valor(valor)

    def _sala_de_actores(self, lista, actor):
        """Mover actores usa la sala actual o un vecino; no barre el mapa."""
        sala = actor.sala
        if sala is None:
            return None
        if lista is sala.actores:
            return sala
        for salida in sala.salidas:
            if salida is not None:
                vecina = salida.otro_lado(sala)
                if lista is vecina.actores:
                    return vecina
        return None

    def capturar_cambio(self, operacion, destino, campo, anterior, nuevo,
                        reversible, elemento=None, posicion_anterior=None,
                        posicion_nueva=None, token=None, usos=None,
                        instante=None, grupo=None):
        from modelo.juego.actor import Actor
        from modelo.juego.objetos import Objeto
        from modelo.juego.sala import Sala

        p = self._partida
        tipo = None
        identidad = None
        if destino is p:
            if campo in ("acciones", "derrotados", "estado"):
                tipo = "partida"
        elif destino is p.conocimiento:
            if campo in ("num_exploradas", "num_avistadas"):
                tipo = "partida"
        elif destino is p.conocimiento.estado_salas:
            tipo = "estado_salas"
        elif destino is p.conocimiento.memoria_puertas:
            tipo = "memoria_puertas"
        elif isinstance(destino, Actor):
            if campo in self.CAMPOS_ACTOR:
                identidad = self._adoptar_actor(destino, grupo)
                tipo = "actor"
                anterior = self._valor_actor(campo, anterior, grupo)
                nuevo = self._valor_actor(campo, nuevo, grupo)
                if campo == "evento_veneno":
                    campo = "veneno"
        elif isinstance(destino, Objeto):
            if campo == "usos":
                identidad = self._adoptar_objeto(destino, grupo)
                tipo = "objeto"
        elif isinstance(destino, Sala):
            if campo == "ultimo_instante_jugador":
                self._adoptar_sala(destino, grupo)
                tipo, identidad = "sala", destino.indice
        elif destino is p.inventario:
            tipo = "inventario"
            token = self._adoptar_objeto(elemento, grupo)
        elif isinstance(destino, list) and isinstance(elemento, Actor):
            sala = self._sala_de_actores(destino, elemento)
            if sala is None:
                raise ValueError("C1: no se pudo identificar la sala de la lista de actores")
            self._adoptar_sala(sala, grupo)
            tipo, identidad = "actores_sala", sala.indice
            token = self._adoptar_actor(elemento, grupo)
        # Agenda, trampas, suelo y puertas físicas no forman el resumen.
        # El conocimiento de puertas se captura una sola vez en sus celdas C1.
        if tipo is None:
            return
        ancla_anterior = ancla_siguiente = None
        if operacion in ("INSERTAR", "QUITAR", "MOVER"):
            if tipo == "inventario":
                secuencia = self.linea.proyeccion.inventario
            else:
                secuencia = self.linea.proyeccion.salas[identidad].actores
            posicion = posicion_anterior if posicion_anterior is not None else posicion_nueva
            if posicion > 0:
                ancla_anterior = secuencia[posicion - 1]
            siguiente = posicion + (operacion != "INSERTAR")
            if siguiente < len(secuencia):
                ancla_siguiente = secuencia[siguiente]
            if operacion == "INSERTAR":
                anterior, nuevo = None, token
            elif operacion == "QUITAR":
                anterior, nuevo = token, None
        self._emitir(
            operacion, tipo, campo=campo, token=identidad,
            anterior=anterior, nuevo=nuevo, reversible=reversible, grupo=grupo,
            elemento=token, posicion_anterior=posicion_anterior,
            posicion_nueva=posicion_nueva, ancla_anterior=ancla_anterior,
            ancla_siguiente=ancla_siguiente)


def inicializar_historia(partida, checkpoint_cada):
    """Conecta C1 después de iniciar(), antes de ejecutar/reconstruir órdenes.

    K pertenece solo a esta sesión. El lector y el adaptador pueden conocer el
    motor; ninguna referencia suya se almacena dentro de una foto o un delta.
    Las fronteras periódicas, consultas y retroceso se incorporan en T026–T031.
    """
    from modelo.juego.linea_tiempo import LineaTiempo

    if getattr(partida, "linea_tiempo", None) is not None:
        raise ValueError("La partida ya tiene una historia inicializada")
    if partida.registro.captura_activa():
        raise ValueError("Ya existe un consumidor C1 conectado a la partida")
    if (partida.jugador.sala is None or partida.jugador.evento_pendiente is None
            or partida.registro.grupo_abierto() is not None
            or partida.acciones != 0 or partida.reloj.tiempo_actual != 0):
        raise ValueError("Inicializar historia después de iniciar() y antes de la primera acción")

    def leer_reloj():
        return partida.reloj.tiempo_actual

    linea = LineaTiempo(checkpoint_cada, leer_reloj)
    normalizador = NormalizadorHistorico(partida, linea)
    # token_de de C1 solo asigna identidades cuando hay consumidor conectado.
    partida.registro.conectar_captura(normalizador, leer_reloj)
    try:
        linea.iniciar(normalizador.crear_proyeccion())
    except Exception:
        partida.registro.conectar_captura(None)
        raise
    partida.linea_tiempo = linea
