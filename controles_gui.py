"""Controles de la interfaz gráfica: tecla -> Orden (MVC, §6).

Este módulo NO importa Pygame: recibe el nombre de la tecla tal como lo da
pygame.key.name(...) ("up", "space", "f5", "g", ...) y devuelve lo mismo que
devolvería la consola, una Orden (orden.py). Así se puede probar sin ventana, y el
Controlador recibe exactamente las mismas órdenes en consola y en Pygame.

Devuelve:
  - una Orden, si la tecla es una acción;
  - una de las cadenas SIG_ENEMIGO / SIG_SUELO, si solo cambia la selección
    visual (no es una orden, no consume tiempo y no va al log);
  - None, si la tecla no hace nada.

Teclas:
  flechas ........... moverse            Shift + flecha ... abrir esa puerta
  Tab ............... elegir enemigo     Espacio .......... atacar al elegido
  F ................. elegir objeto del suelo                G ... recogerlo
  X ................. esperar            R ................ pergamino de retroceso
  W / S ............. cursor del inventario (anterior / siguiente)   Inicio ... al primero
  U / Q / T ......... usar / equipar / soltar el objeto del cursor
  1 / 2 / 3 ......... vista ordenada por peso / valor / nombre (Shift: descendente)
  I ................. ver inventario     P ................ puntajes
  F5 / F9 ........... guardar / cargar   H o F1 ........... ayuda    Esc ... salir
"""

from orden import (ABRIR, AYUDA, ATACAR, CARGAR, EQUIPAR, ESPERAR, GUARDAR, INV_ANTERIOR,
                   INV_INICIO, INV_ORDENAR, INV_SIGUIENTE, INVENTARIO, MOVER, Orden,
                   PERGAMINO, PUNTAJES, RECOGER, SALIR, SOLTAR, USAR)

SIG_ENEMIGO = "sig_enemigo"
SIG_SUELO = "sig_suelo"

# (tecla, texto) en el orden en que se muestran en la barra de botones de la ventana.
BOTONES = (
    ("space", "Atacar"), ("x", "Esperar"), ("g", "Recoger"), ("u", "Usar"),
    ("q", "Equipar"), ("t", "Soltar"), ("r", "Retroceso"), ("f5", "Guardar"),
    ("f9", "Cargar"), ("p", "Puntajes"), ("h", "Ayuda"), ("escape", "Salir"),
)

AYUDA_LINEAS = (
    "Flechas: moverse          Shift + flecha: abrir puerta",
    "Clic en una puerta: moverse (o abrirla si está cerrada)",
    "Tab o clic: elegir enemigo          Espacio: atacar",
    "F o clic: elegir objeto del suelo   G: recoger",
    "X: esperar          R: pergamino de retroceso",
    "W / S: mover el cursor del inventario   Inicio: al primero",
    "U / Q / T: usar / equipar / soltar el objeto del cursor",
    "1 / 2 / 3: ver inventario por peso / valor / nombre (Shift: descendente)",
    "I: inventario   P: puntajes   F5: guardar   F9: cargar   Esc: salir",
)


def direccion_de_tecla(tecla):
    """'up' -> 'N', etc. None si no es una flecha."""
    if tecla == "up":
        return "N"
    if tecla == "down":
        return "S"
    if tecla == "right":
        return "E"
    if tecla == "left":
        return "O"
    return None


def orden_para_tecla(tecla, shift, enemigo_elegido, objeto_elegido):
    """enemigo_elegido / objeto_elegido: posición (desde 0) seleccionada en la sala."""
    direccion = direccion_de_tecla(tecla)
    if direccion is not None:
        return Orden(ABRIR if shift else MOVER, direccion)
    if tecla == "tab":
        return SIG_ENEMIGO
    if tecla == "f":
        return SIG_SUELO
    if tecla == "space":
        return Orden(ATACAR, enemigo_elegido)
    if tecla == "g":
        return Orden(RECOGER, objeto_elegido)
    if tecla == "x":
        return Orden(ESPERAR)
    if tecla == "r":
        return Orden(PERGAMINO)
    if tecla == "w":
        return Orden(INV_ANTERIOR)
    if tecla == "s":
        return Orden(INV_SIGUIENTE)
    if tecla == "home":
        return Orden(INV_INICIO)
    if tecla == "u":
        return Orden(USAR, None)            # None = el objeto del cursor (§4.5)
    if tecla == "q":
        return Orden(EQUIPAR, None)
    if tecla == "t":
        return Orden(SOLTAR, None)
    if tecla in ("1", "2", "3"):
        criterio = ("peso", "valor", "nombre")[int(tecla) - 1]
        return Orden(INV_ORDENAR, criterio, shift)
    if tecla == "i":
        return Orden(INVENTARIO)
    if tecla == "p":
        return Orden(PUNTAJES)
    if tecla == "f5":
        return Orden(GUARDAR)
    if tecla == "f9":
        return Orden(CARGAR)
    if tecla in ("h", "f1"):
        return Orden(AYUDA)
    if tecla == "escape":
        return Orden(SALIR)
    return None


def siguiente_posicion(actual, cantidad):
    """Selección circular: 0, 1, ..., cantidad-1, 0. Con cantidad 0 queda en 0."""
    if cantidad <= 0:
        return 0
    return (actual + 1) % cantidad


def ajustar_posicion(actual, cantidad):
    """Si la lista se achicó (un enemigo murió), la selección vuelve a un valor válido."""
    if cantidad <= 0 or actual < 0:
        return 0
    if actual >= cantidad:
        return cantidad - 1
    return actual