# Archivo: modules/herramientas/backend/herramientas_backend/controllers/esp_idf.py
"""Controlador ESP-IDF para el modulo Herramientas."""

import json
import subprocess

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/herramientas", tags=["herramientas"])


def _ejecutar_idf(comando: list, timeout: int = 60) -> dict:
    """Ejecuta un comando idf.py y retorna el resultado."""
    try:
        result = subprocess.run(
            ["idf.py"] + comando,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "salida": result.stdout.strip(),
            "error": result.stderr.strip() if result.stderr else "",
            "exitoso": result.returncode == 0,
        }
    except FileNotFoundError:
        return {
            "salida": "",
            "error": "idf.py no encontrado. Asegurate de tener ESP-IDF en el PATH.",
            "exitoso": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "salida": "",
            "error": "Tiempo de espera agotado.",
            "exitoso": False,
        }


@router.get("/esp-idf/version", summary="Obtener version de ESP-IDF")
def get_esp_idf_version() -> dict:
    """Obtiene la version de ESP-IDF instalada."""
    return _ejecutar_idf(["version"])


@router.get("/esp-idf/sdkconfig", summary="Obtener configuracion SDK")
def get_sdkconfig() -> dict:
    """Obtiene la configuracion actual del SDK."""
    result = _ejecutar_idf(["menuconfig", "--json"])
    try:
        config = json.loads(result["salida"]) if result["exitoso"] else {}
        return {"configuracion": config, "exitoso": result["exitoso"]}
    except json.JSONDecodeError:
        return {"configuracion": {}, "exitoso": False}


@router.get("/esp-idf/menuconfig", summary="Abrir menu de configuracion")
def menuconfig() -> dict:
    """Abre el menu de configuracion interactivo de ESP-IDF."""
    return _ejecutar_idf(["menuconfig"])
