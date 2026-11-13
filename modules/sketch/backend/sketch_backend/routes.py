"""Rutas HTTP del modulo Sketch."""

from fastapi import APIRouter, HTTPException, status

from ide_core.config.constants import PREFIJO_API
from sketch_backend.controllers.compilacion import (
    iniciar_compilacion,
    obtener_resumen,
    obtener_tarea,
)
from sketch_backend.models import RespuestaTarea, SolicitudCompilacion

router = APIRouter(prefix=f"{PREFIJO_API}/sketch", tags=["sketch"])


@router.post(
    "/compilar",
    response_model=RespuestaTarea,
    status_code=status.HTTP_202_ACCEPTED,
)
def compilar(solicitud: SolicitudCompilacion) -> dict:
    """Inicia una compilacion ESP-IDF en segundo plano."""
    return iniciar_compilacion(solicitud.model_dump())


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
