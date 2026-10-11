"""Prueba rápida contra la API real: python probar_api.py [id_cripta]"""
import sys

from cliente_http import ClienteHTTP
from errores import ErrorCripta


def main():
    id_cripta = sys.argv[1] if len(sys.argv) > 1 else "cripta-01"
    cliente = ClienteHTTP()
    try:
        criptas = cliente.listar_criptas()
        print("1. criptas:", criptas)
        datos = cliente.datos_cripta(id_cripta)
        print("2. datos generales:", datos)
        cliente.presupuesto.fijar_limite(datos["presupuesto_solicitudes"])
        print("3. esqueleto (claves):", list(cliente.pagina_esqueleto(id_cripta, 1).keys()))
        contenido = cliente.contenido_salas(id_cripta, [datos["sala_inicial"]])
        print("4. contenido:", contenido)
        print("5. versión cripta:", cliente.version_cripta(id_cripta))
        print("6. versión catálogo:", cliente.version_catalogo())
        ids = []
        for entrada in contenido["contenido"]:
            for campo in ("enemigos", "objetos", "trampas"):
                for e in entrada.get(campo, []):
                    ids.append(e if isinstance(e, str) else e["tipo"])
        if ids:
            print("7. catálogo:", cliente.catalogo(ids[:10]))
    except ErrorCripta as e:
        print("ERROR:", e)
        return
    print("Solicitudes realizadas:", cliente.presupuesto.realizadas,
          "de", cliente.presupuesto.limite)


if __name__ == "__main__":
    main()