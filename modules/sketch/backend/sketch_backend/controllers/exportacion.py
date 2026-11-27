"""Operaciones de exportacion de binarios ESP-IDF."""

from pathlib import Path

from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sketch_backend.controllers.compilacion import obtener_tarea


def exportar_binario(task_id: str, nombre_archivo: str) -> FileResponse:
    """Devuelve un binario generado por una tarea de compilacion."""

    tarea = obtener_tarea(task_id)

    if tarea is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe la tarea de compilacion.",
        )

    if tarea.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La compilacion no ha finalizado correctamente.",
        )

    resultado = tarea.get("result") or {}

    if not resultado.get("success"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La compilacion no fue exitosa.",
        )

    binarios = resultado.get("bin_files") or []

    archivo_solicitado = Path(nombre_archivo).name

    coincidencias = [
        Path(ruta) for ruta in binarios if Path(ruta).name == archivo_solicitado
    ]

    if len(coincidencias) != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontro un binario con ese nombre.",
        )

    archivo = coincidencias[0].resolve()

    if not archivo.is_file() or archivo.suffix.lower() != ".bin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo binario ya no esta disponible.",
        )

    return FileResponse(
        path=archivo,
        media_type="application/octet-stream",
        filename=archivo.name,
    )
