# Contract: `modelo/juego/resolubilidad.py`

**Feature**: `003-resolubilidad`  
**Date**: 2026-11-08  
**Module**: `modelo/juego/resolubilidad.py`

Este módulo pertenece exclusivamente a la capa de Modelo (`modelo/`). No realiza operaciones de entrada/salida (I/O), no lee archivos del disco ni efectúa peticiones HTTP. Recibe estructuras de datos en memoria y produce un objeto con los resultados del análisis y el texto formateado del reporte.

---

## 1. Función Principal: `verificar_resolubilidad`

### 1.1 Firma

```python
def verificar_resolubilidad(
    esqueleto,
    ubicaciones_llaves,
    sala_inicial,
    sala_salida,
    llave_salida,
    catalogo_llaves=None
) -> ResultadoResolubilidad:
    """Verifica si la cripta puede completarse bajo los supuestos formales.

    Parámetros:
        esqueleto: Instancia de Esqueleto (modelo/datos/esqueleto.py).
        ubicaciones_llaves: Lista contigua de diccionarios con llaves devueltas por la consulta de llaves:
                            [{"id": str, "sala": int, "enemigo": str | None, "abre": str | None}, ...]
        sala_inicial: Identificador (int o str) de la sala inicial de expedición.
        sala_salida: Identificador (int o str) de la sala donde se ubica la salida.
        llave_salida: Identificador textual (str) de la llave necesaria para abrir la salida.
        catalogo_llaves: (Opcional) Fuente o lista de fichas locales para resolver atributo "abre".

    Retorna:
        ResultadoResolubilidad: Objeto con atributos de diagnóstico y método formatear_reporte().
    """
```

---

## 2. Clase de Retorno: `ResultadoResolubilidad`

```python
class ResultadoResolubilidad:
    def __init__(self, estado, orden_llaves=None, llaves_no_obtenibles=None,
                 frontera_bloqueada=None, ubicacion_llaves=None, ciclos=None, motivo=None):
        self.estado = estado                      # "RESOLUBLE" | "NO RESOLUBLE" | "NO VERIFICADA"
        self.orden_llaves = orden_llaves or []    # [(etapa, [id_llave, ...]), ...]
        self.llaves_no_obtenibles = llaves_no_obtenibles or [] # [id_llave, ...]
        self.frontera_bloqueada = frontera_bloqueada or []     # [(id_sala, dir, destino, llave_pedida), ...]
        self.ubicacion_llaves = ubicacion_llaves or []         # [(id_llave, texto_ubicacion), ...]
        self.ciclos = ciclos or []                # ["itm_a -> itm_b [sala X (DIR)] -> itm_a", ...]
        self.motivo = motivo                      # str o None

    def es_resoluble(self) -> bool:
        return self.estado == "RESOLUBLE"

    def formatear_reporte(self) -> str:
        """Devuelve el reporte textual exacto conforme a la plantilla de FR-018."""
```

---

## 3. Formato del Reporte Emitido (`formatear_reporte()`)

La función `formatear_reporte()` genera una cadena de texto estricta conforme a `FR-018`:

- **Caso Resoluble**:
  ```text
  ESTADO: RESOLUBLE
  ORDEN DE LLAVES:
    etapa 0: itm_llave_bronce
    etapa 1: itm_llave_negra
  ```

- **Caso No Resoluble (con frontera y ciclos)**:
  ```text
  ESTADO: NO RESOLUBLE
  LLAVES NO OBTENIBLES: itm_a, itm_b
  FRONTERA BLOQUEADA:
    - sala 4 (E) -> sala 7: pide itm_a
    - sala 5 (N) -> sala 9: sin llave asociada
  UBICACIÓN DE LLAVES:
    - itm_a: sala 12
    - itm_b: sala 9 (suelta del enemigo e-1203)
  CICLOS DETECTADOS:
    - itm_a -> itm_b [sala 3 (S)] -> itm_a [sala 8 (O)]
  ```

- **Caso No Resoluble (con anomalía topológica de salida)**:
  ```text
  ESTADO: NO RESOLUBLE
  MOTIVO: no existe puerta hacia sala_salida que pida llave_salida
  ```

- **Caso No Verificada (error de red o presupuesto)**:
  ```text
  ESTADO: NO VERIFICADA
  MOTIVO: no se pudo consultar /llaves: presupuesto_solicitudes agotado
  ```
