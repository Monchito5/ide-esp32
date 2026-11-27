# Archivo: modules/herramientas/backend/herramientas_backend/controllers/particiones.py
"""Gestion, validacion y generacion binaria de tablas de particiones Espressif ESP-IDF."""

from __future__ import annotations

import hashlib
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

MAGIC_PARTITION_ENTRY = b"\xaa\x50"
MAGIC_MD5_ENTRY = b"\xeb\xeb" + (b"\xff" * 14)

TIPOS_PARTICION = {"app": 0x00, "data": 0x01}
SUBTIPOS_PARTICION = {
    "factory": 0x00,
    "ota": 0x00,
    "phy": 0x01,
    "nvs": 0x02,
    "coredump": 0x03,
    "nvs_keys": 0x04,
    "efuse": 0x05,
    "spiffs": 0x82,
    "fat": 0x81,
    "littlefs": 0x83,
    **{f"ota_{i}": 0x10 + i for i in range(16)},
}
SUBTIPOS_INVERSO_APP = {0x00: "factory", **{0x10 + i: f"ota_{i}" for i in range(16)}}
SUBTIPOS_INVERSO_DATA = {
    0x00: "ota",
    0x01: "phy",
    0x02: "nvs",
    0x03: "coredump",
    0x04: "nvs_keys",
    0x05: "efuse",
    0x81: "fat",
    0x82: "spiffs",
    0x83: "littlefs",
}

PLANTILLAS_PARTICIONES = [
    {
        "id": "single_app",
        "nombre": "Single Factory App (sin OTA)",
        "descripcion": "Esquema estandar ESP-IDF para una aplicacion principal de 1 MB.",
        "csv": (
            "# Name, Type, SubType, Offset, Size, Flags\n"
            "nvs, data, nvs, 0x9000, 0x6000,\n"
            "phy_init, data, phy, 0xf000, 0x1000,\n"
            "factory, app, factory, 0x10000, 0x100000,\n"
        ),
    },
    {
        "id": "single_app_ssl_nvs",
        "nombre": "Factory App + Particion NVS para Certificados SSL",
        "descripcion": "Incluye particion NVS en 0x9000 optimizada para almacenar certificados X.509/TLS.",
        "csv": (
            "# Name, Type, SubType, Offset, Size, Flags\n"
            "nvs, data, nvs, 0x9000, 0x6000,\n"
            "phy_init, data, phy, 0xf000, 0x1000,\n"
            "factory, app, factory, 0x10000, 0x180000,\n"
            "storage, data, spiffs, 0x190000, 0x60000,\n"
        ),
    },
    {
        "id": "factory_ota",
        "nombre": "Two OTA Slots (ota_0 + ota_1)",
        "descripcion": "Esquema con actualizacion inalambrica OTA dual y particion otadata.",
        "csv": (
            "# Name, Type, SubType, Offset, Size, Flags\n"
            "nvs, data, nvs, 0x9000, 0x4000,\n"
            "otadata, data, ota, 0xd000, 0x2000,\n"
            "phy_init, data, phy, 0xf000, 0x1000,\n"
            "ota_0, app, ota_0, 0x10000, 0x140000,\n"
            "ota_1, app, ota_1, 0x150000, 0x140000,\n"
        ),
    },
]


class SolicitudGenerarParticiones(BaseModel):
    csv_contenido: Optional[str] = None
    plantilla_id: Optional[str] = None
    nombre: str = "partition-table"


class SolicitudParsearParticiones(BaseModel):
    bin_path: str


def listar_plantillas_particiones() -> dict:
    """Lista las plantillas oficiales de tablas de particiones para ESP-IDF."""
    return {
        "total": len(PLANTILLAS_PARTICIONES),
        "plantillas": [dict(p) for p in PLANTILLAS_PARTICIONES],
    }


def _parsear_entero_tamano(texto: str) -> int:
    limpio = texto.strip().upper()
    if limpio.endswith("K"):
        return int(limpio[:-1], 0) * 1024
    if limpio.endswith("M"):
        return int(limpio[:-1], 0) * 1024 * 1024
    return int(limpio, 0)


def validar_y_normalizar_csv(csv_texto: str) -> list[dict]:
    """Parsea un CSV de particiones ESP-IDF y verifica ausencia de solapamientos."""
    entradas: list[dict] = []
    cursor_offset = 0x9000

    for num_linea, cruda in enumerate(csv_texto.splitlines(), start=1):
        linea = cruda.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) < 5:
            raise ValueError(
                f"Linea {num_linea} invalida: se requieren al menos Name, Type, SubType, Offset, Size."
            )

        nombre, tipo_str, subtipo_str, offset_str, size_str = partes[:5]
        flags_str = partes[5] if len(partes) > 5 else ""

        tipo_low = tipo_str.lower()
        tipo_cod = (
            TIPOS_PARTICION[tipo_low]
            if tipo_low in TIPOS_PARTICION
            else _parsear_entero_tamano(tipo_str)
        )
        sub_low = subtipo_str.lower()
        sub_cod = (
            SUBTIPOS_PARTICION[sub_low]
            if sub_low in SUBTIPOS_PARTICION
            else _parsear_entero_tamano(subtipo_str)
        )

        size_val = _parsear_entero_tamano(size_str)
        if size_val <= 0:
            raise ValueError(f"Tamano invalido en particion '{nombre}'.")

        if offset_str:
            offset_val = _parsear_entero_tamano(offset_str)
        else:
            alineacion = 0x10000 if tipo_cod == 0x00 else 0x1000
            if cursor_offset % alineacion != 0:
                cursor_offset += alineacion - (cursor_offset % alineacion)
            offset_val = cursor_offset

        cursor_offset = offset_val + size_val

        entradas.append(
            {
                "nombre": nombre[:15],
                "tipo": tipo_low,
                "tipo_codigo": tipo_cod,
                "subtipo": sub_low,
                "subtipo_codigo": sub_cod,
                "offset": f"0x{offset_val:x}",
                "offset_int": offset_val,
                "size": f"0x{size_val:x}",
                "size_bytes": size_val,
                "flags": flags_str,
            }
        )

    if not entradas:
        raise ValueError("La tabla de particiones no contiene entradas validas.")

    ordenadas = sorted(entradas, key=lambda e: e["offset_int"])
    for idx in range(1, len(ordenadas)):
        prev = ordenadas[idx - 1]
        actual = ordenadas[idx]
        fin_prev = prev["offset_int"] + prev["size_bytes"]
        if actual["offset_int"] < fin_prev:
            raise ValueError(
                f"La particion '{actual['nombre']}' ({actual['offset']}) se solapa "
                f"con '{prev['nombre']}' ({prev['offset']}..0x{fin_prev:x})."
            )

    return entradas


def _codificar_binario_esp32part(entradas: list[dict]) -> bytes:
    """Codifica entradas al formato binario oficial de Espressif (0xAA50 + MD5)."""
    registros = bytearray()
    for e in entradas:
        nombre_bytes = e["nombre"].encode("utf-8")[:15].ljust(16, b"\x00")
        flags_int = 1 if "encrypted" in e["flags"].lower() else 0
        registros += struct.pack(
            "<2sBBII16sI",
            MAGIC_PARTITION_ENTRY,
            e["tipo_codigo"],
            e["subtipo_codigo"],
            e["offset_int"],
            e["size_bytes"],
            nombre_bytes,
            flags_int,
        )

    digest = hashlib.md5(bytes(registros)).digest()
    registros += MAGIC_MD5_ENTRY + digest
    # Pad a 0xC00 (3072 bytes) como hace gen_esp32part.py
    if len(registros) < 0xC00:
        registros += b"\xff" * (0xC00 - len(registros))
    return bytes(registros)


def _intentar_gen_esp32part_oficial(csv_path: Path, bin_path: Path) -> bool:
    """Invoca gen_esp32part.py de la instalacion local de ESP-IDF si esta presente."""
    try:
        from herramientas_backend.controllers.esp_idf import (
            _localizar_python_venv_espressif,
            localizar_instalacion_idf,
        )

        idf_dir = localizar_instalacion_idf()
        if idf_dir is None:
            return False
        script = idf_dir / "components" / "partition_table" / "gen_esp32part.py"
        if not script.is_file():
            return False
        py_exe = _localizar_python_venv_espressif(idf_dir)
        interprete = str(py_exe) if py_exe else "python"
        proc = subprocess.run(
            [interprete, str(script), "--quiet", str(csv_path), str(bin_path)],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        return proc.returncode == 0 and bin_path.is_file()
    except Exception:
        return False


def generar_tabla_particiones(solicitud: SolicitudGenerarParticiones) -> dict:
    """Genera y valida un archivo partition-table.bin a partir de CSV o plantilla."""
    csv_texto = solicitud.csv_contenido
    if not csv_texto and solicitud.plantilla_id:
        tpl_buscada = (
            "factory_ota"
            if solicitud.plantilla_id == "factory_ota_twopart"
            else solicitud.plantilla_id
        )
        for tpl in PLANTILLAS_PARTICIONES:
            if tpl["id"] == tpl_buscada:
                csv_texto = tpl["csv"]
                break

    if not csv_texto or not csv_texto.strip():
        return {
            "exitoso": False,
            "error": "Debe proporcionar 'csv_contenido' o un 'plantilla_id' valido.",
        }

    try:
        entradas = validar_y_normalizar_csv(csv_texto)
    except ValueError as exc:
        return {"exitoso": False, "error": str(exc)}

    out_dir = Path(tempfile.mkdtemp(prefix="esp32_partitions_"))

    nombre_limpio = Path(solicitud.nombre).stem or "partition-table"
    csv_path = out_dir / f"{nombre_limpio}.csv"
    bin_path = out_dir / f"{nombre_limpio}.bin"
    csv_path.write_text(csv_texto, encoding="utf-8")

    usado_gen_oficial = _intentar_gen_esp32part_oficial(csv_path, bin_path)
    if not usado_gen_oficial:
        bin_path.write_bytes(_codificar_binario_esp32part(entradas))

    contenido_bin = bin_path.read_bytes()
    sha256_hex = hashlib.sha256(contenido_bin).hexdigest()

    return {
        "exitoso": True,
        "generador": (
            "gen_esp32part.py (ESP-IDF)" if usado_gen_oficial else "esp32part_nativo"
        ),
        "offset_tabla": "0x8000",
        "csv_path": str(csv_path.resolve()),
        "bin_path": str(bin_path.resolve()),
        "size_bytes": len(contenido_bin),
        "sha256": sha256_hex,
        "particiones": entradas,
    }


def parsear_binario_particiones(solicitud: SolicitudParsearParticiones) -> dict:
    """Lee un archivo partition-table.bin y devuelve sus entradas estructuradas."""
    ruta = Path(solicitud.bin_path)
    if not ruta.is_file():
        return {"exitoso": False, "error": f"No existe el archivo: {ruta}"}

    datos = ruta.read_bytes()
    particiones: list[dict] = []

    for pos in range(0, len(datos) - 31, 32):
        bloque = datos[pos : pos + 32]
        if bloque[:2] == b"\xff\xff" or bloque[:16] == MAGIC_MD5_ENTRY:
            break
        if bloque[:2] != MAGIC_PARTITION_ENTRY:
            return {
                "exitoso": False,
                "error": f"Cabecera magica invalida en entrada {pos // 32} (se esperaba 0xAA50).",
            }
        _, tipo_cod, sub_cod, offset_val, size_val, raw_name, flags = struct.unpack(
            "<2sBBII16sI", bloque
        )
        nombre = raw_name.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
        tipo_str = (
            "app"
            if tipo_cod == 0x00
            else ("data" if tipo_cod == 0x01 else hex(tipo_cod))
        )
        if tipo_cod == 0x00:
            sub_str = SUBTIPOS_INVERSO_APP.get(sub_cod, hex(sub_cod))
        elif tipo_cod == 0x01:
            sub_str = SUBTIPOS_INVERSO_DATA.get(sub_cod, hex(sub_cod))
        else:
            sub_str = hex(sub_cod)

        particiones.append(
            {
                "nombre": nombre,
                "tipo": tipo_str,
                "subtipo": sub_str,
                "offset": f"0x{offset_val:x}",
                "offset_int": offset_val,
                "size": f"0x{size_val:x}",
                "size_bytes": size_val,
                "encrypted": bool(flags & 0x1),
            }
        )

    return {
        "exitoso": True,
        "bin_path": str(ruta.resolve()),
        "total": len(particiones),
        "particiones": particiones,
    }
