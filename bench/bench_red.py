import time

from modelo.datos.almacen_local import AlmacenLocalMemoria
from modelo.juego.bitacora_pantalla import BitacoraPantalla
from modelo.datos.ejecutor_red import EjecutorRed
from modelo.datos.esqueleto import descargar_esqueleto
from modelo.datos.precarga_contenido import PrecargaContenido
from modelo.datos.presupuesto_red import PresupuestoRed
from modelo.datos.resolutor_catalogo import ResolutorCatalogo
from tests.test_red import FuenteFalsa

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


if __name__ == "__main__":
    medir_bitacora()
    medir_solicitudes()