import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.responses import FileResponse
from sketch_backend.controllers import exportacion


class TestExportarBinario(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.carpeta = Path(self.temp_dir.name)
        self.binario = self.carpeta / "firmware.bin"
        self.binario.write_bytes(b"contenido de prueba")

    def tearDown(self):
        self.temp_dir.cleanup()

    def tarea_exitosa(self, archivos=None):
        return {
            "status": "completed",
            "result": {
                "success": True,
                "bin_files": archivos or [str(self.binario)],
            },
        }

    def test_tarea_inexistente(self):
        with patch.object(exportacion, "obtener_tarea", return_value=None):
            with self.assertRaises(HTTPException) as contexto:
                exportacion.exportar_binario("inexistente", "firmware.bin")

        self.assertEqual(contexto.exception.status_code, 404)

    def test_tarea_pendiente(self):
        tarea = {"status": "pending", "result": None}

        with patch.object(exportacion, "obtener_tarea", return_value=tarea):
            with self.assertRaises(HTTPException) as contexto:
                exportacion.exportar_binario("123", "firmware.bin")

        self.assertEqual(contexto.exception.status_code, 409)

    def test_compilacion_fallida(self):
        tarea = {
            "status": "completed",
            "result": {"success": False, "bin_files": []},
        }

        with patch.object(exportacion, "obtener_tarea", return_value=tarea):
            with self.assertRaises(HTTPException) as contexto:
                exportacion.exportar_binario("123", "firmware.bin")

        self.assertEqual(contexto.exception.status_code, 409)

    def test_binario_inexistente(self):
        tarea = self.tarea_exitosa([str(self.carpeta / "no_existe.bin")])

        with patch.object(exportacion, "obtener_tarea", return_value=tarea):
            with self.assertRaises(HTTPException) as contexto:
                exportacion.exportar_binario("123", "no_existe.bin")

        self.assertEqual(contexto.exception.status_code, 404)

    def test_archivo_no_binario(self):
        archivo = self.carpeta / "documento.txt"
        archivo.write_text("prueba", encoding="utf-8")
        tarea = self.tarea_exitosa([str(archivo)])

        with patch.object(exportacion, "obtener_tarea", return_value=tarea):
            with self.assertRaises(HTTPException) as contexto:
                exportacion.exportar_binario("123", "documento.txt")

        self.assertEqual(contexto.exception.status_code, 404)

    def test_nombres_binarios_duplicados(self):
        otra_carpeta = self.carpeta / "otra"
        otra_carpeta.mkdir()
        otro_binario = otra_carpeta / "firmware.bin"
        otro_binario.write_bytes(b"otro contenido")

        tarea = self.tarea_exitosa(
            [
                str(self.binario),
                str(otro_binario),
            ]
        )

        with patch.object(exportacion, "obtener_tarea", return_value=tarea):
            with self.assertRaises(HTTPException) as contexto:
                exportacion.exportar_binario("123", "firmware.bin")

        self.assertEqual(contexto.exception.status_code, 404)

    def test_descarga_exitosa(self):
        tarea = self.tarea_exitosa()

        with patch.object(exportacion, "obtener_tarea", return_value=tarea):
            respuesta = exportacion.exportar_binario("123", "firmware.bin")

        self.assertIsInstance(respuesta, FileResponse)
        self.assertEqual(Path(respuesta.path), self.binario)
        self.assertEqual(respuesta.media_type, "application/octet-stream")


if __name__ == "__main__":
    unittest.main(verbosity=2)
