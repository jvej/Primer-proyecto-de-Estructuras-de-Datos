"""Montículo binario de mínimos (contrato C3).

Cola de prioridad propia sobre una lista contigua, sin bibliotecas de colas ni de
búsqueda y sin tablas hash (Constitución, Principio I).

Los elementos son tuplas que se comparan de forma lexicográfica. En la búsqueda de
rutas se usan tuplas que empiezan por (distancia, id_sala): ante igual distancia
sale primero la de menor id_sala, así el desempate es determinista (Principio II).

No hay decrease_key: se usa eliminación perezosa. Si una sala mejora su distancia,
se inserta una entrada nueva y quien extrae descarta las obsoletas.
"""


class MonticuloMin:
    def __init__(self) -> None:
        self._datos = []

    def __len__(self) -> int:
        return len(self._datos)

    def es_vacio(self) -> bool:
        return len(self._datos) == 0

    def insertar(self, elemento) -> None:
        """Agrega un elemento. O(log K)."""
        datos = self._datos
        datos.append(elemento)
        i = len(datos) - 1
        while i > 0:
            padre = (i - 1) // 2
            if datos[i] < datos[padre]:
                datos[i], datos[padre] = datos[padre], datos[i]
                i = padre
            else:
                break

    def extraer_min(self):
        """Quita y devuelve el menor elemento. O(log K). IndexError si está vacío."""
        datos = self._datos
        if len(datos) == 0:
            raise IndexError("el montículo está vacío")
        minimo = datos[0]
        ultimo = datos.pop()
        n = len(datos)
        if n > 0:
            datos[0] = ultimo
            i = 0
            while True:
                izq = 2 * i + 1
                der = izq + 1
                menor = i
                if izq < n and datos[izq] < datos[menor]:
                    menor = izq
                if der < n and datos[der] < datos[menor]:
                    menor = der
                if menor == i:
                    break
                datos[i], datos[menor] = datos[menor], datos[i]
                i = menor
        return minimo