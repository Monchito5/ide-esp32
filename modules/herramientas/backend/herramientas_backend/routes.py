# Archivo: modules/herramientas/backend/herramientas_backend/routes.py
"""Rutas del modulo Herramientas."""

from fastapi import APIRouter
from modules.herramientas.backend.herramientas_backend.controllers.arduino import (
    listar_placas,
    obtener_version,
)
from modules.herramientas.backend.herramientas_backend.controllers.esp_idf import (
    get_esp_idf_version,
    get_sdkconfig,
    menuconfig,
)
from modules.herramientas.backend.herramientas_backend.controllers.platformio import (
    platformio_compilar,
    platformio_estado,
    platformio_flashear,
    platformio_iniciar,
    platformio_puertos_disponibles,
)
from modules.herramientas.backend.herramientas_backend.controllers.puerto import (
    listar_puertos,
)
from modules.herramientas.backend.herramientas_backend.controllers.report import (
    resumen_flash,
)

from ide_core.config.constants import PREFIJO_API

router = APIRouter(prefix=f"{PREFIJO_API}/herramientas", tags=["herramientas"])

router.add_api_route("/puertos", listar_puertos, methods=["GET"])
router.add_api_route("/arduino/version", obtener_version, methods=["GET"])
router.add_api_route("/arduino/placas", listar_placas, methods=["GET"])
router.add_api_route("/reportes/flash", resumen_flash, methods=["GET"])
router.add_api_route("/esp-idf/version", get_esp_idf_version, methods=["GET"])
router.add_api_route("/esp-idf/sdkconfig", get_sdkconfig, methods=["GET"])
router.add_api_route("/esp-idf/menuconfig", menuconfig, methods=["GET"])
router.add_api_route("/platformio/estado", platformio_estado, methods=["GET"])
router.add_api_route("/platformio/iniciar", platformio_iniciar, methods=["POST"])
router.add_api_route("/platformio/compilar", platformio_compilar, methods=["POST"])
router.add_api_route("/platformio/flashear", platformio_flashear, methods=["POST"])
router.add_api_route(
    "/platformio/puertos-disponibles", platformio_puertos_disponibles, methods=["GET"]
)
