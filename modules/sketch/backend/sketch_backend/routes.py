"""Rutas HTTP del modulo Sketch (compilacion nativa Espressif ESP-IDF, explorador y exportacion)."""

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from sketch_backend.controllers.archivos import listar_archivos
from sketch_backend.controllers.compilacion import (
    compilar_codigo_fuente,
    iniciar_compilacion,
    obtener_resumen,
    obtener_tarea,
)
from sketch_backend.controllers.exportacion import exportar_binario
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


@router.get("/tareas/{task_id}/binarios/{nombre_archivo}")
def descargar_binario_tarea(task_id: str, nombre_archivo: str) -> FileResponse:
    """Exporta un archivo .bin generado por una tarea de compilacion ESP-IDF."""
    return exportar_binario(task_id, nombre_archivo)


@router.get("/archivos")
def explorar_archivos(
    project_path: str = Query(..., description="Ruta del proyecto ESP-IDF"),
) -> dict:
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
