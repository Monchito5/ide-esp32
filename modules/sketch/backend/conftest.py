# Archivo: modules/sketch/backend/conftest.py
"""Configuración de pytest para el módulo Sketch (con acceso a core y módulos puente)."""

import sys
from pathlib import Path

MONOREPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parent
CORE_BACKEND = MONOREPO_ROOT / "core" / "backend"

rutas = [
    MONOREPO_ROOT,
    CORE_BACKEND,
    BACKEND_DIR,
    *sorted(MONOREPO_ROOT.glob("modules/*/backend")),
]

for ruta in reversed(rutas):
    ruta_str = str(ruta)
    if ruta_str not in sys.path:
        sys.path.insert(0, ruta_str)
