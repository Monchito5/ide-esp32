# Archivo: modules/simulacion/backend/simulacion_backend/controllers/sesiones.py
"""Controladores de sesiones de simulacion."""

from fastapi import HTTPException

from simulacion_backend.application.simulacion_service import SimulacionService

service = SimulacionService()


def listar_sesiones() -> dict:
    """Lista todas las sesiones de simulacion activas e inactivas."""
    return {"sesiones": service.listar_sesiones()}


def crear_sesion(sesion_data: dict) -> dict:
    """Crea una nueva sesion de simulacion."""
    try:
        return service.crear_sesion(sesion_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def obtener_sesion(sesion_id: str) -> dict:
    """Obtiene el estado de una sesion de simulacion."""
    sesion = service.obtener_sesion(sesion_id)
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")
    return sesion


def iniciar_sesion(sesion_id: str) -> dict:
    """Inicia la simulacion de una sesion."""
    try:
        return service.iniciar_sesion(sesion_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except KeyError:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")


def detener_sesion(sesion_id: str) -> dict:
    """Detiene la simulacion de una sesion."""
    try:
        return service.detener_sesion(sesion_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except KeyError:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")


def reiniciar_sesion(sesion_id: str) -> dict:
    """Reinicia la simulacion de una sesion."""
    try:
        return service.reiniciar_sesion(sesion_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except KeyError:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")


def flashear_sesion(sesion_id: str, flasheo_data: dict) -> dict:
    """Flashea firmware en una sesion de simulacion."""
    try:
        return service.flashear_sesion(sesion_id, flasheo_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except KeyError:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")


def enviar_comando_sesion(sesion_id: str, comando_data: dict) -> dict:
    """Envia un comando UART a una sesion de simulacion."""
    try:
        return service.enviar_comando(sesion_id, comando_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except KeyError:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")


def agregar_componente_sesion(sesion_id: str, componente_data: dict) -> dict:
    """Agrega un componente virtual a una sesion de simulacion."""
    try:
        return service.agregar_componente(sesion_id, componente_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except KeyError:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")


def obtener_reporte_sesion(sesion_id: str) -> dict:
    """Obtiene el reporte de una sesion de simulacion."""
    try:
        return service.obtener_reporte(sesion_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except KeyError:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")
