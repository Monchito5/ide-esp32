# Archivo: modules/simulacion/backend/simulacion_backend/infrastructure/qemu.py
"""Adaptador opcional para QEMU de Espressif."""

import subprocess
from typing import Any, Dict, List, Optional


class QEMUAdapter:
    """Adaptador para QEMU de Espressif."""

    def __init__(self, ruta_qemu: Optional[str] = None) -> None:
        self.ruta_qemu = ruta_qemu

    def esta_disponible(self) -> bool:
        """Verifica si QEMU esta disponible en el sistema."""
        try:
            resultado = subprocess.run(
                ["qemu-system-xtensa", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return resultado.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def ejecutar_comando(self, comando: List[str], tiempo_espera: int = 30) -> Dict[str, Any]:
        """Ejecuta un comando de QEMU de forma segura."""
        try:
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=tiempo_espera,
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
                "salida_estandar": "",
                "salida_error": f"Tiempo de espera agotado: {exc}",
                "codigo_retorno": -1,
            }
        except FileNotFoundError as exc:
            return {
                "exitoso": False,
                "salida_estandar": "",
                "salida_error": f"Comando no encontrado: {exc}",
                "codigo_retorno": -1,
            }
