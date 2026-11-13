"""Modelos de entrada y salida del modulo Sketch."""

from typing import Literal

from pydantic import BaseModel, Field


class SolicitudCompilacion(BaseModel):
    """Datos necesarios para iniciar una compilacion ESP-IDF."""

    project_path: str = Field(min_length=1)
    timeout: int = Field(default=1800, gt=0)
    target: str | None = None


class RespuestaTarea(BaseModel):
    """Estado de una tarea de compilacion."""

    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    result: dict | None = None
    error: str | None = None
