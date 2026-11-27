# Archivo: modules/simulacion/backend/simulacion_backend/controllers/websocket.py
"""Controlador WebSocket para streaming de eventos de sesion."""

import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from simulacion_backend.application.simulacion_service import SimulacionService

service = SimulacionService()
logger = logging.getLogger(__name__)


async def websocket_sesion(websocket: WebSocket, sesion_id: str) -> None:
    """Maneja el WebSocket de streaming para una sesion de simulacion."""
    await websocket.accept()

    try:
        sesion = service.obtener_sesion(sesion_id)
        if not sesion:
            await websocket.close(code=4004, reason="Sesion no encontrada")
            return

        await service.conectar_websocket(sesion_id, websocket)

        try:
            while True:
                data = await websocket.receive_text()
                mensaje = json.loads(data)

                if mensaje.get("tipo") == "ping":
                    await websocket.send_json({"tipo": "pong", "sesion_id": sesion_id})
                elif mensaje.get("tipo") == "obtener_estado":
                    estado = service.obtener_estado_sesion(sesion_id)
                    await websocket.send_json({"tipo": "estado", "datos": estado})
                else:
                    await websocket.send_json(
                        {"tipo": "error", "mensaje": "Tipo de mensaje no reconocido"}
                    )

        except WebSocketDisconnect:
            logger.info("WebSocket desconectado para sesion %s", sesion_id)
        finally:
            await service.desconectar_websocket(sesion_id, websocket)

    except Exception as exc:
        logger.exception("Error en WebSocket de sesion %s: %s", sesion_id, exc)
        try:
            await websocket.close(code=4000, reason=str(exc))
        except Exception:
            pass
