import random

from actor import Actor, Enemigo
from activacion import activar_enemigos
from agenda_eventos import AgendaEventos
from bucle_principal import Reloj, correr
from movimiento import mover_jugador
from sala import Sala

agenda = AgendaEventos()
reloj = Reloj()
azar = random.Random(42)  # semilla fija: reproducible (§2.6)
bitacora = []

# --- Mapa de prueba: tres salas en línea, A - B - C ---
sala_a = Sala(id=1)
sala_b = Sala(id=2)
sala_c = Sala(id=3)
sala_a.conectar("N", sala_b)
sala_b.conectar("N", sala_c)

jugador = Actor(nombre="Jugador", vida=30, ataque=6, defensa=2, velocidad=100, sala=sala_a)
sala_a.marcar_visita_jugador(0)  # la sala inicial recibe rastro en t=0 (§2.9)

rastreadora = Enemigo(
    nombre="Rata gigante", vida=12, ataque=5, defensa=1, velocidad=150,
    comportamiento="rastreador", id_instancia="e-201", sala=sala_c,
)

# El jugador se mueve A -> B; B recibe rastro fresco en t=0.
print(mover_jugador(jugador, "N", tiempo_actual=0))

# En el juego real esto pasa cuando el jugador entra a la sala de la rata;
# aquí la activamos directo para poder probar el comportamiento aislado.
activar_enemigos(agenda, [rastreadora], reloj_actual=0, jugador=jugador, azar=azar, bitacora=bitacora)


def partida_activa():
    return jugador.esta_vivo() and len(bitacora) < 4  # límite arbitrario, solo para la demo


correr(agenda, reloj, partida_activa)

for linea in bitacora:
    print(linea)