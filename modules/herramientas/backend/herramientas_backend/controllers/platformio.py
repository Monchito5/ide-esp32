# Archivo: modules/herramientas/backend/herramientas_backend/controllers/platformio.py
"""Controlador PlatformIO para el modulo Herramientas."""

import json
import os
import subprocess

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/herramientas", tags=["herramientas"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # ide-esp32 root


def _ejecutar_platillo(comando: list, workdir: str = None) -> dict:
    """Ejecuta un comando platformio y retorna el resultado."""
    if workdir is None:
        workdir = PROJECT_ROOT
    try:
        result = subprocess.run(
            ["platformio"] + comando,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=workdir,
        )
        return {
            "salida": result.stdout.strip(),
            "error": result.stderr.strip() if result.stderr else "",
            "exitoso": result.returncode == 0,
        }
    except FileNotFoundError:
        return {
            "salida": "",
            "error": "platformio no encontrado. Instala con: pip install platformio",
            "exitoso": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "salida": "",
            "error": "Tiempo de espera agotado (120s).",
            "exitoso": False,
        }


@router.get("/platformio/estado", summary="Estado de PlatformIO")
def platformio_estado() -> dict:
    """Verifica si PlatformIO esta instalado y configurado."""
    result = _ejecutar_platillo(["version"])
    if result["exitoso"]:
        return {"version": result["salida"], "exitoso": True}
    return {"version": "", "exitoso": False, "error": result["error"]}


@router.post("/platformio/iniciar", summary="Inicializar proyecto PlatformIO")
def platformio_iniciar() -> dict:
    """Inicializa un proyecto PlatformIO en el directorio actual."""
    result = _ejecutar_platillo(["init"])
    # Buscar o crear platformio.ini
    platformio_ini_path = os.path.join(
        workdir if workdir else PROJECT_ROOT, "platformio.ini"
    )
    if not os.path.exists(platformio_ini_path):
        # Crear platformio.ini basico
        with open(platformio_ini_path, "w") as f:
            f.write("[env]\n")
            f.write("platform = espressif32\n")
            f.write("board = esp32dev\n")
            f.write("framework = arduino\n")
        result["archivo_creado"] = platformio_ini_path
    return result


@router.post("/platformio/compilar", summary="Compilar proyecto")
def platformio_compilar() -> dict:
    """Compila el proyecto PlatformIO."""
    return _ejecutar_platillo(["run"])


@router.post("/platformio/flashear", summary="Flash firmware")
def platformio_flashear(puertos: str = None) -> dict:
    """Flashea el firmware al puerto especificado."""
    if puertos:
        return _ejecutar_platillo(["run", "--target", "upload", "--port", puertos])
    return _ejecutar_platillo(["run", "--target", "upload"])


@router.get("/platformio/puertos-disponibles", summary="Puertos disponibles")
def platformio_puertos_disponibles() -> dict:
    """Lista los puertos serie disponibles."""
    try:
        result = subprocess.run(
            ["platformio", "device", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "puertos": (
                result.stdout.strip()
                if result.returncode == 0
                else result.stderr.strip()
            ),
            "exitoso": result.returncode == 0,
        }
    except Exception as e:
        return {"puertos": str(e), "exitoso": False}
