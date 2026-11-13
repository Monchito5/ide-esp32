
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


def localizar_idf():
    """Localiza la instalacion de ESP-IDF."""
    candidatos = []

    idf_path_env = os.environ.get("IDF_PATH")

    if idf_path_env:
        candidatos.append(Path(idf_path_env))

    candidatos.append(IDF_PATH_PREDETERMINADO)

    for candidato in candidatos:
        if (candidato / "export.bat").is_file():
            return candidato.resolve()

    return None


def preparar_entorno_idf():
    """Ejecuta export.bat y recupera las variables de ESP-IDF."""
    idf_path = localizar_idf()

    if idf_path is None:
        return None, None, None, (
            "No se encontro ESP-IDF. Verifica la instalacion "
            "o configura la variable IDF_PATH."
        )

    export_bat = idf_path / "export.bat"
    idf_script = idf_path / "tools" / "idf.py"

    if not idf_script.is_file():
        return None, None, None, (
            f"No se encontro el archivo de ESP-IDF: {idf_script}"
        )

    # Configurar UTF-8, activar ESP-IDF y recuperar sus variables.
    comando_entorno = (
        f'chcp 65001 >nul && '
        f'call "{export_bat}" >nul && '
        f'set'
    )

    proceso_entorno = subprocess.run(
        comando_entorno,
        shell=True,
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
        return None, None, None, (
            "ESP-IDF se activo, pero no se encontro su Python virtual."
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
        python_exe, idf_script, entorno, error_entorno = (
            preparar_entorno_idf()
        )

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
                if archivo.is_file()
                and "CMakeFiles" not in archivo.parts
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
