"""
Suite de pruebas unitarias y de integración para el módulo Archivo de ESP32 IDE.

Cubre:
- TestConfigManager
- TestFileManager
- TestIDEApp
- TestArchivoServiceIntegration (omitida si fastapi/pydantic no están instalados)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

# Resolver la ruta de modules/archivo tanto si se ejecuta desde la raíz del monorepo
# como desde modules/archivo/
_HERE = Path(__file__).resolve().parent
_CANDIDATES = [_HERE.parent, _HERE.parent / "modules" / "archivo"]
ARCHIVO_DIR = next(
    (p for p in _CANDIDATES if (p / "main.py").is_file()),
    _HERE.parent,
)
if str(ARCHIVO_DIR) not in sys.path:
    sys.path.insert(0, str(ARCHIVO_DIR))

BACKEND_ROOT = ARCHIVO_DIR / "integracion_fastapi_flutter" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import main as archivo_main  # noqa: E402
from main import (  # noqa: E402
    APP_NAME,
    DEFAULT_SKETCH_TEMPLATE,
    SUPPORTED_EXTENSIONS,
    ConfigManager,
    ExamplesCatalog,
    FileManager,
    IDEApp,
)

try:
    import fastapi  # noqa: F401
    import pydantic  # noqa: F401

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


class TestConfigManager(unittest.TestCase):
    """Pruebas unitarias para ConfigManager."""

    def test_auto_creation_and_libraries_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
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

            # Simular un config_archivo.json previo sin libraries_path
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
            self.assertTrue(os.path.isdir(cm_legacy.get_libraries_path()))

            defaults = cm_legacy.reset_defaults()
            self.assertEqual(defaults["language"], "es")
            self.assertEqual(defaults["theme"], "claro")
            self.assertEqual(defaults["sketchbook_path"], cm_legacy.default_sketchbook)

    def test_recent_files_lifo_limit_remove_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
            paths = [os.path.join(tmpdir, f"sketch_{i}.ino") for i in range(12)]
            for p in paths:
                cm.add_recent_file(p)

            recent = cm.settings["recent_files"]
            self.assertEqual(len(recent), ConfigManager.MAX_RECENT_FILES)
            self.assertEqual(recent[0], os.path.abspath(paths[-1]))
            self.assertNotIn(os.path.abspath(paths[0]), recent)
            self.assertNotIn(os.path.abspath(paths[1]), recent)

            # Re-agregar uno existente debe moverlo al inicio sin duplicar
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

            # Crear carpetas reservadas y ocultas con archivos .ino que deben ignorarse
            for reserved in ("libraries", "build", ".git", "__pycache__", ".vscode", ".idea", ".oculta"):
                r_dir = os.path.join(sb, reserved)
                os.makedirs(r_dir, exist_ok=True)
                with open(os.path.join(r_dir, "ignored.ino"), "w", encoding="utf-8") as f:
                    f.write("// ignored")

            # Crear proyecto estándar con varios archivos donde <carpeta>.ino debe priorizarse
            proj_dir = os.path.join(sb, "MiProyectoESP32")
            os.makedirs(proj_dir, exist_ok=True)
            with open(os.path.join(proj_dir, "auxiliar.cpp"), "w", encoding="utf-8") as f:
                f.write("// cpp")
            with open(os.path.join(proj_dir, "config.h"), "w", encoding="utf-8") as f:
                f.write("// h")
            with open(os.path.join(proj_dir, "MiProyectoESP32.ino"), "w", encoding="utf-8") as f:
                f.write("// main ino")

            # Proyecto suelto en raíz del Sketchbook
            loose_ino = os.path.join(sb, "Suelto.ino")
            with open(loose_ino, "w", encoding="utf-8") as f:
                f.write("// loose")

            simple = cm.list_sketchbook_projects()
            names = [name for name, _ in simple]
            self.assertIn("MiProyectoESP32/MiProyectoESP32.ino", names)
            self.assertIn("Suelto.ino", names)
            for ignored in ("libraries", "build", ".git", "__pycache__", ".vscode", ".idea", ".oculta"):
                self.assertFalse(any(ignored in n for n in names))

            detailed = cm.list_sketchbook_projects_detailed()
            proj_entry = next(p for p in detailed if p["name"] == "MiProyectoESP32")
            self.assertEqual(proj_entry["display_name"], "MiProyectoESP32/MiProyectoESP32.ino")
            self.assertEqual(
                proj_entry["path"],
                os.path.join(proj_dir, "MiProyectoESP32.ino"),
            )
            self.assertEqual(proj_entry["project_dir"], proj_dir)
            self.assertTrue(proj_entry["is_folder_project"])
            self.assertEqual(len(proj_entry["files"]), 3)


class TestFileManager(unittest.TestCase):
    """Pruebas unitarias para FileManager."""

    def test_save_new_ino_creates_project_folder_and_inplace_overwrite_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
            cm.settings["auto_backup_on_save"] = True
            fm = FileManager(cm)

            # Guardar .ino nuevo (sin extensión) debe crear <parent>/<Nombre>/<Nombre>.ino
            raw_target = os.path.join(cm.settings["sketchbook_path"], "SensorTemp")
            resolved_path, gen_files = fm.write_file(
                raw_target,
                "// v1",
                create_project_folder=True,
            )
            expected_path = os.path.abspath(
                os.path.join(cm.settings["sketchbook_path"], "SensorTemp", "SensorTemp.ino")
            )
            self.assertEqual(resolved_path, expected_path)
            self.assertEqual(gen_files, [expected_path])
            self.assertTrue(os.path.isfile(expected_path))

            # Sobrescritura in-place con archivo existente: no mueve y genera .bak
            resolved_2, gen_files_2 = fm.write_file(
                expected_path,
                "// v2",
                create_project_folder=True,
            )
            self.assertEqual(resolved_2, expected_path)
            self.assertIn(expected_path + ".bak", gen_files_2)
            self.assertTrue(os.path.isfile(expected_path + ".bak"))
            with open(expected_path + ".bak", "r", encoding="utf-8") as fb:
                self.assertEqual(fb.read(), "// v1")
            with open(expected_path, "r", encoding="utf-8") as fn:
                self.assertEqual(fn.read(), "// v2")

    def test_save_header_without_extra_subfolder(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
            fm = FileManager(cm)
            header_target = os.path.join(tmpdir, "pines.h")
            resolved, _ = fm.write_file(
                header_target,
                "#define LED_PIN 2\n",
                create_project_folder=True,
            )
            self.assertEqual(resolved, os.path.abspath(header_target))
            self.assertTrue(os.path.isfile(header_target))

    def test_open_folder_utf8_latin1_and_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
            fm = FileManager(cm)

            proj_dir = os.path.join(tmpdir, "ProyectoWiFi")
            os.makedirs(proj_dir, exist_ok=True)
            ino_path = os.path.join(proj_dir, "ProyectoWiFi.ino")
            with open(ino_path, "w", encoding="utf-8") as f_utf:
                f_utf.write("// Código UTF-8 áéíóú 🚀")

            resolved, content, enc = fm.read_file(proj_dir)
            self.assertEqual(resolved, os.path.abspath(ino_path))
            self.assertEqual(enc, "utf-8")
            self.assertIn("🚀", content)

            # Archivo codificado en Latin-1 (bytes inválidos en UTF-8)
            latin_path = os.path.join(tmpdir, "legacy.ino")
            with open(latin_path, "wb") as f_lat:
                f_lat.write("// Configuración clásica ñ á é".encode("latin-1"))

            _, content_lat, enc_lat = fm.read_file(latin_path)
            self.assertEqual(enc_lat, "latin-1")
            self.assertIn("Configuración", content_lat)

            # Errores esperados
            bad_ext = os.path.join(tmpdir, "notas.txt")
            with open(bad_ext, "w", encoding="utf-8") as f_bad:
                f_bad.write("texto")
            with self.assertRaises(ValueError):
                fm.resolve_open_path(bad_ext)
            with self.assertRaises(ValueError):
                fm.resolve_save_path(os.path.join(tmpdir, "script.py"))
            with self.assertRaises(FileNotFoundError):
                fm.resolve_open_path(os.path.join(tmpdir, "no_existe.ino"))

    def test_project_info_create_file_backup_and_stats(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(base_dir=tmpdir)
            fm = FileManager(cm)

            empty_info = fm.get_project_info(None)
            self.assertFalse(empty_info["has_active_project"])
            self.assertEqual(empty_info["sketchbook_path"], cm.settings["sketchbook_path"])
            self.assertEqual(empty_info["libraries_path"], cm.get_libraries_path())

            ino_path, _ = fm.write_file(
                os.path.join(cm.settings["sketchbook_path"], "BlinkESP32.ino"),
                DEFAULT_SKETCH_TEMPLATE,
                create_project_folder=True,
            )
            project_dir = os.path.dirname(ino_path)

            # Crear archivo secundario válido
            header_path = fm.create_project_file(project_dir, "config.h", "#pragma once\n")
            self.assertTrue(os.path.isfile(header_path))

            # Bloqueo de path traversal, extensión inválida y duplicados
            with self.assertRaises(ValueError):
                fm.create_project_file(project_dir, "../evil.h", "")
            with self.assertRaises(ValueError):
                fm.create_project_file(project_dir, "sub/evil.h", "")
            with self.assertRaises(ValueError):
                fm.create_project_file(project_dir, "sub\\evil.h", "")
            with self.assertRaises(ValueError):
                fm.create_project_file(project_dir, "bad.txt", "")
            with self.assertRaises(FileExistsError):
                fm.create_project_file(project_dir, "config.h", "")

            info = fm.get_project_info(ino_path)
            self.assertTrue(info["has_active_project"])
            self.assertEqual(info["project_name"], "BlinkESP32")
            self.assertEqual(info["project_dir"], project_dir)
            self.assertEqual(info["main_file"], ino_path)
            self.assertTrue(info["is_standard_arduino_layout"])
            self.assertIn(ino_path, info["project_files"])
            self.assertIn(header_path, info["project_files"])

            # create_backup desde disco y con content_override
            bak_disk = fm.create_backup(ino_path)
            self.assertTrue(os.path.isfile(bak_disk))
            bak_override = fm.create_backup(ino_path, content_override="// override")
            with open(bak_override, "r", encoding="utf-8") as f_bo:
                self.assertEqual(f_bo.read(), "// override")

            # get_sketch_stats
            stats = fm.get_sketch_stats("linea1\nlinea2", filepath=ino_path, encoding="utf-8")
            self.assertEqual(stats["lines"], 2)
            self.assertEqual(stats["chars"], len("linea1\nlinea2"))
            self.assertEqual(stats["size_bytes"], len("linea1\nlinea2".encode("utf-8")))
            self.assertEqual(stats["encoding"], "utf-8")
            self.assertEqual(stats["project_info"]["project_name"], "BlinkESP32")


class TestIDEApp(unittest.TestCase):
    """Pruebas de interfaz tkinter para IDEApp (con ventana oculta y mocks de diálogos)."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.cm = ConfigManager(base_dir=self._tmpdir.name)
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = IDEApp(self.root, config_manager=self.cm)

    def tearDown(self) -> None:
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass
        self._tmpdir.cleanup()

    def test_branding_wifi_category_and_no_cloud_features(self) -> None:
        self.assertEqual(APP_NAME, "ESP32 IDE")
        self.assertIn("ESP32 IDE", self.root.title())
        self.assertIn("04. WiFi ESP32", ExamplesCatalog.CATEGORIES)
        self.assertEqual(SUPPORTED_EXTENSIONS, (".ino", ".cpp", ".c", ".h"))

        # Verificar ausencia total de CloudManager o menciones a nube
        self.assertFalse(hasattr(archivo_main, "CloudManager"))
        end_idx = self.app.file_dropdown.index("end") or 0
        labels = []
        for idx in range(end_idx + 1):
            try:
                lbl = self.app.file_dropdown.entrycget(idx, "label")
                if lbl:
                    labels.append(lbl.lower())
            except tk.TclError:
                pass
        for forbidden in ("nube", "cloud", "firebase", "supabase"):
            self.assertFalse(any(forbidden in lbl for lbl in labels))

        self.assertFalse(self.root.bind("<Alt-Control-n>"))
        self.assertFalse(self.root.bind("<Control-Alt-n>"))

    def test_initial_and_new_file_load_default_template(self) -> None:
        self.assertIsNone(self.app.current_file)
        self.assertFalse(bool(self.app.editor.edit_modified()))
        self.assertEqual(self.app.editor.get("1.0", "end-1c"), DEFAULT_SKETCH_TEMPLATE)

        self.app.editor.insert("1.0", "// cambio\n")
        self.app.editor.edit_modified(False)
        self.app.new_file()
        self.assertIsNone(self.app.current_file)
        self.assertFalse(bool(self.app.editor.edit_modified()))
        self.assertEqual(self.app.editor.get("1.0", "end-1c"), DEFAULT_SKETCH_TEMPLATE)

    def test_close_file_handles_unsaved_changes(self) -> None:
        self.app.editor.insert("1.0", "// modificado\n")
        self.app.editor.edit_modified(True)

        with patch("main.messagebox.askyesnocancel", return_value=None) as mock_ask:
            self.app.close_file()
            mock_ask.assert_called_once()
        self.assertIn("// modificado", self.app.editor.get("1.0", "end-1c"))

        with patch("main.messagebox.askyesnocancel", return_value=False) as mock_ask:
            self.app.close_file()
            mock_ask.assert_called_once()
        self.assertEqual(self.app.editor.get("1.0", "end-1c"), "")
        self.assertIsNone(self.app.current_file)

    def test_exit_app_handles_unsaved_changes(self) -> None:
        self.app.editor.insert("1.0", "// pendiente\n")
        self.app.editor.edit_modified(True)

        with patch("main.messagebox.askyesnocancel", return_value=None):
            self.app.exit_app()
        self.assertTrue(bool(self.root.winfo_exists()))

        with patch("main.messagebox.askyesnocancel", return_value=False):
            self.app.exit_app()
        try:
            exists = bool(self.root.winfo_exists())
        except tk.TclError:
            exists = False
        self.assertFalse(exists)

    def test_shortcut_bindings_on_root_and_editor(self) -> None:
        expected_sequences = [
            "<Control-n>",
            "<Control-N>",
            "<Control-o>",
            "<Control-O>",
            "<Control-w>",
            "<Control-W>",
            "<Control-s>",
            "<Control-S>",
            "<Control-Shift-s>",
            "<Control-Shift-S>",
            "<Control-comma>",
            "<Control-q>",
            "<Control-Q>",
        ]
        for seq in expected_sequences:
            self.assertTrue(self.app.root.bind(seq), f"Falta binding en root para {seq}")
            self.assertTrue(self.app.editor.bind(seq), f"Falta binding en editor para {seq}")


@unittest.skipUnless(HAS_FASTAPI, "FastAPI/Pydantic no instalados en este entorno")
class TestArchivoServiceIntegration(unittest.TestCase):
    """Pruebas de integración de ArchivoService (requieren FastAPI y Pydantic)."""

    def test_full_service_lifecycle(self) -> None:
        from app.modules.archivo.schemas import (
            CreateProjectFileRequest,
            OpenFileRequest,
            PreferencesModel,
            SaveFileRequest,
            SketchInfoRequest,
        )
        from app.modules.archivo.service import ArchivoService

        with tempfile.TemporaryDirectory() as tmpdir:
            svc = ArchivoService(base_dir=tmpdir)

            res_new = svc.new_sketch()
            self.assertTrue(res_new.success)
            self.assertEqual(res_new.content, DEFAULT_SKETCH_TEMPLATE)
            self.assertFalse(res_new.metadata["has_active_project"])

            target_ino = os.path.join(svc.config_manager.settings["sketchbook_path"], "DemoESP.ino")
            res_save = svc.save_sketch(
                SaveFileRequest(
                    filepath=target_ino,
                    content=DEFAULT_SKETCH_TEMPLATE,
                    create_project_folder=True,
                )
            )
            self.assertTrue(res_save.success)
            self.assertTrue(res_save.metadata["has_active_project"])
            self.assertTrue(res_save.metadata["is_standard_arduino_layout"])

            res_cur = svc.get_current_project()
            self.assertEqual(res_cur.metadata["project_name"], "DemoESP")

            res_add = svc.create_project_file(
                CreateProjectFileRequest(filename="pines.h", content="#define PIN_LED 2\n")
            )
            self.assertTrue(res_add.success)

            res_files = svc.get_project_files()
            self.assertEqual(len(res_files.files), 2)

            res_info = svc.get_sketch_info(SketchInfoRequest())
            self.assertTrue(res_info.success)
            self.assertGreater(res_info.metadata["lines"], 0)

            res_sub = svc.get_submenus_data()
            self.assertIn("sketchbook_path", res_sub.metadata)
            self.assertIn("libraries_path", res_sub.metadata)
            self.assertEqual(len(res_sub.metadata["sketchbook_projects"]), 1)

            custom_sb = os.path.join(tmpdir, "CustomSB")
            res_prefs = svc.update_preferences(
                PreferencesModel(sketchbook_path=custom_sb, libraries_path=None)
            )
            self.assertEqual(
                res_prefs.metadata["libraries_path"],
                os.path.join(custom_sb, "libraries"),
            )

            res_reset = svc.reset_preferences()
            self.assertTrue(res_reset.success)

            res_clear = svc.clear_recent_files()
            self.assertEqual(res_clear.metadata["recent_files"], [])

            res_close = svc.close_sketch()
            self.assertTrue(res_close.success)
            self.assertIsNone(svc.current_file)

            res_open = svc.open_sketch(OpenFileRequest(filepath=res_save.files[0]))
            self.assertTrue(res_open.success)
            self.assertEqual(svc.current_file, res_save.files[0])


if __name__ == "__main__":
    unittest.main()
