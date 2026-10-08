import os
from almacen_cripta import AlmacenCripta

RUTA = "prueba_cripta.dat"

def borrar():
    if os.path.exists(RUTA):
        os.remove(RUTA)
borrar()

a = AlmacenCripta(RUTA, "v1")
assert a.tiene_generales() is False
assert a.tiene_pagina(1) is False
assert a.tiene_sala(1) is False
assert a.leer_sala(1) is None
print("vacío OK")

general = {"id": "cripta-01", "version": "v1", "salas_total": 20, "paginas": 1}
pagina = {"pagina": 1, "total_paginas": 1, "salas": [{"id": 1, "salidas": {}}]}
sala_con_cosas = {"sala": 2, "enemigos": [{"instancia": "e-201", "tipo": "ent_rata"}],
                  "objetos": ["itm_daga"], "trampas": []}
sala_vacia = {"sala": 3, "enemigos": [], "objetos": [], "trampas": []}

a.guardar_generales(general)
a.guardar_pagina(1, pagina)
a.guardar_sala(2, sala_con_cosas)
a.guardar_sala(3, sala_vacia)
assert a.leer_generales() == general
assert a.leer_pagina(1) == pagina
assert a.leer_sala(2) == sala_con_cosas
print("guardar y leer OK")

assert a.tiene_sala(3) is True
assert a.leer_sala(3) == sala_vacia
print("sala vacía OK")

b = AlmacenCripta(RUTA, "v1")
assert b.se_descarto() is False
assert b.leer_generales() == general
assert b.leer_sala(2) == sala_con_cosas
print("persistencia OK")

assert b.salas_faltantes([1, 2, 3, 4, 5]) == [1, 4, 5]
assert b.salas_faltantes([2, 3]) == []
print("salas faltantes OK")

c = AlmacenCripta(RUTA, "v2")
assert c.se_descarto() is True
assert c.tiene_generales() is False
assert c.tiene_sala(2) is False
print("versión distinta OK")

RUTA2 = "prueba_cripta_2.dat"
if os.path.exists(RUTA2):
    os.remove(RUTA2)
x = AlmacenCripta(RUTA, "v2")
y = AlmacenCripta(RUTA2, "w1")
x.guardar_sala(1, {"sala": 1, "enemigos": []})
assert y.tiene_sala(1) is False
print("criptas separadas OK")

borrar()
os.remove(RUTA2)