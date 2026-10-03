from actor import Enemigo
from activacion import activar_enemigos
from agenda_eventos import AgendaEventos
from evento import Evento

agenda = AgendaEventos()


def ejecutar_turno(enemigo):
    print(f"ejecuta: turno de {enemigo.nombre} ({enemigo.id_instancia})")


# --- Caso 1: activación simultánea con desempate por id_instancia ---
rata_2 = Enemigo(nombre="Rata gigante", vida=12, ataque=5, defensa=1, velocidad=150, id_instancia="e-202")
rata_1 = Enemigo(nombre="Rata gigante", vida=12, ataque=5, defensa=1, velocidad=150, id_instancia="e-201")

# Se pasan en orden e-202, e-201 a propósito: deben agendarse como e-201 primero.
activar_enemigos(agenda, [rata_2, rata_1], reloj_actual=0, ejecutar_turno=ejecutar_turno)

print(f"e-201 tiempo_siguiente = {rata_1.evento_pendiente.tiempo_siguiente}")  # esperado: 66
print(f"e-202 tiempo_siguiente = {rata_2.evento_pendiente.tiempo_siguiente}")  # esperado: 66
print(f"e-201 secuencia = {rata_1.evento_pendiente.secuencia}")  # esperado: 1 (menor, por id_instancia)
print(f"e-202 secuencia = {rata_2.evento_pendiente.secuencia}")  # esperado: 2

# --- Caso 2: cambio de velocidad mientras una acción está programada ---
# Jugador con una acción programada en t=175, ahora en t=100 recibe una poción
# que lo acelera de velocidad 100 a 150.
evento_jugador = Evento(tiempo_siguiente=175, secuencia=agenda.nueva_secuencia(), actor=None, accion=lambda: None)
agenda.agendar(evento_jugador)

reagendado = agenda.reprogramar_por_cambio_velocidad(
    evento_jugador, tiempo_actual=100, velocidad_anterior=100, velocidad_nueva=150
)
# restante = 175 - 100 = 75; restante_nuevo = max(1, 75*100//150) = 50; nuevo tiempo = 150
print(f"nuevo tiempo_siguiente tras acelerar = {reagendado.tiempo_siguiente}")  # esperado: 150

while len(agenda) > 0:
    evento = agenda.siguiente()
    if evento:
        evento.ejecutar()