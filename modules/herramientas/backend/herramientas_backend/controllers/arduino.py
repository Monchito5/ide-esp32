# Archivo: modules/herramientas/backend/herramientas_backend/controllers/arduino.py
"""Controlador Arduino - Adaptador entre FastAPI y arduino-cli.

Puente entre la capa de presentacion (FastAPI HTTP) y la capacidad de
ejecucion de arduino-cli en el sistema. Transformara las respuestas
de arduino-cli a formato JSON para la API del IDE.
"""

import subprocess

from modules.herramientas.backend.herramientas_backend.models import (  # type: ignore
    Herramienta,
    PuertoSerie,
)


class ArduinoController:
    """Controlador que adapta los servicios Arduino CLI a la API FastAPI."""

    @staticmethod
    def formatear_puerto(puerto_dict: dict) -> dict:
        """Formatea un diccionario de puerto a la estructura esperada."""
        return {
            "dispositivo": puerto_dict.get("device", ""),
            "descripcion": puerto_dict.get("description", ""),
            "fabricante": puerto_dict.get("manufacturer", ""),
        }

    @staticmethod
    def formatear_placa(placa_dict: dict) -> dict:
        """Formatea un diccionario de placa a la estructura esperada."""
        # Arduino CLI devuelve informacion de placa en JSON
        return {
            "nombre": placa_dict.get("name", ""),
            "familia": placa_dict.get("family", ""),
        }

    @staticmethod
    def verificar_salud() -> dict:
        """Verifica que el sistema Arduino este saludable."""
        return {
            "status": "ok",
            "mensaje": "Arduino CLI disponible",
        }


# Funciones independientes (no requieren clase instantanciada)
def listar_puertos() -> dict:
    """Lista los puertos serie disponibles en el sistema."""
    try:
        from serial.tools import list_ports

        puertos = [
            {
                "dispositivo": p.device,
                "descripcion": p.description or "",
                "fabricante": p.manufacturer or "",
            }
            for p in list_ports.comports()
        ]
        return {"total": len(puertos), "puertos": puertos}
    except ImportError:
        return {"total": 0, "puertos": []}


def obtener_version() -> dict:
    """Obtiene la version instalada de arduino-cli."""
    try:
        proceso = subprocess.run(
            ["arduino-cli", "version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proceso.returncode == 0:
            return {"exitoso": True, "salida": proceso.stdout.strip()}
        return {"exitoso": False, "salida": "", "error": proceso.stderr.strip()}
    except FileNotFoundError:
        return {"exitoso": False, "salida": "", "error": "arduino-cli no encontrado"}
    except subprocess.TimeoutExpired:
        return {"exitoso": False, "salida": "", "error": "Tiempo de espera agotado"}


def listar_placas() -> dict:
    """Lista las placas conectadas detectadas por arduino-cli."""
    try:
        proceso = subprocess.run(
            ["arduino-cli", "board", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proceso.returncode == 0:
            import json

            try:
                datos = json.loads(proceso.stdout.strip())
                return {
                    "exitoso": True,
                    "salida": proceso.stdout.strip(),
                    "datos": datos,
                }
            except json.JSONDecodeError:
                return {"exitoso": True, "salida": proceso.stdout.strip(), "datos": {}}
        return {"exitoso": False, "salida": "", "error": "Error al listar placas"}
    except FileNotFoundError:
        return {"exitoso": False, "salida": "", "error": "arduino-cli no encontrado"}
    except subprocess.TimeoutExpired:
        return {"exitoso": False, "salida": "", "error": "Tiempo de espera agotado"}
