import json
import os
import sys

from bench.generador_criptas import generar_cripta
from tests.cripta_de_prueba import CATALOGO, entrada, esqueleto_linea, ubicar_llaves

ID = "cripta-prueba"
VERSION = "p2"
VERSION_CATALOGO = "cat-prueba-3"
ID_CICLO = "cripta-ciclo"
ID_CAZADORES = "cripta-cazadores"


def salas_y_contenido():
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


def _escribir_cripta(carpeta, general, paginas, contenido, llaves):
    base = os.path.join(carpeta, "criptas", general["id"])
    escribir(os.path.join(base, "general.json"), general)
    escribir(os.path.join(base, "version.json"),
             {"id": general["id"], "version": general["version"]})
    escribir(os.path.join(base, "llaves.json"), llaves)
    for pagina in paginas:
        escribir(os.path.join(base, "salas_%d.json" % pagina["pagina"]), pagina)
        for sala in pagina["salas"]:
            datos = entrada(sala["id"])
            for e in contenido:
                if e["sala"] == sala["id"]:
                    datos = e
                    break
            escribir(os.path.join(base, "contenido_%s.json" % sala["id"]), datos)


def crear(carpeta):
    salas, contenido = salas_y_contenido()
    general = {"id": ID, "version": VERSION, "salas_total": len(salas), "paginas": 1,
               "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 8,
               "llave_salida": "itm_llave_negra", "presupuesto_solicitudes": 12,
               "inventario_max": 6,
               "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}}
    _escribir_cripta(carpeta, general,
                     [{"pagina": 1, "total_paginas": 1, "salas": salas}],
                     contenido, ubicar_llaves(contenido))
    listado = [{"id": ID, "nombre": "Cripta de prueba", "salas": len(salas), "dificultad": 1}]
    for ficha in CATALOGO:
        escribir(os.path.join(carpeta, "catalogo", ficha["id"] + ".json"), ficha)

    ciclo = generar_cripta(numero_salas=2, semilla=1)
    ciclo["general"]["id"] = ID_CICLO
    # La llave queda al otro lado de la única puerta que la pide.
    ciclo["contenido"]["contenido"][0]["objetos"] = []
    ciclo["contenido"]["contenido"][1]["objetos"] = [ciclo["general"]["llave_salida"]]
    ciclo["llaves"]["llaves"][0]["sala"] = 2
    referencia = generar_cripta(numero_salas=48, semilla=7, rango_costos=(40, 200),
                               cantidad_cazadores=32, rango_cazadores=600,
                               cadena_llaves=12, cierre_automatico=300, salas_por_pagina=20)
    referencia["general"]["id"] = ID_CAZADORES
    for datos in (ciclo, referencia):
        datos["general"]["version"] = VERSION
        _escribir_cripta(carpeta, datos["general"], datos["paginas"],
                         datos["contenido"]["contenido"], datos["llaves"])
        listado.append({"id": datos["general"]["id"], "nombre": datos["general"]["id"],
                        "salas": datos["general"]["salas_total"], "dificultad": 1})
        for ficha in datos["catalogo"]["entidades"]:
            escribir(os.path.join(carpeta, "catalogo", ficha["id"] + ".json"), ficha)
    escribir(os.path.join(carpeta, "criptas.json"), {"criptas": listado})
    escribir(os.path.join(carpeta, "catalogo", "version.json"), {"version": VERSION_CATALOGO})
    return carpeta


if __name__ == "__main__":
    destino = crear(sys.argv[1] if len(sys.argv) > 1 else "paquete_prueba")
    print("Paquete de prueba creado en %s" % destino)
