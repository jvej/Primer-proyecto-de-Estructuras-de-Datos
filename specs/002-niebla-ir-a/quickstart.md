# Quickstart: Niebla de guerra, mapa conocido y viaje automático "ir a"

**Feature**: `002-niebla-ir-a`  
**Date**: 2026-11-08  
**Constitution Authority**: `.specify/memory/constitution.md` (Version 1.0.0)

---

## 1. Requisitos Previos

- Entorno Python 3.13 con las dependencias básicas instaladas (`requests`, `pygame`).
- Ejecución desde la raíz del repositorio:
  ```powershell
  python --version
  # Debe indicar Python 3.13.x
  ```

---

## 2. Escenarios de Validación Rápida

### Escenario 1: Pruebas automatizadas de aceptación
Ejecución de la suite completa de pruebas de niebla de guerra, mapa conocido y "ir a", donde cada prueba cita su requisito funcional (`FR-###`):

```powershell
python -m tests.test_niebla_ir_a
```

**Resultado esperado**:
- Todas las pruebas pasan (`OK`).
- Se validan:
  - `test_FR001_clasificacion_estados_conocimiento`
  - `test_FR002_estado_inicial_instante_cero`
  - `test_FR004_sala_avistada_no_revela_id_ni_nombre`
  - `test_FR006_actualizacion_memoria_puertas_en_acciones`
  - `test_FR007_antorcha_enciende_vecinas_sin_activar_contenido`
  - `test_FR012_reversion_conocimiento_con_pergamino`
  - `test_FR014_ir_a_destino_no_explorado_rechazado`
  - `test_FR015_ir_a_camino_costo_minimo`
  - `test_FR016_desempate_menor_id_en_vecina`
  - `test_FR019_interrupcion_por_dano_o_enemigo`
  - `test_FR022_log_asienta_pasos_y_comentario`
  - `test_FR024_guardado_v3_reporta_incompatibilidad_explicta`

---

### Escenario 2: Verificación de no regresión del sistema
Ejecutar las pruebas unitarias y de integración de la base existente:

```powershell
python -m tests.test_motor_base
python -m tests.test_guardado_binario
```

**Resultado esperado**:
- Las suites existentes de motor, agenda y guardado ejecutan limpiamente.

---

### Escenario 3: Ejecución de Benchmarks Oficiales

#### 3.1 Benchmark de Mapa Conocido y "ir a" (SC-001..SC-004)
```powershell
python main.py --bench mapa_conocido
```

**Criterios de Éxito**:
- `SC-001`: Tiempo de recálculo de Dijkstra acotado sobre el mapa completo $< 5.0\text{ ms}$.
- `SC-002`: Consulta de estado de sala y puerta recordada en tiempo constante $O(1)$.
- `SC-003`: Exploración de sala proporcional a sus salidas directas e independiente de $N$.
- `SC-004`: Reversión de conocimiento mediante pergamino en tiempo constante $O(1)$.

#### 3.2 Repetición de Benchmarks de Regresión
```powershell
python main.py --bench cache lista_ordenada ordenamiento guardado
```

**Resultado esperado**:
- Todas las mediciones históricas confirman estabilidad y ausencia de degradación de rendimiento.

---

### Escenario 4: Verificación de Replay sin divergencia

```powershell
python main.py --replay datos_cripta/partidas/ejemplo_ir_a.log --detalle
```

**Resultado esperado**:
- Las órdenes ordinarias `mover <dir>` registradas a partir de viajes automáticos se reproducen deterministamente sin divergencias.
- Las líneas de comentario `# ir a <destino>` son ignoradas de forma transparente por el reproductor.
