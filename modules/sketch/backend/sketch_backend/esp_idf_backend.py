"""Backend de compilacion ESP-IDF para el modulo Sketch."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

# Ruta predeterminada de ESP-IDF 6.1.
# Si IDF_PATH existe en el entorno, se utiliza primero.
IDF_PATH_PREDETERMINADO = Path(r"C:\espp\v6.1\esp-idf")


def _raices_busqueda_espressif() -> list[Path]:
    """Genera directorios candidatos donde EIM o el instalador de Espressif ubican ESP-IDF."""
    candidatos: list[Path] = []

    for var in ("IDF_PATH", "ESP_IDF_PATH"):
        idf_path_env = os.environ.get(var)
        if idf_path_env:
            candidatos.append(Path(idf_path_env).expanduser())

    espressif_env = os.environ.get("ESPRESSIF_PATH")
    raices_eim: list[Path] = []
    if espressif_env:
        raices_eim.append(Path(espressif_env).expanduser())

    home = Path.home()
    candidatos.extend(
        [
            IDF_PATH_PREDETERMINADO,
            Path(r"C:\esp\esp-idf"),
            home / "esp" / "esp-idf",
        ]
    )

    raices_eim.extend(
        [
            Path(r"E:\DATOS\PROGRAMAS\esp\.espressif"),
            Path(r"C:\Espressif\frameworks"),
            Path(r"C:\Espressif"),
            Path(r"C:\espp"),
            Path(r"E:\Espressif\frameworks"),
            Path(r"E:\esp\.espressif"),
            Path(r"D:\Espressif\frameworks"),
            Path(r"D:\esp\.espressif"),
            home / ".espressif" / "frameworks",
            home / ".espressif",
        ]
    )

    for base in raices_eim:
        if base.is_dir():
            if (base / "tools" / "idf.py").is_file():
                candidatos.append(base)
            for sub in sorted(base.glob("v*/esp-idf"), reverse=True):
                if sub.is_dir():
                    candidatos.append(sub)
            for sub in sorted(base.glob("*esp-idf*"), reverse=True):
                if sub.is_dir():
                    candidatos.append(sub)

    return candidatos


def localizar_idf():
    """Localiza la instalacion de Espressif ESP-IDF (incluyendo instalaciones EIM en C:/ y E:/)."""
    for candidato in _raices_busqueda_espressif():
        if os.name == "nt":
            if (candidato / "export.bat").is_file() or (
                candidato / "tools" / "idf.py"
            ).is_file():
                return candidato.resolve()
        else:
            if (candidato / "export.sh").is_file() or (
                candidato / "tools" / "idf.py"
            ).is_file():
                return candidato.resolve()

    return None


def _variables_eim_para_idf(idf_path: Path) -> dict[str, str]:
    """Detecta estructura de Espressif Installation Manager (EIM) junto a esp-idf."""
    extras: dict[str, str] = {"IDF_PATH": str(idf_path)}
    contenedor_version = idf_path.parent
    carpeta_tools = contenedor_version / "tools"

    if carpeta_tools.is_dir():
        if not os.environ.get("IDF_TOOLS_PATH"):
            extras["IDF_TOOLS_PATH"] = str(contenedor_version)

        if not os.environ.get("IDF_PYTHON_ENV_PATH"):
            venvs = (
                sorted((carpeta_tools / "python").glob("*/venv"), reverse=True)
                if (carpeta_tools / "python").is_dir()
                else []
            )
            if venvs:
                extras["IDF_PYTHON_ENV_PATH"] = str(venvs[0])

        constraints_en_raiz = list(contenedor_version.glob("espidf.constraints.*.txt"))
        if not constraints_en_raiz and not os.environ.get(
            "IDF_PYTHON_CHECK_CONSTRAINTS"
        ):
            extras["IDF_PYTHON_CHECK_CONSTRAINTS"] = "no"

    return extras


def preparar_entorno_idf():
    """Prepara y recupera las variables del entorno Espressif ESP-IDF (estandar y EIM)."""
    idf_path = localizar_idf()

    if idf_path is None:
        idf_en_path = shutil.which("idf.py")
        python_activo = shutil.which("python")
        if idf_en_path and python_activo:
            entorno_activo = os.environ.copy()
            entorno_activo["PYTHONUTF8"] = "1"
            entorno_activo["PYTHONIOENCODING"] = "utf-8"
            return python_activo, Path(idf_en_path), entorno_activo, None

        return (
            None,
            None,
            None,
            (
                "No se encontro Espressif ESP-IDF. Verifica la instalacion "
                "o configura la variable de entorno IDF_PATH."
            ),
        )

    idf_script = idf_path / "tools" / "idf.py"

    if not idf_script.is_file():
        return None, None, None, (f"No se encontro el archivo de ESP-IDF: {idf_script}")

    vars_base = os.environ.copy()
    vars_base.update(_variables_eim_para_idf(idf_path))
    vars_base["PYTHONUTF8"] = "1"
    vars_base["PYTHONIOENCODING"] = "utf-8"

    # En sistemas Linux/macOS (incluyendo CI), activar export.sh o entorno directo
    if os.name != "nt":
        export_sh = idf_path / "export.sh"
        entorno = vars_base.copy()
        if export_sh.is_file():
            proc_posix = subprocess.run(
                ["bash", "-c", f'source "{export_sh}" >/dev/null 2>&1 && env'],
                env=entorno,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if proc_posix.returncode == 0:
                for linea in proc_posix.stdout.splitlines():
                    if "=" in linea:
                        k, v = linea.split("=", 1)
                        entorno[k] = v
        python_exe = shutil.which("python3", path=entorno.get("PATH")) or shutil.which(
            "python", path=entorno.get("PATH")
        )
        if not python_exe:
            return None, None, None, "No se encontro interprete Python para ESP-IDF."
        return python_exe, idf_script, entorno, None

    export_bat = idf_path / "export.bat"
    if not export_bat.is_file():
        python_exe = shutil.which("python", path=vars_base.get("PATH"))
        if python_exe:
            return python_exe, idf_script, vars_base, None
        return None, None, None, f"No se encontro export.bat en {idf_path}"

    # Configurar UTF-8, activar ESP-IDF (con soporte EIM) y recuperar sus variables.
    comando_entorno = f"chcp 65001 >nul && " f'call "{export_bat}" >nul && ' f"set"

    proceso_entorno = subprocess.run(
        comando_entorno,
        shell=True,
        env=vars_base,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )

    if proceso_entorno.returncode != 0:
        detalle = (
            proceso_entorno.stderr.strip()
            or proceso_entorno.stdout.strip()
            or "No se pudo activar el entorno ESP-IDF."
        )

        return None, None, None, detalle

    # Recuperar las variables del proceso cmd.exe.
    entorno = os.environ.copy()

    for linea in proceso_entorno.stdout.splitlines():
        if "=" in linea and not linea.startswith("="):
            clave, valor = linea.split("=", 1)

            # Windows trata las variables de entorno sin distinguir
            # mayusculas y minusculas. Normalizar PATH evita usar
            # accidentalmente el Python global.
            if clave.lower() == "path":
                entorno["PATH"] = valor
            else:
                entorno[clave] = valor

    # Evitar problemas de codificacion en Windows.
    entorno["PYTHONUTF8"] = "1"
    entorno["PYTHONIOENCODING"] = "utf-8"

    # export.bat coloca el Python virtual de ESP-IDF al inicio del PATH.
    python_exe = shutil.which(
        "python",
        path=entorno.get("PATH"),
    )

    if not python_exe:
        return (
            None,
            None,
            None,
            ("ESP-IDF se activo, pero no se encontro su Python virtual."),
        )

    return python_exe, idf_script, entorno, None


def crear_resultado(
    success=False,
    returncode=None,
    stdout="",
    stderr="",
    command=None,
    proyecto=None,
    build=None,
    bin_files=None,
    error=None,
    target=None,
):
    """Devuelve un resultado con una estructura consistente."""
    resultado = {
        "success": success,
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "command": command or [],
        "framework": "ESP-IDF",
        "project_path": str(proyecto) if proyecto else None,
        "build_path": str(build) if build else None,
        "artifacts_dir": str(build) if build else None,
        "bin_files": bin_files or [],
        "target": target,
    }

    if error:
        resultado["error"] = error

    return resultado


def compilar_proyecto(ruta_proyecto, timeout=1800, target=None):
    """Prepara ESP-IDF, compila el proyecto y devuelve un JSON normalizado."""
    proyecto = Path(ruta_proyecto).expanduser().resolve()
    build = proyecto / "build"

    if not proyecto.is_dir():
        return crear_resultado(
            error=f"No existe la carpeta del proyecto: {proyecto}",
            proyecto=proyecto,
            build=build,
            target=target,
        )

    if not (proyecto / "CMakeLists.txt").is_file():
        return crear_resultado(
            error="Falta CMakeLists.txt en la raiz del proyecto.",
            proyecto=proyecto,
            build=build,
            target=target,
        )

    if timeout <= 0:
        return crear_resultado(
            error="El tiempo maximo debe ser mayor que cero.",
            proyecto=proyecto,
            build=build,
            target=target,
        )

    comandos = []

    try:
        # Preparar automaticamente el entorno ESP-IDF.
        python_exe, idf_script, entorno, error_entorno = preparar_entorno_idf()

        if error_entorno:
            return crear_resultado(
                proyecto=proyecto,
                build=build,
                target=target,
                error=error_entorno,
            )

        # Configurar el objetivo si fue especificado.
        if target:
            comando_target = [
                python_exe,
                str(idf_script),
                "set-target",
                target,
            ]

            comandos.append(comando_target)

            configuracion = subprocess.run(
                comando_target,
                cwd=str(proyecto),
                env=entorno,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )

            if configuracion.returncode != 0:
                detalle = (
                    configuracion.stderr.strip()
                    or configuracion.stdout.strip()
                    or "ESP-IDF no proporciono detalles adicionales."
                )

                return crear_resultado(
                    returncode=configuracion.returncode,
                    stdout=configuracion.stdout,
                    stderr=configuracion.stderr,
                    command=comandos,
                    proyecto=proyecto,
                    build=build,
                    target=target,
                    error=(
                        "No se pudo configurar el objetivo ESP-IDF. "
                        f"Detalle: {detalle}"
                    ),
                )

        # Ejecutar la compilacion.
        comando_build = [
            python_exe,
            str(idf_script),
            "build",
        ]

        comandos.append(comando_build)

        proceso = subprocess.run(
            comando_build,
            cwd=str(proyecto),
            env=entorno,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )

        compilacion_ok = proceso.returncode == 0

        # Detectar los archivos BIN generados.
        bin_files = []

        if compilacion_ok and build.is_dir():
            bin_files = sorted(
                str(archivo.resolve())
                for archivo in build.rglob("*.bin")
                if archivo.is_file() and "CMakeFiles" not in archivo.parts
            )

        detalle_error = None

        if not compilacion_ok:
            detalle_error = (
                proceso.stderr.strip()
                or proceso.stdout.strip()
                or "La compilacion fallo sin proporcionar detalles."
            )

        return crear_resultado(
            success=compilacion_ok,
            returncode=proceso.returncode,
            stdout=proceso.stdout,
            stderr=proceso.stderr,
            command=comandos,
            proyecto=proyecto,
            build=build,
            bin_files=bin_files,
            target=target,
            error=detalle_error,
        )

    except subprocess.TimeoutExpired:
        return crear_resultado(
            command=comandos,
            proyecto=proyecto,
            build=build,
            target=target,
            error=f"Tiempo maximo excedido ({timeout} segundos).",
        )

    except OSError as exc:
        return crear_resultado(
            command=comandos,
            proyecto=proyecto,
            build=build,
            target=target,
            error=f"No se pudo ejecutar ESP-IDF: {exc}",
        )


def main():
    """Procesa los argumentos de la linea de comandos."""
    parser = argparse.ArgumentParser(
        description="Backend ESP-IDF para ESP32, sin Arduino CLI."
    )

    parser.add_argument(
        "project",
        help="Ruta de la carpeta raiz de un proyecto ESP-IDF.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Tiempo maximo por operacion, en segundos.",
    )

    parser.add_argument(
        "--target",
        help="Objetivo ESP-IDF, por ejemplo esp32 o esp32s3.",
    )

    args = parser.parse_args()

    resultado = compilar_proyecto(
        args.project,
        timeout=args.timeout,
        target=args.target,
    )

    print(json.dumps(resultado, ensure_ascii=False, indent=2))

    return 0 if resultado["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
