# Archivo: modules/simulacion/backend/simulacion_backend/infrastructure/process.py
"""Administracion segura de procesos para el modulo de simulacion."""

import subprocess
from typing import Any, Dict, List, Optional


def ejecutar_seguro(
    comando: List[str],
    tiempo_espera: int = 30,
    directorio_trabajo: Optional[str] = None,
    variables_entorno: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Ejecuta un comando externo de forma segura."""
    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=tiempo_espera,
            cwd=directorio_trabajo,
            env=variables_entorno,
        )
        return {
            "exitoso": resultado.returncode == 0,
            "salida_estandar": resultado.stdout,
            "salida_error": resultado.stderr,
            "codigo_retorno": resultado.returncode,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "exitoso": False,
            "salida_estandar": exc.stdout or "",
            "salida_error": f"Tiempo de espera agotado ({tiempo_espera}s): {exc.stderr or ''}",
            "codigo_retorno": -1,
        }
    except FileNotFoundError as exc:
        return {
            "exitoso": False,
            "salida_estandar": "",
            "salida_error": f"Comando no encontrado: {exc}",
            "codigo_retorno": -1,
        }
    except Exception as exc:
        return {
            "exitoso": False,
            "salida_estandar": "",
            "salida_error": f"Error inesperado: {exc}",
            "codigo_retorno": -1,
        }


def validar_ruta_archivo(ruta: str) -> bool:
    """Valida que una ruta de archivo sea segura para procesar."""
    import os

    if ruta.startswith("/") or ".." in ruta:
        return False
    extensiones_validas = (".bin", ".elf", ".hex")
    return ruta.lower().endswith(extensiones_validas)
