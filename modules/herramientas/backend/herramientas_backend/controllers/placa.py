# Archivo: modules/herramientas/backend/herramientas_backend/controllers/placa.py
"""Controlador de deteccion nativa de placas ESP32 mediante USB Espressif y esptool.

Opera de forma autonoma con metadatos USB (VID/PID oficiales de Espressif y
puentes USB-UART comunes en DevKits) y sondeo opcional con esptool, sin
depender de Arduino CLI.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from typing import Optional

from herramientas_backend.models import Puerto

try:
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    list_ports = None

# VID oficial de Espressif Systems (USB nativo / USB-JTAG-Serial)
VID_ESPRESSIF = 0x303A

# Puentes USB-UART habituales en placas de desarrollo ESP32 oficiales y compatibles
VIDS_PUENTES_UART = {
    0x10C4: "Silicon Labs CP210x",
    0x1A86: "QinHeng CH340/CH343/CH9102",
    0x0403: "FTDI FT232/FT2232",
}

PERFILES_PLACAS_ESP32 = [
    {
        "id": "esp32s3_devkitc_1",
        "nombre": "ESP32-S3 DevKitC-1",
        "target_idf": "esp32s3",
        "chip": "ESP32-S3",
        "arquitectura": "Xtensa dual-core 32-bit LX7",
        "frecuencia_mhz": 240,
        "flash_mb": 8,
        "bootloader_offset": "0x0",
        "partition_offset": "0x8000",
        "app_offset": "0x10000",
    },
    {
        "id": "esp32c3_devkitm_1",
        "nombre": "ESP32-C3 DevKitM-1",
        "target_idf": "esp32c3",
        "chip": "ESP32-C3",
        "arquitectura": "RISC-V single-core 32-bit",
        "frecuencia_mhz": 160,
        "flash_mb": 4,
        "bootloader_offset": "0x0",
        "partition_offset": "0x8000",
        "app_offset": "0x10000",
    },
    {
        "id": "esp32_devkitc_v4",
        "nombre": "ESP32 DevKitC V4",
        "target_idf": "esp32",
        "chip": "ESP32",
        "arquitectura": "Xtensa dual-core 32-bit LX6",
        "frecuencia_mhz": 240,
        "flash_mb": 4,
        "bootloader_offset": "0x1000",
        "partition_offset": "0x8000",
        "app_offset": "0x10000",
    },
    {
        "id": "esp32s2_saola_1",
        "nombre": "ESP32-S2 Saola-1",
        "target_idf": "esp32s2",
        "chip": "ESP32-S2",
        "arquitectura": "Xtensa single-core 32-bit LX7",
        "frecuencia_mhz": 240,
        "flash_mb": 4,
        "bootloader_offset": "0x1000",
        "partition_offset": "0x8000",
        "app_offset": "0x10000",
    },
    {
        "id": "esp32c6_devkitc_1",
        "nombre": "ESP32-C6 DevKitC-1",
        "target_idf": "esp32c6",
        "chip": "ESP32-C6",
        "arquitectura": "RISC-V 32-bit (Wi-Fi 6 / BLE / 802.15.4)",
        "frecuencia_mhz": 160,
        "flash_mb": 8,
        "bootloader_offset": "0x0",
        "partition_offset": "0x8000",
        "app_offset": "0x10000",
    },
]

_MAPA_TARGET_A_PERFIL = {p["target_idf"]: p for p in PERFILES_PLACAS_ESP32}


def listar_placas_soportadas() -> dict:
    """Devuelve el catalogo de perfiles de placas ESP32 compatibles con ESP-IDF."""
    return {
        "total": len(PERFILES_PLACAS_ESP32),
        "placas": [dict(p) for p in PERFILES_PLACAS_ESP32],
    }


def obtener_perfil_por_target(target_idf: str) -> dict:
    """Obtiene el perfil de placa asociado a un target de ESP-IDF."""
    clave = (target_idf or "").strip().lower().replace("-", "")
    return dict(_MAPA_TARGET_A_PERFIL.get(clave, _MAPA_TARGET_A_PERFIL["esp32s3"]))


def _inferir_target_desde_texto(texto: str) -> Optional[str]:
    texto_norm = texto.upper()
    if "ESP32-S3" in texto_norm or "ESP32S3" in texto_norm:
        return "esp32s3"
    if "ESP32-C6" in texto_norm or "ESP32C6" in texto_norm:
        return "esp32c6"
    if "ESP32-C3" in texto_norm or "ESP32C3" in texto_norm:
        return "esp32c3"
    if "ESP32-S2" in texto_norm or "ESP32S2" in texto_norm:
        return "esp32s2"
    if "ESP32" in texto_norm:
        return "esp32"
    return None


def identificar_placa_por_usb(
    vid: Optional[int],
    pid: Optional[int],
    descripcion: str = "",
    fabricante: str = "",
) -> dict:
    """Identifica si un puerto USB corresponde a una placa Espressif ESP32."""
    texto_combinado = f"{descripcion} {fabricante}".strip()
    target_texto = _inferir_target_desde_texto(texto_combinado)

    # 1. USB nativo de Espressif Systems (0x303A)
    if vid == VID_ESPRESSIF:
        if target_texto:
            target = target_texto
        elif pid in (0x0002, 0x0003):
            target = "esp32s2"
        else:
            # 0x1001 corresponde a USB JTAG/Serial nativo (predeterminado S3 en el IDE)
            target = "esp32s3"

        perfil = obtener_perfil_por_target(target)
        return {
            "es_esp32": True,
            "placa": perfil["nombre"],
            "chip": perfil["chip"],
            "target_idf": perfil["target_idf"],
            "confianza": "alta",
            "tipo_conexion": "usb_nativo_espressif",
        }

    # 2. Puentes USB-UART tipicos en DevKits ESP32
    if vid in VIDS_PUENTES_UART:
        target = target_texto or "esp32"
        perfil = obtener_perfil_por_target(target)
        return {
            "es_esp32": True,
            "placa": perfil["nombre"],
            "chip": perfil["chip"],
            "target_idf": perfil["target_idf"],
            "confianza": "alta" if target_texto else "media",
            "tipo_conexion": f"puente_uart ({VIDS_PUENTES_UART[vid]})",
        }

    # 3. Coincidencia explicita por descripcion/fabricante
    if target_texto or "ESPRESSIF" in texto_combinado.upper():
        target = target_texto or "esp32s3"
        perfil = obtener_perfil_por_target(target)
        return {
            "es_esp32": True,
            "placa": perfil["nombre"],
            "chip": perfil["chip"],
            "target_idf": perfil["target_idf"],
            "confianza": "media",
            "tipo_conexion": "descripcion_serie",
        }

    return {
        "es_esp32": False,
        "placa": None,
        "chip": None,
        "target_idf": None,
        "confianza": "ninguna",
        "tipo_conexion": "otro_dispositivo",
    }


def _resolver_comando_esptool() -> Optional[list[str]]:
    """Localiza el ejecutable oficial esptool en el entorno EIM de Espressif o en el sistema."""
    try:
        from herramientas_backend.controllers.esp_idf import localizar_esptool

        ruta_eim = localizar_esptool()
        if ruta_eim:
            return [ruta_eim]
    except ImportError:
        pass

    for binario in ("esptool", "esptool.py"):
        ruta = shutil.which(binario)
        if ruta:
            return [ruta]

    # Verificar si el modulo python esptool esta instalado en el interprete actual
    try:
        verificacion = subprocess.run(
            [sys.executable, "-m", "esptool", "version"],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
        if verificacion.returncode == 0:
            return [sys.executable, "-m", "esptool"]
    except (OSError, subprocess.SubprocessError):
        pass

    return None


def sondear_chip_esptool(puerto: str, timeout: int = 5) -> dict:
    """Interroga fisicamente al bootloader ROM del ESP32 mediante esptool."""
    cmd_base = _resolver_comando_esptool()
    if not cmd_base:
        return {
            "exitoso": False,
            "chip": None,
            "target_idf": None,
            "placa": None,
            "mac": None,
            "salida": "",
            "error": "esptool no encontrado en el entorno.",
        }

    try:
        proceso = subprocess.run(
            cmd_base + ["--port", puerto, "chip_id"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "exitoso": False,
            "chip": None,
            "target_idf": None,
            "placa": None,
            "mac": None,
            "salida": "",
            "error": f"Tiempo agotado al sondear {puerto} con esptool.",
        }
    except OSError as exc:
        return {
            "exitoso": False,
            "chip": None,
            "target_idf": None,
            "placa": None,
            "mac": None,
            "salida": "",
            "error": str(exc),
        }

    salida = f"{proceso.stdout}\n{proceso.stderr}".strip()
    if proceso.returncode != 0:
        return {
            "exitoso": False,
            "chip": None,
            "target_idf": None,
            "placa": None,
            "mac": None,
            "salida": salida,
            "error": proceso.stderr.strip() or "No se pudo leer chip_id con esptool.",
        }

    target = _inferir_target_desde_texto(salida) or "esp32"
    perfil = obtener_perfil_por_target(target)

    mac_match = re.search(r"MAC:\s*([0-9a-fA-F:]{17})", salida)
    mac = mac_match.group(1).upper() if mac_match else None

    chip_match = re.search(r"Chip is\s+([^\r\n]+)", salida)
    chip_detalle = chip_match.group(1).strip() if chip_match else perfil["chip"]

    return {
        "exitoso": True,
        "chip": chip_detalle,
        "target_idf": perfil["target_idf"],
        "placa": perfil["nombre"],
        "mac": mac,
        "salida": salida,
        "error": None,
    }


def detectar_placas_conectadas(
    puerto: Optional[str] = None,
    sondear: bool = False,
) -> dict:
    """Detecta placas ESP32 conectadas usando USB Espressif y opcionalmente esptool."""
    from herramientas_backend.controllers.puerto import listar_puertos

    datos_puertos = listar_puertos()
    todos = datos_puertos.get("puertos", [])

    if puerto:
        todos = [p for p in todos if p.get("dispositivo") == puerto]

    dispositivos_esp32 = []
    for item in todos:
        enriquecido = dict(item)
        if enriquecido.get("es_esp32") and sondear:
            sondeo = sondear_chip_esptool(enriquecido["dispositivo"])
            if sondeo["exitoso"]:
                enriquecido["placa"] = sondeo["placa"]
                enriquecido["placa_sugerida"] = sondeo["placa"]
                enriquecido["chip"] = sondeo["chip"]
                enriquecido["target_idf"] = sondeo["target_idf"]
                enriquecido["mac"] = sondeo["mac"]
                enriquecido["confianza"] = "verificada_esptool"
        if enriquecido.get("es_esp32"):
            dispositivos_esp32.append(enriquecido)

    # Priorizar confianza alta / verificada
    orden_confianza = {"verificada_esptool": 3, "alta": 2, "media": 1}
    dispositivos_esp32.sort(
        key=lambda d: orden_confianza.get(d.get("confianza", ""), 0),
        reverse=True,
    )

    recomendada = dispositivos_esp32[0] if dispositivos_esp32 else None

    return {
        "detectada": recomendada is not None,
        "total_puertos": len(todos),
        "total_esp32": len(dispositivos_esp32),
        "recomendada": recomendada,
        "dispositivos": dispositivos_esp32,
        "herramienta": "espressif_usb_esptool",
    }
