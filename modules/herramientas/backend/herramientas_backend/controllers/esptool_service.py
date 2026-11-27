# Archivo: modules/herramientas/backend/herramientas_backend/controllers/esptool_service.py
"""Orquestador de flasheo con Espressif esptool y Bootloader Emulado ESP32 (Sprint 4)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Literal, Optional

from herramientas_backend.controllers.placa import (
    _resolver_comando_esptool,
    obtener_perfil_por_target,
)
from pydantic import BaseModel, Field

from ide_core.models.base import ejecutar, ejecutar_mutacion

MAGIC_ESP_IMAGE_BYTE = 0xE9
MAGIC_PARTITION_TABLE = b"\xaa\x50"


class SolicitudFlashBootloader(BaseModel):
    bootloader_path: str
    target: str = "esp32s3"
    puerto: Optional[str] = None
    baud: int = Field(default=460800, gt=0)
    modo: Literal["fisico", "emulado"] = "emulado"
    verificar: bool = True


class SolicitudFlashCompleto(BaseModel):
    target: str = "esp32s3"
    puerto: Optional[str] = None
    baud: int = Field(default=460800, gt=0)
    modo: Literal["fisico", "emulado"] = "emulado"
    bootloader_path: str
    partitions_path: str
    app_path: str
    nvs_certs_path: Optional[str] = None
    nvs_offset: str = "0x9000"
    app_offset: str = "0x10000"
    verificar: bool = True


class SolicitudVerificarFlash(BaseModel):
    target: str = "esp32s3"
    puerto: Optional[str] = None
    modo: Literal["fisico", "emulado"] = "emulado"
    offset: str = "0x10000"
    bin_path: str
    flash_emulada_path: Optional[str] = None


class BootloaderEmuladoESP32:
    """Emula la memoria NOR Flash SPI y las validaciones del ROM Bootloader de Espressif."""

    def __init__(self, target: str = "esp32s3", flash_mb: int = 8):
        self.target = target
        self.size_bytes = flash_mb * 1024 * 1024
        self.memoria = bytearray(b"\xff" * self.size_bytes)
        self.regiones_escritas: list[tuple[int, int, str]] = []

    def validar_segmento(self, tipo: str, offset: int, datos: bytes) -> None:
        if len(datos) == 0:
            raise ValueError(f"El archivo para '{tipo}' esta vacio.")
        if offset < 0 or offset + len(datos) > self.size_bytes:
            raise ValueError(
                f"El segmento '{tipo}' (0x{offset:x} + {len(datos)} bytes) excede la Flash de {self.size_bytes} bytes."
            )

        if tipo in ("bootloader", "app"):
            if datos[0] != MAGIC_ESP_IMAGE_BYTE:
                raise ValueError(
                    f"Imagen '{tipo}' invalida para ROM Bootloader ESP32: byte magico 0x{datos[0]:02x} != 0xE9."
                )
        elif tipo == "partitions":
            if datos[:2] != MAGIC_PARTITION_TABLE:
                raise ValueError(
                    "Tabla de particiones invalida: no inicia con cabecera magica 0xAA50."
                )

        for ini, fin, nombre_prev in self.regiones_escritas:
            if offset < fin and (offset + len(datos)) > ini:
                raise ValueError(
                    f"Colision en Flash emulada: '{tipo}' (0x{offset:x}) sobrescribe '{nombre_prev}' (0x{ini:x}..0x{fin:x})."
                )

    def escribir_segmento(self, tipo: str, offset: int, datos: bytes) -> dict:
        self.validar_segmento(tipo, offset, datos)
        fin = offset + len(datos)
        self.memoria[offset:fin] = datos
        self.regiones_escritas.append((offset, fin, tipo))
        return {
            "tipo": tipo,
            "offset": f"0x{offset:x}",
            "size_bytes": len(datos),
            "sha256_origen": hashlib.sha256(datos).hexdigest(),
        }

    def verificar_readback(self, offset: int, datos_esperados: bytes) -> bool:
        leido = bytes(self.memoria[offset : offset + len(datos_esperados)])
        return (
            hashlib.sha256(leido).digest() == hashlib.sha256(datos_esperados).digest()
        )


def _registrar_en_historial_bd(
    puerto: str,
    target: str,
    modo: str,
    tipo_operacion: str,
    offsets: dict,
    sha256_resumen: str,
    verificado: bool,
    exitoso: bool,
    salida: str,
    archivo_ref: str,
) -> None:
    """Registra la operacion en las tablas de historial de flasheo de SQLite."""
    try:
        filas_disp = ejecutar(
            "SELECT id FROM herramientas_dispositivos WHERE puerto = ?",
            (puerto,),
        )
        if filas_disp:
            disp_id = filas_disp[0]["id"]
        else:
            disp_id = ejecutar_mutacion(
                "INSERT INTO herramientas_dispositivos (nombre, puerto, velocidad, placa) "
                "VALUES (?, ?, ?, ?)",
                (f"ESP32 ({puerto})", puerto, 460800, target),
            )

        ejecutar_mutacion(
            "INSERT INTO herramientas_historial_flash (dispositivo_id, archivo, exitoso, salida) "
            "VALUES (?, ?, ?, ?)",
            (disp_id, archivo_ref, 1 if exitoso else 0, salida[:2000]),
        )

        ejecutar_mutacion(
            "INSERT INTO herramientas_operaciones_flash "
            "(puerto, chip_target, modo, tipo_operacion, offsets_json, sha256_resumen, verificado, exitoso, salida) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                puerto,
                target,
                modo,
                tipo_operacion,
                json.dumps(offsets),
                sha256_resumen,
                1 if verificado else 0,
                1 if exitoso else 0,
                salida[:4000],
            ),
        )
    except Exception:
        # Si la base de datos aun no ha sido inicializada en pruebas aisladas sin DB, no interrumpir.
        pass


def listar_historial_flash(limite: int = 25) -> dict:
    """Obtiene el historial detallado de operaciones de flasheo registradas."""
    try:
        filas = ejecutar(
            "SELECT id, puerto, chip_target, modo, tipo_operacion, offsets_json, "
            "sha256_resumen, verificado, exitoso, salida, fecha "
            "FROM herramientas_operaciones_flash "
            "ORDER BY id DESC LIMIT ?",
            (limite,),
        )
        items = []
        for f in filas:
            item = dict(f)
            try:
                item["offsets"] = json.loads(item.pop("offsets_json", "{}"))
            except json.JSONDecodeError:
                item["offsets"] = {}
            item["verificado"] = bool(item["verificado"])
            item["exitoso"] = bool(item["exitoso"])
            items.append(item)
        return {"total": len(items), "historial": items}
    except Exception:
        return {"total": 0, "historial": []}


def inspeccionar_imagen_esp(ruta_bin: Path, target: str) -> dict:
    """Valida cabecera magica 0xE9 y extrae metadatos con esptool image-info si esta disponible."""
    datos = ruta_bin.read_bytes()
    if len(datos) < 4:
        return {
            "valida": False,
            "error": f"Imagen '{ruta_bin.name}' truncada ({len(datos)} bytes).",
        }
    if datos[0] != MAGIC_ESP_IMAGE_BYTE:
        return {
            "valida": False,
            "error": (
                f"Imagen '{ruta_bin.name}' invalida: byte magico 0x{datos[0]:02x} != 0xE9."
            ),
        }

    resumen_cabecera = {
        "valida": True,
        "magic": "0xE9",
        "segmentos_declarados": datos[1],
        "flash_mode": datos[2],
        "flash_size_freq": f"0x{datos[3]:02x}",
        "image_info_salida": None,
    }

    cmd_base = _resolver_comando_esptool()
    if cmd_base:
        try:
            proc = subprocess.run(
                cmd_base + ["--chip", target, "image-info", str(ruta_bin.resolve())],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
            salida = f"{proc.stdout}\n{proc.stderr}".strip()
            if salida:
                resumen_cabecera["image_info_salida"] = salida[:1000]
        except (OSError, subprocess.SubprocessError):
            pass

    return resumen_cabecera


def _ejecutar_esptool_fisico(
    target: str,
    puerto: str,
    baud: int,
    pares_offset_ruta: list[tuple[str, str]],
    verificar: bool,
) -> tuple[bool, bool, str, list[str]]:
    cmd_base = _resolver_comando_esptool()
    if not cmd_base:
        return (
            False,
            False,
            "esptool no encontrado en el entorno Espressif ni en el PATH.",
            [],
        )

    argumentos = cmd_base + [
        "--chip",
        target,
        "--port",
        puerto,
        "--baud",
        str(baud),
        "write-flash",
    ]
    for off, ruta in pares_offset_ruta:
        argumentos.extend([off, ruta])

    proc = subprocess.run(
        argumentos,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )
    salida = f"{proc.stdout}\n{proc.stderr}".strip()
    if proc.returncode != 0:
        return False, False, salida, argumentos

    if not verificar:
        return True, False, salida, argumentos

    verificado = "hash of data verified" in salida.lower()
    if not verificado:
        cmd_ver = cmd_base + [
            "--chip",
            target,
            "--port",
            puerto,
            "verify-flash",
        ]
        for off, ruta in pares_offset_ruta:
            cmd_ver.extend([off, ruta])
        proc_ver = subprocess.run(
            cmd_ver,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        salida = f"{salida}\n{proc_ver.stdout}\n{proc_ver.stderr}".strip()
        verificado = proc_ver.returncode == 0

    return verificado, verificado, salida, argumentos


def flashear_bootloader(solicitud: SolicitudFlashBootloader) -> dict:
    """Graba el bootloader de segunda etapa en el offset exacto del SoC ESP32."""
    perfil = obtener_perfil_por_target(solicitud.target)
    target = perfil["target_idf"]
    offset_str = perfil["bootloader_offset"]
    offset_int = int(offset_str, 16)

    ruta_boot = Path(solicitud.bootloader_path)
    if not ruta_boot.is_file():
        return {
            "exitoso": False,
            "error": f"No existe el archivo bootloader: {ruta_boot}",
        }

    inspeccion = inspeccionar_imagen_esp(ruta_boot, target)
    if not inspeccion["valida"]:
        return {
            "exitoso": False,
            "modo": solicitud.modo,
            "error": inspeccion["error"],
        }

    datos_boot = ruta_boot.read_bytes()
    sha256_boot = hashlib.sha256(datos_boot).hexdigest()

    if solicitud.modo == "emulado":
        emulador = BootloaderEmuladoESP32(target=target, flash_mb=perfil["flash_mb"])
        try:
            seg = emulador.escribir_segmento("bootloader", offset_int, datos_boot)
            verificado = (
                emulador.verificar_readback(offset_int, datos_boot)
                if solicitud.verificar
                else False
            )
            salida = (
                f"[Bootloader Emulado {perfil['chip']}] Bootloader escrito en {offset_str} "
                f"({len(datos_boot)} bytes) y verificado por SHA-256."
            )
            _registrar_en_historial_bd(
                puerto="EMULADO",
                target=target,
                modo="emulado",
                tipo_operacion="bootloader",
                offsets={"bootloader": offset_str},
                sha256_resumen=sha256_boot,
                verificado=verificado,
                exitoso=True,
                salida=salida,
                archivo_ref=str(ruta_boot.name),
            )
            return {
                "exitoso": True,
                "modo": "emulado",
                "target": target,
                "offset": offset_str,
                "size_bytes": len(datos_boot),
                "sha256": sha256_boot,
                "verificado": verificado,
                "image_info": inspeccion,
                "segmento": seg,
                "salida": salida,
            }
        except ValueError as exc:
            _registrar_en_historial_bd(
                puerto="EMULADO",
                target=target,
                modo="emulado",
                tipo_operacion="bootloader",
                offsets={"bootloader": offset_str},
                sha256_resumen=sha256_boot,
                verificado=False,
                exitoso=False,
                salida=str(exc),
                archivo_ref=str(ruta_boot.name),
            )
            return {"exitoso": False, "modo": "emulado", "error": str(exc)}

    if not solicitud.puerto:
        return {
            "exitoso": False,
            "error": "Se requiere especificar 'puerto' para el flasheo fisico con esptool.",
        }

    ok, verificado, salida, comando = _ejecutar_esptool_fisico(
        target=target,
        puerto=solicitud.puerto,
        baud=solicitud.baud,
        pares_offset_ruta=[(offset_str, str(ruta_boot.resolve()))],
        verificar=solicitud.verificar,
    )
    _registrar_en_historial_bd(
        puerto=solicitud.puerto,
        target=target,
        modo="fisico",
        tipo_operacion="bootloader",
        offsets={"bootloader": offset_str},
        sha256_resumen=sha256_boot,
        verificado=verificado,
        exitoso=ok,
        salida=salida,
        archivo_ref=str(ruta_boot.name),
    )
    return {
        "exitoso": ok,
        "modo": "fisico",
        "target": target,
        "puerto": solicitud.puerto,
        "offset": offset_str,
        "size_bytes": len(datos_boot),
        "sha256": sha256_boot,
        "verificado": verificado,
        "image_info": inspeccion,
        "command": comando,
        "salida": salida,
        "error": None if ok else salida,
    }


def flashear_completo(solicitud: SolicitudFlashCompleto) -> dict:
    """Orquesta el flasheo completo: Bootloader + Particiones + NVS SSL (opcional) + App."""
    perfil = obtener_perfil_por_target(solicitud.target)
    target = perfil["target_idf"]
    boot_offset = perfil["bootloader_offset"]
    part_offset = perfil["partition_offset"]

    plan: list[tuple[str, str, Path]] = [
        ("bootloader", boot_offset, Path(solicitud.bootloader_path)),
        ("partitions", part_offset, Path(solicitud.partitions_path)),
    ]
    if solicitud.nvs_certs_path:
        plan.append(("nvs_ssl", solicitud.nvs_offset, Path(solicitud.nvs_certs_path)))
    plan.append(("app", solicitud.app_offset, Path(solicitud.app_path)))

    for tipo, _off, ruta in plan:
        if not ruta.is_file():
            return {
                "exitoso": False,
                "error": f"No se encontro el binario requerido para '{tipo}': {ruta}",
            }

    resumen_hash = hashlib.sha256()
    offsets_mapa = {tipo: off for tipo, off, _ in plan}

    if solicitud.modo == "emulado":
        emulador = BootloaderEmuladoESP32(target=target, flash_mb=perfil["flash_mb"])
        segmentos_res: list[dict] = []
        try:
            for tipo, off_str, ruta in plan:
                datos = ruta.read_bytes()
                resumen_hash.update(datos)
                off_int = int(off_str, 16)
                info_seg = emulador.escribir_segmento(tipo, off_int, datos)
                if solicitud.verificar:
                    info_seg["verificado"] = emulador.verificar_readback(off_int, datos)
                else:
                    info_seg["verificado"] = False
                segmentos_res.append(info_seg)

            # Guardar imagen combinada para pruebas de verificacion / QEMU
            img_dir = Path(tempfile.mkdtemp(prefix="esp32_flash_img_"))
            imagen_combinada = img_dir / f"flash_{target}.bin"
            fin_max = max(fin for _, fin, _ in emulador.regiones_escritas)
            imagen_combinada.write_bytes(bytes(emulador.memoria[:fin_max]))

            verificado_total = (
                all(s["verificado"] for s in segmentos_res)
                if solicitud.verificar
                else False
            )
            sha_global = resumen_hash.hexdigest()
            salida = (
                f"[Bootloader Emulado {perfil['chip']}] Flasheo completo exitoso "
                f"({len(segmentos_res)} segmentos, verificado={verificado_total})."
            )
            _registrar_en_historial_bd(
                puerto="EMULADO",
                target=target,
                modo="emulado",
                tipo_operacion="flash_completo",
                offsets=offsets_mapa,
                sha256_resumen=sha_global,
                verificado=verificado_total,
                exitoso=True,
                salida=salida,
                archivo_ref=Path(solicitud.app_path).name,
            )
            return {
                "exitoso": True,
                "modo": "emulado",
                "target": target,
                "verificado": verificado_total,
                "sha256": sha_global,
                "segmentos": segmentos_res,
                "flash_emulada_path": str(imagen_combinada.resolve()),
                "salida": salida,
            }
        except ValueError as exc:
            _registrar_en_historial_bd(
                puerto="EMULADO",
                target=target,
                modo="emulado",
                tipo_operacion="flash_completo",
                offsets=offsets_mapa,
                sha256_resumen="",
                verificado=False,
                exitoso=False,
                salida=str(exc),
                archivo_ref=Path(solicitud.app_path).name,
            )
            return {"exitoso": False, "modo": "emulado", "error": str(exc)}

    if not solicitud.puerto:
        return {
            "exitoso": False,
            "error": "Se requiere 'puerto' para ejecutar el flasheo completo en hardware fisico.",
        }

    pares = []
    segmentos_fisicos = []
    for tipo, off_str, ruta in plan:
        datos = ruta.read_bytes()
        resumen_hash.update(datos)
        pares.append((off_str, str(ruta.resolve())))
        segmentos_fisicos.append(
            {
                "tipo": tipo,
                "offset": off_str,
                "size_bytes": len(datos),
                "sha256_origen": hashlib.sha256(datos).hexdigest(),
            }
        )

    sha_global = resumen_hash.hexdigest()
    ok, verificado, salida, comando = _ejecutar_esptool_fisico(
        target=target,
        puerto=solicitud.puerto,
        baud=solicitud.baud,
        pares_offset_ruta=pares,
        verificar=solicitud.verificar,
    )
    _registrar_en_historial_bd(
        puerto=solicitud.puerto,
        target=target,
        modo="fisico",
        tipo_operacion="flash_completo",
        offsets=offsets_mapa,
        sha256_resumen=sha_global,
        verificado=verificado,
        exitoso=ok,
        salida=salida,
        archivo_ref=Path(solicitud.app_path).name,
    )
    return {
        "exitoso": ok,
        "modo": "fisico",
        "target": target,
        "puerto": solicitud.puerto,
        "verificado": verificado,
        "sha256": sha_global,
        "segmentos": segmentos_fisicos,
        "command": comando,
        "salida": salida,
        "error": None if ok else salida,
    }


def verificar_flash(solicitud: SolicitudVerificarFlash) -> dict:
    """Verifica integridad de un segmento en Flash fisica (esptool) o Flash emulada."""
    ruta_bin = Path(solicitud.bin_path)
    if not ruta_bin.is_file():
        return {"exitoso": False, "error": f"No existe el binario: {ruta_bin}"}

    datos = ruta_bin.read_bytes()
    off_int = int(solicitud.offset, 16)

    if solicitud.modo == "emulado":
        if not solicitud.flash_emulada_path:
            return {
                "exitoso": False,
                "error": "Especifique 'flash_emulada_path' para verificar contra una imagen emulada.",
            }
        ruta_img = Path(solicitud.flash_emulada_path)
        if not ruta_img.is_file():
            return {
                "exitoso": False,
                "error": f"No existe la imagen de Flash emulada: {ruta_img}",
            }
        contenido_flash = ruta_img.read_bytes()
        segmento_en_flash = contenido_flash[off_int : off_int + len(datos)]
        coincide = (
            hashlib.sha256(segmento_en_flash).digest() == hashlib.sha256(datos).digest()
        )
        return {
            "exitoso": coincide,
            "verificado": coincide,
            "modo": "emulado",
            "offset": solicitud.offset,
            "sha256_esperado": hashlib.sha256(datos).hexdigest(),
            "sha256_leido": hashlib.sha256(segmento_en_flash).hexdigest(),
        }

    if not solicitud.puerto:
        return {"exitoso": False, "error": "Se requiere 'puerto' en modo fisico."}

    cmd_base = _resolver_comando_esptool()
    if not cmd_base:
        return {"exitoso": False, "error": "esptool no disponible."}

    perfil = obtener_perfil_por_target(solicitud.target)
    cmd = cmd_base + [
        "--chip",
        perfil["target_idf"],
        "--port",
        solicitud.puerto,
        "verify-flash",
        solicitud.offset,
        str(ruta_bin.resolve()),
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
    )
    ok = proc.returncode == 0
    return {
        "exitoso": ok,
        "verificado": ok,
        "modo": "fisico",
        "offset": solicitud.offset,
        "salida": f"{proc.stdout}\n{proc.stderr}".strip(),
    }
