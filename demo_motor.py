from evento import Evento
from agenda_eventos import AgendaEventos

agenda = AgendaEventos()


def accion(nombre):
    def ejecutar():
        print(f"ejecuta: {nombre}")
    return ejecutar


e1 = Evento(100, agenda.nueva_secuencia(), None, accion("goblin ataca"), "goblin ataca")
e2 = Evento(50, agenda.nueva_secuencia(), None, accion("esqueleto se mueve"), "esqueleto se mueve")
e3 = Evento(50, agenda.nueva_secuencia(), None, accion("trampa se activa"), "trampa se activa")

for e in (e1, e2, e3):
    agenda.agendar(e)

agenda.cancelar(e3)  # simula que su actor murió antes de que le tocara

while len(agenda) > 0:
    evento = agenda.siguiente()
    if evento:
        evento.ejecutar()

# Esperado: "esqueleto se mueve" (t=50) y luego "goblin ataca" (t=100).
# "trampa se activa" nunca se imprime.