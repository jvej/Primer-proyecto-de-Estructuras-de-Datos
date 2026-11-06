<!--
Sync Impact Report:
- Version change: 1.0.0 (simplificación de redacción y tono para defensa de curso)
- Modificaciones: Títulos simplificados y lenguaje directo de estudiantes; eliminados términos grandilocuentes.
- Reglas y principios: Exactamente los 7 principios y las reglas del mensaje original, sin agregar ni quitar ninguno.
-->

# Proyecto CRIPTA - Constitución

## Core Principles

### I. Estructuras propias
- **Qué dice**: En los problemas evaluados programamos las estructuras a mano. No usamos `dict` ni `set` como índice o caché, ni `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` u otra biblioteca de grafos o rutas, ni `sorted()` o `list.sort()` en los ordenamientos evaluados. `list` solo se usa como almacenamiento contiguo. Los `dict` que devuelve `respuesta.json()` solo se leen.
- **Por qué lo tenemos**: Porque lo que se evalúa en el curso es que sepamos diseñar, implementar y justificar nuestras propias estructuras de datos con su costo en tiempo y memoria.
- **Cómo se comprueba**: Revisando cada `plan.md` antes de generar tareas y buscando esos nombres prohibidos en el código.

### II. Determinismo
- **Qué dice**: La misma cripta, la misma semilla y las mismas acciones dan siempre la misma partida. El azar sale solo del `random.Random(semilla)` propio de la partida (`partida.azar`). Los empates se resuelven siempre por el menor `id` o por número de secuencia.
- **Por qué lo tenemos**: Para poder reproducir cualquier partida con `--replay`, depurar errores con certeza y asegurar que las pruebas y mediciones sean justas y repetibles.
- **Cómo se comprueba**: Con pruebas automatizadas que corren la misma partida dos veces con la misma semilla y comparan que el resultado y los eventos sean idénticos.

### III. Separación MVC
- **Qué dice**: El Modelo (`modelo/`) no sabe de HTTP, archivos, consola ni Pygame, y no importa `controlador/` ni `vista/`. Los modos `--replay`, `--bench` y `--verificar` no crean la vista.
- **Por qué lo tenemos**: Para mantener las responsabilidades separadas y permitir que las pruebas y los análisis de rendimiento corran rápido en consola sin depender de gráficos.
- **Cómo se comprueba**: Revisando que `modelo/` no importe nada de controlador ni vista, y verificando que `--bench` y `--verificar` corran sin inicializar Pygame.

### IV. Ningún dato de una cripta concreta en el código
- **Qué dice**: Ningún dato de una cripta concreta va en el código: ni ids de salas, ni llaves, ni presupuestos, ni nombres.
- **Por qué lo tenemos**: Porque el programa debe ser general y resolver cualquier cripta que entregue la API, no solo las de prueba.
- **Cómo se comprueba**: Revisando el código y ejecutando pruebas con criptas sintéticas generadas proceduralmente.

### V. Respeto del presupuesto de solicitudes
- **Qué dice**: Toda solicitud HTTP cuenta en `presupuesto_solicitudes`, incluidos los reintentos tras un error 429, las verificaciones de versión y la consulta a `/llaves`.
- **Por qué lo tenemos**: Porque es una restricción central de la partida; si gastamos más solicitudes de las permitidas, la expedición falla.
- **Cómo se comprueba**: Con un contador en el cliente HTTP verificado en pruebas que simulan errores 429 y consultas adicionales, confirmando que no se supere el límite.

### VI. Rendimiento medido
- **Qué dice**: Toda afirmación de rendimiento se respalda con `python main.py --bench <subsistema>`, usando criptas sintéticas deterministas por semilla y comparando contra la alternativa que descartamos.
- **Por qué lo tenemos**: Para defender nuestras decisiones con datos y mediciones reales del proyecto frente al profesor, no con suposiciones teóricas.
- **Cómo se comprueba**: Ejecutando el comando de bench y guardando las comparaciones en `DECISIONES.md`.

### VII. Especificación antes que código
- **Qué dice**: En Git, el `spec.md` de cada capacidad se confirma antes que el código que la implementa. Si una especificación estaba mal, primero se corrige la especificación y después el código, en commits separados.
- **Por qué lo tenemos**: Para obligarnos a pensar el diseño y las pruebas antes de escribir código y tener trazabilidad limpia en el repositorio.
- **Cómo se comprueba**: Revisando el historial y el orden de los commits en Git.

## Reglas del proyecto

- **Puntos únicos de cambio de estado**: Todo cambio de estado del juego pasa por los métodos únicos de `Partida` (`cambiar`, `_lista_*`, `_inv_*`, y el método único de puertas), para que el pergamino lo pueda revertir y la línea de tiempo lo pueda registrar.
- **Identificadores estables y pruebas de aceptación**: Cada requisito tiene un id estable (`FR-###` para funcionales, `SC-###` para rendimiento) y cada escenario de aceptación tiene una prueba automatizada que cita ese id en su nombre (por ejemplo, `test_FR007_...`).
- **Dependencias**: No se agregan dependencias fuera de `requests` y `pygame`. Todo el código corre en Python 3.13.
- **Rol del agente**: El agente de programación es Google Antigravity con spec-kit v1.0.10. El agente no hace commits ni push; los hacemos nosotros.
- **Registro de decisiones**: `DECISIONES.md` enlaza el `spec.md` y el `plan.md` de cada decisión.

## Flujo de trabajo y validación

- **Ejecución de pruebas**: Las pruebas se ejecutan con `python -m tests.<modulo>`.
- **Contenido de spec.md**: `spec.md` no contiene nombres de estructuras, clases ni módulos; eso va en `plan.md`.
- **Ejecución del bench**: El bench se ejecuta con `python main.py --bench <subsistema>`.

## Governance

- **Regla general**: La constitución guía las decisiones técnicas del equipo; si una propuesta no la cumple, se ajusta la propuesta.
- **Enmiendas**: Cualquier cambio se acuerda en el equipo y se deja documentado en un commit específico.
- **Versionado**:
  - **MAJOR (X.0.0)**: Si cambia o se elimina un principio central.
  - **MINOR (1.X.0)**: Si se agrega una nueva regla o sección.
  - **PATCH (1.0.X)**: Aclaraciones de redacción o formato.
- **Cumplimiento**: Antes de avanzar en cada fase de spec-kit (`/speckit-plan`, `/speckit-tasks`, `/speckit-implement`), revisamos que se cumpla esta constitución.

**Version**: 1.0.0 | **Ratified**: 2026-11-06 | **Last Amended**: 2026-11-06
