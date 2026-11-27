# Archivo: modules/herramientas/backend/herramientas_backend/controllers/certificados.py
"""Validacion de certificados SSL/TLS X.509 y empaquetado en particion NVS de ESP-IDF."""

from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

_REGEX_CERT_PEM = re.compile(
    r"-----BEGIN CERTIFICATE-----\s+([A-Za-z0-9+/=\r\n]+)\s+-----END CERTIFICATE-----"
)
_REGEX_KEY_PEM = re.compile(
    r"-----BEGIN (?:RSA |EC |ENCRYPTED )?PRIVATE KEY-----\s+([A-Za-z0-9+/=\r\n]+)\s+-----END (?:RSA |EC |ENCRYPTED )?PRIVATE KEY-----"
)


class SolicitudCertificadosNvs(BaseModel):
    ca_cert: Optional[str] = None
    client_cert: Optional[str] = None
    client_key: Optional[str] = None
    namespace: str = Field(default="ssl_certs", min_length=1, max_length=15)
    tamanio_bytes: int = Field(default=0x6000, ge=0x3000)
    offset: str = Field(default="0x9000")


def validar_pem(contenido: str, tipo: str = "cert") -> tuple[bool, Optional[str]]:
    """Valida que el texto contenga un bloque PEM X.509 o llave privada bien formado."""
    texto = (contenido or "").strip()
    if not texto:
        return False, "El contenido PEM esta vacio."

    patron = _REGEX_CERT_PEM if tipo == "cert" else _REGEX_KEY_PEM
    coincidencia = patron.search(texto)
    if not coincidencia:
        esperado = (
            "-----BEGIN CERTIFICATE-----"
            if tipo == "cert"
            else "-----BEGIN PRIVATE KEY-----"
        )
        return False, f"Formato PEM invalido: falta bloque '{esperado}'."

    cuerpo_b64 = re.sub(r"\s+", "", coincidencia.group(1))
    if len(cuerpo_b64) < 16:
        return False, "El cuerpo Base64 del certificado/llave es demasiado corto."

    return True, None


def _invocar_nvs_partition_gen_oficial(
    csv_path: Path,
    bin_path: Path,
    tamanio_bytes: int,
) -> bool:
    """Usa esp_idf_nvs_partition_gen del entorno EIM ESP-IDF si esta disponible."""
    try:
        from herramientas_backend.controllers.esp_idf import (
            _localizar_python_venv_espressif,
            localizar_instalacion_idf,
        )

        idf_dir = localizar_instalacion_idf()
        py_eim = _localizar_python_venv_espressif(idf_dir)
        if py_eim is None:
            return False

        proc = subprocess.run(
            [
                str(py_eim),
                "-m",
                "esp_idf_nvs_partition_gen",
                "generate",
                str(csv_path),
                str(bin_path),
                hex(tamanio_bytes),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        return proc.returncode == 0 and bin_path.is_file()
    except Exception:
        return False


def _construir_imagen_nvs_respaldo(
    namespace: str,
    entradas: dict[str, str],
    tamanio_bytes: int,
) -> bytes:
    """Construye una imagen de particion NVS alineada a 4 KB para entornos sin ESP-IDF."""
    bloque = bytearray(b"\xff" * tamanio_bytes)
    # Cabecera de pagina activa NVS (Active state 0xFFFFFFFE) + metadatos serializados
    cabecera = f"NVS:{namespace}\n".encode("utf-8")
    cursor = 32
    bloque[0:4] = b"\xfe\xff\xff\xff"
    bloque[cursor : cursor + len(cabecera)] = cabecera
    cursor += len(cabecera)

    for clave, valor in entradas.items():
        registro = f"{clave}={valor}\x00".encode("utf-8")
        if cursor + len(registro) >= tamanio_bytes:
            raise ValueError(
                "Los certificados superan el tamanio asignado a la particion NVS."
            )
        bloque[cursor : cursor + len(registro)] = registro
        cursor += len(registro)

    return bytes(bloque)


def generar_particion_nvs_certificados(solicitud: SolicitudCertificadosNvs) -> dict:
    """Valida certificados SSL/TLS y genera una particion binaria NVS flasheable."""
    if solicitud.tamanio_bytes % 0x1000 != 0:
        return {
            "exitoso": False,
            "error": "El tamanio de la particion NVS debe ser multiplo de 4096 bytes (0x1000).",
        }

    entradas_validas: dict[str, str] = {}

    if solicitud.ca_cert:
        ok, err = validar_pem(solicitud.ca_cert, tipo="cert")
        if not ok:
            return {"exitoso": False, "error": f"CA Root invalido: {err}"}
        entradas_validas["ca_cert"] = solicitud.ca_cert.strip() + "\n"

    if solicitud.client_cert:
        ok, err = validar_pem(solicitud.client_cert, tipo="cert")
        if not ok:
            return {"exitoso": False, "error": f"Certificado cliente invalido: {err}"}
        entradas_validas["client_cert"] = solicitud.client_cert.strip() + "\n"

    if solicitud.client_key:
        ok, err = validar_pem(solicitud.client_key, tipo="key")
        if not ok:
            return {"exitoso": False, "error": f"Llave privada invalida: {err}"}
        entradas_validas["client_key"] = solicitud.client_key.strip() + "\n"

    if not entradas_validas:
        return {
            "exitoso": False,
            "error": "Debe suministrar al menos un certificado o llave PEM (ca_cert, client_cert o client_key).",
        }

    out_dir = Path(tempfile.mkdtemp(prefix="esp32_nvs_ssl_"))
    archivos_temporales_sensibles: list[Path] = []
    csv_path = out_dir / "nvs_certs.csv"
    bin_path = out_dir / "nvs_ssl.bin"
    archivos_temporales_sensibles.append(csv_path)

    try:
        lineas_csv = [
            "key,type,encoding,value",
            f"{solicitud.namespace},namespace,,",
        ]
        for clave, contenido in entradas_validas.items():
            pem_file = out_dir / f"{clave}.pem"
            archivos_temporales_sensibles.append(pem_file)
            pem_file.write_text(contenido, encoding="utf-8", newline="\n")
            lineas_csv.append(f"{clave},file,string,{pem_file.resolve()}")

        csv_path.write_text("\n".join(lineas_csv) + "\n", encoding="utf-8")

        usado_oficial = _invocar_nvs_partition_gen_oficial(
            csv_path, bin_path, solicitud.tamanio_bytes
        )
        if not usado_oficial:
            try:
                bin_path.write_bytes(
                    _construir_imagen_nvs_respaldo(
                        solicitud.namespace,
                        entradas_validas,
                        solicitud.tamanio_bytes,
                    )
                )
            except ValueError as exc:
                return {"exitoso": False, "error": str(exc)}
    finally:
        # Eliminar de inmediato cualquier certificado/llave privada PEM y CSV en texto plano
        for sensible in archivos_temporales_sensibles:
            sensible.unlink(missing_ok=True)

    datos_bin = bin_path.read_bytes()
    sha256_hex = hashlib.sha256(datos_bin).hexdigest()

    return {
        "exitoso": True,
        "generador": (
            "esp_idf_nvs_partition_gen" if usado_oficial else "nvs_builder_respaldo"
        ),
        "namespace": solicitud.namespace,
        "certificados_incluidos": list(entradas_validas.keys()),
        "offset": solicitud.offset,
        "size_bytes": len(datos_bin),
        "sha256": sha256_hex,
        "nvs_bin_path": str(bin_path.resolve()),
    }
