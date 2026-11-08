# Contract: Endpoint `GET /criptas/<id>/llaves` y Almacenamiento Local

**Feature**: `003-resolubilidad`  
**Date**: 2026-11-08  
**Endpoints**: `GET /criptas/<id>/llaves`, persistencia `llaves.json`

Este contrato formaliza la comunicación HTTP para la obtención de llaves y el formato de datos serializado tanto para el almacenamiento local de `AlmacenCripta` como para el modo desconectado `--offline`.

---

## 1. Solicitud HTTP

- **Método**: `GET`
- **Ruta**: `/v1/criptas/<id>/llaves`
- **Cabeceras obligatorias**:
  - `X-Cripta-Client-Id`: `<UUID único del cliente>`
- **Presupuesto**: Cada solicitud cuenta como 1 intento consumido en `PresupuestoRed`, incluyendo reintentos tras código 429.

---

## 2. Respuestas del Servidor

### 2.1 Código 200 OK

Retorna una lista de objetos JSON que definen la ubicación de cada llave:

```json
{
  "llaves": [
    {
      "id": "itm_llave_bronce",
      "sala": 3
    },
    {
      "id": "itm_llave_negra",
      "sala": 8,
      "enemigo": "e-1203"
    }
  ]
}
```

- **Interpretación**:
  - Si no viene el campo `enemigo`, la llave reposa estáticamente en el suelo de la sala indicada por `sala`.
  - Si viene el campo `enemigo`, contiene el identificador textual de la instancia de enemigo (ej. `"e-1203"`). La llave reside en el campo `suelta` de dicha instancia, y `sala` es la sala donde el enemigo se encuentra inicialmente ubicado.

### 2.2 Código 404 Not Found

```json
{
  "error": "cripta no encontrada"
}
```

### 2.3 Código 429 Too Many Requests

```json
{
  "error": "límite de tasa excedido",
  "reintentar_en": 1.5
}
```

---

## 3. Almacenamiento Local y Modo Offline

### 3.1 `AlmacenCripta` (`<id>__<version>.bin`)
- Almacena el payload completo de llaves bajo la clave interna `"llaves"` en el archivo binario estructurado `AlmacenFichas`.
- Si la versión de la cripta cambia en el servidor, `AlmacenFichas` detecta la disparidad en el encabezado y descarta el archivo binario, forzando una nueva consulta HTTP.

### 3.2 Paquete Offline (`--offline <carpeta>`)
- Ubicación del archivo: `<carpeta>/criptas/<id>/llaves.json`.
- Estructura exacta idéntica a la respuesta HTTP 200:
  ```json
  {
    "llaves": [
      {
        "id": "itm_llave_bronce",
        "sala": 3
      }
    ]
  }
  ```
