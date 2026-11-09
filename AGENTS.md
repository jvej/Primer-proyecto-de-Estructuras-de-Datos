# Reglas del proyecto CRIPTA (Estructuras de Datos II, Parte II)

- Responde siempre en español.
- Antes de cualquier fase de spec-kit ($speckit-constitution, $speckit-specify, $speckit-clarify, $speckit-plan, $speckit-tasks, $speckit-analyze, $speckit-implement), lee .specify/memory/constitution.md y respétala.
- Código en Python 3.13, sin dependencias nuevas. requirements.txt solo tiene requests y pygame.
- En las estructuras evaluadas está PROHIBIDO usar: dict o set como índice o caché, heapq, bisect, collections (deque, OrderedDict, defaultdict, Counter), networkx o cualquier biblioteca de grafos o rutas, sorted() y list.sort(). Los dict de respuesta.json() solo se leen. list solo como almacenamiento contiguo.
- El Modelo (modelo/) no importa controlador/ ni vista/. --replay, --bench y --verificar no crean la vista.
- Ningún dato de una cripta concreta (ids de salas, llaves, presupuestos, nombres) se escribe en el código.
- Todo cambio de estado del juego pasa por los métodos únicos de Partida (cambiar, _lista_*, _inv_*, el método único de puertas), para que lo revierta el pergamino y lo vea la línea de tiempo.
- Desempates: siempre el menor id. El azar solo sale de partida.azar (random.Random(semilla) de la partida).
- Toda solicitud HTTP cuenta en presupuesto_solicitudes, incluidos reintentos y /llaves.
- No hagas git commit, git push, git merge, git reset ni git checkout. No borres archivos. No instales paquetes. Los commits los hace el integrante.
- Solo modifica los archivos que pide la tarea actual. No toques specs/ salvo que se pida.
- spec.md no contiene nombres de estructuras, clases ni módulos; eso va en plan.md.
- Cada requisito tiene id estable (FR-###, SC-###). Cada prueba de aceptación cita su requisito en el nombre (por ejemplo, test_FR007_...).
   - Ejecuta Python SIEMPRE con el del entorno virtual del proyecto: venv\Scripts\python.exe (Python 3.13). Pruebas: venv\Scripts\python.exe -m tests.<modulo>. Bench: venv\Scripts\python.exe main.py --bench <subsistema>. Nunca uses el python del sistema.