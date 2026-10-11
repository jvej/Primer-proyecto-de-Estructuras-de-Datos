"""Cripta sintética para probar el motor sin red, con la misma forma que las respuestas de la
API (§3.3), pasando por el cliente real: ejecutor, presupuesto, resolutor, precarga y esqueleto.

InventarioDePrueba es una lista simple que cumple el contrato que usa Partida;
Axel lo reemplaza con su estructura de §4.5.
"""

from almacen_local import AlmacenLocalMemoria
from bitacora_pantalla import BitacoraPantalla
from ejecutor_red import EjecutorRed
from esqueleto import descargar_esqueleto
from fuente_datos import FuenteDatos
from objetos import Objeto
from partida import Partida
from precarga_contenido import PrecargaContenido
from presupuesto_red import PresupuestoRed
from resolutor_catalogo import ResolutorCatalogo

CATALOGO = [
    {"id": "ent_rata", "clase": "enemigo", "nombre": "Rata gigante", "vida_max": 12, "ataque": 5,
     "defensa": 1, "velocidad": 150, "comportamiento": "rastreador", "suelta": ["itm_pocion"]},
    {"id": "ent_esqueleto", "clase": "enemigo", "nombre": "Esqueleto", "vida_max": 10, "ataque": 4,
     "defensa": 2, "velocidad": 100, "comportamiento": "guardian", "suelta": ["itm_pocion"]},
    {"id": "ent_errante", "clase": "enemigo", "nombre": "Murciélago", "vida_max": 6, "ataque": 3,
     "defensa": 0, "velocidad": 100, "comportamiento": "errante", "suelta": []},
    {"id": "ent_troll", "clase": "enemigo", "nombre": "Troll", "vida_max": 20, "ataque": 6,
     "defensa": 1, "velocidad": 100, "comportamiento": "guardian", "regeneracion": 2, "suelta": []},
    {"id": "itm_daga", "clase": "arma", "nombre": "Daga", "peso": 2, "valor": 15, "ataque_bonus": 3},
    {"id": "itm_cota", "clase": "armadura", "nombre": "Cota", "peso": 8, "valor": 40, "defensa_bonus": 2},
    {"id": "itm_pocion", "clase": "pocion", "nombre": "Poción menor", "peso": 1, "valor": 5, "cura": 10},
    {"id": "itm_pocion_rapida", "clase": "pocion", "nombre": "Poción de velocidad", "peso": 1,
     "valor": 9, "modificador_velocidad": 50, "duracion": 300},
    {"id": "itm_antidoto", "clase": "antidoto", "nombre": "Antídoto", "peso": 1, "valor": 8},
    {"id": "itm_antorcha", "clase": "antorcha", "nombre": "Antorcha", "peso": 1, "valor": 5, "duracion": 2000},
    {"id": "itm_pergamino", "clase": "pergamino_retroceso", "nombre": "Pergamino de retroceso", "peso": 1, "valor": 30},
    {"id": "itm_llave_bronce", "clase": "llave", "nombre": "Llave de bronce", "peso": 1, "valor": 3},
    {"id": "itm_llave_negra", "clase": "llave", "nombre": "Llave negra", "peso": 1, "valor": 3},
    {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos en la pared", "daño": 4, "rearme": 300},
    {"id": "trp_mortal", "clase": "trampa", "nombre": "Foso", "daño": 500, "rearme": 300},
    {"id": "trp_aguja", "clase": "trampa", "nombre": "Aguja envenenada", "daño": 0, "veneno": 2, "rearme": 300},
]

DATOS = {"id": "cripta-test", "version": "t1", "sala_inicial": 1, "sala_salida": 4,
         "llave_salida": "itm_llave_negra", "presupuesto_solicitudes": 200, "inventario_max": 3,
         "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}}


def esqueleto_linea(n, puertas=()):
    """Salas 1..n en línea (N sube, S baja). puertas: [(a, a+1, {"cerrada": True, "llave": ...})]."""
    salas = []
    for i in range(1, n + 1):
        salidas = {}
        for destino, direccion in ((i - 1, "S"), (i + 1, "N")):
            if destino < 1 or destino > n:
                continue
            datos = {"sala": destino}
            for a, b, extra in puertas:
                if (a == i and b == destino) or (b == i and a == destino):
                    datos.update(extra)
            salidas[direccion] = datos
        salas.append({"id": i, "nombre": "Sala %d" % i, "salidas": salidas})
    return salas


def entrada(sala, enemigos=(), objetos=(), trampas=()):
    """enemigos: [(instancia, tipo, vida)]; objetos: [ids]; trampas: [(instancia, tipo)]."""
    return {"sala": sala,
            "enemigos": [{"instancia": i, "tipo": t, "vida": v} for i, t, v in enemigos],
            "objetos": list(objetos),
            "trampas": [{"instancia": i, "tipo": t} for i, t in trampas]}


class FuenteSimulada(FuenteDatos):
    def __init__(self, datos, salas, contenido, presupuesto):
        self.presupuesto = presupuesto
        self._datos = datos
        self._salas = salas
        self._contenido = contenido
        self.solicitudes = 0

    def datos_cripta(self, id_cripta):
        return self._datos

    def pagina_esqueleto(self, id_cripta, pagina):
        return {"pagina": 1, "total_paginas": 1, "salas": self._salas}

    def contenido_salas(self, id_cripta, ids_salas):
        self.presupuesto.registrar("contenido")
        self.solicitudes += 1
        resultado = []
        for id_sala in ids_salas:
            encontrada = entrada(id_sala)
            for e in self._contenido:
                if e["sala"] == id_sala:
                    encontrada = e
            resultado.append(encontrada)
        return {"contenido": resultado}

    def catalogo(self, ids):
        self.presupuesto.registrar("catalogo")
        self.solicitudes += 1
        fichas = []
        for id_ in ids:
            for f in CATALOGO:
                if f["id"] == id_:
                    fichas.append(f)
        return {"entidades": fichas}


class InventarioDePrueba:
    def __init__(self, capacidad):
        self.capacidad = capacidad
        self._lista = []

    def lleno(self):
        return len(self._lista) >= self.capacidad

    def objetos(self):
        return list(self._lista)

    def agregar(self, objeto):
        self._lista.append(objeto)

    def agregar_al_frente(self, objeto):
        self._lista.insert(0, objeto)

    def quitar(self, objeto):
        posicion = self._lista.index(objeto)
        del self._lista[posicion]
        return posicion

    def restaurar(self, objeto, posicion):
        self._lista.insert(posicion, objeto)


class Escenario:
    def __init__(self, partida, ejecutor, fuente, inventario, bitacora, presupuesto):
        self.partida = partida
        self.ejecutor = ejecutor
        self.fuente = fuente
        self.inventario = inventario
        self.bitacora = bitacora
        self.presupuesto = presupuesto

    def dar(self, id_ficha):
        """Mete un objeto del catálogo directo al inventario (atajo para pruebas)."""
        for ficha in CATALOGO:
            if ficha["id"] == id_ficha:
                objeto = Objeto(ficha)
                self.inventario.agregar(objeto)
                return objeto

    def mensajes(self):
        return self.bitacora.ultimos()

    def cerrar(self):
        self.ejecutor.cerrar()


def armar(salas, contenido=(), datos=None, semilla=1, capacidad=3, limite=None, capacidad_bitacora=500):
    datos_cripta = dict(DATOS)
    if datos is not None:
        datos_cripta.update(datos)
    presupuesto = PresupuestoRed(limite, activo=limite is not None)
    fuente = FuenteSimulada(datos_cripta, salas, list(contenido), presupuesto)
    ejecutor = EjecutorRed()
    local = AlmacenLocalMemoria()
    resolutor = ResolutorCatalogo(fuente, ejecutor, local, presupuesto)
    esqueleto = descargar_esqueleto(fuente, datos_cripta["id"])
    precarga = PrecargaContenido(fuente, datos_cripta["id"], esqueleto, ejecutor, presupuesto, resolutor)
    inventario = InventarioDePrueba(capacidad)
    bitacora = BitacoraPantalla(capacidad_bitacora)
    partida = Partida(datos_cripta, esqueleto, precarga, resolutor, inventario, bitacora, semilla)
    partida.iniciar()
    return Escenario(partida, ejecutor, fuente, inventario, bitacora, presupuesto)