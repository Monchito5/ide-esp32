# Archivo: modules/herramientas/backend/herramientas_backend/models/puerto.py
"""Modelo del puerto serie."""

from dataclasses import asdict, dataclass

from ide_core.models.base import ejecutar, ejecutar_mutacion


@dataclass
class Puerto:
    """Representacion de un puerto serie."""

    dispositivo: str
    descripcion: str = ""
    fabricante: str = ""
    vid: int | None = None
    pid: int | None = None

    def a_dict(self) -> dict:
        """Convierte el objeto a diccionario."""
        return asdict(self)


def guardar_dispositivo(nombre: str, puerto: str, velocidad: int, placa: str) -> int:
    """Guarda un dispositivo en la base de datos."""
    return ejecutar_mutacion(
        "INSERT OR REPLACE INTO herramientas_dispositivos "
        "(nombre, puerto, velocidad, placa) VALUES (?, ?, ?, ?)",
        (nombre, puerto, velocidad, placa),
    )


def listar_dispositivos() -> list[dict]:
    """Lista todos los dispositivos guardados."""
    return ejecutar(
        "SELECT * FROM herramientas_dispositivos ORDER BY fecha_creacion DESC"
    )
