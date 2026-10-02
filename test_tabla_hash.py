from tabla_hash import TablaHash

t = TablaHash()

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

t = TablaHash()
referencia = []
for i in range(2000):
    t.insertar("itm_" + str(i), i)
    referencia.append(i)
assert t.cantidad() == 2000
for i in range(2000):
    assert t.buscar("itm_" + str(i)) == i
assert t.buscar("itm_2000") is None
print("insertar y buscar OK")

for i in range(0, 2000, 2):
    assert t.eliminar("itm_" + str(i)) is True
assert t.cantidad() == 1000
for i in range(2000):
    if i % 2 == 0:
        assert t.buscar("itm_" + str(i)) is None
    else:
        assert t.buscar("itm_" + str(i)) == i
print("eliminar OK")

assert len(t.claves()) == 1000
print("claves OK")