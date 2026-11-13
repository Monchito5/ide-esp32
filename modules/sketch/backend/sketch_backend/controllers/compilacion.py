"""Administrador de tareas de compilacion ESP-IDF."""

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from uuid import uuid4

from sketch_backend.esp_idf_backend import compilar_proyecto

# Una sola compilacion a la vez para evitar conflictos en ESP-IDF.
_ejecutor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sketch")
_bloqueo = Lock()
_tareas: dict[str, dict] = {}


def _ejecutar_compilacion(task_id: str, solicitud: dict) -> None:
    """Ejecuta una compilacion y conserva su resultado."""
    with _bloqueo:
        _tareas[task_id]["status"] = "running"

    try:
        resultado = compilar_proyecto(
            solicitud["project_path"],
            timeout=solicitud["timeout"],
            target=solicitud.get("target"),
        )

        with _bloqueo:
            _tareas[task_id]["result"] = resultado
            _tareas[task_id]["status"] = (
                "completed" if resultado.get("success") else "failed"
            )
            _tareas[task_id]["error"] = resultado.get("error")

    except Exception as exc:
        with _bloqueo:
            _tareas[task_id]["status"] = "failed"
            _tareas[task_id]["error"] = str(exc)


def iniciar_compilacion(solicitud: dict) -> dict:
    """Registra una tarea y la envía al trabajador."""
    task_id = str(uuid4())

    with _bloqueo:
        _tareas[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "result": None,
            "error": None,
        }

    _ejecutor.submit(_ejecutar_compilacion, task_id, solicitud)

    return obtener_tarea(task_id)


def obtener_tarea(task_id: str) -> dict | None:
    """Consulta una tarea por su identificador."""
    with _bloqueo:
        tarea = _tareas.get(task_id)
        return dict(tarea) if tarea else None


def obtener_resumen() -> dict:
    """Devuelve el estado general del administrador de compilaciones."""
    with _bloqueo:
        cantidades = {
            estado: sum(1 for tarea in _tareas.values() if tarea["status"] == estado)
            for estado in ("pending", "running", "completed", "failed")
        }

    return {
        "module": "sketch",
        "framework": "ESP-IDF",
        "tasks": cantidades,
        "total": sum(cantidades.values()),
    }
