# Archivo: modules/herramientas/backend/pruebas/unitarias/test_sprint04_flash_particiones_ssl.py
"""Pruebas unitarias e integracion del Sprint 4: Bootloader, Particiones, Certificados SSL NVS y Flasheo."""

import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from herramientas_backend.modulo import registrar

from ide_core.db import connection as db_conn


@contextmanager
def _cliente_con_bd_aislada():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        ruta_original = db_conn.RUTA_BD
        try:
            db_conn.RUTA_BD = tmp_path / "test_sprint4.db"
            db_conn.init_pool()
            db_conn.aplicar_esquemas_completos()
            app = FastAPI()
            registrar(app)
            yield TestClient(app), tmp_path
        finally:
            db_conn.RUTA_BD = ruta_original


def test_plantillas_y_generacion_tabla_particiones():
    with _cliente_con_bd_aislada() as (client, _tmp):
        r_tpl = client.get("/api/v1/herramientas/particiones/plantillas")
        assert r_tpl.status_code == 200
        plantillas = r_tpl.json()["plantillas"]
        ids = {p["id"] for p in plantillas}
        assert {"single_app", "single_app_ssl_nvs", "factory_ota"}.issubset(ids)

        r_ota = client.post(
            "/api/v1/herramientas/particiones/generar",
            json={"plantilla_id": "factory_ota"},
        )
        assert r_ota.status_code == 200
        assert r_ota.json()["exitoso"] is True

        csv_texto = (
            "# Name, Type, SubType, Offset, Size, Flags\n"
            "nvs, data, nvs, 0x9000, 0x6000,\n"
            "phy_init, data, phy, 0xf000, 0x1000,\n"
            "factory, app, factory, 0x10000, 0x100000,\n"
        )
        r_gen = client.post(
            "/api/v1/herramientas/particiones/generar",
            json={"csv_contenido": csv_texto, "nombre": "tabla_test"},
        )
        assert r_gen.status_code == 200
        datos = r_gen.json()
        assert datos["exitoso"] is True
        assert datos["size_bytes"] >= 96
        assert Path(datos["bin_path"]).is_file()

        r_parse = client.post(
            "/api/v1/herramientas/particiones/parsear",
            json={"bin_path": datos["bin_path"]},
        )
        assert r_parse.status_code == 200
        entradas = r_parse.json()["particiones"]
        nombres = [e["nombre"] for e in entradas]
        assert nombres == ["nvs", "phy_init", "factory"]


def test_rechaza_particiones_solapadas():
    with _cliente_con_bd_aislada() as (client, _tmp):
        csv_solapado = (
            "nvs, data, nvs, 0x9000, 0x8000,\n" "phy_init, data, phy, 0xf000, 0x1000,\n"
        )
        r = client.post(
            "/api/v1/herramientas/particiones/generar",
            json={"csv_contenido": csv_solapado},
        )
        assert r.status_code == 200
        assert r.json()["exitoso"] is False
        assert "solapa" in r.json()["error"].lower()


def test_certificados_ssl_validacion_generacion_y_limpieza_llave_privada():
    with _cliente_con_bd_aislada() as (client, _tmp):
        r_bad = client.post(
            "/api/v1/herramientas/certificados/generar-nvs",
            json={"ca_cert": "NO_ES_UN_CERTIFICADO_PEM"},
        )
        assert r_bad.status_code == 200
        assert r_bad.json()["exitoso"] is False

        pem_ca = (
            "-----BEGIN CERTIFICATE-----\n"
            "MIIBszCCAVmgAwIBAgIUFAKECERTDATAFORESP32IDETESTING0123456789ABCD\n"
            "-----END CERTIFICATE-----\n"
        )
        pem_key = (
            "-----BEGIN PRIVATE KEY-----\n"
            "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC0123456789ABC\n"
            "-----END PRIVATE KEY-----\n"
        )
        r_ok = client.post(
            "/api/v1/herramientas/certificados/generar-nvs",
            json={
                "ca_cert": pem_ca,
                "client_key": pem_key,
                "namespace": "ssl_certs",
                "tamanio_bytes": 0x6000,
                "offset": "0x9000",
            },
        )
        assert r_ok.status_code == 200
        datos = r_ok.json()
        assert datos["exitoso"] is True
        assert datos["offset"] == "0x9000"
        assert datos["size_bytes"] == 0x6000
        assert len(datos["sha256"]) == 64

        nvs_bin = Path(datos["nvs_bin_path"])
        assert nvs_bin.is_file()
        # Seguridad: la llave privada y el CSV en texto plano deben haberse eliminado tras empaquetar
        assert not (nvs_bin.parent / "client_key.pem").exists()
        assert not (nvs_bin.parent / "nvs_certs.csv").exists()


def test_grabar_bootloader_emulado_y_fisico_offsets_y_verificacion():
    with _cliente_con_bd_aislada() as (client, tmp_path):
        boot_invalido = tmp_path / "corrupto.bin"
        boot_invalido.write_bytes(b"\x00\x01\x02\x03" * 16)

        # Rechaza bootloader sin magic 0xE9 incluso en modo fisico
        r_corrupto = client.post(
            "/api/v1/herramientas/esptool/bootloader",
            json={
                "bootloader_path": str(boot_invalido),
                "target": "esp32s3",
                "puerto": "COM5",
                "modo": "fisico",
            },
        )
        assert r_corrupto.json()["exitoso"] is False
        assert "0xE9" in r_corrupto.json()["error"]

        boot_valido = tmp_path / "bootloader.bin"
        boot_valido.write_bytes(b"\xe9\x03\x02\x20" + b"\x00" * 256)

        # 1. Modo bootloader emulado en ESP32-S3 -> offset 0x0 + image_info
        r_emu = client.post(
            "/api/v1/herramientas/esptool/bootloader",
            json={
                "bootloader_path": str(boot_valido),
                "target": "esp32s3",
                "modo": "emulado",
            },
        )
        assert r_emu.status_code == 200
        d_emu = r_emu.json()
        assert d_emu["exitoso"] is True
        assert d_emu["offset"] == "0x0"
        assert d_emu["verificado"] is True
        assert d_emu["image_info"]["magic"] == "0xE9"

        # 2. Modo fisico en ESP32 clasico -> offset 0x1000 y verificar=False => verificado=False
        proc_sin_hash = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Wrote 260 bytes.", stderr=""
        )
        with (
            patch(
                "herramientas_backend.controllers.esptool_service._resolver_comando_esptool",
                return_value=["esptool"],
            ),
            patch(
                "herramientas_backend.controllers.esptool_service.subprocess.run",
                return_value=proc_sin_hash,
            ) as mock_run,
        ):
            r_fis = client.post(
                "/api/v1/herramientas/esptool/bootloader",
                json={
                    "bootloader_path": str(boot_valido),
                    "target": "esp32",
                    "puerto": "COM5",
                    "modo": "fisico",
                    "verificar": False,
                },
            )

        assert r_fis.status_code == 200
        d_fis = r_fis.json()
        assert d_fis["exitoso"] is True
        assert d_fis["verificado"] is False
        assert d_fis["offset"] == "0x1000"
        assert "image-info" in mock_run.call_args_list[0][0][0]
        assert "0x1000" in mock_run.call_args_list[-1][0][0]


def test_flasheo_completo_orquestado_verificacion_e_historial_bd():
    with _cliente_con_bd_aislada() as (client, tmp_path):
        boot_bin = tmp_path / "bootloader.bin"
        app_bin = tmp_path / "firmware.bin"
        boot_bin.write_bytes(b"\xe9\x03\x02\x20" + b"\x11" * 512)
        app_bin.write_bytes(b"\xe9\x04\x02\x20" + b"\x22" * 2048)

        r_part = client.post(
            "/api/v1/herramientas/particiones/generar",
            json={"plantilla_id": "single_app_ssl_nvs"},
        )
        part_path = r_part.json()["bin_path"]

        pem_ca = (
            "-----BEGIN CERTIFICATE-----\n"
            "MIIBszCCAVmgAwIBAgIUFAKECERTDATAFORESP32IDETESTING0123456789ABCD\n"
            "-----END CERTIFICATE-----\n"
        )
        r_nvs = client.post(
            "/api/v1/herramientas/certificados/generar-nvs",
            json={"ca_cert": pem_ca},
        )
        nvs_path = r_nvs.json()["nvs_bin_path"]

        r_boot_prev = client.post(
            "/api/v1/herramientas/esptool/bootloader",
            json={
                "bootloader_path": str(boot_bin),
                "target": "esp32s3",
                "modo": "emulado",
            },
        )
        assert r_boot_prev.json()["exitoso"] is True

        r_flash = client.post(
            "/api/v1/herramientas/esptool/flash-completo",
            json={
                "target": "esp32s3",
                "modo": "emulado",
                "bootloader_path": str(boot_bin),
                "partitions_path": part_path,
                "nvs_certs_path": nvs_path,
                "app_path": str(app_bin),
                "verificar": True,
            },
        )
        assert r_flash.status_code == 200
        d_flash = r_flash.json()
        assert d_flash["exitoso"] is True
        assert d_flash["verificado"] is True
        assert len(d_flash["segmentos"]) == 4

        r_ver = client.post(
            "/api/v1/herramientas/esptool/verificar-flash",
            json={
                "target": "esp32s3",
                "modo": "emulado",
                "offset": "0x10000",
                "bin_path": str(app_bin),
                "flash_emulada_path": d_flash["flash_emulada_path"],
            },
        )
        assert r_ver.status_code == 200
        assert r_ver.json()["verificado"] is True

        r_hist = client.get("/api/v1/herramientas/historial-flash")
        assert r_hist.status_code == 200
        historial = r_hist.json()["historial"]
        assert len(historial) >= 2
        assert any(h["tipo_operacion"] == "flash_completo" for h in historial)

        r_resumen = client.get("/api/v1/herramientas/reportes/flash")
        assert r_resumen.status_code == 200
        assert r_resumen.json()["exitosos"] >= 2
