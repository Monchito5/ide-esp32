# Archivo: modules/herramientas/backend/herramientas_backend/controllers/puerto.py
"""Controlador de puertos serie."""

try:
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    list_ports = None

from modules.herramientas.backend.herramientas_backend.models import Puerto


def listar_puertos() -> dict:
    """Lista los puertos serie disponibles en el sistema."""
    if list_ports is None:
        return {"total": 0, "puertos": []}

    puertos = [
        Puerto(
            dispositivo=p.device,
            descripcion=p.description or "",
            fabricante=p.manufacturer or "",
            vid=p.vid,
            pid=p.pid,
        ).a_dict()
        for p in list_ports.comports()
    ]
    return {"total": len(puertos), "puertos": puertos}
