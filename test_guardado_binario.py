import os
from guardado_binario import (guardar, leer_sala, cargar_general, cargar_todo,
                              PartidaGuardada, SalaGuardada, ErrorFormato)

RUTA = "prueba_partida.bin"


def armar_partida(n):
    p = PartidaGuardada(1250, 42, 27, 3)
    p.inventario = ["itm_daga", "itm_llave_negra"]
    for i in range(n):
        id_sala = (i * 37) % n + 1
        s = SalaGuardada(id_sala, rastro=i)
        if i % 3 == 0:
            s.enemigos.append(["e-" + str(i), "ent_rata_gigante", 12, 300 + i])
        if i % 2 == 0:
            s.objetos.append("itm_antorcha")
        s.puertas.append(["N", i % 2])
        s.puertas.append(["E", 1])
        p.salas.append(s)
    return p


def igual(a, b):
    return (a.id == b.id and a.rastro == b.rastro and a.enemigos == b.enemigos
            and a.objetos == b.objetos and a.puertas == b.puertas)


p = armar_partida(101)
guardar(RUTA, p)

g = cargar_general(RUTA)
assert g.reloj == 1250 and g.semilla == 42 and g.vida == 27 and g.sala_actual == 3
assert g.inventario == ["itm_daga", "itm_llave_negra"]
assert g.salas == []
print("general OK")

for s in p.salas:
    assert igual(leer_sala(RUTA, s.id), s)
assert leer_sala(RUTA, 99999) is None
assert leer_sala(RUTA, 0) is None
print("leer una sala OK")

t = cargar_todo(RUTA)
assert len(t.salas) == 101
for s in t.salas:
    original = None
    for x in p.salas:
        if x.id == s.id:
            original = x
    assert igual(s, original)
print("carga completa OK")

# partida sin salas y con textos con tildes
v = PartidaGuardada(0, 1, 10, 1)
v.inventario = ["poción ñ"]
guardar(RUTA, v)
assert cargar_general(RUTA).inventario == ["poción ñ"]
assert leer_sala(RUTA, 1) is None
print("partida vacía OK")

# versión de formato distinta
guardar(RUTA, p)
with open(RUTA, "r+b") as f:
    f.seek(4)
    f.write(bytes([99, 0]))
try:
    leer_sala(RUTA, 1)
    assert False, "debió fallar"
except ErrorFormato:
    pass
print("versión incompatible OK")

# archivo que no es una partida
with open(RUTA, "wb") as f:
    f.write(b"hola esto no es una partida de cripta")
try:
    cargar_general(RUTA)
    assert False, "debió fallar"
except ErrorFormato:
    pass
print("marca incorrecta OK")

os.remove(RUTA)