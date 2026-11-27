# Archivo: modules/simulacion/backend/simulacion_backend/infrastructure/esp_emulator.py
"""Adaptador para el emulador ESP Emulator de Espressif."""

import subprocess
from typing import Any, Dict, List, Optional


class ESPEmulatorAdapter:
    """Adaptador para el emulador ESP Emulator."""

    def __init__(self, ruta_emulador: Optional[str] = None) -> None:
        self.ruta_emulador = ruta_emulador

    def esta_disponible(self) -> bool:
        """Verifica si el emulador ESP Emulator esta disponible en el sistema."""
        try:
            resultado = subprocess.run(
                ["esptool.py", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return resultado.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def obtener_version(self) -> Optional[str]:
        """Obtiene la version del emulador ESP Emulator instalado."""
        try:
            resultado = subprocess.run(
                ["esptool.py", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if resultado.returncode == 0:
                return resultado.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    def ejecutar_comando(self, comando: List[str], tiempo_espera: int = 30) -> Dict[str, Any]:
        """Ejecuta un comando del emulador ESP de forma segura."""
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

    def flashear_firmware(
        self,
        puerto: str,
        archivo_bin: str,
        direccion: str = "0x10000",
        velocidad: int = 115200,
    ) -> Dict[str, Any]:
        """Flashea un firmware binario usando esptool.py."""
        comando = [
            "esptool.py",
            "--port", puerto,
            "--baud", str(velocidad),
            "write_flash",
            "-z",
            direccion,
            archivo_bin,
        ]
        return self.ejecutar_comando(comando)

    def borrar_flash(self, puerto: str, velocidad: int = 115200) -> Dict[str, Any]:
        """Borra todo el flash del dispositivo ESP32."""
        comando = [
            "esptool.py",
            "--port", puerto,
            "--baud", str(velocidad),
            "erase_flash",
        ]
        return self.ejecutar_comando(comando)

    def obtener_info_chip(self, puerto: str, velocidad: int = 115200) -> Dict[str, Any]:
        """Obtiene informacion del chip ESP32 conectado."""
        comando = [
            "esptool.py",
            "--port", puerto,
            "--baud", str(velocidad),
            "chip_id",
        ]
        return self.ejecutar_comando(comando)
