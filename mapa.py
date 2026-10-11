"""Mapa de la cripta: construye el modelo (salas, puertas, actores) a partir de los datos.

El motor no sabe de dónde vienen los datos (red, disco u offline, §3.4): recibe el
esqueleto ya descargado y, por sala, el contenido y las fichas del catálogo.
Para buscar una sala por id usa el índice del Esqueleto (posición en listas paralelas).
"""

from actor import Enemigo
from objetos import Objeto, Trampa
from sala import DIRECCIONES, Sala


def _id_de(elemento):
    """Un objeto del contenido puede venir como id o como {"tipo": id}."""
    if isinstance(elemento, str):
        return elemento
    return elemento.get("tipo", elemento.get("id"))


class Mapa:
    def __init__(self, esqueleto) -> None:
        self.esqueleto = esqueleto
        self.salas = []
        self.enemigos = []          # todos los enemigos creados (para saber qué fichas siguen en uso)
        for p in range(esqueleto.cantidad()):
            self.salas.append(Sala(esqueleto.ids[p], esqueleto.nombres[p]))
        for p in range(len(self.salas)):
            origen = self.salas[p]
            detalle = esqueleto.salidas[p]
            for i in range(len(DIRECCIONES)):
                if DIRECCIONES[i] not in detalle or origen.salidas[i] is not None:
                    continue    # no existe, o ya la creó la sala del otro lado
                datos = detalle[DIRECCIONES[i]]
                destino = self.sala(datos["sala"])
                if destino is None:
                    continue
                estado = "cerrada" if datos.get("cerrada") else "abierta"
                origen.conectar(DIRECCIONES[i], destino, estado,
                                datos.get("llave"), datos.get("cierre_automatico"))

    def sala(self, id_sala):
        p = self.esqueleto.posicion(id_sala)
        if p is None:
            return None
        return self.salas[p]

    def incorporar(self, sala, entrada, resolutor) -> None:
        """Crea los enemigos (dormidos), objetos y trampas de la sala (§2.4, §3.2).
        Cada tipo se convierte en su ficha con resolutor.obtener(id)."""
        if sala.incorporada:
            return
        for e in entrada.get("enemigos", []):
            ficha = resolutor.obtener(e["tipo"])
            vida_max = ficha["vida_max"]
            enemigo = Enemigo(
                ficha.get("nombre", e["tipo"]), e.get("vida", vida_max),
                ficha["ataque"], ficha["defensa"], ficha["velocidad"],
                ficha.get("comportamiento", "guardian"), e["instancia"], None, vida_max,
                list(ficha.get("suelta", [])), ficha.get("regeneracion", 0), e["tipo"])
            enemigo.mover_a(sala)
            self.enemigos.append(enemigo)
        for o in entrada.get("objetos", []):
            sala.objetos.append(Objeto(resolutor.obtener(_id_de(o))))
        for t in entrada.get("trampas", []):
            sala.trampas.append(Trampa(t["instancia"], resolutor.obtener(t["tipo"])))
        sala.incorporada = True