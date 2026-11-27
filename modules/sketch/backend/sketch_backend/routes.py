"""Rutas HTTP del modulo Sketch (compilacion nativa Espressif ESP-IDF)."""

from fastapi import APIRouter, HTTPException, status
from sketch_backend.controllers.compilacion import (
    compilar_codigo_fuente,
    iniciar_compilacion,
    obtener_resumen,
    obtener_tarea,
)
from sketch_backend.models import (
    RespuestaTarea,
    SolicitudCompilacion,
    SolicitudCompilacionCodigo,
)

from ide_core.config.constants import PREFIJO_API

router = APIRouter(prefix=f"{PREFIJO_API}/sketch", tags=["sketch"])


@router.post(
    "/compilar",
    response_model=RespuestaTarea,
    status_code=status.HTTP_202_ACCEPTED,
)
def compilar(solicitud: SolicitudCompilacion) -> dict:
    """Inicia una compilacion ESP-IDF en segundo plano sobre un directorio existente."""
    return iniciar_compilacion(solicitud.model_dump())


@router.post("/compilar-codigo")
def compilar_codigo(solicitud: SolicitudCompilacionCodigo) -> dict:
    """Estructura el codigo fuente en formato CMake ESP-IDF, compila y retorna binarios .bin."""
    return compilar_codigo_fuente(solicitud.model_dump())


@router.get("/tareas/{task_id}", response_model=RespuestaTarea)
def consultar_tarea(task_id: str) -> dict:
    """Consulta el estado y resultado de una compilacion."""
    tarea = obtener_tarea(task_id)

    if tarea is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe una tarea con ese identificador.",
        )

    return tarea


@router.get("/estado")
def estado() -> dict:
    """Consulta el estado general del modulo Sketch."""
    return obtener_resumen()
