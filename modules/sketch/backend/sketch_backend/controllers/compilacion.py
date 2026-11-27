"""Administrador y pipeline end-to-end de compilacion nativa ESP-IDF."""

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Callable
from uuid import uuid4

from sketch_backend.esp_idf_backend import compilar_proyecto

# Una sola compilacion a la vez para evitar conflictos en ESP-IDF.
_ejecutor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sketch")
_bloqueo = Lock()
_tareas: dict[str, dict] = {}


def _publicar_log_azul(mensaje: str, nivel: str = "INFO") -> None:
    """Publica eventos de compilacion en el modulo Azul si esta cargado."""
    try:
        from azul_backend.modulo import publish

        publish(mensaje, nivel, source="sketch-espidf")
    except ImportError:
        pass


def _obtener_servicio_archivo():
    """Obtiene la instancia compartida de ArchivoService para estructurar proyectos ESP-IDF."""
    from archivo_backend.router import archivo_service

    return archivo_service


def _ejecutar_compilacion(task_id: str, solicitud: dict) -> None:
    """Ejecuta una compilacion en segundo plano y conserva su resultado."""
    with _bloqueo:
        _tareas[task_id]["status"] = "running"

    try:
        _publicar_log_azul(
            f"Compilando proyecto ESP-IDF en {solicitud['project_path']}...", "INFO"
        )
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

        _publicar_log_azul(
            (
                "Compilacion ESP-IDF finalizada con exito."
                if resultado.get("success")
                else f"Fallo en compilacion ESP-IDF: {resultado.get('error')}"
            ),
            "SUCCESS" if resultado.get("success") else "ERROR",
        )

    except Exception as exc:
        with _bloqueo:
            _tareas[task_id]["status"] = "failed"
            _tareas[task_id]["error"] = str(exc)
        _publicar_log_azul(f"Excepcion en compilacion ESP-IDF: {exc}", "ERROR")


def iniciar_compilacion(solicitud: dict) -> dict:
    """Registra una tarea asincrona y la envia al trabajador."""
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


def compilar_codigo_fuente(solicitud: dict) -> dict:
    """Pipeline completo: estructura proyecto CMake ESP-IDF, compila y empaqueta .bin."""
    from archivo_backend.schemas import CompilerInputResultRequest

    codigo: str = solicitud["codigo"]
    nombre_proyecto: str = solicitud.get("nombre_proyecto", "esp32_sketch")
    nombre_archivo: str = solicitud.get("nombre_archivo", "main.c")
    target: str = (
        (solicitud.get("target") or "esp32s3").strip().lower().replace("-", "")
    )
    timeout: int = solicitud.get("timeout", 600)
    incluir_base64: bool = bool(solicitud.get("incluir_base64", False))

    advertencias: list[str] = []
    if "app_main" not in codigo and ("void setup" in codigo or "void loop" in codigo):
        advertencias.append(
            "Advertencia ESP-IDF: No se detecto 'void app_main(void)'. "
            "ESP-IDF requiere app_main() como punto de entrada nativo en lugar de setup()/loop()."
        )

    servicio_archivo = _obtener_servicio_archivo()
    preparacion = servicio_archivo.prepare_espidf_project_from_source(
        source_code=codigo,
        filename=nombre_archivo,
        project_name=nombre_proyecto,
    )

    if not preparacion.success:
        return {
            "success": False,
            "status": "PREPARATION_FAILED",
            "framework": "ESP-IDF",
            "target": target,
            "project_id": preparacion.project_id,
            "project_path": "",
            "result_summary": preparacion.message,
            "compilation_logs": "",
            "errors": preparacion.errors,
            "warnings": advertencias,
            "binaries": [],
            "command": [],
        }

    _publicar_log_azul(
        f"Iniciando compilacion nativa ESP-IDF (target={target}) para '{preparacion.project_name}'",
        "INFO",
    )

    resultado_idf = compilar_proyecto(
        preparacion.project_absolute_path,
        timeout=timeout,
        target=target,
    )

    errores_compilador: list[str] = []
    if not resultado_idf.get("success"):
        if resultado_idf.get("error"):
            errores_compilador.append(str(resultado_idf["error"]))
        elif resultado_idf.get("stderr"):
            errores_compilador.extend(
                [l for l in str(resultado_idf["stderr"]).splitlines() if l.strip()]
            )

    entrega = servicio_archivo.collect_build_results_for_flutter(
        CompilerInputResultRequest(
            project_id=preparacion.project_id,
            compilation_success=bool(resultado_idf.get("success")),
            compiler_stdout=str(resultado_idf.get("stdout") or ""),
            compiler_stderr=errores_compilador,
            include_base64=incluir_base64,
            target=target,
        )
    )

    _publicar_log_azul(
        entrega.result_summary,
        "SUCCESS" if entrega.success else "ERROR",
    )

    return {
        "success": entrega.success,
        "status": entrega.status,
        "framework": "ESP-IDF",
        "target": target,
        "project_id": entrega.project_id,
        "project_path": entrega.project_absolute_path,
        "result_summary": entrega.result_summary,
        "compilation_logs": entrega.compilation_logs,
        "errors": entrega.errors,
        "warnings": advertencias,
        "binaries": [b.model_dump() for b in entrega.binaries],
        "command": resultado_idf.get("command", []),
    }


def adaptador_compilacion_azul(
    ruta_proyecto: str,
    publicar: Callable[[str, str], None],
) -> dict:
    """Adaptador compatible con azul_backend.modulo.registrar(app, compile_adapter=...)."""
    publicar(f"Ejecutando idf.py build sobre {ruta_proyecto}", "INFO")
    res = compilar_proyecto(ruta_proyecto)
    errores = [res["error"]] if res.get("error") else []
    return {
        "success": bool(res.get("success")),
        "errors": errores,
        "artifacts": res.get("bin_files", []),
        "exit_code": res.get("returncode"),
    }


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
