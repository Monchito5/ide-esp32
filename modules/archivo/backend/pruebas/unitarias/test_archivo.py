# Archivo: modules/archivo/backend/pruebas/unitarias/test_archivo.py
"""Suite de pruebas unitarias e integracion para el modulo Archivo (Sprint 6 — S6-01)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from archivo_backend.config import (
    APP_NAME,
    DEFAULT_SKETCH_TEMPLATE,
    SUPPORTED_EXTENSIONS,
    ConfigManager,
    FileManager,
)
from archivo_backend.modulo import registrar
from archivo_backend.schemas import (
    CompilerInputResultRequest,
    CreateProjectFileRequest,
    OpenFileRequest,
    PreferencesModel,
    SaveFileRequest,
    SketchInfoRequest,
)
from archivo_backend.service import ArchivoService
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestConfigManager(unittest.TestCase):
    """Pruebas unitarias para ConfigManager y libraries_path."""

    def test_auto_creation_and_libraries_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
            self.assertEqual(APP_NAME, "ESP32 IDE")
            self.assertEqual(SUPPORTED_EXTENSIONS, (".ino", ".cpp", ".c", ".h"))
            self.assertTrue(os.path.isfile(cm.config_path))
            self.assertTrue(os.path.isdir(cm.settings["sketchbook_path"]))
            self.assertTrue(os.path.isdir(cm.get_libraries_path()))
            self.assertEqual(
                cm.get_libraries_path(),
                os.path.join(cm.settings["sketchbook_path"], "libraries"),
            )

    def test_persistence_derivation_and_reset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
            cm.settings["theme"] = "oscuro"
            cm.settings["font_size"] = 16
            cm.save_config()

            cm_reloaded = ConfigManager(base_dir=tmpdir)
            self.assertEqual(cm_reloaded.settings["theme"], "oscuro")
            self.assertEqual(cm_reloaded.settings["font_size"], 16)

            custom_sb = os.path.join(tmpdir, "MiSketchbook")
            with open(cm.config_path, "w", encoding="utf-8") as f_cfg:
                json.dump(
                    {
                        "language": "en",
                        "sketchbook_path": custom_sb,
                        "libraries_path": "",
                    },
                    f_cfg,
                )

            cm_legacy = ConfigManager(base_dir=tmpdir)
            self.assertEqual(
                cm_legacy.get_libraries_path(),
                os.path.join(custom_sb, "libraries"),
            )
            defaults = cm_legacy.reset_defaults()
            self.assertEqual(defaults["language"], "es")
            self.assertEqual(defaults["theme"], "claro")

    def test_recent_files_lifo_limit_remove_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
            paths = [os.path.join(tmpdir, f"sketch_{i}.ino") for i in range(12)]
            for p in paths:
                cm.add_recent_file(p)

            recent = cm.settings["recent_files"]
            self.assertEqual(len(recent), ConfigManager.MAX_RECENT_FILES)
            self.assertEqual(recent[0], os.path.abspath(paths[-1]))

            target = paths[5]
            cm.add_recent_file(target)
            self.assertEqual(cm.settings["recent_files"][0], os.path.abspath(target))
            self.assertEqual(
                cm.settings["recent_files"].count(os.path.abspath(target)), 1
            )

            cm.remove_recent_file(target)
            self.assertNotIn(os.path.abspath(target), cm.settings["recent_files"])
            cm.clear_recent_files()
            self.assertEqual(cm.settings["recent_files"], [])

    def test_sketchbook_listing_ignores_reserved_and_hidden(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
            sb = cm.settings["sketchbook_path"]

            for reserved in (
                "libraries",
                "build",
                ".git",
                "__pycache__",
                ".vscode",
                ".oculta",
            ):
                r_dir = os.path.join(sb, reserved)
                os.makedirs(r_dir, exist_ok=True)
                Path(r_dir, "ignored.ino").write_text("// ignored", encoding="utf-8")

            proj_dir = os.path.join(sb, "MiProyectoESP32")
            os.makedirs(proj_dir, exist_ok=True)
            Path(proj_dir, "auxiliar.cpp").write_text("// cpp", encoding="utf-8")
            Path(proj_dir, "MiProyectoESP32.ino").write_text(
                "// main ino", encoding="utf-8"
            )

            detailed = cm.list_sketchbook_projects_detailed()
            proj_entry = next(p for p in detailed if p["name"] == "MiProyectoESP32")
            self.assertEqual(
                proj_entry["display_name"], "MiProyectoESP32/MiProyectoESP32.ino"
            )
            self.assertEqual(len(proj_entry["files"]), 2)


class TestFileManager(unittest.TestCase):
    """Pruebas unitarias para FileManager."""

    def test_save_new_ino_and_backup_on_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
            cm.settings["auto_backup_on_save"] = True
            fm = FileManager(cm)

            raw_target = os.path.join(cm.settings["sketchbook_path"], "SensorTemp")
            resolved_path, _ = fm.write_file(
                raw_target, "// v1", create_project_folder=True
            )
            expected = os.path.abspath(
                os.path.join(
                    cm.settings["sketchbook_path"], "SensorTemp", "SensorTemp.ino"
                )
            )
            self.assertEqual(resolved_path, expected)

            _, gen_files_2 = fm.write_file(
                expected, "// v2", create_project_folder=True
            )
            self.assertIn(expected + ".bak", gen_files_2)
            self.assertEqual(
                Path(expected + ".bak").read_text(encoding="utf-8"), "// v1"
            )

    def test_open_utf8_latin1_and_path_traversal_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
            fm = FileManager(cm)

            latin_path = os.path.join(tmpdir, "legacy.ino")
            Path(latin_path).write_bytes(
                "// Configuracion clasica ñ á é".encode("latin-1")
            )
            _, content_lat, enc_lat = fm.read_file(latin_path)
            self.assertEqual(enc_lat, "latin-1")
            self.assertIn("ñ", content_lat)

            ino_path, _ = fm.write_file(
                os.path.join(cm.settings["sketchbook_path"], "BlinkESP32.ino"),
                DEFAULT_SKETCH_TEMPLATE,
                create_project_folder=True,
            )
            project_dir = os.path.dirname(ino_path)
            header_path = fm.create_project_file(
                project_dir, "config.h", "#pragma once\n"
            )
            self.assertTrue(os.path.isfile(header_path))

            with self.assertRaises(ValueError):
                fm.create_project_file(project_dir, "../evil.h", "")
            with self.assertRaises(ValueError):
                fm.create_project_file(project_dir, "bad.txt", "")
            with self.assertRaises(FileExistsError):
                fm.create_project_file(project_dir, "config.h", "")


class TestArchivoServiceAndRouter(unittest.TestCase):
    """Pruebas de integracion de ArchivoService, puente ESP-IDF y router HTTP."""

    def test_full_service_lifecycle_and_espidf_s3_offsets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            svc = ArchivoService(base_dir=tmpdir)
            res_new = svc.new_sketch()
            self.assertTrue(res_new.success)

            target_ino = os.path.join(
                svc.config_manager.settings["sketchbook_path"], "DemoESP.ino"
            )
            res_save = svc.save_sketch(
                SaveFileRequest(
                    filepath=target_ino,
                    content=DEFAULT_SKETCH_TEMPLATE,
                    create_project_folder=True,
                )
            )
            self.assertTrue(res_save.success)
            self.assertEqual(
                svc.get_current_project().metadata["project_name"], "DemoESP"
            )

            res_add = svc.create_project_file(
                CreateProjectFileRequest(
                    filename="pines.h", content="#define PIN_LED 2\n"
                )
            )
            self.assertTrue(res_add.success)
            self.assertEqual(len(svc.get_project_files().files), 2)
            self.assertTrue(svc.get_sketch_info(SketchInfoRequest()).success)

            custom_sb = os.path.join(tmpdir, "CustomSB")
            res_prefs = svc.update_preferences(
                PreferencesModel(sketchbook_path=custom_sb, libraries_path=None)
            )
            self.assertEqual(
                res_prefs.metadata["libraries_path"],
                os.path.join(custom_sb, "libraries"),
            )
            self.assertTrue(svc.reset_preferences().success)
            self.assertTrue(svc.close_sketch().success)
            self.assertTrue(
                svc.open_sketch(OpenFileRequest(filepath=res_save.files[0])).success
            )

            # Verificar preservacion de estructura CMake ESP-IDF y offset 0x0 para ESP32-S3
            prep = svc.prepare_espidf_project_from_source(
                "void app_main(void) {}\n",
                filename="main.c",
                project_name="s3_demo",
            )
            self.assertTrue(prep.success)
            build_boot = Path(prep.project_absolute_path) / "build" / "bootloader"
            build_boot.mkdir(parents=True, exist_ok=True)
            (build_boot / "bootloader.bin").write_bytes(b"\xe9\x00\x00\x00")
            entrega = svc.collect_build_results_for_flutter(
                CompilerInputResultRequest(
                    project_id=prep.project_id,
                    target="esp32s3",
                    compilation_success=True,
                )
            )
            self.assertTrue(entrega.success)
            self.assertEqual(entrega.binaries[0].flash_offset, "0x0")
            svc.cleanup_temp_project(prep.project_id)

    def test_router_endpoints_http(self) -> None:
        app = FastAPI()
        registrar(app)
        with TestClient(app) as client:
            r_tpl = client.get("/api/v1/archivo/plantilla-base")
            self.assertEqual(r_tpl.status_code, 200)
            r_new = client.post("/api/v1/archivo/nuevo")
            self.assertEqual(r_new.status_code, 200)
            self.assertTrue(r_new.json()["success"])
            r_act = client.get("/api/v1/archivo/actual")
            self.assertEqual(r_act.status_code, 200)
            r_sub = client.get("/api/v1/archivo/submenus")
            self.assertEqual(r_sub.status_code, 200)
            self.assertIn("libraries_path", r_sub.json()["metadata"])
