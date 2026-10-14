import os
from almacen_fichas import AlmacenFichas
from almacen_local_cache import AlmacenLocalCache

RUTA = "prueba_local.dat"
if os.path.exists(RUTA):
    os.remove(RUTA)

disco = AlmacenFichas(RUTA, "v1")
a = AlmacenLocalCache(25, disco)

for i in range(30):
    a.guardar("id_" + str(i), {"n": i})
assert a.cache.cantidad() == 25
assert a.cache.contiene("id_0") is False
assert a.disponible("id_0") is True      
print("liberadas siguen en disco OK")

assert a.obtener("id_0") == {"n": 0}
assert disco.lecturas == 1
assert a.obtener("id_0") == {"n": 0}      
assert disco.lecturas == 1
print("recuperar de disco OK")
assert a.obtener("no_existe") is None
assert a.disponible("no_existe") is False
print("ficha inexistente OK")

os.remove(RUTA)