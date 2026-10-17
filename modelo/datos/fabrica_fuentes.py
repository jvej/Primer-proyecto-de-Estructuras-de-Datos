"""Elige la fuente de datos según --offline; el modelo no sabe cuál recibió (§3.4, §6)."""
from modelo.datos.cliente_http import ClienteHTTP
from modelo.datos.cliente_offline import ClienteOffline
from modelo.datos.presupuesto_red import PresupuestoRed


def crear_fuente_datos(offline=False, carpeta_offline=None):
    """Devuelve (fuente, presupuesto)."""
    if offline:
        if not carpeta_offline:
            raise ValueError("--offline requiere indicar la carpeta del paquete de respuestas")
        fuente = ClienteOffline(carpeta_offline)
        return fuente, fuente.presupuesto
    presupuesto = PresupuestoRed()
    return ClienteHTTP(presupuesto), presupuesto