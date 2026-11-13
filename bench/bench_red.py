import time

from bench.generador_criptas import generar_cripta
from modelo.datos.almacen_local import AlmacenLocalMemoria
from modelo.datos.cliente_http import ClienteHTTP
from modelo.juego.bitacora_pantalla import BitacoraPantalla
from modelo.datos.ejecutor_red import EjecutorRed
from modelo.datos.esqueleto import Esqueleto, descargar_esqueleto
from modelo.datos.precarga_contenido import PrecargaContenido
from modelo.datos.presupuesto_red import PresupuestoRed
from modelo.datos.resolutor_catalogo import ResolutorCatalogo
from tests.test_red import FuenteFalsa, RespuestaFalsa, SesionFalsa
from tests.test_resolubilidad import _AlmacenMemoria, _integracion_memoria

class BitacoraConPop:

    def __init__(self, capacidad=20):
        self.capacidad = capacidad
        self.mensajes = []

    def agregar(self, mensaje):
        self.mensajes.append(mensaje)
        if len(self.mensajes) > self.capacidad:
            self.mensajes.pop(0)


def medir_bitacora():
    print("== §4.8 Bitácora: circular vs lista con pop(0) (us por mensaje) ==")
    print("capacidad | circular | pop(0)")
    for capacidad in [20, 1000, 20000, 200000]:
        n = 20000
        resultados = []
        for clase in (BitacoraPantalla, BitacoraConPop):
            b = clase(capacidad)
            for i in range(capacidad):        
                b.agregar("m")
            inicio = time.perf_counter()
            for i in range(n):
                b.agregar("mensaje de prueba")
            resultados.append((time.perf_counter() - inicio) / n * 1e6)
        print("%9d | %8.3f | %8.3f" % (capacidad, resultados[0], resultados[1]))


def contar_solicitudes(n_salas, tam_lote):
    presupuesto = PresupuestoRed(None)
    fuente = FuenteFalsa(n_salas, 0, presupuesto)
    ejecutor = EjecutorRed()
    resolutor = ResolutorCatalogo(fuente, ejecutor, AlmacenLocalMemoria(), presupuesto,
                                  tam_lote=tam_lote)
    esqueleto = descargar_esqueleto(fuente, "c")
    precarga = PrecargaContenido(fuente, "c", esqueleto, ejecutor, presupuesto, resolutor,
                                 tam_lote=tam_lote)
    precarga.iniciar(1)
    for destino in range(2, n_salas + 1):
        precarga.asegurar(destino)
        precarga.al_entrar(destino)
    ejecutor.cerrar()
    return presupuesto.realizadas, precarga.esperas_bloqueantes


def medir_solicitudes():
    print("== §4.2/§4.3 Recorrer toda la cripta (cripta lineal sintética) ==")
    print("salas | lotes de 10: solicitudes (esperas) | 1 por solicitud: solicitudes (esperas)")
    for n in [20, 60, 200]:
        con, esp_con = contar_solicitudes(n, 10)
        sin, esp_sin = contar_solicitudes(n, 1)
        print("%5d | %22d (%d) | %28d (%d)" % (n, con, esp_con, sin, esp_sin))


def contar_solicitudes_llaves(copia_local=False, codigos=(200,)):
    """Aísla /llaves con la versión ya comprobada; toda respuesta es simulada."""
    datos = generar_cripta(numero_salas=2, semilla=7, cadena_llaves=1, topologia="linea")
    general = datos["general"]
    salas = datos["paginas"][0]["salas"]
    cuerpo = datos["llaves"]
    esqueleto = Esqueleto()
    esqueleto.agregar_pagina(datos["paginas"][0])
    almacen = _AlmacenMemoria(general, salas, cuerpo if copia_local else None)
    presupuesto = PresupuestoRed(None)
    sesion = SesionFalsa([RespuestaFalsa(codigo, cuerpo if codigo == 200 else {"reintentar_en": 0})
                          for codigo in codigos])
    cliente = ClienteHTTP(presupuesto, sesion=sesion, dormir=lambda segundos: None)
    # Solo se aísla la preparación de disco y motor; la selección de copia y
    # el conteo de cada intento HTTP se ejecutan con los métodos de producción.
    with _integracion_memoria(cliente, almacen) as (modulo, _):
        app = modulo.Aplicacion(cliente, presupuesto, registrar_log=False, registrar_puntajes=False)
        app.local = AlmacenLocalMemoria()
        try:
            inicio = time.perf_counter()
            resultado = app._verificar_cripta(general["id"], general, esqueleto, almacen)
            tiempo_ms = (time.perf_counter() - inicio) * 1000
        finally:
            app.cerrar()
    if not resultado.es_resoluble() or almacen.leer_llaves() != cuerpo:
        raise AssertionError("La consulta o copia de llaves cambió el resultado esperado")
    ruta = cliente.base_url + "/criptas/%s/llaves" % general["id"]
    if presupuesto.realizadas != len(sesion.llamadas) or any(
            llamada[0] != ruta for llamada in sesion.llamadas):
        raise AssertionError("El presupuesto debe contar solo los intentos de /llaves")
    return presupuesto.realizadas, tiempo_ms


def medir_llaves():
    print("== FR-003/FR-004 /llaves: presupuesto y latencia con sesión simulada ==")
    print("Sin red real ni espera de reintento; versión de cripta ya comprobada.")
    print("Tiempo incluye selección de copia, lectura/consulta y verificación; excluye preparación.")
    print("caso                              | solicitudes gastadas | tiempo (ms)")
    for nombre, copia, codigos, esperadas in (
            ("sin copia local (200)", False, (200,), 1),
            ("copia local de la misma versión", True, (), 0),
            ("sin copia local (429 -> 200)", False, (429, 200), 2)):
        solicitudes, tiempo_ms = contar_solicitudes_llaves(copia, codigos)
        if solicitudes != esperadas:
            raise AssertionError("Conteo incorrecto de /llaves: " + nombre)
        print("%-33s | %20d | %11.3f" % (nombre, solicitudes, tiempo_ms))


if __name__ == "__main__":
    medir_bitacora()
    medir_solicitudes()
    medir_llaves()
