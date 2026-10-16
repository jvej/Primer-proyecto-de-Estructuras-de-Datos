"""Pruebas de las correcciones pedidas en la revisión del proyecto.
Ejecutar: python test_revision.py

  2.1  la lista de criptas cuenta en el presupuesto de la partida siguiente
  2.2/3.2  las respuestas del catálogo no retienen fichas desalojadas de la caché
  3.1  --cache-size 1, 2 y 3 no se caen al cargar la sala inicial
  3.3  política explícita cuando todas las fichas están en uso
  5.1  soltar el objeto del cursor no recorre el inventario (no depende de su posición)
  5.2  guardar y reabrir no devuelve presupuesto de red
"""
import gc
import os
import shutil
import tempfile

import crear_paquete_prueba
from aplicacion import Aplicacion
from cache import Cache
from cliente_offline import ClienteOffline
from controlador import Controlador
import lista_doble
from cripta_de_prueba import armar, esqueleto_linea
from orden import ATACAR, MOVER, Orden, RECOGER, SOLTAR
from persistencia_partida import PersistenciaPartida
from presupuesto_red import PresupuestoRed


class FuenteContada(ClienteOffline):
    """Paquete offline, pero cada llamada cuenta como solicitud (igual que la red)."""

    def __init__(self, carpeta):
        super().__init__(carpeta)
        self.presupuesto = PresupuestoRed()
        self.llamadas = 0

    def _contar(self, operacion):
        self.presupuesto.registrar(operacion)
        self.llamadas += 1

    def listar_criptas(self):
        self._contar("listar")
        return super().listar_criptas()

    def datos_cripta(self, id_cripta):
        self._contar("datos")
        return super().datos_cripta(id_cripta)

    def pagina_esqueleto(self, id_cripta, pagina):
        self._contar("pagina")
        return super().pagina_esqueleto(id_cripta, pagina)

    def contenido_salas(self, id_cripta, ids_salas):
        self._contar("contenido")
        return super().contenido_salas(id_cripta, ids_salas)

    def catalogo(self, ids):
        self._contar("catalogo")
        return super().catalogo(ids)

    def version_cripta(self, id_cripta):
        self._contar("version")
        return super().version_cripta(id_cripta)

    def version_catalogo(self):
        self._contar("version catalogo")
        return super().version_catalogo()


def entorno():
    base = tempfile.mkdtemp(prefix="cripta_rev_")
    paquete = crear_paquete_prueba.crear(os.path.join(base, "paquete"))
    return base, paquete


def test_cache_pequena_no_se_cae():
    for tope in (1, 2, 3):
        base, paquete = entorno()
        app = Aplicacion(ClienteOffline(paquete), PresupuestoRed(activo=False),
                         os.path.join(base, "datos"), cache_size=tope, semilla=7, nombre="P")
        partida = app.crear_partida(crear_paquete_prueba.ID)
        c = Controlador(partida)
        for orden in (Orden(RECOGER, 0), Orden(MOVER, "N"), Orden(ATACAR, 0), Orden(MOVER, "N")):
            c.ejecutar(orden)
        assert partida.reloj.tiempo_actual > 0
        app.cerrar()
        shutil.rmtree(base, ignore_errors=True)


def test_la_lista_cuenta_en_la_segunda_partida():
    base, paquete = entorno()
    fuente = FuenteContada(paquete)
    app = Aplicacion(fuente, fuente.presupuesto, os.path.join(base, "datos"), semilla=1)
    app.listar_criptas()
    app.crear_partida(crear_paquete_prueba.ID)
    assert fuente.presupuesto.realizadas == fuente.llamadas          # primera partida
    antes = fuente.llamadas
    app.listar_criptas()                                           # se pide para la segunda
    app.crear_partida(crear_paquete_prueba.ID)
    assert fuente.presupuesto.realizadas == fuente.llamadas - antes, \
        (fuente.presupuesto.realizadas, fuente.llamadas - antes)
    app.cerrar()
    shutil.rmtree(base, ignore_errors=True)


def test_respuestas_del_catalogo_no_retienen_fichas():
    base, paquete = entorno()
    app = Aplicacion(ClienteOffline(paquete), PresupuestoRed(activo=False),
                     os.path.join(base, "datos"), cache_size=2, semilla=7)
    partida = app.crear_partida(crear_paquete_prueba.ID)
    partida.resolutor.esperar()                                    # todos los lotes incorporados
    assert partida.resolutor.respuestas_retenidas() == 0
    gc.collect()
    ids = []
    for nombre in os.listdir(os.path.join(paquete, "catalogo")):
        if nombre != "version.json":
            ids.append(nombre[:-5])
    vivas = 0
    for objeto in gc.get_objects():
        if isinstance(objeto, dict) and "clase" in objeto and objeto.get("id") in ids:
            estatica = False                 # el catálogo de ejemplo del módulo de pruebas
            for ficha in crear_paquete_prueba.CATALOGO:
                if objeto is ficha:
                    estatica = True
            if not estatica:
                vivas += 1
    cache = app.local.cache
    assert vivas <= cache.cantidad(), (vivas, cache.cantidad())     # solo lo que guarda la caché
    app.cerrar()
    shutil.rmtree(base, ignore_errors=True)


def test_saturacion_explicita_y_vuelve_al_tope():
    usadas = ["a", "b", "c"]
    c = Cache(tope=3, en_uso=lambda i: i in usadas)
    for i in usadas:
        c.poner(i, i)
    assert c.poner("d", "d") is None and c.cantidad() == 4 and c.desbordes == 1
    usadas[:] = []                                                 # ya nada está en uso
    c.poner("e", "e")
    assert c.cantidad() == 3                                       # se corrige en el siguiente poner
    assert c.contiene("e") and c.desbordes == 1


def test_soltar_desde_el_cursor_no_depende_de_la_posicion():
    visitas = [0]
    original = lista_doble.ListaDoble.nodos

    def nodos_contados(self):
        for nodo in original(self):
            visitas[0] += 1
            yield nodo

    lista_doble.ListaDoble.nodos = nodos_contados
    try:
        resultados = []
        for cual in ("primero", "ultimo"):
            esc = armar(esqueleto_linea(2), capacidad=1000)
            for i in range(1000):
                esc.dar("itm_daga")
            esc.inventario.ir_al_inicio()
            if cual == "ultimo":
                while esc.inventario.siguiente():
                    pass
            visitas[0] = 0
            assert Controlador(esc.partida).ejecutar(Orden(SOLTAR, None))
            resultados.append(visitas[0])
            esc.cerrar()
    finally:
        lista_doble.ListaDoble.nodos = original
    assert resultados[0] == resultados[1] == 0, resultados     # ni el primero ni el último recorren


def test_guardar_y_reabrir_conserva_el_presupuesto_gastado():
    base, paquete = entorno()
    datos = os.path.join(base, "datos")
    fuente = FuenteContada(paquete)
    app = Aplicacion(fuente, fuente.presupuesto, datos, semilla=7)
    app.listar_criptas()
    partida = app.crear_partida(crear_paquete_prueba.ID)
    controlador = Controlador(partida)
    controlador.agregar_observador(app.registrar_orden)        # así las órdenes van al guardado
    controlador.ejecutar(Orden(MOVER, "N"))
    gastadas = fuente.presupuesto.realizadas
    PersistenciaPartida(app).guardar(partida)
    app.cerrar()

    otra_fuente = FuenteContada(paquete)                       # "se reabre el programa"
    otra = Aplicacion(otra_fuente, otra_fuente.presupuesto, datos)
    otra.listar_criptas()
    otra.crear_partida(crear_paquete_prueba.ID)
    antes_de_cargar = otra_fuente.llamadas
    PersistenciaPartida(otra).cargar()
    al_cargar = otra_fuente.llamadas - antes_de_cargar
    assert al_cargar > 0
    assert otra_fuente.presupuesto.realizadas == gastadas + al_cargar, \
        (otra_fuente.presupuesto.realizadas, gastadas, al_cargar)
    otra.cerrar()
    shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    pruebas = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for nombre, funcion in pruebas:
        funcion()
        print("ok  ", nombre)
    print("\n%d pruebas correctas" % len(pruebas))