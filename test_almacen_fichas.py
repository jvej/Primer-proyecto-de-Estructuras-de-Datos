import os
from almacen_fichas import AlmacenFichas

RUTA = "prueba_catalogo.dat"


def borrar():
    if os.path.exists(RUTA):
        os.remove(RUTA)


borrar()

a = AlmacenFichas(RUTA, "cat-1")
rata = {"id": "ent_rata_gigante", "nombre": "Rata gigante", "vida_max": 12}
daga = {"id": "itm_daga_oxidada", "nombre": "Daga oxidada", "ataque_bonus": 3}
a.guardar("ent_rata_gigante", rata)
a.guardar("itm_daga_oxidada", daga)
assert a.leer("ent_rata_gigante") == rata
assert a.leer("itm_daga_oxidada") == daga
assert a.leer("no_existe") is None
assert a.cantidad() == 2
print("guardar y leer OK")

b = AlmacenFichas(RUTA, "cat-1")
assert b.se_descarto is False
assert b.cantidad() == 2
assert b.leer("ent_rata_gigante") == rata
assert b.contiene("itm_daga_oxidada") is True
print("persistencia OK")

b.guardar("itm_poción", {"nombre": "Poción de curación ñ"})
c = AlmacenFichas(RUTA, "cat-1")
assert c.leer("itm_poción") == {"nombre": "Poción de curación ñ"}
print("texto con tildes OK")

c.guardar("ent_rata_gigante", {"nombre": "Rata nueva"})
assert c.leer("ent_rata_gigante") == {"nombre": "Rata nueva"}
d = AlmacenFichas(RUTA, "cat-1")
assert d.leer("ent_rata_gigante") == {"nombre": "Rata nueva"}
assert d.cantidad() == 3
print("actualizar OK")

e = AlmacenFichas(RUTA, "cat-2")
assert e.se_descarto is True
assert e.cantidad() == 0
assert e.leer("ent_rata_gigante") is None
f = AlmacenFichas(RUTA, "cat-2")
assert f.se_descarto is False
assert f.cantidad() == 0
print("versión distinta OK")

f.guardar("a", {"x": 1})
f.guardar("b", {"x": 2})
tamano = os.path.getsize(RUTA)
with open(RUTA, "r+b") as arch:
    arch.truncate(tamano - 3)
g = AlmacenFichas(RUTA, "cat-2")
assert g.leer("a") == {"x": 1}
assert g.leer("b") is None
print("archivo cortado OK")

# muchas fichas
borrar()
h = AlmacenFichas(RUTA, "cat-3")
for i in range(500):
    h.guardar("id_" + str(i), {"n": i})
k = AlmacenFichas(RUTA, "cat-3")
assert k.cantidad() == 500
for i in range(0, 500, 7):
    assert k.leer("id_" + str(i)) == {"n": i}
print("muchas fichas OK")

borrar()