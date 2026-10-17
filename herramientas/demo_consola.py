"""Demo jugable en la terminal, sin red: python -m herramientas.demo_consola

Arma la aplicación (Modelo + Vista + Controlador) con la cripta sintética de
cripta_de_prueba.py. Es también el ejemplo de cómo debe cablear main.py: el
Controlador recibe listar_criptas() y crear_partida(id), y no sabe de dónde vienen.
"""
from controlador.controlador import Controlador
from tests.cripta_de_prueba import armar, entrada, esqueleto_linea
from vista.vista_consola import VistaConsola

_escenarios = []   # para cerrar los hilos de red simulada al salir


def listar_criptas():
    return [{"id": "cripta-demo", "nombre": "Cripta de demostración", "salas": 5, "dificultad": 1}]


def crear_partida(id_cripta):
    salas = esqueleto_linea(5, [(3, 4, {"cerrada": True, "llave": "itm_llave_negra"})])
    contenido = [
        entrada(1, objetos=["itm_daga", "itm_llave_negra", "itm_pergamino", "itm_pocion"]),
        entrada(2, enemigos=[("e-201", "ent_rata", 12)], objetos=["itm_cota"]),
        entrada(3, enemigos=[("e-301", "ent_esqueleto", 10)], trampas=[("t-1", "trp_dardos")]),
    ]
    escenario = armar(salas, contenido, capacidad=6)
    _escenarios.append(escenario)
    return escenario.partida


def main():
    controlador = Controlador(vista=VistaConsola())
    try:
        print("CRIPTA - demo en terminal. Escribe 'ayuda' para ver los comandos.")
        controlador.correr_sesion(listar_criptas, crear_partida)
    finally:
        for escenario in _escenarios:
            escenario.cerrar()
    print("Hasta pronto.")


if __name__ == "__main__":
    main()