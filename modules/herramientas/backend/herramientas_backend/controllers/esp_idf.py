# Archivo: modules/herramientas/backend/herramientas_backend/controllers/esp_idf.py
"""Controlador ESP-IDF y herramientas Espressif (EIM y estandar) para el modulo Herramientas."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/herramientas", tags=["herramientas"])

TARGETS_ESP_IDF_SOPORTADOS = [
    "esp32",
    "esp32s2",
    "esp32s3",
    "esp32c3",
    "esp32c6",
]


def localizar_instalacion_idf() -> Optional[Path]:
    """Busca una instalacion local de Espressif ESP-IDF en C:/, E:/, variables y rutas EIM."""
    try:
        from sketch_backend.esp_idf_backend import localizar_idf

        encontrado = localizar_idf()
        if encontrado is not None:
            return encontrado
    except ImportError:
        pass

    candidatos: list[Path] = []
    for var in ("IDF_PATH", "ESP_IDF_PATH"):
        valor = os.environ.get(var)
        if valor:
            candidatos.append(Path(valor).expanduser())

    home = Path.home()
    raices = [
        Path(r"E:\DATOS\PROGRAMAS\esp\.espressif"),
        Path(r"C:\Espressif\frameworks"),
        Path(r"C:\espp"),
        Path(r"E:\esp\.espressif"),
        home / ".espressif",
    ]
    for base in raices:
        if base.is_dir():
            for sub in sorted(base.glob("v*/esp-idf"), reverse=True):
                if sub.is_dir():
                    candidatos.append(sub)
            for sub in sorted(base.glob("*esp-idf*"), reverse=True):
                if sub.is_dir():
                    candidatos.append(sub)

    for candidato in candidatos:
        if (candidato / "tools" / "idf.py").is_file():
            return candidato.resolve()

    return None


def _localizar_python_venv_espressif(idf_dir: Optional[Path]) -> Optional[Path]:
    """Obtiene el ejecutable Python del entorno virtual aislado de Espressif EIM si existe."""
    if idf_dir is None:
        return None
    carpeta_python = idf_dir.parent / "tools" / "python"
    if carpeta_python.is_dir():
        for exe in sorted(
            carpeta_python.glob("*/venv/Scripts/python.exe"), reverse=True
        ):
            if exe.is_file():
                return exe
        for exe in sorted(carpeta_python.glob("*/venv/bin/python"), reverse=True):
            if exe.is_file():
                return exe
    return None


def localizar_esptool(idf_dir: Optional[Path] = None) -> Optional[str]:
    """Localiza esptool en el entorno virtual de Espressif EIM o en el PATH del sistema."""
    if idf_dir is None:
        idf_dir = localizar_instalacion_idf()
    py_eim = _localizar_python_venv_espressif(idf_dir)
    if py_eim is not None:
        esptool_eim = py_eim.parent / ("esptool.exe" if os.name == "nt" else "esptool")
        if esptool_eim.is_file():
            return str(esptool_eim)

    return shutil.which("esptool") or shutil.which("esptool.py")


def _ejecutar_idf(comando: list[str], timeout: int = 60) -> dict:
    """Ejecuta un comando idf.py activando automaticamente el entorno Espressif/EIM."""
    idf_en_path = shutil.which("idf.py")
    entorno = os.environ.copy()

    if idf_en_path:
        ejecutable = [idf_en_path] + comando
    else:
        idf_dir = localizar_instalacion_idf()
        if idf_dir is None:
            return {
                "salida": "",
                "error": (
                    "ESP-IDF (idf.py) no encontrado. Configure IDF_PATH o instale "
                    "Espressif ESP-IDF."
                ),
                "exitoso": False,
            }

        python_prep = None
        idf_script_prep = None
        entorno_prep = None
        try:
            from sketch_backend.esp_idf_backend import preparar_entorno_idf

            python_prep, idf_script_prep, entorno_prep, err_prep = (
                preparar_entorno_idf()
            )
            if err_prep:
                python_prep = None
        except ImportError:
            pass

        if python_prep and idf_script_prep and entorno_prep:
            entorno = entorno_prep
            ejecutable = [python_prep, str(idf_script_prep)] + comando
        else:
            idf_script = idf_dir / "tools" / "idf.py"
            py_eim = _localizar_python_venv_espressif(idf_dir)
            python_exe = str(py_eim) if py_eim else (shutil.which("python") or "python")

            entorno["IDF_PATH"] = str(idf_dir)
            if (idf_dir.parent / "tools").is_dir():
                entorno.setdefault("IDF_TOOLS_PATH", str(idf_dir.parent))
                if py_eim is not None:
                    entorno.setdefault("IDF_PYTHON_ENV_PATH", str(py_eim.parent.parent))
                if not list(idf_dir.parent.glob("espidf.constraints.*.txt")):
                    entorno.setdefault("IDF_PYTHON_CHECK_CONSTRAINTS", "no")

            entorno["PYTHONUTF8"] = "1"
            entorno["PYTHONIOENCODING"] = "utf-8"
            ejecutable = [python_exe, str(idf_script)] + comando

    try:
        result = subprocess.run(
            ejecutable,
            env=entorno,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "salida": result.stdout.strip(),
            "error": result.stderr.strip() if result.stderr else "",
            "exitoso": result.returncode == 0,
        }
    except FileNotFoundError:
        return {
            "salida": "",
            "error": "idf.py no encontrado. Asegurate de tener ESP-IDF configurado.",
            "exitoso": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "salida": "",
            "error": "Tiempo de espera agotado.",
            "exitoso": False,
        }


@router.get(
    "/esp-idf/estado",
    summary="Estado del ecosistema Espressif (ESP-IDF + esptool)",
)
def estado_esp_idf() -> dict:
    """Verifica disponibilidad, version y rutas de Espressif ESP-IDF y esptool."""
    idf_dir = localizar_instalacion_idf()
    idf_en_path = shutil.which("idf.py")
    esptool_ruta = localizar_esptool(idf_dir)

    esp_idf_disponible = bool(idf_dir or idf_en_path)
    version = None
    if esp_idf_disponible:
        res_ver = _ejecutar_idf(["--version"], timeout=25)
        if res_ver["exitoso"] and res_ver["salida"]:
            # La ultima linea de idf.py --version contiene 'ESP-IDF vX.Y.Z'
            lineas = [l.strip() for l in res_ver["salida"].splitlines() if l.strip()]
            version = lineas[-1] if lineas else res_ver["salida"]

    return {
        "framework_principal": "Espressif ESP-IDF",
        "esp_idf_disponible": esp_idf_disponible,
        "idf_path": str(idf_dir) if idf_dir else None,
        "idf_py_en_path": idf_en_path,
        "version": version,
        "esptool_disponible": esptool_ruta is not None,
        "esptool_ruta": esptool_ruta,
        "targets_soportados": list(TARGETS_ESP_IDF_SOPORTADOS),
    }


@router.get("/esp-idf/version", summary="Obtener version de ESP-IDF")
def get_esp_idf_version() -> dict:
    """Obtiene la version de ESP-IDF instalada."""
    return _ejecutar_idf(["--version"])


@router.get("/esp-idf/sdkconfig", summary="Obtener configuracion SDK")
def get_sdkconfig() -> dict:
    """Obtiene la configuracion actual del SDK."""
    result = _ejecutar_idf(["menuconfig", "--json"])
    try:
        config = json.loads(result["salida"]) if result["exitoso"] else {}
        return {"configuracion": config, "exitoso": result["exitoso"]}
    except json.JSONDecodeError:
        return {"configuracion": {}, "exitoso": False}


@router.get("/esp-idf/menuconfig", summary="Abrir menu de configuracion")
def menuconfig() -> dict:
    """Abre el menu de configuracion interactivo de ESP-IDF."""
    return _ejecutar_idf(["menuconfig"])
