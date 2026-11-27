"""Rutas HTTP del modulo Sketch."""

from fastapi import APIRouter, HTTPException, status

from ide_core.config.constants import PREFIJO_API
from sketch_backend.controllers.archivos import listar_archivos
from sketch_backend.controllers.exportacion import exportar_binario
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


@router.get("/tareas/{task_id}/binarios/{nombre_archivo}")
def descargar_binario(task_id: str, nombre_archivo: str):
    """Descarga un binario generado por una tarea de compilacion."""
    return exportar_binario(task_id, nombre_archivo)


@router.get("/archivos")
def consultar_archivos(project_path: str) -> dict:
    """Lista los archivos y directorios de un proyecto ESP-IDF."""
    try:
        return listar_archivos(project_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/estado")
def estado() -> dict:
    """Consulta el estado general del modulo Sketch."""
    return obtener_resumen()
