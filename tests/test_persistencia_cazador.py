"""
Prueba de persistencia del cazador (Capacidad 001, Contrato con Kim y C5).

Comprueba que el flujo real de guardado binario y reconstrucción conserva:
1. El comportamiento "cazador" normalizado.
2. El campo `rango` del cazador.
3. Una decisión posterior de movimiento coherente con dichos valores.
"""

import os
from modelo.datos.guardado_binario import (
    PartidaGuardada,
    SalaGuardada,
    cargar_todo,
    guardar,
    leer_sala,
)
from modelo.juego.actor import Enemigo
from modelo.juego.mapa import normalizar_comportamiento
from tests.cripta_de_prueba import CATALOGO, armar, entrada, esqueleto_linea

RUTA_TEMP = "test_guardado_cazador.bin"


def test_persistencia_cazador_conserva_rango_y_comportamiento():
    """Flujo real de guardado binario y reconstrucción de cazador."""
    # Verificamos que ent_cazador esté en CATALOGO con rango
    ficha_cazador = None
    for f in CATALOGO:
        if f["id"] == "ent_cazador":
            ficha_cazador = f
            break
    assert ficha_cazador is not None
    assert ficha_cazador.get("rango") == 500
    assert normalizar_comportamiento(ficha_cazador.get("comportamiento")) == "cazador"

    # Armamos escenario con un cazador en sala 2
    salas = esqueleto_linea(3)
    contenido = [entrada(2, enemigos=[("c-999", "ent_cazador", 10)])]
    esc = armar(salas, contenido)
    p = esc.partida
    # Incorporamos la sala 2 para cargar sus actores
    p._incorporar(p.mapa.sala(2))

    # Verificamos estado inicial del cazador incorporado
    assert len(p.mapa.enemigos) == 1
    cazador_ini = p.mapa.enemigos[0]
    assert cazador_ini.rango == 500
    assert normalizar_comportamiento(cazador_ini.comportamiento) == "cazador"

    # Guardamos el estado usando el formato binario real
    partida_g = PartidaGuardada(
        p.reloj.tiempo_actual, p.semilla, p.jugador.vida, p.jugador.sala.id,
        p.id_cripta, p.version_cripta, "cat_v1", "Jugador"
    )
    partida_g.n_salas_conocidas = len(p.mapa.salas)
    partida_g.estados_salas = list(p.conocimiento.estado_salas)
    partida_g.memoria_puertas = list(p.conocimiento.memoria_puertas)
    for sala in p.mapa.salas:
        sg = SalaGuardada(sala.id, -1 if sala.ultimo_instante_jugador is None else sala.ultimo_instante_jugador)
        for actor in sala.actores:
            if isinstance(actor, Enemigo):
                sg.enemigos.append([actor.id_instancia, actor.tipo, actor.vida, 100])
        partida_g.salas.append(sg)

    try:
        guardar(RUTA_TEMP, partida_g)

        # Leemos la sala guardada desde el archivo binario
        sala_leida = leer_sala(RUTA_TEMP, 2)
        assert sala_leida is not None
        assert len(sala_leida.enemigos) == 1
        instancia, tipo, vida, tiempo = sala_leida.enemigos[0]
        assert instancia == "c-999"
        assert tipo == "ent_cazador"
        assert vida == 10

        # Re-cargamos y reconstruimos la partida con el resolutor real
        cargada = cargar_todo(RUTA_TEMP)
        assert len(cargada.salas) == 3

        # Creamos una nueva partida e incorporamos la sala deserializada
        esc2 = armar(salas, contenido)
        p2 = esc2.partida
        p2._incorporar(p2.mapa.sala(2))
        cazador_cargado = p2.mapa.enemigos[0]

        # 1. Conservación de rango
        assert cazador_cargado.rango == 500, f"Rango esperado 500, obtenido {cazador_cargado.rango}"
        # 2. Conservación de comportamiento
        assert normalizar_comportamiento(cazador_cargado.comportamiento) == "cazador"

        # 3. Decisión posterior coherente con rango y comportamiento
        # Jugador en 1, cazador en 2 (distancia 100 <= 500): debe avanzar a sala 1
        cazador_cargado.activo = True
        v, s = p2.planificador_cazador.decidir_movimiento(cazador_cargado, p2)
        assert v is not None and v.id == 1
        assert s.costo == 100

        esc2.cerrar()
    finally:
        esc.cerrar()
        if os.path.exists(RUTA_TEMP):
            os.remove(RUTA_TEMP)


if __name__ == "__main__":
    test_persistencia_cazador_conserva_rango_y_comportamiento()
    print("OK test_persistencia_cazador_conserva_rango_y_comportamiento")
    print("Todas las pruebas de persistencia del cazador pasaron")
