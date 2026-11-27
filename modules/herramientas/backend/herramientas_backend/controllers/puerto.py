# Archivo: modules/herramientas/backend/herramientas_backend/controllers/puerto.py
"""Controlador de puertos serie con identificacion automatica de placas ESP32."""

try:
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    list_ports = None

from herramientas_backend.controllers.placa import identificar_placa_por_usb
from herramientas_backend.models import Puerto


def listar_puertos() -> dict:
    """Lista los puertos serie disponibles enriquecidos con metadatos Espressif."""
    if list_ports is None:
        return {"total": 0, "puertos": []}

    puertos = []
    for p in list_ports.comports():
        base = Puerto(
            dispositivo=p.device,
            descripcion=p.description or "",
            fabricante=p.manufacturer or "",
            vid=p.vid,
            pid=p.pid,
        ).a_dict()
        info_esp = identificar_placa_por_usb(
            vid=p.vid,
            pid=p.pid,
            descripcion=base["descripcion"],
            fabricante=base["fabricante"],
        )
        base.update(
            {
                "es_esp32": info_esp["es_esp32"],
                "placa_sugerida": info_esp["placa"],
                "chip": info_esp["chip"],
                "target_idf": info_esp["target_idf"],
                "confianza": info_esp["confianza"],
                "tipo_conexion": info_esp["tipo_conexion"],
            }
        )
        puertos.append(base)

    return {"total": len(puertos), "puertos": puertos}
