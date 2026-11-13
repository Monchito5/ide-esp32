"""Módulo Azul para registrar en el FastAPI existente; no crea otra aplicación."""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4
import os

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/azul", tags=["azul"])
_lock = Lock()
_events = deque(maxlen=1000)
_jobs = {}
_sequence = 0
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="azul-sketch")
_adapter = None


class LogInput(BaseModel):
    level: str = "INFO"
    message: str = Field(min_length=1, max_length=10000)
    source: str = "general"


class CompileInput(BaseModel):
    project_path: str = Field(min_length=1, max_length=4096)


def publish(message: str, level: str = "INFO", source: str = "general", job_id: str | None = None):
    global _sequence
    level = level.upper()
    if level not in {"INFO", "SUCCESS", "WARNING", "ERROR"}:
        level = "INFO"
    with _lock:
        _sequence += 1
        event = {"id": _sequence, "timestamp": datetime.now(timezone.utc).isoformat(),
                 "level": level, "message": str(message), "source": source, "job_id": job_id}
        _events.append(event)
    return event


@router.post("/logs")
def add_log(payload: LogInput):
    return publish(payload.message, payload.level, payload.source)


@router.get("/logs")
def get_logs(after_id: int = 0):
    with _lock:
        return {"messages": [dict(e) for e in _events if e["id"] > after_id]}


def _allowed_path(path: str) -> str:
    root = os.getenv("ESP32_PROJECTS_ROOT")
    if not root:
        raise HTTPException(503, "Configura ESP32_PROJECTS_ROOT en el backend")
    base = Path(root).resolve()
    candidate = Path(path).resolve()
    if not candidate.is_relative_to(base) or not candidate.is_dir():
        raise HTTPException(400, "Ruta inválida o fuera del directorio autorizado")
    return str(candidate)


def _run_job(job_id: str, project_path: str):
    with _lock:
        _jobs[job_id]["status"] = "running"

    def send(message, level="INFO"):
        return publish(message, level, "sketch", job_id)

    try:
        send("Iniciando compilación ESP-IDF")
        result = _adapter(project_path, send)
        if not isinstance(result, dict) or not isinstance(result.get("success"), bool):
            raise ValueError("Sketch debe devolver {'success': bool, 'errors': [], 'artifacts': [], 'exit_code': int}")
        normalized = {"success": result["success"], "errors": result.get("errors", []),
                      "artifacts": result.get("artifacts", []), "exit_code": result.get("exit_code")}
        with _lock:
            _jobs[job_id].update(status="completed" if normalized["success"] else "failed", result=normalized)
        send("Compilación exitosa" if normalized["success"] else "Compilación fallida",
             "SUCCESS" if normalized["success"] else "ERROR")
    except Exception as exc:
        with _lock:
            _jobs[job_id].update(status="failed", result={"success": False, "errors": [str(exc)],
                                                        "artifacts": [], "exit_code": None})
        send(f"Error de compilación: {exc}", "ERROR")


@router.post("/compile", status_code=202)
def start_compile(payload: CompileInput):
    if _adapter is None:
        raise HTTPException(503, "El backend Sketch aún no está conectado")
    path = _allowed_path(payload.project_path)
    job_id = uuid4().hex
    with _lock:
        _jobs[job_id] = {"job_id": job_id, "status": "queued", "result": None}
    _executor.submit(_run_job, job_id, path)
    return {"job_id": job_id, "status": "queued"}


@router.get("/compile/{job_id}")
def compile_status(job_id: str):
    with _lock:
        if job_id not in _jobs:
            raise HTTPException(404, "Trabajo no encontrado")
        return dict(_jobs[job_id])


def registrar(app: FastAPI, compile_adapter=None):
    """Llamar una vez desde el registrador central; adapter(path, publish) -> dict."""
    global _adapter
    _adapter = compile_adapter
    app.include_router(router)
