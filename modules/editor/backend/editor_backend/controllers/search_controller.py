# Archivo: modules/editor/backend/editor_backend/controllers/search_controller.py
"""Controlador para búsqueda y reemplazo en múltiples archivos (Replace in Files)."""

import os
from pathlib import Path
from typing import List, Optional

EXTENSIONES_PERMITIDAS = {".ino", ".cpp", ".c", ".h", ".hpp", ".txt"}


def buscar_en_archivos(
    termino: str,
    directorio: Optional[str] = None,
    sensible_mayusculas: bool = False,
    palabra_completa: bool = False,
) -> dict:
    """Busca coincidencias del término en los archivos de código del proyecto."""
    if not termino:
        return {"total_coincidencias": 0, "archivos": []}

    ruta_base = Path(directorio) if directorio else Path.cwd()
    if not ruta_base.exists() or not ruta_base.is_dir():
        return {"total_coincidencias": 0, "archivos": [], "error": "Directorio no valido"}

    coincidencias_por_archivo = []
    total = 0

    for raiz, dirs, archivos in os.walk(ruta_base):
        # Excluir carpetas irrelevantes como git, build, cache
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"build", "venv", "node_modules"}]

        for nombre_archivo in archivos:
            ext = os.path.splitext(nombre_archivo)[1].lower()
            if ext not in EXTENSIONES_PERMITIDAS:
                continue

            ruta_completa = Path(raiz) / nombre_archivo
            try:
                with open(ruta_completa, "r", encoding="utf-8", errors="ignore") as f:
                    lineas = f.readlines()
            except Exception:
                continue

            coincidencias_archivo = []
            for num_linea, contenido in enumerate(lineas, start=1):
                cadena_buscada = termino if sensible_mayusculas else termino.lower()
                cadena_evaluar = contenido if sensible_mayusculas else contenido.lower()

                if cadena_buscada in cadena_evaluar:
                    columna = cadena_evaluar.find(cadena_buscada)
                    coincidencias_archivo.append({
                        "linea": num_linea,
                        "columna": columna + 1,
                        "texto": contenido.strip(),
                    })
                    total += 1

            if coincidencias_archivo:
                coincidencias_por_archivo.append({
                    "archivo": str(ruta_completa.relative_to(ruta_base)),
                    "ruta_absoluta": str(ruta_completa),
                    "total": len(coincidencias_archivo),
                    "coincidencias": coincidencias_archivo,
                })

    return {
        "total_coincidencias": total,
        "archivos_con_coincidencias": len(coincidencias_por_archivo),
        "archivos": coincidencias_por_archivo,
    }


def reemplazar_en_archivos(
    termino: str,
    reemplazo: str,
    directorio: Optional[str] = None,
    sensible_mayusculas: bool = False,
) -> dict:
    """Reemplaza coincidencias de un término en los archivos permitidos del proyecto."""
    if not termino:
        return {"archivos_modificados": 0, "total_reemplazos": 0, "detalles": []}

    busqueda = buscar_en_archivos(termino, directorio, sensible_mayusculas)
    archivos = busqueda.get("archivos", [])

    archivos_modificados = 0
    total_reemplazos = 0
    detalles = []

    for item in archivos:
        ruta = item["ruta_absoluta"]
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()

            if sensible_mayusculas:
                ocurrencias = contenido.count(termino)
                nuevo_contenido = contenido.replace(termino, reemplazo)
            else:
                import re
                regex = re.compile(re.escape(termino), re.IGNORECASE)
                ocurrencias = len(regex.findall(contenido))
                nuevo_contenido = regex.sub(reemplazo, contenido)

            if ocurrencias > 0:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(nuevo_contenido)
                archivos_modificados += 1
                total_reemplazos += ocurrencias
                detalles.append({"archivo": item["archivo"], "reemplazos": ocurrencias})
        except Exception as e:
            detalles.append({"archivo": item["archivo"], "error": str(e)})

    return {
        "exitoso": True,
        "archivos_modificados": archivos_modificados,
        "total_reemplazos": total_reemplazos,
        "detalles": detalles,
    }
