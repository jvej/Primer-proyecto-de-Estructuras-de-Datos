import os

from modelo.juego.errores import ErrorCripta
from modelo.datos.guardado_binario import (ErrorFormato, PartidaGuardada, SalaGuardada, cargar_general,
                              guardar, leer_sala)
from controlador.orden import Orden
from modelo.juego.sala import DIRECCIONES


class ErrorCarga(ErrorCripta):
    """No se pudo cargar la partida guardada (mensaje listo para el usuario)."""


def foto_de(partida, version_catalogo, nombre, ordenes, solicitudes=0):
    foto = PartidaGuardada(partida.reloj.tiempo_actual, partida.semilla, partida.jugador.vida,
                           partida.jugador.sala.id, partida.id_cripta, partida.version_cripta,
                           version_catalogo, nombre)
    foto.solicitudes = solicitudes
    foto.n_salas_conocidas = len(partida.mapa.salas)
    foto.estados_salas = list(partida.conocimiento.estado_salas)
    foto.memoria_puertas = list(partida.conocimiento.memoria_puertas)
    for objeto in partida.inventario.objetos():
        foto.inventario.append(objeto.id)
    for orden in ordenes:
        foto.ordenes.append(orden.a_texto())
    for sala in partida.mapa.salas:
        if not sala.incorporada and sala.ultimo_instante_jugador is None:
            continue                         
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
            general = cargar_general(self.ruta)    
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
            try:
                sala_guardada = leer_sala(self.ruta, general.sala_actual)
            except (ErrorFormato, OSError) as error:
                raise ErrorCarga("No se pudo leer la sala guardada: %s" % error) from error
            c = partida.conocimiento
            salas = partida.mapa.salas
            n = len(salas)
            if (type(general.n_salas_conocidas) is not int
                    or general.n_salas_conocidas != n or c.total_salas != n):
                raise ErrorCarga("Conocimiento incompatible: N no coincide con el mapa.")
            if c.mapa is not partida.mapa or c.salas_por_indice is not salas:
                raise ErrorCarga("Conocimiento incompatible: referencias del mapa incorrectas.")
            for i, sala in enumerate(salas):
                if type(sala.indice) is not int or sala.indice != i:
                    raise ErrorCarga("Conocimiento incompatible: índices de salas no contiguos.")
            # Solo lectura: conservar objetos, arreglos e inversos del replay.
            for estados, memoria in ((general.estados_salas, general.memoria_puertas),
                                     (c.estado_salas, c.memoria_puertas)):
                if len(estados) != n or len(memoria) != 4 * n:
                    raise ErrorCarga("Conocimiento incompatible: longitud de los arreglos.")
                for estado in estados:
                    if type(estado) is not int or estado not in (0, 1, 2):
                        raise ErrorCarga("Conocimiento incompatible: estado de sala inválido.")
                for posicion, estado in enumerate(memoria):
                    if type(estado) is not int or estado not in (0, 1, 2):
                        raise ErrorCarga("Conocimiento incompatible: estado de puerta inválido.")
                    if estado == 0:
                        continue
                    sala = salas[posicion // 4]
                    salida = sala.salidas[posicion % 4]
                    if salida is None:
                        raise ErrorCarga("Conocimiento incompatible: memoria sin salida existente.")
                    vecina = salida.otro_lado(sala)
                    indice = vecina.indice
                    if (type(indice) is not int or not 0 <= indice < n
                            or salas[indice] is not vecina):
                        raise ErrorCarga("Conocimiento incompatible: extremo de puerta inválido.")
                    for direccion, otra_salida in enumerate(vecina.salidas):
                        if otra_salida is salida:
                            if memoria[indice * 4 + direccion] != estado:
                                raise ErrorCarga("Conocimiento incompatible: memoria incoherente entre extremos.")
                            break
                    else:
                        raise ErrorCarga("Conocimiento incompatible: falta el otro extremo de puerta.")
                actual = partida.jugador.sala.indice
                if estados[actual] != 2:
                    raise ErrorCarga("Conocimiento incompatible: sala actual no explorada.")
            exploradas = sum(estado == 2 for estado in c.estado_salas)
            avistadas = sum(estado == 1 for estado in c.estado_salas)
            if (c.num_exploradas != exploradas or c.num_avistadas != avistadas):
                raise ErrorCarga("Conocimiento incompatible: contadores distintos del recuento de estados.")
            diferencias = []
            if general.estados_salas != c.estado_salas:
                diferencias.append("estado_salas distinto del replay")
            if general.memoria_puertas != c.memoria_puertas:
                diferencias.append("memoria_puertas distinta del replay")
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
        app.presupuesto.continuar(general.solicitudes, marca)
        partida.bitacora.agregar("Partida cargada: %d acciones re-ejecutadas." % len(ordenes))
        return partida