# Archivo: modules/simulacion/backend/simulacion_backend/routes.py
"""Rutas del modulo Simulacion."""

from fastapi import APIRouter

from simulacion_backend.controllers.sesiones import (
    crear_sesion,
    detener_sesion,
    obtener_sesion,
    listar_sesiones,
    reiniciar_sesion,
    iniciar_sesion,
    flashear_sesion,
    enviar_comando_sesion,
    agregar_componente_sesion,
    obtener_reporte_sesion,
)
from simulacion_backend.controllers.motores import listar_motores, listar_chips
from simulacion_backend.controllers.websocket import websocket_sesion

from ide_core.config.constants import PREFIJO_API

router = APIRouter(prefix=f"{PREFIJO_API}/simulacion", tags=["simulacion"])

# Motores y chips
router.add_api_route("/motores", listar_motores, methods=["GET"])
router.add_api_route("/chips", listar_chips, methods=["GET"])

# Sesiones
router.add_api_route("/sesiones", listar_sesiones, methods=["GET"])
router.add_api_route("/sesiones", crear_sesion, methods=["POST"])
router.add_api_route("/sesiones/{sesion_id}", obtener_sesion, methods=["GET"])
router.add_api_route("/sesiones/{sesion_id}/iniciar", iniciar_sesion, methods=["POST"])
router.add_api_route("/sesiones/{sesion_id}/detener", detener_sesion, methods=["POST"])
router.add_api_route("/sesiones/{sesion_id}/reiniciar", reiniciar_sesion, methods=["POST"])
router.add_api_route("/sesiones/{sesion_id}/flashear", flashear_sesion, methods=["POST"])
router.add_api_route(
    "/sesiones/{sesion_id}/comandos", enviar_comando_sesion, methods=["POST"]
)
router.add_api_route(
    "/sesiones/{sesion_id}/componentes", agregar_componente_sesion, methods=["POST"]
)
router.add_api_route(
    "/sesiones/{sesion_id}/reportes", obtener_reporte_sesion, methods=["GET"]
)

# WebSocket para streaming de eventos
router.add_websocket_route(
    "/sesiones/{sesion_id}/stream", websocket_sesion
)
