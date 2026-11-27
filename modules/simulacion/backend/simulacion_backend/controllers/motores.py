# Archivo: modules/simulacion/backend/simulacion_backend/controllers/motores.py
"""Controladores de motores y chips de simulacion."""

from simulacion_backend.application.simulacion_service import SimulacionService

service = SimulacionService()


def listar_motores() -> dict:
    """Lista los motores de simulacion disponibles."""
    return {"motores": service.listar_motores()}


def listar_chips() -> dict:
    """Lista los chips ESP32 soportados para simulacion."""
    return {"chips": service.listar_chips()}
