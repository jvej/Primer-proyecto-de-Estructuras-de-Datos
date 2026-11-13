# Quickstart: Verificación de Resolubilidad y Extensión del Servicio Web

**Feature**: `003-resolubilidad`  
**Date**: 2026-11-08  
**Spec Reference**: `specs/003-resolubilidad/spec.md`

Esta guía describe los escenarios de validación y comandos para verificar de extremo a extremo la funcionalidad de resolubilidad, extensiones de datos y mediciones de rendimiento en CRIPTA.

---

## 1. Prerrequisitos

- Entorno Python 3.13.
- Dependencias base instaladas (`requests`, `pygame`):
  ```powershell
  python -m pip install -r requirements.txt
  ```

---

## 2. Escenarios de Validación

### Escenario 1: Verificación de cripta resoluble (`--verificar`)
Ejecuta la verificación en modo frío sin interfaz gráfica sobre una cripta resoluble del paquete offline:
```powershell
python main.py --offline paquete_prueba/ --verificar cripta-resoluble
```
**Resultado esperado**:
- Salida estándar muestra:
  ```text
  ESTADO: RESOLUBLE
  ORDEN DE LLAVES:
    etapa 0: ...
    etapa 1: ...
  ```
- Código de salida (`$LASTEXITCODE`): `0`.

---

### Escenario 2: Verificación de cripta no resoluble con ciclo (`--verificar`)
Ejecuta la verificación sobre una cripta sintética con dependencia circular de llaves:
```powershell
python main.py --offline paquete_prueba/ --verificar cripta-ciclo
```
**Resultado esperado**:
- Salida estándar muestra:
  ```text
  ESTADO: NO RESOLUBLE
  LLAVES NO OBTENIBLES: ...
  FRONTERA BLOQUEADA:
    ...
  CICLOS DETECTADOS:
    - itm_a -> itm_b [sala 3 (S)] -> itm_a [sala 8 (O)]
  ```
- Código de salida (`$LASTEXITCODE`): `1`.

---

### Escenario 3: Manejo de error de cripta inexistente o falta de presupuesto
Ejecuta la verificación sobre un identificador que no existe:
```powershell
python main.py --offline paquete_prueba/ --verificar cripta-fantasma
```
**Resultado esperado**:
- Salida estándar muestra:
  ```text
  ESTADO: NO VERIFICADA
  MOTIVO: no se pudo consultar /llaves: cripta inexistente
  ```
- Código de salida (`$LASTEXITCODE`): `2`.

---

### Escenario 4: Bloqueo de inicio sin `--forzar` e inicio forzado con `--forzar`
1. Intentar iniciar una partida sobre una cripta no resoluble sin forzar:
   ```powershell
   python main.py --offline paquete_prueba/
   ```
   *La partida no arranca, se muestra el reporte y finaliza con mensaje informativo.*
2. Iniciar la misma partida forzando el arranque:
   ```powershell
   python main.py --offline paquete_prueba/ --forzar
   ```
   *Se muestra el reporte de no resolubilidad y la partida inicia normalmente.*

---

### Escenario 5: Benchmark de rendimiento
Ejecutar la medición comparativa entre el recorrido incremental y el recorrido repetido:
```powershell
python main.py --bench resolubilidad
```
**Resultado esperado**:
- Muestra los tiempos de ejecución para cadenas de 10, 50, 100 y 200 llaves.
- El algoritmo incremental exhibe crecimiento lineal $O(S + E + L)$ y velocidad superior al algoritmo repetido $O(L \cdot (S + E))$.

Repetir el benchmark de red para verificar el impacto de la consulta de llaves:
```powershell
python main.py --bench red
```

---

### Escenario 6: Ejecución de la suite de pruebas unitarias y de integración
```powershell
python -m tests.test_resolubilidad
python -m tests.test_cliente_http
python -m tests.test_esqueleto
```
Todas las pruebas deben concluir exitosamente (`OK`).
