import struct
from ordenamiento import ordenar

MARCA = b"CRPT"
VERSION_FORMATO = 3      # 2: cripta, versiones, jugador y órdenes; 3: + solicitudes de red gastadas
ENCABEZADO = "<4sHIQI"   
ENTRADA = "<IQI"          
TAM_ENCABEZADO = struct.calcsize(ENCABEZADO)
TAM_ENTRADA = struct.calcsize(ENTRADA)


class ErrorFormato(Exception):
    pass

class SalaGuardada:
    def __init__(self, id_sala, rastro=-1):
        self.id = id_sala
        self.rastro = rastro
        self.enemigos = []     
        self.objetos = []     
        self.puertas = []      

class PartidaGuardada:
    def __init__(self, reloj, semilla, vida, sala_actual, id_cripta="", version_cripta="",
                 version_catalogo="", nombre=""):
        self.reloj = reloj
        self.semilla = semilla
        self.vida = vida
        self.sala_actual = sala_actual
        self.inventario = []
        self.salas = []
        # Para reconstruir la partida exacta (agenda incluida) re-simulando (ver persistencia_partida.py)
        self.id_cripta = id_cripta
        self.version_cripta = version_cripta
        self.version_catalogo = version_catalogo
        self.nombre = nombre
        self.ordenes = []     # órdenes de partida en texto ("mover N", "recoger 0", ...)
        self.solicitudes = 0  # solicitudes de red ya gastadas por esta partida (§5.1)


def _texto(s):
    datos = s.encode("utf-8")
    return struct.pack("<H", len(datos)) + datos


def _leer_texto(datos, pos):
    largo = struct.unpack_from("<H", datos, pos)[0]
    pos += 2
    texto = datos[pos:pos + largo].decode("utf-8")
    return texto, pos + largo


def _empaquetar_sala(sala):
    b = struct.pack("<iiH", sala.id, sala.rastro, len(sala.enemigos))
    for e in sala.enemigos:
        b += _texto(e[0]) + _texto(e[1]) + struct.pack("<ii", e[2], e[3])
    b += struct.pack("<H", len(sala.objetos))
    for o in sala.objetos:
        b += _texto(o)
    b += struct.pack("<B", len(sala.puertas))
    for p in sala.puertas:
        b += struct.pack("<cB", p[0].encode(), p[1])
    return b


def _desempaquetar_sala(datos):
    id_sala, rastro, n_enemigos = struct.unpack_from("<iiH", datos, 0)
    pos = struct.calcsize("<iiH")
    sala = SalaGuardada(id_sala, rastro)
    for i in range(n_enemigos):
        instancia, pos = _leer_texto(datos, pos)
        tipo, pos = _leer_texto(datos, pos)
        vida, tiempo = struct.unpack_from("<ii", datos, pos)
        pos += 8
        sala.enemigos.append([instancia, tipo, vida, tiempo])
    n_objetos = struct.unpack_from("<H", datos, pos)[0]
    pos += 2
    for i in range(n_objetos):
        objeto, pos = _leer_texto(datos, pos)
        sala.objetos.append(objeto)
    n_puertas = struct.unpack_from("<B", datos, pos)[0]
    pos += 1
    for i in range(n_puertas):
        direccion, abierta = struct.unpack_from("<cB", datos, pos)
        pos += 2
        sala.puertas.append([direccion.decode(), abierta])
    return sala


def _empaquetar_general(partida):
    b = struct.pack("<qqii", partida.reloj, partida.semilla, partida.vida, partida.sala_actual)
    b += struct.pack("<H", len(partida.inventario))
    for o in partida.inventario:
        b += _texto(o)
    b += _texto(partida.id_cripta) + _texto(partida.version_cripta)
    b += _texto(partida.version_catalogo) + _texto(partida.nombre)
    b += struct.pack("<I", len(partida.ordenes))
    for orden in partida.ordenes:
        b += _texto(orden)
    b += struct.pack("<I", partida.solicitudes)
    return b


def _desempaquetar_general(datos):
    reloj, semilla, vida, sala_actual = struct.unpack_from("<qqii", datos, 0)
    partida = PartidaGuardada(reloj, semilla, vida, sala_actual)
    pos = struct.calcsize("<qqii")
    n = struct.unpack_from("<H", datos, pos)[0]
    pos += 2
    for i in range(n):
        objeto, pos = _leer_texto(datos, pos)
        partida.inventario.append(objeto)
    partida.id_cripta, pos = _leer_texto(datos, pos)
    partida.version_cripta, pos = _leer_texto(datos, pos)
    partida.version_catalogo, pos = _leer_texto(datos, pos)
    partida.nombre, pos = _leer_texto(datos, pos)
    n_ordenes = struct.unpack_from("<I", datos, pos)[0]
    pos += 4
    for i in range(n_ordenes):
        orden, pos = _leer_texto(datos, pos)
        partida.ordenes.append(orden)
    partida.solicitudes = struct.unpack_from("<I", datos, pos)[0]
    return partida


def guardar(ruta, partida):
    salas = ordenar(partida.salas, clave=lambda s: s.id)  
    bloques = []
    for s in salas:
        bloques.append(_empaquetar_sala(s))
    general = _empaquetar_general(partida)

    pos = TAM_ENCABEZADO + len(salas) * TAM_ENTRADA
    indice = b""
    for i in range(len(salas)):
        indice += struct.pack(ENTRADA, salas[i].id, pos, len(bloques[i]))
        pos += len(bloques[i])
    pos_general = pos

    with open(ruta, "wb") as f:
        f.write(struct.pack(ENCABEZADO, MARCA, VERSION_FORMATO, len(salas), pos_general, len(general)))
        f.write(indice)
        for b in bloques:
            f.write(b)
        f.write(general)

def _leer_encabezado(f):
    datos = f.read(TAM_ENCABEZADO)
    if len(datos) < TAM_ENCABEZADO:
        raise ErrorFormato("archivo incompleto")
    marca, version, n_salas, pos_general, largo_general = struct.unpack(ENCABEZADO, datos)
    if marca != MARCA:
        raise ErrorFormato("no es un archivo de partida")
    if version != VERSION_FORMATO:
        raise ErrorFormato("versión de formato " + str(version) + " incompatible (se esperaba " + str(VERSION_FORMATO) + ")")
    return n_salas, pos_general, largo_general


def cargar_general(ruta):
    """Devuelve una PartidaGuardada con los datos generales y SIN salas."""
    with open(ruta, "rb") as f:
        n_salas, pos_general, largo_general = _leer_encabezado(f)
        f.seek(pos_general)
        return _desempaquetar_general(f.read(largo_general))


def leer_sala(ruta, id_sala):
    """Busca la sala en el índice (búsqueda binaria con seek). None si no existe."""
    with open(ruta, "rb") as f:
        n_salas, pos_general, largo_general = _leer_encabezado(f)
        bajo = 0
        alto = n_salas - 1
        while bajo <= alto:
            medio = (bajo + alto) // 2
            f.seek(TAM_ENCABEZADO + medio * TAM_ENTRADA)
            id_medio, pos, largo = struct.unpack(ENTRADA, f.read(TAM_ENTRADA))
            if id_medio == id_sala:
                f.seek(pos)
                return _desempaquetar_sala(f.read(largo))
            if id_medio < id_sala:
                bajo = medio + 1
            else:
                alto = medio - 1
    return None


def cargar_todo(ruta):
    with open(ruta, "rb") as f:
        n_salas, pos_general, largo_general = _leer_encabezado(f)
        entradas = []
        for i in range(n_salas):
            entradas.append(struct.unpack(ENTRADA, f.read(TAM_ENTRADA)))
        bloques = []
        for e in entradas:
            f.seek(e[1])
            bloques.append(f.read(e[2]))
        f.seek(pos_general)
        partida = _desempaquetar_general(f.read(largo_general))
    for b in bloques:
        partida.salas.append(_desempaquetar_sala(b))
    return partida