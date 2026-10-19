import random

from modelo.juego.inventario import (Inventario, InventarioLleno, ObjetoNoEstaEnInventario)
from modelo.estructuras.lista_doble import ListaDoble
from modelo.estructuras.ordenamiento import ordenar

PERGAMINO = "pergamino_retroceso"


class Obj:
    def __init__(self, nombre, clase="llave", peso=1, valor=1):
        self.nombre = nombre
        self.clase = clase
        self.peso = peso
        self.valor = valor

    def es_pergamino(self):
        return self.clase == PERGAMINO

    def __repr__(self):
        return "Obj(%s)" % self.nombre


def nombres(inv):
    return [o.nombre for o in inv.objetos()]


def inventario_con(*objetos, capacidad=10):
    inv = Inventario(capacidad, ordenador=ordenar)
    for o in objetos:
        inv.agregar(o)
    return inv


def equipar(inv, objeto):
    posicion = inv.quitar(objeto)
    inv.agregar_al_frente(objeto)

    def deshacer():
        inv.quitar(objeto)
        inv.restaurar(objeto, posicion)
    return deshacer

def test_lista_basica():
    lista = ListaDoble()
    assert len(lista) == 0 and lista.primero() is None and lista.ultimo() is None
    a = lista.agregar_al_final("a")
    b = lista.agregar_al_final("b")
    c = lista.agregar_al_frente("c")
    assert list(lista) == ["c", "a", "b"]
    assert lista.anterior_de(c) is None and lista.siguiente_de(b) is None
    assert lista.siguiente_de(c) is a and lista.anterior_de(b) is a
    assert lista.primero() is c and lista.ultimo() is b


def test_lista_quitar_y_reinsertar_en_su_sitio():
    lista = ListaDoble()
    a = lista.agregar_al_final("a")
    b = lista.agregar_al_final("b")
    c = lista.agregar_al_final("c")
    anterior = lista.anterior_de(b)
    lista.quitar(b)
    assert list(lista) == ["a", "c"] and len(lista) == 2
    lista.reinsertar(b, anterior)
    assert list(lista) == ["a", "b", "c"]
    lista.quitar(a)
    lista.reinsertar(a, None)              
    assert list(lista) == ["a", "b", "c"]
    lista.quitar(c)
    lista.reinsertar(c, b)                  
    assert list(lista) == ["a", "b", "c"]


def test_lista_claves_frente_y_final():
    lista = ListaDoble()
    a = lista.agregar_al_final("a")
    b = lista.agregar_al_final("b")
    z = lista.agregar_al_frente("z")
    y = lista.agregar_al_frente("y")
    assert list(lista) == ["y", "z", "a", "b"]
    assert y.clave < z.clave < a.clave < b.clave
    lista.quitar(z)
    lista.reinsertar(z, y)
    assert list(lista) == ["y", "z", "a", "b"]


def test_lista_reinsertar_cuando_el_vecino_fue_quitado():
    lista = ListaDoble()
    a = lista.agregar_al_final("a")
    b = lista.agregar_al_final("b")
    c = lista.agregar_al_final("c")
    lista.quitar(c)               
    lista.quitar(b)             
    lista.reinsertar(c, b)                  
    assert list(lista) == ["a", "c"]
    lista2 = ListaDoble()
    x = lista2.agregar_al_final("x")
    y = lista2.agregar_al_final("y")
    lista2.quitar(y)
    lista2.quitar(x)
    lista2.reinsertar(y, x)               
    assert list(lista2) == ["y"]


def test_lista_errores():
    lista = ListaDoble()
    a = lista.agregar_al_final("a")
    for operacion in (lambda: lista.reinsertar(a, None),
                      lambda: lista.siguiente_de(None)):
        try:
            operacion()
            assert False
        except ValueError:
            pass
    lista.quitar(a)
    try:
        lista.quitar(a)
        assert False
    except ValueError:
        pass

def test_capacidad_y_lleno():
    inv = inventario_con(Obj("a"), Obj("b"), capacidad=2)
    assert inv.lleno() and len(inv) == 2
    for operacion in (lambda: inv.agregar(Obj("c")), lambda: inv.agregar_al_frente(Obj("c"))):
        try:
            operacion()
            assert False
        except InventarioLleno:
            pass
    assert nombres(inv) == ["a", "b"]         
    inv.quitar(inv.objeto_actual())
    assert not inv.lleno()
    inv.agregar(Obj("c"))
    assert nombres(inv) == ["b", "c"]


def test_objetos_devuelve_copia():
    inv = inventario_con(Obj("a"), Obj("b"))
    copia = inv.objetos()
    copia.clear()
    assert nombres(inv) == ["a", "b"]


def test_recorrer_adelante_y_atras():
    inv = inventario_con(Obj("a"), Obj("b"), Obj("c"))
    assert inv.objeto_actual().nombre == "a" and not inv.anterior()
    assert inv.siguiente() and inv.objeto_actual().nombre == "b"
    assert inv.siguiente() and inv.objeto_actual().nombre == "c"
    assert not inv.siguiente() and inv.objeto_actual().nombre == "c"
    assert inv.anterior() and inv.objeto_actual().nombre == "b"
    inv.ir_al_inicio()
    assert inv.objeto_actual().nombre == "a"


def test_inventario_vacio():
    inv = inventario_con()
    assert inv.esta_vacio() and inv.objeto_actual() is None
    assert not inv.siguiente() and not inv.anterior()
    try:
        inv.quitar(Obj("x"))
        assert False
    except ObjetoNoEstaEnInventario:
        pass


def test_soltar_el_objeto_que_se_ve_en_cualquier_posicion():
    inv = inventario_con(Obj("a"), Obj("b"), Obj("c"))
    inv.siguiente()                             
    inv.quitar(inv.objeto_actual())
    assert nombres(inv) == ["a", "c"] and inv.objeto_actual().nombre == "c"
    inv.siguiente()                               
    inv.quitar(inv.objeto_actual())
    assert nombres(inv) == ["a"] and inv.objeto_actual().nombre == "a"
    inv.quitar(inv.objeto_actual())              
    assert inv.esta_vacio() and inv.objeto_actual() is None
    inv.agregar(Obj("z"))
    assert inv.objeto_actual().nombre == "z"


def test_quitar_un_objeto_que_no_es_el_actual_y_uno_ajeno():
    a, b, c = Obj("a"), Obj("b"), Obj("c")
    inv = inventario_con(a, b, c)
    inv.quitar(c)
    assert nombres(inv) == ["a", "b"] and inv.objeto_actual() is a
    assert inv.contiene(b) and not inv.contiene(c)
    try:
        inv.quitar(c)
        assert False
    except ObjetoNoEstaEnInventario:
        pass


def test_quitar_y_restaurar_en_cada_posicion():
    for indice in range(4):
        objetos = [Obj("a"), Obj("b"), Obj("c"), Obj("d")]
        inv = inventario_con(*objetos)
        posicion = inv.quitar(objetos[indice])
        assert len(inv) == 3
        inv.restaurar(objetos[indice], posicion)
        assert nombres(inv) == ["a", "b", "c", "d"], indice
        assert inv.objeto_actual() is objetos[indice]


def test_equipar_mueve_al_frente_y_se_deshace():
    llave, daga, pocion = Obj("llave"), Obj("daga", "arma"), Obj("pocion", "pocion")
    inv = inventario_con(llave, daga, pocion)
    deshacer = equipar(inv, daga)
    assert nombres(inv) == ["daga", "llave", "pocion"]
    assert inv.objeto_actual() is daga       
    deshacer()
    assert nombres(inv) == ["llave", "daga", "pocion"]


def test_pergamino_antes_del_objeto_equipado():
    perg, daga, cota = Obj("perg", PERGAMINO), Obj("daga", "arma"), Obj("cota", "armadura")
    inv = inventario_con(perg, daga, cota)
    deshacer = equipar(inv, daga)
    assert nombres(inv) == ["daga", "perg", "cota"]
    inv.quitar(perg)                         
    deshacer()
    assert nombres(inv) == ["daga", "cota"]


def test_pergamino_antes_del_objeto_soltado():
    perg, a, b = Obj("perg", PERGAMINO), Obj("a"), Obj("b")
    inv = inventario_con(perg, a, b)
    posicion = inv.quitar(a)                 
    inv.quitar(perg)                           
    inv.restaurar(a, posicion)               
    assert nombres(inv) == ["a", "b"]


def test_dos_acciones_seguidas_con_dos_pergaminos():
    o0, o1, o3 = Obj("o0"), Obj("o1", "arma"), Obj("o3")
    s, s2 = Obj("s", PERGAMINO), Obj("s2", PERGAMINO)
    inv = inventario_con(o0, o1, s, o3, s2)
    pos_o3 = inv.quitar(o3)                   
    deshacer_equipar = equipar(inv, o1)           
    assert nombres(inv) == ["o1", "o0", "s", "s2"]
    inv.quitar(s)                                 
    deshacer_equipar()                        
    inv.quitar(s2)                            
    inv.restaurar(o3, pos_o3)              
    assert nombres(inv) == ["o0", "o1", "o3"]


def test_restaurar_con_posicion_de_otro_objeto_falla():
    a, b = Obj("a"), Obj("b")
    inv = inventario_con(a, b)
    posicion = inv.quitar(a)
    try:
        inv.restaurar(b, posicion)
        assert False
    except ValueError:
        pass


def test_vista_ordenada_no_altera_el_orden_real():
    inv = inventario_con(Obj("Zeta", peso=5, valor=10), Obj("alfa", peso=1, valor=30),
                         Obj("Mu", peso=3, valor=20))
    real = nombres(inv)
    assert [o.nombre for o in inv.vista_ordenada("peso")] == ["alfa", "Mu", "Zeta"]
    assert [o.nombre for o in inv.vista_ordenada("valor", descendente=True)] == ["alfa", "Mu", "Zeta"]
    assert [o.nombre for o in inv.vista_ordenada("nombre")] == ["alfa", "Mu", "Zeta"]
    assert nombres(inv) == real


def test_vista_ordenada_estable_en_empates():
    inv = inventario_con(Obj("a", peso=2), Obj("b", peso=1), Obj("c", peso=2), Obj("d", peso=1))
    assert [o.nombre for o in inv.vista_ordenada("peso")] == ["b", "d", "a", "c"]


def test_vista_ordenada_errores():
    inv = inventario_con(Obj("a"))
    for operacion in (lambda: inv.vista_ordenada("color"),
                      lambda: Inventario(5).vista_ordenada("peso")):
        try:
            operacion()
            assert False
        except ValueError:
            pass


def test_objeto_en_e_indice_de():
    a, b, c = Obj("a"), Obj("b"), Obj("c")
    inv = inventario_con(a, b, c)
    for i, esperado in enumerate([a, b, c]):
        assert inv.objeto_en(i) is esperado and inv.indice_de(esperado) == i
    equipar(inv, c)                              
    assert inv.objeto_en(0) is c and inv.indice_de(a) == 1
    for malo in (-1, 3):
        try:
            inv.objeto_en(malo)
            assert False
        except IndexError:
            pass
    try:
        inv.indice_de(Obj("x"))
        assert False
    except ObjetoNoEstaEnInventario:
        pass


def test_contar_clase():
    inv = inventario_con(Obj("p1", PERGAMINO), Obj("llave"), Obj("p2", PERGAMINO))
    assert inv.contar_clase(PERGAMINO) == 2 and inv.contar_clase("arma") == 0

def test_aleatoria_deshacer_intervalos_consumiendo_pergaminos():
    """Imita a Partida: hasta 5 acciones (soltar / recoger / equipar) sobre objetos que
    no son pergaminos (o recoger un pergamino, que no se registra); luego, por cada
    deshacer, se consume un pergamino SIN registrar. Al final el orden debe ser el
    original sin los pergaminos consumidos, y los pergaminos recogidos, al final."""
    azar = random.Random(2026)
    for _ in range(500):
        inv = Inventario(12, ordenador=ordenar)
        todos = []
        for i in range(azar.randint(2, 9)):
            clase = PERGAMINO if azar.random() < 0.4 else azar.choice(["arma", "armadura", "llave"])
            objeto = Obj("o%d" % i, clase)
            todos.append(objeto)
            inv.agregar(objeto)
        original = list(todos)
        recogidos = []
        intervalos = []
        for _paso in range(azar.randint(1, 5)):
            inversos = []
            normales = [o for o in inv.objetos() if not o.es_pergamino()]
            accion = azar.randint(0, 3)
            if accion == 3 and not inv.lleno():
                perg_nuevo = Obj("p%d" % len(todos) + "r", PERGAMINO)
                todos.append(perg_nuevo)
                recogidos.append(perg_nuevo)
                inv.agregar(perg_nuevo)             
            elif accion == 0 and normales:
                objeto = azar.choice(normales)
                posicion = inv.quitar(objeto)
                inversos.append(lambda o=objeto, p=posicion: inv.restaurar(o, p))
            elif accion == 1 and not inv.lleno():
                nuevo = Obj("n%d" % len(todos), "llave")
                inv.agregar(nuevo)
                inversos.append(lambda o=nuevo: inv.quitar(o))
            elif accion == 2 and normales:
                inversos.append(equipar(inv, azar.choice(normales)))
            intervalos.append(inversos)
        consumidos = []
        while intervalos:
            for p in inv.objetos():
                if p.es_pergamino():
                    inv.quitar(p)              
                    consumidos.append(p)
                    break
            for deshacer in reversed(intervalos.pop()):
                deshacer()
        esperado = [o for o in original if o not in consumidos]
        esperado += [o for o in recogidos if o not in consumidos]  
        restantes = [o for o in inv.objetos()]
        assert restantes == esperado, (restantes, esperado)


if __name__ == "__main__":
    pruebas = [(n, f) for n, f in sorted(globals().items())
               if n.startswith("test_") and callable(f)]
    for nombre, funcion in pruebas:
        funcion()
        print("ok  ", nombre)
    print("\n%d pruebas correctas" % len(pruebas))