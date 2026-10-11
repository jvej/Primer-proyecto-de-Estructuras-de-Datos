"""Partida: el modelo del juego (§2, §6). No conoce HTTP, archivos ni interfaz.

Recibe ya armados los adaptadores que sí los conocen:
  precarga   -> iniciar(id_sala), asegurar(id_sala), al_entrar(id_sala), contenido_de(id_sala)
  resolutor  -> obtener(id_ficha)                      (ficha de catálogo lista para usar)
  inventario -> lleno(), objetos(), agregar(o), agregar_al_frente(o),
                quitar(o) -> posicion, restaurar(o, posicion)       (lo implementa Axel, §4.5)
  bitacora   -> agregar(mensaje)                       (BitacoraPantalla, §4.8)

El jugador es un actor más de la agenda. Cuando le toca, la partida se detiene
(esperando = True) y el controlador llama a UNA de sus acciones. Cada acción aceptada:
cobra su tiempo, aplica su efecto y deja correr a enemigos y efectos hasta la siguiente
decisión del jugador. Ese tramo completo es un "ciclo" (§5.2) y es lo que revierte un pergamino.
Una acción rechazada no cobra tiempo ni cambia nada (Apéndice B) y devuelve False.
"""

import random

import efectos
from actor import Enemigo, Jugador
from agenda_eventos import AgendaEventos
from combate import calcular_dano
from costos import (COSTO_ABRIR_PUERTA, COSTO_ACTIVACION, COSTO_ATACAR, COSTO_ESPERAR,
                    COSTO_MOVER, COSTO_RECOGER_SOLTAR, COSTO_USAR_EQUIPAR, costo_accion)
from errores import ErrorCripta
from evento import Evento
from mapa import Mapa
from motor_enemigos import agendar_turno
from objetos import Objeto
from ordenamiento import ordenar
from registro import Registro
from sala import DIRECCIONES


class Reloj:
    def __init__(self) -> None:
        self.tiempo_actual = 0


class Partida:
    def __init__(self, datos, esqueleto, precarga, resolutor, inventario, bitacora, semilla) -> None:
        self.reloj = Reloj()
        self.registro = Registro()
        self.agenda = AgendaEventos(self.registro)
        self.azar = random.Random(semilla)     # única fuente de azar del modelo (§2.6)
        self.semilla = semilla
        self.mapa = Mapa(esqueleto)
        self.precarga = precarga
        self.resolutor = resolutor
        self.inventario = inventario
        self.bitacora = bitacora
        self.sala_inicial_id = datos["sala_inicial"]
        self.sala_salida_id = datos["sala_salida"]
        self.llave_salida = datos["llave_salida"]
        j = datos["jugador"]
        self.jugador = Jugador(j["vida_max"], j["ataque"], j["defensa"], j["velocidad"])
        self.estado = "jugando"        # "jugando" | "victoria" | "derrota"
        self.esperando = False         # True cuando le toca decidir al jugador
        self.acciones = 0              # acciones del jugador (puntaje, §2.12)
        self.derrotados = 0            # enemigos derrotados (puntaje)

    # ------------------------------------------------------------------ inicio

    def iniciar(self) -> None:
        """§2.4: el contenido de la sala inicial se carga antes de aceptar la primera acción."""
        self.precarga.iniciar(self.sala_inicial_id)
        sala = self.mapa.sala(self.sala_inicial_id)
        self._incorporar(sala)
        self.jugador.mover_a(sala)
        sala.marcar_visita_jugador(0)
        evento = self.programar(0, self._turno_jugador, self.jugador, "turno del jugador")
        self.jugador.evento_pendiente = evento      # primero: así gana el empate en t=0
        self._activar_sala(sala)
        self._avanzar()

    # ------------------------------------------- punto único de cambio (retroceso)

    def cambiar(self, objeto, campo, valor) -> None:
        self.registro.cambiar(objeto, campo, valor)

    def programar(self, tiempo, accion, actor=None, descripcion="") -> Evento:
        evento = Evento(tiempo, self.agenda.nueva_secuencia(), actor, accion, descripcion)
        self.agenda.agendar(evento)
        return evento

    def cancelar(self, evento) -> None:
        if evento is not None:
            self.agenda.cancelar(evento)

    def _lista_agregar(self, lista, elemento, registrar=True) -> None:
        lista.append(elemento)
        if registrar:
            self.registro.inverso(lambda: lista.remove(elemento))

    def _lista_quitar(self, lista, elemento, registrar=True) -> None:
        posicion = lista.index(elemento)
        del lista[posicion]
        if registrar:
            self.registro.inverso(lambda: lista.insert(posicion, elemento))

    def _mover_actor(self, actor, destino) -> None:
        self._lista_quitar(actor.sala.actores, actor)
        self._lista_agregar(destino.actores, actor)
        self.cambiar(actor, "sala", destino)

    def danar(self, actor, cantidad) -> None:
        self.cambiar(actor, "vida", max(0, actor.vida - cantidad))
        if actor.vida == 0:
            self._morir(actor)

    def curar(self, actor, cantidad) -> None:
        self.cambiar(actor, "vida", min(actor.vida_max, actor.vida + cantidad))

    def _morir(self, actor) -> None:
        if actor is self.jugador:
            self.cambiar(self, "estado", "derrota")
            self.bitacora.agregar("Has muerto. Derrota.")
            return
        self.bitacora.agregar(f"{actor.etiqueta()} muere.")
        for campo in ("evento_pendiente", "evento_veneno", "evento_regeneracion"):
            self.cancelar(getattr(actor, campo))     # §4.1: sus eventos futuros ya no ocurren
        self._lista_quitar(actor.sala.actores, actor)
        for id_ficha in actor.suelta:                # lo que suelta cae al suelo de su sala
            self._lista_agregar(actor.sala.objetos, Objeto(self.resolutor.obtener(id_ficha)))
        self.cambiar(self, "derrotados", self.derrotados + 1)

    # ------------------------------------------------------ bucle de eventos (§2.3)

    def _turno_jugador(self, ahora) -> None:
        self.esperando = True

    def _avanzar(self) -> None:
        """Ejecuta eventos en orden hasta que le toque decidir al jugador o termine la partida."""
        while self.estado == "jugando" and not self.esperando:
            evento = self.agenda.siguiente()
            if evento is None:
                break
            self.reloj.tiempo_actual = evento.tiempo_siguiente
            evento.ejecutar(evento.tiempo_siguiente)

    def _accion(self, costo, efecto) -> None:
        ahora = self.reloj.tiempo_actual
        self.registro.abrir_grupo()
        self.registro.inverso(lambda: setattr(self.reloj, "tiempo_actual", ahora))
        self.esperando = False
        self._marcar_rastro(self.jugador.sala)       # Apéndice B: cada acción refresca el rastro
        self.cambiar(self, "acciones", self.acciones + 1)
        siguiente = self.programar(ahora + costo_accion(costo, self.jugador.velocidad),
                                   self._turno_jugador, self.jugador, "turno del jugador")
        self.cambiar(self.jugador, "evento_pendiente", siguiente)
        efecto()
        self._avanzar()
        self.registro.cerrar_grupo()

    def _marcar_rastro(self, sala) -> None:
        self.cambiar(sala, "ultimo_instante_jugador", self.reloj.tiempo_actual)

    def _rechazar(self, mensaje) -> bool:
        self.bitacora.agregar(mensaje)
        return False

    def _puede_actuar(self) -> bool:
        return self.estado == "jugando" and self.esperando

    # --------------------------------------------------- contenido y activación

    def _incorporar(self, sala) -> None:
        if not sala.incorporada:
            self.mapa.incorporar(sala, self.precarga.contenido_de(sala.id), self.resolutor)

    def _activar_sala(self, sala) -> None:
        """§2.4: al entrar el jugador se activan los enemigos dormidos de la sala,
        en orden ascendente de id de instancia (secuencias deterministas)."""
        dormidos = []
        for actor in sala.actores:
            if isinstance(actor, Enemigo) and not actor.activo:
                dormidos.append(actor)
        ahora = self.reloj.tiempo_actual
        for enemigo in ordenar(dormidos, clave=lambda e: e.id_instancia):
            self.cambiar(enemigo, "activo", True)
            agendar_turno(self, enemigo, ahora + costo_accion(COSTO_ACTIVACION, enemigo.velocidad))
            if enemigo.regeneracion > 0:
                efectos.iniciar_regeneracion(self, enemigo)

    # ------------------------------------------------------ acciones del jugador

    def mover(self, direccion) -> bool:
        if not self._puede_actuar():
            return False
        salida = self.jugador.sala.salidas[DIRECCIONES.index(direccion)]
        if salida is None:
            return self._rechazar(f"No hay salida al {direccion}.")
        if not salida.esta_abierta():
            return self._rechazar("La puerta está cerrada.")
        destino = salida.otro_lado(self.jugador.sala)
        try:    # §4.2: el contenido debe estar disponible antes de confirmar; la espera es de
            self.precarga.asegurar(destino.id)       # tiempo real y no mueve el reloj virtual
            self._incorporar(destino)
        except ErrorCripta as error:
            return self._rechazar(f"No se pudo cargar la sala {destino.id}: {error}")
        self._accion(COSTO_MOVER, lambda: self._entrar(destino))
        return True

    def _entrar(self, destino) -> None:
        self._mover_actor(self.jugador, destino)
        self._marcar_rastro(destino)
        self.bitacora.agregar(f"Entras a {destino.nombre or destino.id}.")
        self._activar_sala(destino)
        for trampa in destino.trampas:               # antes de procesar el siguiente evento (§2.10)
            if trampa.armada and self.estado == "jugando":
                efectos.disparar_trampa(self, trampa)
        if (self.estado == "jugando" and destino.id == self.sala_salida_id
                and self.jugador.abrio_salida):
            self.cambiar(self, "estado", "victoria")
            self.bitacora.agregar("¡Has salido de la cripta! Victoria.")
        self.precarga.al_entrar(destino.id)          # precarga anticipada (no es estado del juego)

    def abrir(self, direccion) -> bool:
        if not self._puede_actuar():
            return False
        salida = self.jugador.sala.salidas[DIRECCIONES.index(direccion)]
        if salida is None:
            return self._rechazar(f"No hay salida al {direccion}.")
        if salida.esta_abierta():
            return self._rechazar("La puerta ya está abierta.")
        if salida.llave is None or not self._tiene_llave(salida.llave):
            return self._rechazar("No tienes la llave correcta.")

        def efecto():
            self.cambiar(salida, "estado", "abierta")
            if salida.llave == self.llave_salida:
                self.cambiar(self.jugador, "abrio_salida", True)
            if salida.cierre_automatico:
                efectos.programar_cierre(self, salida)
            self.bitacora.agregar(f"Abres la puerta al {direccion}.")

        self._accion(COSTO_ABRIR_PUERTA, efecto)
        return True

    def _tiene_llave(self, id_llave) -> bool:
        for objeto in self.inventario.objetos():
            if objeto.clase == "llave" and (objeto.id == id_llave or objeto.abre == id_llave):
                return True
        return False

    def esperar(self) -> bool:
        if not self._puede_actuar():
            return False
        self._accion(COSTO_ESPERAR, lambda: self.bitacora.agregar("Esperas."))
        return True

    def atacar(self, indice) -> bool:
        """indice: posición en enemigos_en_sala()."""
        if not self._puede_actuar():
            return False
        objetivos = self.enemigos_en_sala()
        if indice < 0 or indice >= len(objetivos):
            return self._rechazar("No hay ese enemigo en la sala.")
        enemigo = objetivos[indice]

        def efecto():
            dano = calcular_dano(self.jugador, enemigo, self.azar)
            self.bitacora.agregar(f"Atacas a {enemigo.etiqueta()} y le haces {dano} de daño.")
            self.danar(enemigo, dano)

        self._accion(COSTO_ATACAR, efecto)
        return True

    def recoger(self, indice) -> bool:
        """indice: posición en objetos_en_sala()."""
        if not self._puede_actuar():
            return False
        suelo = self.jugador.sala.objetos
        if indice < 0 or indice >= len(suelo):
            return self._rechazar("No hay ese objeto en el suelo.")
        if self.inventario.lleno():
            return self._rechazar("Inventario lleno: suelta algo primero.")
        objeto = suelo[indice]

        def efecto():
            self._lista_quitar(suelo, objeto, registrar=not objeto.es_pergamino())
            self._inv_agregar(objeto)
            self.bitacora.agregar(f"Recoges {objeto.nombre}.")

        self._accion(COSTO_RECOGER_SOLTAR, efecto)
        return True

    def soltar(self, objeto) -> bool:
        if not self._puede_actuar():
            return False
        if objeto not in self.inventario.objetos():
            return self._rechazar("No tienes ese objeto.")
        sala = self.jugador.sala

        def efecto():
            if self.jugador.arma is objeto:
                self.cambiar(self.jugador, "arma", None)
            if self.jugador.armadura is objeto:
                self.cambiar(self.jugador, "armadura", None)
            self._inv_quitar(objeto)
            self._lista_agregar(sala.objetos, objeto, registrar=not objeto.es_pergamino())
            self.bitacora.agregar(f"Sueltas {objeto.nombre}.")

        self._accion(COSTO_RECOGER_SOLTAR, efecto)
        return True

    def equipar(self, objeto) -> bool:
        if not self._puede_actuar():
            return False
        if objeto not in self.inventario.objetos():
            return self._rechazar("No tienes ese objeto.")
        if objeto.clase not in ("arma", "armadura"):
            return self._rechazar("Eso no se puede equipar.")
        campo = "arma" if objeto.clase == "arma" else "armadura"
        if getattr(self.jugador, campo) is objeto:
            return self._rechazar("Ya lo tienes equipado.")

        def efecto():
            self._inv_al_frente(objeto)               # equipar lo mueve al frente (§2.7)
            self.cambiar(self.jugador, campo, objeto)  # sustituye al anterior, que sigue en el inventario
            self.bitacora.agregar(f"Equipas {objeto.nombre}.")

        self._accion(COSTO_USAR_EQUIPAR, efecto)
        return True

    def usar(self, objeto) -> bool:
        if not self._puede_actuar():
            return False
        if objeto not in self.inventario.objetos():
            return self._rechazar("No tienes ese objeto.")
        if objeto.es_pergamino():
            return self.usar_pergamino()
        if objeto.clase == "pocion":
            efecto = lambda: self._beber(objeto)
        elif objeto.clase == "antidoto":
            efecto = lambda: self._tomar_antidoto(objeto)
        elif objeto.clase == "antorcha":
            if self.jugador.antorcha_encendida:
                return self._rechazar("Ya tienes una antorcha encendida.")
            efecto = lambda: self._encender(objeto)
        else:
            return self._rechazar("Eso no se puede usar.")
        self._accion(COSTO_USAR_EQUIPAR, efecto)
        return True

    def _beber(self, pocion) -> None:
        self._inv_quitar(pocion)
        self.bitacora.agregar(f"Bebes {pocion.nombre}.")
        if pocion.cura > 0:
            self.curar(self.jugador, pocion.cura)
        if pocion.modificador_velocidad != 0 and pocion.duracion > 0:
            efectos.velocidad_temporal(self, self.jugador, pocion.modificador_velocidad, pocion.duracion)

    def _tomar_antidoto(self, antidoto) -> None:
        self._inv_quitar(antidoto)
        efectos.cancelar_veneno(self, self.jugador)
        self.bitacora.agregar("Tomas el antídoto.")

    def _encender(self, antorcha) -> None:
        self.cambiar(antorcha, "usos", antorcha.usos - 1)
        if antorcha.usos <= 0:
            self._inv_quitar(antorcha)
        efectos.encender_antorcha(self, antorcha)
        self.bitacora.agregar("Enciendes la antorcha.")

    def usar_pergamino(self) -> bool:
        """§2.11: deshace la última acción del jugador y todo lo ocurrido después.
        No consume tiempo virtual, no cuenta como acción y no se registra en el historial.
        El pergamino queda fuera del alcance de la reversión."""
        if not self._puede_actuar():
            return False
        pergamino = None
        for objeto in self.inventario.objetos():
            if objeto.es_pergamino():
                pergamino = objeto
                break
        if pergamino is None:
            return self._rechazar("No tienes pergaminos de retroceso.")
        if not self.registro.puede_deshacer():
            return self._rechazar("No hay acciones que deshacer.")
        self.inventario.quitar(pergamino)        # sin registrar: la reversión no lo devuelve
        self.registro.deshacer_ultimo()
        self.esperando = True
        self.bitacora.agregar("Usas un pergamino de retroceso: el tiempo vuelve atrás.")
        return True

    # ----------------------------------------- inventario con registro de cambios

    def _inv_agregar(self, objeto) -> None:
        self.inventario.agregar(objeto)
        if not objeto.es_pergamino():
            self.registro.inverso(lambda: self.inventario.quitar(objeto))

    def _inv_quitar(self, objeto) -> None:
        posicion = self.inventario.quitar(objeto)
        if not objeto.es_pergamino():
            self.registro.inverso(lambda: self.inventario.restaurar(objeto, posicion))

    def _inv_al_frente(self, objeto) -> None:
        posicion = self.inventario.quitar(objeto)
        self.inventario.agregar_al_frente(objeto)

        def deshacer():
            self.inventario.quitar(objeto)
            self.inventario.restaurar(objeto, posicion)

        self.registro.inverso(deshacer)

    # ------------------------------------------- consultas para la vista y la caché

    def sala_actual(self):
        return self.jugador.sala

    def enemigos_en_sala(self) -> list:
        lista = []
        for actor in self.jugador.sala.actores:
            if isinstance(actor, Enemigo) and actor.esta_vivo():
                lista.append(actor)
        return lista

    def objetos_en_sala(self) -> list:
        return self.jugador.sala.objetos

    def trampas_en_sala(self) -> list:
        return self.jugador.sala.trampas

    def salidas_visibles(self) -> list:
        """[(direccion, estado, id de la sala vecina, llave requerida)]"""
        sala = self.jugador.sala
        resultado = []
        for i in range(len(DIRECCIONES)):
            salida = sala.salidas[i]
            if salida is not None:
                resultado.append((DIRECCIONES[i], salida.estado, salida.otro_lado(sala).id, salida.llave))
        return resultado

    def efectos_activos(self) -> list:
        j = self.jugador
        lista = []
        if j.evento_veneno is not None:
            lista.append("veneno")
        if j.velocidad != j.velocidad_base:
            lista.append(f"velocidad {j.velocidad}")
        if j.antorcha_encendida:
            lista.append("antorcha encendida")
        return lista

    def ficha_en_uso(self, id_ficha) -> bool:
        """Para la caché (§4.4): una ficha en uso no se puede liberar. Está en uso si la
        referencia un enemigo vivo, un objeto del inventario o del suelo de la sala actual,
        o una trampa de la sala actual."""
        for enemigo in self.mapa.enemigos:
            if enemigo.esta_vivo() and enemigo.tipo == id_ficha:
                return True
        for objeto in self.inventario.objetos():
            if objeto.id == id_ficha:
                return True
        for objeto in self.jugador.sala.objetos:
            if objeto.id == id_ficha:
                return True
        for trampa in self.jugador.sala.trampas:
            if trampa.id == id_ficha:
                return True
        return False