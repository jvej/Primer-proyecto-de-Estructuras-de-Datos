"""Crea un paquete --offline de prueba con la cripta sintética de cripta_de_prueba.py.

    python -m tests.crear_paquete_prueba [carpeta]        (por defecto: paquete_prueba/)
    python main.py --offline paquete_prueba/

Sirve para probar el programa completo (main, replay, guardar/cargar, puntajes) sin
red mientras no se tenga el paquete oficial del curso. La estructura de carpetas es la
que lee cliente_offline.py; si el paquete oficial usa otra, se ajusta ese archivo.
"""

import json
import os
import sys

from tests.cripta_de_prueba import CATALOGO, entrada, esqueleto_linea

ID = "cripta-prueba"
VERSION = "p1"
VERSION_CATALOGO = "cat-prueba-2"


def salas_y_contenido():
    # 8 salas en línea; la puerta 7 -> 8 (salida) se abre con la llave negra y se cierra sola.
    salas = esqueleto_linea(8, [(7, 8, {"cerrada": True, "llave": "itm_llave_negra",
                                        "cierre_automatico": 300})])
    contenido = [
        entrada(1, objetos=["itm_daga", "itm_pergamino", "itm_pocion"]),
        entrada(2, enemigos=[("e-201", "ent_rata", 12)], objetos=["itm_cota"]),
        entrada(3, trampas=[("t-301", "trp_aguja")], objetos=["itm_antidoto"]),
        entrada(4, enemigos=[("e-401", "ent_errante", 6)], objetos=["itm_pergamino"]),
        entrada(5, enemigos=[("e-501", "ent_troll", 20)], objetos=["itm_pocion_rapida"]),
        entrada(6, objetos=["itm_llave_negra", "itm_antorcha"]),
        entrada(7, enemigos=[("e-701", "ent_esqueleto", 10)]),
    ]
    return salas, contenido


def escribir(ruta, datos):
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)


def crear(carpeta):
    salas, contenido = salas_y_contenido()
    general = {"id": ID, "version": VERSION, "salas_total": len(salas), "paginas": 1,
               "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 8,
               "llave_salida": "itm_llave_negra", "presupuesto_solicitudes": 12,
               "inventario_max": 6,
               "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}}
    escribir(os.path.join(carpeta, "criptas.json"),
             {"criptas": [{"id": ID, "nombre": "Cripta de prueba", "salas": len(salas),
                           "dificultad": 1}]})
    base = os.path.join(carpeta, "criptas", ID)
    escribir(os.path.join(base, "general.json"), general)
    escribir(os.path.join(base, "version.json"), {"id": ID, "version": VERSION})
    escribir(os.path.join(base, "salas_1.json"), {"pagina": 1, "total_paginas": 1, "salas": salas})
    for sala in salas:
        datos = entrada(sala["id"])
        for e in contenido:
            if e["sala"] == sala["id"]:
                datos = e
        escribir(os.path.join(base, "contenido_%s.json" % sala["id"]), datos)
    for ficha in CATALOGO:
        escribir(os.path.join(carpeta, "catalogo", ficha["id"] + ".json"), ficha)
    escribir(os.path.join(carpeta, "catalogo", "version.json"), {"version": VERSION_CATALOGO})
    return carpeta


if __name__ == "__main__":
    destino = crear(sys.argv[1] if len(sys.argv) > 1 else "paquete_prueba")
    print("Paquete de prueba creado en %s" % destino)