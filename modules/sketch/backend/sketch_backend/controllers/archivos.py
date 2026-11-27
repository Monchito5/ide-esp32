"""Operaciones de exploracion de archivos del modulo Sketch."""

from pathlib import Path


DIRECTORIOS_EXCLUIDOS = {
    ".git",
    ".venv",
    "build",
    "__pycache__",
}


def listar_archivos(ruta_proyecto: str) -> dict:
    """Lista los directorios y archivos de un proyecto ESP-IDF."""

    proyecto = Path(ruta_proyecto).expanduser().resolve()

    if not proyecto.is_dir():
        raise ValueError(
            f"No existe la carpeta del proyecto: {proyecto}"
        )

    if not (proyecto / "CMakeLists.txt").is_file():
        raise ValueError(
            "La carpeta seleccionada no contiene CMakeLists.txt."
        )

    elementos = []

    for ruta in sorted(proyecto.rglob("*")):
        relativa = ruta.relative_to(proyecto)

        if any(
            parte in DIRECTORIOS_EXCLUIDOS
            for parte in relativa.parts
        ):
            continue

        if ruta.is_dir():
            elementos.append({
                "name": ruta.name,
                "path": str(relativa),
                "type": "directory",
            })
        elif ruta.is_file():
            elementos.append({
                "name": ruta.name,
                "path": str(relativa),
                "type": "file",
                "size": ruta.stat().st_size,
            })

    return {
        "project_path": str(proyecto),
        "total": len(elementos),
        "items": elementos,
    }
