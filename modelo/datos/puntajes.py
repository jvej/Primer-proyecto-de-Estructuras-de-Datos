import os

from modelo.estructuras.ordenamiento import ordenar

SEPARADOR = "\t"


class RegistroPuntaje:
    __slots__ = ("nombre", "id_cripta", "version_cripta", "resultado", "acciones",
                 "derrotados", "tiempo", "fecha")

    def __init__(self, nombre, id_cripta, version_cripta, resultado, acciones, derrotados,
                 tiempo, fecha=""):
        self.nombre = nombre
        self.id_cripta = id_cripta
        self.version_cripta = version_cripta
        self.resultado = resultado        
        self.acciones = int(acciones)
        self.derrotados = int(derrotados)
        self.tiempo = int(tiempo)
        self.fecha = fecha

    def a_linea(self):
        campos = (self.nombre, self.id_cripta, self.version_cripta, self.resultado,
                  str(self.acciones), str(self.derrotados), str(self.tiempo), self.fecha)
        limpios = []
        for campo in campos:
            limpios.append(str(campo).replace(SEPARADOR, " ").replace("\n", " "))
        return SEPARADOR.join(limpios)

    @staticmethod
    def desde_linea(linea):
        partes = linea.split(SEPARADOR)
        if len(partes) < 7:
            return None
        try:
            return RegistroPuntaje(partes[0], partes[1], partes[2], partes[3], partes[4],
                                   partes[5], partes[6], partes[7] if len(partes) > 7 else "")
        except ValueError:
            return None

    def __repr__(self):
        return "RegistroPuntaje(%s, %s, %s, t=%d)" % (self.nombre, self.id_cripta,
                                                       self.resultado, self.tiempo)


def _clave(registro):
    return (0 if registro.resultado == "victoria" else 1, registro.tiempo,
            registro.acciones, -registro.derrotados)


class TablaPuntajes:
    def __init__(self, ruta):
        self.ruta = ruta

    def registrar(self, partida, nombre, fecha=""):
        registro = RegistroPuntaje(nombre or "Jugador", partida.id_cripta, partida.version_cripta,
                                   partida.estado, partida.acciones, partida.derrotados,
                                   partida.reloj.tiempo_actual, fecha)
        carpeta = os.path.dirname(self.ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(self.ruta, "a", encoding="utf-8") as f:
            f.write(registro.a_linea() + "\n")
        return registro

    def listar(self, id_cripta=None):
        registros = []
        if not os.path.exists(self.ruta):
            return registros
        with open(self.ruta, "r", encoding="utf-8") as f:
            for linea in f:
                registro = RegistroPuntaje.desde_linea(linea.rstrip("\n"))
                if registro is None:
                    continue            
                if id_cripta is None or registro.id_cripta == id_cripta:
                    registros.append(registro)
        return ordenar(registros, clave=_clave)