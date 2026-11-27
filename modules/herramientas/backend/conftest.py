# Archivo: modules/herramientas/backend/conftest.py
"""Configuración de pytest para el módulo Herramientas.

Este archivo se ejecuta automáticamente antes de cada suite de pruebas y
configura el path de imports para permitir imports absolutos usando la
estructura PEP 420 de namespace packages (sin __init__.py).

Configurado según IEEE 12207 para pruebas de software.
"""

import sys
from pathlib import Path

# Obtener la ruta raíz del monorepo (tres niveles arriba desde este archivo)
# conftest.py está en: modules/herramientas/backend/
# El monorepo está en: ide-esp32/ (tres niveles arriba)
MONOREPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parent

# Agregar el monorepo y el backend local al path de Python (PEP 420 sin __init__.py)
if str(MONOREPO_ROOT) not in sys.path:
    sys.path.insert(0, str(MONOREPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Verificación de configuración
print(f"\n[conftest.py] MONOREPO_ROOT configurado: {MONOREPO_ROOT}")
print(f"[conftest.py] sys.path actualizado para imports absolutos")
