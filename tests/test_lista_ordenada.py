from modelo.estructuras.lista_ordenada import ListaOrdenada

t = ListaOrdenada()
assert t.cantidad() == 0
assert t.buscar("nada") is None
assert t.contiene("nada") is False
assert t.eliminar("nada") is False

t.insertar("ent_rata_gigante", "ficha rata")
t.insertar("itm_antorcha", "ficha antorcha")
assert t.buscar("ent_rata_gigante") == "ficha rata"
assert t.cantidad() == 2

t.insertar("itm_antorcha", "otra ficha")
assert t.buscar("itm_antorcha") == "otra ficha"
assert t.cantidad() == 2

assert t.eliminar("itm_antorcha") is True
assert t.buscar("itm_antorcha") is None
assert t.cantidad() == 1

t = ListaOrdenada()
for i in range(2000):
    t.insertar("itm_" + str((i * 37) % 2000), i)
assert t.cantidad() == 2000
assert t.buscar("itm_2000") is None
claves = t.claves()
for i in range(len(claves) - 1):
    assert claves[i] < claves[i + 1]
print("insertar y buscar OK")

for i in range(0, 2000, 2):
    assert t.eliminar("itm_" + str(i)) is True
assert t.cantidad() == 1000
for i in range(2000):
    assert t.contiene("itm_" + str(i)) == (i % 2 == 1)
print("eliminar OK")

t = ListaOrdenada()
t.insertar("b", 1)
t.insertar_muchos([["z", 1], ["a", 2], ["b", 3], ["a", 9]])
assert t.claves() == ["a", "b", "z"]
assert t.buscar("a") == 9
assert t.buscar("b") == 3
print("insertar muchos OK")