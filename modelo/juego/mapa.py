from modelo.juego.actor import Enemigo
from modelo.juego.objetos import Objeto, Trampa
from modelo.juego.sala import DIRECCIONES, Sala


def _id_de(elemento):
    if isinstance(elemento, str):
        return elemento
    return elemento.get("tipo", elemento.get("id"))


def normalizar_comportamiento(texto: str) -> str:
    if not texto:
        return "guardian"
    texto = str(texto).lower().strip()
    tildes = (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ü", "u"))
    for con_tilde, sin_tilde in tildes:
        texto = texto.replace(con_tilde, sin_tilde)
    return texto


class Mapa:
    def __init__(self, esqueleto) -> None:
        self.esqueleto = esqueleto
        self.salas = []
        self.enemigos = []         
        for p in range(esqueleto.cantidad()):
            sala = Sala(esqueleto.ids[p], esqueleto.nombres[p])
            sala.indice = p
            self.salas.append(sala)
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
                costo = datos.get("costo", 100)
                origen.conectar(DIRECCIONES[i], destino, estado,
                                datos.get("llave"), datos.get("cierre_automatico"),
                                costo)

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
            comportamiento = normalizar_comportamiento(ficha.get("comportamiento", "guardian"))
            rango = ficha.get("rango", 0)
            enemigo = Enemigo(
                ficha.get("nombre", e["tipo"]), e.get("vida", vida_max),
                ficha["ataque"], ficha["defensa"], ficha["velocidad"],
                comportamiento, e["instancia"], None, vida_max,
                list(ficha.get("suelta", [])), ficha.get("regeneracion", 0), e["tipo"],
                rango=rango)
            enemigo.mover_a(sala)
            self.enemigos.append(enemigo)
        for o in entrada.get("objetos", []):
            sala.objetos.append(Objeto(resolutor.obtener(_id_de(o))))
        for t in entrada.get("trampas", []):
            sala.trampas.append(Trampa(t["instancia"], resolutor.obtener(t["tipo"])))
        sala.incorporada = True
