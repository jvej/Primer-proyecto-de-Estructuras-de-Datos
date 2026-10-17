"""Excepciones del proyecto. Todas llevan la operación que falló (§3.1)."""


class ErrorCripta(Exception):
    """Base de los errores propios del programa."""


class ErrorRed(ErrorCripta):
    def __init__(self, operacion, detalle, codigo=None):
        self.operacion = operacion
        self.detalle = detalle
        self.codigo = codigo
        super().__init__("Falló la operación '%s': %s" % (operacion, detalle))


class ErrorPresupuesto(ErrorCripta):
    def __init__(self, operacion, limite):
        self.operacion = operacion
        self.limite = limite
        super().__init__("Se agotó el presupuesto de solicitudes (%s) al intentar '%s'"
                         % (limite, operacion))


class ErrorDatosNoDisponibles(ErrorCripta):
    def __init__(self, operacion, detalle):
        self.operacion = operacion
        self.detalle = detalle
        super().__init__("Datos no disponibles en '%s': %s" % (operacion, detalle))