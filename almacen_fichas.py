import json
import os
import struct
from tabla_hash import TablaHash

MARCA = b"CATA"
FORMATO_LARGO = "<I"   
TAM_LARGO = 4


class AlmacenFichas:
    def __init__(self, ruta, version_catalogo):
        """Abre el almacén. Si la versión guardada es distinta, lo vacía."""
        self.ruta = ruta
        self.version = version_catalogo
        self.indice = TablaHash()  
        self.lecturas = 0            
        self.se_descarto = False     

        if os.path.exists(ruta) and self._leer_encabezado() == version_catalogo:
            self._reconstruir_indice()
        else:
            if os.path.exists(ruta):
                self.se_descarto = True
            self._crear_archivo_nuevo()


    def _leer_encabezado(self):
        """Devuelve la versión guardada, o None si el archivo no sirve."""
        with open(self.ruta, "rb") as f:
            marca = f.read(len(MARCA))
            if marca != MARCA:
                return None
            datos = f.read(TAM_LARGO)
            if len(datos) < TAM_LARGO:
                return None
            largo = struct.unpack(FORMATO_LARGO, datos)[0]
            texto = f.read(largo)
            if len(texto) < largo:
                return None
            return texto.decode("utf-8")

    def _crear_archivo_nuevo(self):
        version = self.version.encode("utf-8")
        with open(self.ruta, "wb") as f:
            f.write(MARCA)
            f.write(struct.pack(FORMATO_LARGO, len(version)))
            f.write(version)


    def _reconstruir_indice(self):
        """Recorre el archivo leyendo solo largos e ids; salta los JSON."""
        tamano = os.path.getsize(self.ruta)
        with open(self.ruta, "rb") as f:
            f.seek(len(MARCA))
            largo_version = struct.unpack(FORMATO_LARGO, f.read(TAM_LARGO))[0]
            f.seek(largo_version, 1)

            while f.tell() < tamano:
                datos = f.read(TAM_LARGO)
                if len(datos) < TAM_LARGO:
                    break                       # registro cortado: se ignora
                largo_id = struct.unpack(FORMATO_LARGO, datos)[0]
                id_ficha = f.read(largo_id).decode("utf-8")
                datos = f.read(TAM_LARGO)
                if len(datos) < TAM_LARGO:
                    break
                largo_json = struct.unpack(FORMATO_LARGO, datos)[0]
                posicion = f.tell()
                if posicion + largo_json > tamano:
                    break                       # registro incompleto
                self.indice.insertar(id_ficha, [posicion, largo_json])
                f.seek(largo_json, 1)

    def contiene(self, id_ficha):
        return self.indice.contiene(id_ficha)

    def cantidad(self):
        return self.indice.cantidad()

    def guardar(self, id_ficha, ficha):
        """Añade la ficha al final del archivo y actualiza el índice."""
        texto = json.dumps(ficha).encode("utf-8")
        id_bytes = id_ficha.encode("utf-8")
        with open(self.ruta, "ab") as f:
            f.write(struct.pack(FORMATO_LARGO, len(id_bytes)))
            f.write(id_bytes)
            f.write(struct.pack(FORMATO_LARGO, len(texto)))
            posicion = f.tell()
            f.write(texto)
        self.indice.insertar(id_ficha, [posicion, len(texto)])

    def leer(self, id_ficha):
        """Devuelve la ficha leída de disco, o None si no está."""
        entrada = self.indice.buscar(id_ficha)
        if entrada is None:
            return None
        with open(self.ruta, "rb") as f:
            f.seek(entrada[0])
            texto = f.read(entrada[1])
        self.lecturas += 1
        return json.loads(texto.decode("utf-8"))

    def ids(self):
        return self.indice.claves()