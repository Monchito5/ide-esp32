# Archivo: modules/herramientas/backend/pruebas/unitarias/test_deteccion_placa_espressif.py
"""Pruebas unitarias para deteccion nativa de placas ESP32 (Espressif USB + esptool + ESP-IDF)."""

import subprocess
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from herramientas_backend.controllers.esp_idf import estado_esp_idf
from herramientas_backend.controllers.placa import (
    detectar_placas_conectadas,
    identificar_placa_por_usb,
    listar_placas_soportadas,
    sondear_chip_esptool,
)
from herramientas_backend.modulo import registrar


def test_catalogo_placas_soportadas_incluye_s3_y_c3():
    respuesta = listar_placas_soportadas()
    assert respuesta["total"] >= 5
    targets = {p["target_idf"] for p in respuesta["placas"]}
    nombres = {p["nombre"] for p in respuesta["placas"]}
    assert {"esp32", "esp32s2", "esp32s3", "esp32c3", "esp32c6"}.issubset(targets)
    assert "ESP32-S3 DevKitC-1" in nombres
    assert "ESP32-C3 DevKitM-1" in nombres


def test_identificar_placa_usb_nativo_espressif_s3():
    info = identificar_placa_por_usb(
        vid=0x303A,
        pid=0x1001,
        descripcion="USB JTAG/serial debug unit (ESP32-S3)",
        fabricante="Espressif",
    )
    assert info["es_esp32"] is True
    assert info["target_idf"] == "esp32s3"
    assert info["placa"] == "ESP32-S3 DevKitC-1"
    assert info["confianza"] == "alta"


def test_identificar_placa_usb_puente_cp210x_c3():
    info = identificar_placa_por_usb(
        vid=0x10C4,
        pid=0xEA60,
        descripcion="Silicon Labs CP210x USB to UART Bridge - ESP32-C3",
        fabricante="Silicon Labs",
    )
    assert info["es_esp32"] is True
    assert info["target_idf"] == "esp32c3"
    assert info["placa"] == "ESP32-C3 DevKitM-1"


def test_identificar_puerto_no_esp32():
    info = identificar_placa_por_usb(
        vid=0x045E,
        pid=0x07A5,
        descripcion="Standard Serial over Bluetooth link",
        fabricante="Microsoft",
    )
    assert info["es_esp32"] is False
    assert info["target_idf"] is None


def test_sondear_chip_esptool_parsea_chip_y_mac():
    salida_simulada = (
        "esptool.py v4.7.0\n"
        "Serial port COM5\n"
        "Connecting....\n"
        "Detecting chip type... ESP32-S3\n"
        "Chip is ESP32-S3 (QFN56) (revision v0.2)\n"
        "MAC: 24:6f:28:aa:bb:cc\n"
    )
    proc_ok = subprocess.CompletedProcess(
        args=["esptool", "--port", "COM5", "chip_id"],
        returncode=0,
        stdout=salida_simulada,
        stderr="",
    )
    with patch(
        "herramientas_backend.controllers.placa._resolver_comando_esptool",
        return_value=["esptool"],
    ), patch(
        "herramientas_backend.controllers.placa.subprocess.run",
        return_value=proc_ok,
    ):
        resultado = sondear_chip_esptool("COM5")

    assert resultado["exitoso"] is True
    assert resultado["target_idf"] == "esp32s3"
    assert resultado["placa"] == "ESP32-S3 DevKitC-1"
    assert resultado["mac"] == "24:6F:28:AA:BB:CC"


def test_detectar_placas_conectadas_endpoint_http():
    puerto_falso = SimpleNamespace(
        device="COM7",
        description="USB JTAG/serial debug unit",
        manufacturer="Espressif Systems",
        vid=0x303A,
        pid=0x1001,
    )
    app = FastAPI()
    registrar(app)
    client = TestClient(app)

    with patch(
        "herramientas_backend.controllers.puerto.list_ports.comports",
        return_value=[puerto_falso],
    ):
        resp = client.get("/api/v1/herramientas/detectar-placa")

    assert resp.status_code == 200
    datos = resp.json()
    assert datos["detectada"] is True
    assert datos["total_esp32"] == 1
    assert datos["recomendada"]["dispositivo"] == "COM7"
    assert datos["recomendada"]["target_idf"] == "esp32s3"
    assert datos["herramienta"] == "espressif_usb_esptool"


def test_estado_esp_idf_sin_instalacion_no_falla():
    with patch(
        "herramientas_backend.controllers.esp_idf.localizar_instalacion_idf",
        return_value=None,
    ), patch(
        "herramientas_backend.controllers.esp_idf.shutil.which",
        return_value=None,
    ):
        estado = estado_esp_idf()

    assert estado["esp_idf_disponible"] is False
    assert "targets_soportados" in estado
    assert "esp32s3" in estado["targets_soportados"]
