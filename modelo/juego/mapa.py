from modelo.juego.actor import Enemigo
from modelo.juego.objetos import Objeto, Trampa
from modelo.juego.sala import DIRECCIONES, Sala


def _id_de(elemento):
    if isinstance(elemento, str):
        return elemento
    return elemento.get("tipo", elemento.get("id"))


class Mapa:
    def __init__(self, esqueleto) -> None:
        self.esqueleto = esqueleto
        self.salas = []
        self.enemigos = []         
        for p in range(esqueleto.cantidad()):
            self.salas.append(Sala(esqueleto.ids[p], esqueleto.nombres[p]))
        for p in range(len(self.salas)):
            origen = self.salas[p]
            detalle = esqueleto.salidas[p]
            for i in range(len(DIRECCIONES)):
                if DIRECCIONES[i] not in detalle or origen.salidas[i] is not None:
                    continue    
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