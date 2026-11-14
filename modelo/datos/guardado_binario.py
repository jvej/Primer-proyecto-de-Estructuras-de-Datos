import struct
from functools import wraps
from modelo.estructuras.ordenamiento import ordenar

MARCA = b"CRPT"
VERSION_FORMATO = 4
ENCABEZADO = "<4sHIQI"   
ENTRADA = "<IQI"          
TAM_ENCABEZADO = struct.calcsize(ENCABEZADO)
TAM_ENTRADA = struct.calcsize(ENTRADA)


class ErrorFormato(Exception):
    pass


def _validar_binario(funcion):
    @wraps(funcion)
    def ejecutar(*args, **kwargs):
        try:
            return funcion(*args, **kwargs)
        except (struct.error, UnicodeError, ValueError, TypeError, OverflowError) as error:
            raise ErrorFormato("datos binarios inválidos: %s" % error) from error
    return ejecutar

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
        self.id_cripta = id_cripta
        self.version_cripta = version_cripta
        self.version_catalogo = version_catalogo
        self.nombre = nombre
        self.ordenes = []  
        self.solicitudes = 0  
        # Ausencia explícita: nunca deducir el mapa de self.salas.
        self.n_salas_conocidas = None
        self.estados_salas = None
        self.memoria_puertas = None


@_validar_binario
def _texto(s):
    datos = s.encode("utf-8")
    return struct.pack("<H", len(datos)) + datos


@_validar_binario
def _leer_texto(datos, pos):
    largo = struct.unpack_from("<H", datos, pos)[0]
    pos += 2
    if pos + largo > len(datos):
        raise ErrorFormato("texto truncado")
    texto = datos[pos:pos + largo].decode("utf-8")
    return texto, pos + largo


@_validar_binario
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


@_validar_binario
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
    if pos != len(datos):
        raise ErrorFormato("datos sobrantes en bloque de sala")
    return sala


def _conocimiento_binario(partida):
    n = partida.n_salas_conocidas
    if type(n) is not int or not 0 <= n <= 65535:
        raise ErrorFormato("N ausente o fuera de uint16")
    estados = partida.estados_salas
    memoria = partida.memoria_puertas
    if estados is None or memoria is None:
        raise ErrorFormato("conocimiento ausente para guardado v4")
    if len(estados) != n or len(memoria) != 4 * n:
        raise ErrorFormato("longitudes de conocimiento incompatibles con N")
    for estado in estados:
        if type(estado) is not int or estado not in (0, 1, 2):
            raise ErrorFormato("estado de sala inválido")
    entradas = bytearray()
    p = 0
    for posicion, estado in enumerate(memoria):
        if type(estado) is not int or estado not in (0, 1, 2):
            raise ErrorFormato("estado de puerta inválido")
        if estado:
            p += 1
            if p > 65535:
                raise ErrorFormato("P fuera de uint16")
            entradas.extend(struct.pack("<HBB", posicion // 4, posicion % 4, estado))
    return struct.pack("<H", n) + bytes(estados) + struct.pack("<H", p) + entradas


@_validar_binario
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
    b += _conocimiento_binario(partida)
    return b


@_validar_binario
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
    pos += 4
    n = struct.unpack_from("<H", datos, pos)[0]
    pos += 2
    if pos + n + 2 > len(datos):
        raise ErrorFormato("estados de conocimiento truncados")
    estados = list(datos[pos:pos + n])
    pos += n
    if any(estado not in (0, 1, 2) for estado in estados):
        raise ErrorFormato("estado de sala inválido")
    p = struct.unpack_from("<H", datos, pos)[0]
    pos += 2
    if len(datos) != pos + p * 4:
        raise ErrorFormato("longitud de memoria inválida: datos truncados o sobrantes")
    memoria = [0] * (4 * n)
    for _ in range(p):
        indice, direccion, estado = struct.unpack_from("<HBB", datos, pos)
        pos += 4
        if indice >= n or direccion >= 4 or estado not in (1, 2):
            raise ErrorFormato("entrada de puerta inválida")
        posicion = indice * 4 + direccion
        if memoria[posicion] != 0:
            raise ErrorFormato("entrada de memoria duplicada")
        memoria[posicion] = estado
    partida.n_salas_conocidas = n
    partida.estados_salas = estados
    partida.memoria_puertas = memoria
    return partida


@_validar_binario
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
        if version == 3:
            raise ErrorFormato("versión de formato 3 incompatible (se esperaba 4): formato previo sin soporte de niebla de guerra")
        raise ErrorFormato("versión de formato " + str(version) + " incompatible (se esperaba " + str(VERSION_FORMATO) + ")")
    f.seek(0, 2)
    largo_archivo = f.tell()
    fin_indice = TAM_ENCABEZADO + n_salas * TAM_ENTRADA
    if pos_general < fin_indice or pos_general + largo_general != largo_archivo:
        raise ErrorFormato("offsets o longitudes de archivo inválidos")
    f.seek(TAM_ENCABEZADO)
    return n_salas, pos_general, largo_general


def _leer_exacto(f, largo):
    datos = f.read(largo)
    if len(datos) != largo:
        raise ErrorFormato("archivo truncado")
    return datos


def _validar_entrada(pos, largo, n_salas, pos_general):
    if pos < TAM_ENCABEZADO + n_salas * TAM_ENTRADA or largo == 0 or pos + largo > pos_general:
        raise ErrorFormato("offset o longitud de sala inválidos")


@_validar_binario
def cargar_general(ruta):
    """Devuelve una PartidaGuardada con los datos generales y SIN salas."""
    with open(ruta, "rb") as f:
        n_salas, pos_general, largo_general = _leer_encabezado(f)
        f.seek(pos_general)
        return _desempaquetar_general(_leer_exacto(f, largo_general))


@_validar_binario
def leer_sala(ruta, id_sala):
    """Busca la sala en el índice (búsqueda binaria con seek). None si no existe."""
    with open(ruta, "rb") as f:
        n_salas, pos_general, largo_general = _leer_encabezado(f)
        bajo = 0
        alto = n_salas - 1
        while bajo <= alto:
            medio = (bajo + alto) // 2
            f.seek(TAM_ENCABEZADO + medio * TAM_ENTRADA)
            id_medio, pos, largo = struct.unpack(ENTRADA, _leer_exacto(f, TAM_ENTRADA))
            _validar_entrada(pos, largo, n_salas, pos_general)
            if id_medio == id_sala:
                f.seek(pos)
                sala = _desempaquetar_sala(_leer_exacto(f, largo))
                if sala.id != id_medio:
                    raise ErrorFormato("ID de sala distinto del índice")
                return sala
            if id_medio < id_sala:
                bajo = medio + 1
            else:
                alto = medio - 1
    return None


@_validar_binario
def cargar_todo(ruta):
    with open(ruta, "rb") as f:
        n_salas, pos_general, largo_general = _leer_encabezado(f)
        entradas = []
        for i in range(n_salas):
            entrada = struct.unpack(ENTRADA, _leer_exacto(f, TAM_ENTRADA))
            _validar_entrada(entrada[1], entrada[2], n_salas, pos_general)
            if entradas and entrada[0] <= entradas[-1][0]:
                raise ErrorFormato("índice de salas desordenado o duplicado")
            entradas.append(entrada)
        bloques = []
        siguiente = TAM_ENCABEZADO + n_salas * TAM_ENTRADA
        for e in entradas:
            if e[1] != siguiente:
                raise ErrorFormato("bloques de salas solapados o con datos sobrantes")
            f.seek(e[1])
            bloques.append(_leer_exacto(f, e[2]))
            siguiente += e[2]
        if siguiente != pos_general:
            raise ErrorFormato("datos sobrantes antes del bloque general")
        f.seek(pos_general)
        partida = _desempaquetar_general(_leer_exacto(f, largo_general))
    for i, b in enumerate(bloques):
        sala = _desempaquetar_sala(b)
        if sala.id != entradas[i][0]:
            raise ErrorFormato("ID de sala distinto del índice")
        partida.salas.append(sala)
    return partida
