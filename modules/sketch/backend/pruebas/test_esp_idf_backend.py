
import sys
import tempfile
import unittest
import subprocess

from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sketch_backend import esp_idf_backend as backend


class TestCompilarProyecto(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.proyecto = Path(self.temp_dir.name) / "proyecto"
        self.proyecto.mkdir()

        (self.proyecto / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.16)",
            encoding="utf-8"
        )

        self.build = self.proyecto / "build"
        self.build.mkdir()

        self.entorno_falso = (
            "python.exe",
            Path("idf.py"),
            {},
            None
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_proyecto_inexistente(self):
        with patch.object(backend, "preparar_entorno_idf") as preparar:
            resultado = backend.compilar_proyecto(
                self.proyecto / "inexistente"
            )

        self.assertFalse(resultado["success"])
        self.assertIn("No existe la carpeta", resultado["error"])
        preparar.assert_not_called()

    def test_proyecto_sin_cmakelists(self):
        proyecto_sin_cmake = Path(self.temp_dir.name) / "sin_cmake"
        proyecto_sin_cmake.mkdir()

        with patch.object(backend, "preparar_entorno_idf") as preparar:
            resultado = backend.compilar_proyecto(proyecto_sin_cmake)

        self.assertFalse(resultado["success"])
        self.assertIn("CMakeLists.txt", resultado["error"])
        preparar.assert_not_called()

    def test_timeout_invalido(self):
        with patch.object(
            backend,
            "preparar_entorno_idf",
            return_value=self.entorno_falso
        ) as preparar:
            resultado = backend.compilar_proyecto(
                self.proyecto,
                timeout=0
            )

        self.assertFalse(resultado["success"])
        preparar.assert_not_called()

    def test_error_al_configurar_target(self):
        respuesta_falsa = subprocess.CompletedProcess(
            args=[],
            returncode=2,
            stdout="",
            stderr="target failed"
        )

        with patch.object(
            backend,
            "preparar_entorno_idf",
            return_value=self.entorno_falso
        ), patch.object(
            backend.subprocess,
            "run",
            return_value=respuesta_falsa
        ) as ejecutar:

            resultado = backend.compilar_proyecto(
                self.proyecto,
                target="esp32"
            )

        self.assertFalse(resultado["success"])
        self.assertIn("No se pudo configurar el objetivo", resultado["error"])
        self.assertEqual(ejecutar.call_count, 1)

    def test_error_de_compilacion(self):
        respuesta_falsa = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="build failed",
            stderr="compile error"
        )

        with patch.object(
            backend,
            "preparar_entorno_idf",
            return_value=self.entorno_falso
        ), patch.object(
            backend.subprocess,
            "run",
            return_value=respuesta_falsa
        ):

            resultado = backend.compilar_proyecto(self.proyecto)

        self.assertFalse(resultado["success"])
        self.assertEqual(resultado["returncode"], 1)
        self.assertIn("compile error", resultado["error"])

    def test_compilacion_exitosa_identifica_binarios(self):
        bootloader = self.build / "bootloader"
        bootloader.mkdir()

        (bootloader / "bootloader.bin").write_bytes(b"boot")
        (self.build / "proyecto.bin").write_bytes(b"app")

        cmake_files = self.build / "CMakeFiles"
        cmake_files.mkdir()
        (cmake_files / "ignorar.bin").write_bytes(b"ignorar")

        respuesta_falsa = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="build ok",
            stderr=""
        )

        with patch.object(
            backend,
            "preparar_entorno_idf",
            return_value=self.entorno_falso
        ), patch.object(
            backend.subprocess,
            "run",
            return_value=respuesta_falsa
        ):

            resultado = backend.compilar_proyecto(self.proyecto)

        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["returncode"], 0)
        self.assertEqual(len(resultado["bin_files"]), 2)

        nombres = [Path(ruta).name for ruta in resultado["bin_files"]]

        self.assertIn("bootloader.bin", nombres)
        self.assertIn("proyecto.bin", nombres)
        self.assertNotIn("ignorar.bin", nombres)


if __name__ == "__main__":
    unittest.main(verbosity=2)
