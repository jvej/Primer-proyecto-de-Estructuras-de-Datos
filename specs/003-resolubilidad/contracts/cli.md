# Contract: CLI Flags `--verificar`, `--forzar` y `--bench resolubilidad`

**Feature**: `003-resolubilidad`  
**Date**: 2026-11-08  
**Interfaces**: Consola, Terminal y Códigos de Salida

---

## 1. Modificador `--verificar <cripta>`

Ejecuta de forma aislada la verificación de resolubilidad para la cripta indicada, imprimiendo el reporte exclusivamente en la salida estándar y saliendo de inmediato sin inicializar ninguna interfaz gráfica (Pygame) ni bucle de consola interactivo.

### 1.1 Invocación
```bash
python main.py --verificar <id_cripta>
python main.py --offline <carpeta> --verificar <id_cripta>
```

### 1.2 Códigos de Salida del Proceso (`sys.exit`)
- **`0`**: La cripta es verificada exitosamente y resulta **RESOLUBLE**.
- **`1`**: La cripta es verificada exitosamente y resulta **NO RESOLUBLE**.
- **`2`**: La verificación **NO PUDO COMPLETARSE** (cripta inexistente / 404, error de conexión de red, o agotamiento de `presupuesto_solicitudes` sin datos locales válidos).

---

## 2. Modificador `--forzar`

Permite iniciar una partida interactiva normal aun cuando la verificación previa determine que la cripta no es resoluble o no haya podido verificarse.

### 2.1 Invocación
```bash
python main.py --forzar
python main.py --offline <carpeta> --forzar
python main.py --gui --forzar
```

### 2.2 Comportamiento
- Se ejecuta la verificación previa obligatoria.
- Se presenta el reporte emitido en la interfaz activa (en texto por consola, o como pantalla previa en Pygame bajo `--gui`).
- A pesar de que el estado sea `NO RESOLUBLE` o `NO VERIFICADA`, la partida procede a inicializarse y la expedición comienza normalmente.
- Sin `--forzar`: ante una cripta no resoluble o no verificada, la partida no inicia (en modo consola termina con mensaje informativo; en Pygame retorna a la pantalla de selección de cripta).

---

## 3. Benchmark `--bench resolubilidad`

Ejecuta las pruebas de rendimiento comparativo entre el algoritmo incremental por etapas y el algoritmo de recorrido repetido por llave.

### 3.1 Invocación
```bash
python main.py --bench resolubilidad
```

### 3.2 Salida
Imprime una tabla comparativa en consola que muestra para diferentes tamaños de criptas sintéticas encadenadas ($N = 10, 50, 100, 200$ llaves):
- Tiempo de ejecución incremental (ms).
- Tiempo de ejecución de recorrido repetido (ms).
- Factor de aceleración obtenido (Speedup).
- Verificación de que ambos algoritmos coinciden en el diagnóstico.
