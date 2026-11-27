import sys
import tempfile
import unittest

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sketch_backend.controllers.archivos import listar_archivos


class TestListarArchivos(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.proyecto = Path(self.temp_dir.name) / "proyecto"
        self.proyecto.mkdir()

        (self.proyecto / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.16)",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_proyecto_inexistente(self):
        with self.assertRaises(ValueError):
            listar_archivos(str(self.proyecto / "inexistente"))

    def test_proyecto_sin_cmakelists(self):
        proyecto = Path(self.temp_dir.name) / "sin_cmake"
        proyecto.mkdir()

        with self.assertRaises(ValueError):
            listar_archivos(str(proyecto))

    def test_lista_archivos_y_directorios(self):
        main = self.proyecto / "main"
        main.mkdir()

        codigo = main / "main.c"
        codigo.write_text("int main() {}", encoding="utf-8")

        resultado = listar_archivos(str(self.proyecto))

        self.assertEqual(resultado["total"], 3)

        rutas = [item["path"] for item in resultado["items"]]

        self.assertIn("CMakeLists.txt", rutas)
        self.assertIn("main", rutas)
        self.assertIn(str(Path("main") / "main.c"), rutas)

        archivo_codigo = next(
            item for item in resultado["items"]
            if item["path"] == str(Path("main") / "main.c")
        )

        self.assertEqual(archivo_codigo["type"], "file")
        self.assertEqual(archivo_codigo["size"], 13)

    def test_excluye_directorios_reservados(self):
        for nombre in (".git", ".venv", "build", "__pycache__"):
            carpeta = self.proyecto / nombre
            carpeta.mkdir()
            (carpeta / "oculto.txt").write_text(
                "no debe aparecer",
                encoding="utf-8",
            )

        resultado = listar_archivos(str(self.proyecto))
        rutas = [item["path"] for item in resultado["items"]]

        for nombre in (".git", ".venv", "build", "__pycache__"):
            self.assertFalse(
                any(nombre in Path(ruta).parts for ruta in rutas)
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
