"""Guardar y cargar desde la interfaz (§4.10, §10.2). Camino A acordado por el grupo.

El archivo es el binario de formato propio de guardado_binario.py (Kim):
  - un índice ordenado de salas: se puede leer UNA sala sin leer el archivo completo;
  - una marca y una versión de formato: detecta archivos incompatibles;
  - un bloque general con reloj, semilla, vida, sala actual, inventario y, desde el
    formato 2, la cripta, sus versiones, el jugador y la lista de órdenes jugadas;
    desde el formato 3, las solicitudes de red que la partida ya gastó (§5.1).

Por qué se guardan las órdenes: la agenda contiene eventos cuya acción es una función
(turnos de enemigos, pulsos de veneno, rearmes...), y una función no se puede escribir
en un archivo. Cargar = reconstruir la partida con la misma semilla y re-ejecutar las
mismas órdenes (el juego es determinista, §2.6). El resultado es idéntico, agenda
incluida. Después se comprueba contra la foto guardada (reloj, vida, sala y la sala
actual leída por el índice): si algo no coincide, se avisa en vez de seguir en silencio.

Cumple la interfaz que espera el Controlador:
    guardar(partida) -> str (mensaje)
    cargar() -> Partida | None (None = no hay partida guardada)
"""

import os

from modelo.juego.errores import ErrorCripta
from modelo.datos.guardado_binario import (ErrorFormato, PartidaGuardada, SalaGuardada, cargar_general,
                              guardar, leer_sala)
from controlador.orden import Orden
from modelo.juego.sala import DIRECCIONES


class ErrorCarga(ErrorCripta):
    """No se pudo cargar la partida guardada (mensaje listo para el usuario)."""


def foto_de(partida, version_catalogo, nombre, ordenes, solicitudes=0):
    """Convierte la Partida real en la estructura que escribe guardado_binario."""
    foto = PartidaGuardada(partida.reloj.tiempo_actual, partida.semilla, partida.jugador.vida,
                           partida.jugador.sala.id, partida.id_cripta, partida.version_cripta,
                           version_catalogo, nombre)
    foto.solicitudes = solicitudes
    for objeto in partida.inventario.objetos():
        foto.inventario.append(objeto.id)
    for orden in ordenes:
        foto.ordenes.append(orden.a_texto())
    for sala in partida.mapa.salas:
        if not sala.incorporada and sala.ultimo_instante_jugador is None:
            continue                          # el jugador nunca supo nada de esa sala
        guardada = SalaGuardada(sala.id, -1 if sala.ultimo_instante_jugador is None
                                else sala.ultimo_instante_jugador)
        for actor in sala.actores:
            if actor is partida.jugador:
                continue
            tiempo = actor.tiempo_siguiente
            guardada.enemigos.append([actor.id_instancia, actor.tipo, actor.vida,
                                      -1 if tiempo is None else tiempo])
        for objeto in sala.objetos:
            guardada.objetos.append(objeto.id)
        for i in range(len(DIRECCIONES)):
            salida = sala.salidas[i]
            if salida is not None:
                guardada.puertas.append([DIRECCIONES[i], 1 if salida.esta_abierta() else 0])
        foto.salas.append(guardada)
    return foto


class PersistenciaPartida:
    def __init__(self, aplicacion, ruta=None):
        self.aplicacion = aplicacion
        self.ruta = ruta if ruta is not None else aplicacion.ruta_guardado

    def guardar(self, partida):
        app = self.aplicacion
        carpeta = os.path.dirname(self.ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        foto = foto_de(partida, app.version_catalogo, app.nombre, app.ordenes,
                       app.presupuesto.realizadas)
        try:
            guardar(self.ruta, foto)
        except OSError as error:
            return "No se pudo guardar la partida: %s" % error
        return "Partida guardada en %s (%d acciones, %d salas)." % (
            self.ruta, len(foto.ordenes), len(foto.salas))

    def cargar(self):
        if not os.path.exists(self.ruta):
            return None
        try:
            general = cargar_general(self.ruta)        # solo el bloque general
        except (ErrorFormato, OSError) as error:
            raise ErrorCarga("No se pudo leer el archivo de partida: %s" % error)

        ordenes = []
        for linea in general.ordenes:
            try:
                ordenes.append(Orden.desde_texto(linea))
            except ValueError as error:
                raise ErrorCarga("El archivo de partida está dañado: %s" % error)

        app = self.aplicacion
        marca = app.presupuesto.marca()

        def validar(partida):
            """Compara la re-simulación con la foto guardada. Corre dentro de
            crear_partida, ANTES de reemplazar la partida actual: si lanza, la aplicación,
            el controlador y el log siguen con la partida que se estaba jugando."""
            sala_guardada = leer_sala(self.ruta, general.sala_actual)   # una sala, vía el índice
            diferencias = []
            if partida.reloj.tiempo_actual != general.reloj:
                diferencias.append("reloj %d en vez de %d" % (partida.reloj.tiempo_actual,
                                                              general.reloj))
            if partida.jugador.vida != general.vida:
                diferencias.append("vida %d en vez de %d" % (partida.jugador.vida, general.vida))
            if partida.jugador.sala.id != general.sala_actual:
                diferencias.append("sala %s en vez de %s" % (partida.jugador.sala.id,
                                                             general.sala_actual))
            if sala_guardada is not None:
                objetos = []
                for objeto in partida.objetos_en_sala():
                    objetos.append(objeto.id)
                if objetos != sala_guardada.objetos:
                    diferencias.append("objetos del suelo distintos en la sala actual")
            if len(diferencias) > 0:
                raise ErrorCarga("La partida reconstruida no coincide con la guardada (%s)."
                                 % ", ".join(diferencias))

        try:
            partida = app.crear_partida(general.id_cripta, semilla=general.semilla,
                                        ordenes_previas=ordenes, partida_nueva=False,
                                        exigir_versiones=(general.version_cripta,
                                                          general.version_catalogo),
                                        validar=validar)
        except ErrorCarga:
            raise
        except ErrorCripta as error:
            raise ErrorCarga("No se puede cargar la partida guardada: %s" % error)
        # §5.1: la partida cargada sigue gastando SU presupuesto: lo que ya había usado
        # antes de guardarse + lo que costó cargarla ahora. Solo si la carga se completó.
        app.presupuesto.continuar(general.solicitudes, marca)
        partida.bitacora.agregar("Partida cargada: %d acciones re-ejecutadas." % len(ordenes))
        return partida