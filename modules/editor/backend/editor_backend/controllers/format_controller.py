# Archivo: modules/editor/backend/editor_backend/controllers/format_controller.py
"""Controlador para formateo de código C/C++/Arduino (Auto Format)."""

import re
import shutil
import subprocess


def formatear_codigo_cpp(codigo: str, tab_size: int = 2) -> dict:
    """Aplica reglas de formateo al código C/C++/Arduino.

    Intenta usar clang-format si está instalado; de lo contrario, aplica
    formato por reglas de indentación estructural y limpieza sintáctica.
    """
    if not codigo.strip():
        return {"exitoso": True, "codigo_formateado": codigo, "error": ""}

    # 1. Intentar clang-format si existe en el sistema
    clang_format_path = shutil.which("clang-format")
    if clang_format_path:
        try:
            estilo = f"{{BasedOnStyle: Google, IndentWidth: {tab_size}}}"
            proceso = subprocess.run(
                [clang_format_path, f"-style={estilo}"],
                input=codigo,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if proceso.returncode == 0:
                return {
                    "exitoso": True,
                    "codigo_formateado": proceso.stdout,
                    "error": "",
                }
        except Exception:
            pass

    # 2. Formateador nativo basado en análisis de llaves y estructura C/C++
    indent_unit = " " * tab_size
    lineas = codigo.split("\n")
    nivel_indent = 0
    lineas_formateadas = []
    en_comentario_bloque = False

    for linea in lineas:
        linea_strip = linea.strip()

        # Manejo de comentarios de bloque
        if "/*" in linea_strip and "*/" not in linea_strip:
            en_comentario_bloque = True
            lineas_formateadas.append((indent_unit * nivel_indent) + linea_strip)
            continue
        if en_comentario_bloque:
            if "*/" in linea_strip:
                en_comentario_bloque = False
            lineas_formateadas.append((indent_unit * nivel_indent) + linea_strip)
            continue

        # Líneas vacías
        if not linea_strip:
            lineas_formateadas.append("")
            continue

        # Directivas de preprocesador (#include, #define) se alinean a la izquierda
        if linea_strip.startswith("#"):
            lineas_formateadas.append(linea_strip)
            continue

        # Contar llaves de apertura y cierre para ajustar indentación
        aperturas = linea_strip.count("{")
        cierres = linea_strip.count("}")

        # Si la línea empieza con '}', reducir la sangría antes de renderizarla
        if linea_strip.startswith("}"):
            nivel_indent = max(0, nivel_indent - 1)
            lineas_formateadas.append((indent_unit * nivel_indent) + linea_strip)
            nivel_indent = max(0, nivel_indent + aperturas - (cierres - 1))
        else:
            lineas_formateadas.append((indent_unit * nivel_indent) + linea_strip)
            nivel_indent = max(0, nivel_indent + aperturas - cierres)

    resultado = "\n".join(lineas_formateadas)
    return {"exitoso": True, "codigo_formateado": resultado, "error": ""}
