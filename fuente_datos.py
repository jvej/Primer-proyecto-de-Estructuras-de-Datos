
class FuenteDatos:
    presupuesto = None

    def listar_criptas(self):
        raise NotImplementedError

    def datos_cripta(self, id_cripta):
        raise NotImplementedError

    def pagina_esqueleto(self, id_cripta, pagina):
        raise NotImplementedError

    def contenido_salas(self, id_cripta, ids_salas):
        """Hasta 10 salas por llamada."""
        raise NotImplementedError

    def catalogo(self, ids):
        """Hasta 10 ids por llamada."""
        raise NotImplementedError

    def version_cripta(self, id_cripta):
        raise NotImplementedError

    def version_catalogo(self):
        raise NotImplementedError


TAM_LOTE_MAX = 10


def validar_lote(operacion, elementos):
    if len(elementos) == 0:
        raise ValueError("%s: el lote está vacío" % operacion)
    if len(elementos) > TAM_LOTE_MAX:
        raise ValueError("%s: el lote tiene %d elementos (máximo %d)"
                         % (operacion, len(elementos), TAM_LOTE_MAX))