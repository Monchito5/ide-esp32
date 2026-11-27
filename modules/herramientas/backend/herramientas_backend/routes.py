# Archivo: modules/herramientas/backend/herramientas_backend/routes.py
"""Rutas del modulo Herramientas (ecosistema nativo Espressif ESP-IDF, Particiones, SSL NVS y esptool)."""

from fastapi import APIRouter
from herramientas_backend.controllers.arduino import (
    listar_placas,
    obtener_version,
)
from herramientas_backend.controllers.certificados import (
    generar_particion_nvs_certificados,
)
from herramientas_backend.controllers.esp_idf import (
    estado_esp_idf,
    get_esp_idf_version,
    get_sdkconfig,
    menuconfig,
)
from herramientas_backend.controllers.esptool_service import (
    flashear_bootloader,
    flashear_completo,
    listar_historial_flash,
    verificar_flash,
)
from herramientas_backend.controllers.monitor_serie import (
    conectar_monitor_serie,
    desconectar_monitor_serie,
    enviar_monitor_serie,
    estado_monitor_serie,
    exportar_logs_herramientas,
    limpiar_monitor_serie,
    listar_eventos_monitor_serie,
    monitor_serie_ws,
    obtener_muestras_plotter_endpoint,
    parsear_lote_plotter,
)
from herramientas_backend.controllers.particiones import (
    generar_tabla_particiones,
    listar_plantillas_particiones,
    parsear_binario_particiones,
)
from herramientas_backend.controllers.placa import (
    detectar_placas_conectadas,
    listar_placas_soportadas,
)
from herramientas_backend.controllers.platformio import (
    platformio_compilar,
    platformio_estado,
    platformio_flashear,
    platformio_iniciar,
    platformio_puertos_disponibles,
)
from herramientas_backend.controllers.puerto import listar_puertos
from herramientas_backend.controllers.report import resumen_flash

from ide_core.config.constants import PREFIJO_API

router = APIRouter(prefix=f"{PREFIJO_API}/herramientas", tags=["herramientas"])

# Sprint 3: Deteccion nativa Espressif (USB VID/PID + esptool) y catalogo ESP-IDF
router.add_api_route("/puertos", listar_puertos, methods=["GET"])
router.add_api_route("/placas-soportadas", listar_placas_soportadas, methods=["GET"])
router.add_api_route("/detectar-placa", detectar_placas_conectadas, methods=["GET"])

# Toolchain principal: Espressif ESP-IDF
router.add_api_route("/esp-idf/estado", estado_esp_idf, methods=["GET"])
router.add_api_route("/esp-idf/version", get_esp_idf_version, methods=["GET"])
router.add_api_route("/esp-idf/sdkconfig", get_sdkconfig, methods=["GET"])
router.add_api_route("/esp-idf/menuconfig", menuconfig, methods=["GET"])

# Sprint 4: Bootloader, Tablas de Particiones, Certificados SSL (NVS) y Flasheo Completo (esptool)
router.add_api_route(
    "/particiones/plantillas", listar_plantillas_particiones, methods=["GET"]
)
router.add_api_route(
    "/particiones/generar", generar_tabla_particiones, methods=["POST"]
)
router.add_api_route(
    "/particiones/parsear", parsear_binario_particiones, methods=["POST"]
)
router.add_api_route(
    "/certificados/generar-nvs", generar_particion_nvs_certificados, methods=["POST"]
)
router.add_api_route("/esptool/bootloader", flashear_bootloader, methods=["POST"])
router.add_api_route("/esptool/flash-completo", flashear_completo, methods=["POST"])
router.add_api_route("/esptool/verificar-flash", verificar_flash, methods=["POST"])
router.add_api_route("/historial-flash", listar_historial_flash, methods=["GET"])

# Reportes de flasheo
router.add_api_route("/reportes/flash", resumen_flash, methods=["GET"])

# Sprint 5: Monitor Serie bidireccional, Plotter Serie multicanal y Exportacion de Logs
router.add_api_route(
    "/monitor-serie/conectar", conectar_monitor_serie, methods=["POST"]
)
router.add_api_route(
    "/monitor-serie/desconectar", desconectar_monitor_serie, methods=["POST"]
)
router.add_api_route("/monitor-serie/estado", estado_monitor_serie, methods=["GET"])
router.add_api_route("/monitor-serie/enviar", enviar_monitor_serie, methods=["POST"])
router.add_api_route(
    "/monitor-serie/eventos", listar_eventos_monitor_serie, methods=["GET"]
)
router.add_api_route("/monitor-serie/limpiar", limpiar_monitor_serie, methods=["POST"])
router.add_api_websocket_route("/monitor-serie/stream", monitor_serie_ws)
router.add_api_route("/plotter/parsear", parsear_lote_plotter, methods=["POST"])
router.add_api_route(
    "/plotter/muestras", obtener_muestras_plotter_endpoint, methods=["GET"]
)
router.add_api_route("/logs/exportar", exportar_logs_herramientas, methods=["GET"])

# Adaptadores secundarios opcionales (PlatformIO / Arduino CLI)
router.add_api_route("/arduino/version", obtener_version, methods=["GET"])
router.add_api_route("/arduino/placas", listar_placas, methods=["GET"])
router.add_api_route("/platformio/estado", platformio_estado, methods=["GET"])
router.add_api_route("/platformio/iniciar", platformio_iniciar, methods=["POST"])
router.add_api_route("/platformio/compilar", platformio_compilar, methods=["POST"])
router.add_api_route("/platformio/flashear", platformio_flashear, methods=["POST"])
router.add_api_route(
    "/platformio/puertos-disponibles", platformio_puertos_disponibles, methods=["GET"]
)
