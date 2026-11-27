# Archivo: modules/sketch/backend/pruebas/test_pipeline_espidf_sprint3.py
"""Pruebas unitarias e integracion para el pipeline end-to-end ESP-IDF (Sprint 3)."""

from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sketch_backend.modulo import registrar as registrar_sketch


def _simular_compilacion_exitosa(ruta_proyecto, timeout=1800, target=None):
    proyecto = Path(ruta_proyecto)
    build = proyecto / "build"
    bootloader_dir = build / "bootloader"
    partition_dir = build / "partition_table"
    bootloader_dir.mkdir(parents=True, exist_ok=True)
    partition_dir.mkdir(parents=True, exist_ok=True)

    boot_bin = bootloader_dir / "bootloader.bin"
    part_bin = partition_dir / "partition-table.bin"
    app_bin = build / "esp32_sketch.bin"

    boot_bin.write_bytes(b"\xe9\x00\x02\x10BOOT")
    part_bin.write_bytes(b"\xaa\x50PART")
    app_bin.write_bytes(b"\xe9\x04\x02\x20APP_FIRMWARE")

    return {
        "success": True,
        "returncode": 0,
        "stdout": f"Project build complete ({target}). To flash, run idf.py flash",
        "stderr": "",
        "command": [
            ["python", "idf.py", "set-target", target],
            ["python", "idf.py", "build"],
        ],
        "framework": "ESP-IDF",
        "project_path": str(proyecto),
        "build_path": str(build),
        "artifacts_dir": str(build),
        "bin_files": [str(boot_bin), str(part_bin), str(app_bin)],
        "target": target,
    }


def test_compilar_codigo_end_to_end_esp32s3_genera_estructura_y_offsets():
    app = FastAPI()
    registrar_sketch(app)
    client = TestClient(app)

    codigo_c = (
        "#include <stdio.h>\n"
        "void app_main(void) {\n"
        '    printf("Hola ESP32-S3 con ESP-IDF\\n");\n'
        "}\n"
    )

    with patch(
        "sketch_backend.controllers.compilacion.compilar_proyecto",
        side_effect=_simular_compilacion_exitosa,
    ):
        resp = client.post(
            "/api/v1/sketch/compilar-codigo",
            json={
                "codigo": codigo_c,
                "nombre_proyecto": "demo_s3",
                "nombre_archivo": "main.c",
                "target": "esp32s3",
            },
        )

    assert resp.status_code == 200
    datos = resp.json()
    assert datos["success"] is True
    assert datos["framework"] == "ESP-IDF"
    assert datos["target"] == "esp32s3"
    assert len(datos["binaries"]) == 3

    offsets = {b["filename"]: b["flash_offset"] for b in datos["binaries"]}
    # En ESP32-S3 y ESP32-C3 el bootloader va en 0x0 (no en 0x1000)
    assert offsets["bootloader.bin"] == "0x0"
    assert offsets["partition-table.bin"] == "0x8000"
    assert offsets["esp32_sketch.bin"] == "0x10000"
    from archivo_backend.router import archivo_service

    archivo_service.cleanup_temp_project(datos["project_id"])


def test_compilar_codigo_esp32_clasico_usa_offset_bootloader_0x1000():
    app = FastAPI()
    registrar_sketch(app)
    client = TestClient(app)

    codigo_c = "void app_main(void) {}\n"

    with patch(
        "sketch_backend.controllers.compilacion.compilar_proyecto",
        side_effect=_simular_compilacion_exitosa,
    ):
        resp = client.post(
            "/api/v1/sketch/compilar-codigo",
            json={
                "codigo": codigo_c,
                "nombre_proyecto": "demo_esp32",
                "target": "esp32",
            },
        )

    assert resp.status_code == 200
    datos = resp.json()
    offsets = {b["filename"]: b["flash_offset"] for b in datos["binaries"]}
    assert offsets["bootloader.bin"] == "0x1000"
    from archivo_backend.router import archivo_service

    archivo_service.cleanup_temp_project(datos["project_id"])


def test_compilar_codigo_advierte_si_falta_app_main():
    app = FastAPI()
    registrar_sketch(app)
    client = TestClient(app)

    codigo_arduino = "void setup() {}\nvoid loop() {}\n"

    with patch(
        "sketch_backend.controllers.compilacion.compilar_proyecto",
        return_value={
            "success": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "undefined reference to `app_main'",
            "framework": "ESP-IDF",
            "bin_files": [],
            "target": "esp32s3",
            "error": "undefined reference to `app_main'",
        },
    ):
        resp = client.post(
            "/api/v1/sketch/compilar-codigo",
            json={"codigo": codigo_arduino, "target": "esp32s3"},
        )

    assert resp.status_code == 200
    datos = resp.json()
    assert datos["success"] is False
    assert any("app_main" in adv for adv in datos.get("warnings", []))
    from archivo_backend.router import archivo_service

    archivo_service.cleanup_temp_project(datos["project_id"])
