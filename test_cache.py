from cache import Cache

c = Cache(tope=3)
c.poner("a", 1)
c.poner("b", 2)
c.poner("c", 3)
assert c.obtener("a") == 1      
assert c.poner("d", 4) == "b"       
assert c.contiene("b") is False
assert c.contiene("a") is True
assert c.cantidad() == 3
print("LRU OK")

c = Cache(tope=3, usar_lru=False)
c.poner("a", 1)
c.poner("b", 2)
c.poner("c", 3)
c.obtener("a")
assert c.poner("d", 4) == "a"
print("FIFO OK")

usadas = ["b"]
def en_uso(id_ficha):
    return id_ficha in usadas

c = Cache(tope=3, en_uso=en_uso)
c.poner("a", 1)
c.poner("b", 2)
c.poner("c", 3)
c.obtener("a")                      
assert c.poner("d", 4) == "c"       
assert c.contiene("b") is True
print("en uso OK")

usadas = ["a", "b", "c"]
c = Cache(tope=3, en_uso=en_uso)
c.poner("a", 1)
c.poner("b", 2)
c.poner("c", 3)
assert c.poner("d", 4) is None
assert c.cantidad() == 4
print("todas en uso OK")

c = Cache(tope=3)
c.poner("a", 1)
c.obtener("a")
c.obtener("a")
c.obtener("zzz")
assert c.aciertos == 2
assert c.fallos == 1
print("contadores OK")

c = Cache(tope=3)
c.poner("a", 1)
c.poner("a", 99)
assert c.cantidad() == 1
assert c.obtener("a") == 99
print("actualizar OK")

c = Cache(tope=25)
for i in range(1000):
    c.poner("id_" + str(i), i)
    assert c.cantidad() <= 25
n = 0
nodo = c.primero
while nodo is not None:
    n += 1
    nodo = nodo.siguiente
assert n == c.cantidad()
print("enlaces OK")