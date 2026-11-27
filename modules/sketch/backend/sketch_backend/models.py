"""Modelos de entrada y salida del modulo Sketch (compilacion nativa ESP-IDF)."""

from typing import Literal

from pydantic import BaseModel, Field


class SolicitudCompilacion(BaseModel):
    """Datos necesarios para iniciar una compilacion ESP-IDF sobre ruta existente."""

    project_path: str = Field(min_length=1)
    timeout: int = Field(default=1800, gt=0)
    target: str | None = None


class SolicitudCompilacionCodigo(BaseModel):
    """Datos para estructurar y compilar codigo fuente directamente con ESP-IDF."""

    codigo: str = Field(min_length=1)
    nombre_proyecto: str = Field(default="esp32_sketch", min_length=1)
    nombre_archivo: str = Field(default="main.c", min_length=1)
    target: str = Field(default="esp32s3", min_length=1)
    timeout: int = Field(default=600, gt=0)
    incluir_base64: bool = False


class RespuestaTarea(BaseModel):
    """Estado de una tarea de compilacion."""

    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    result: dict | None = None
    error: str | None = None
