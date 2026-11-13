# Archivo: modules/editor/backend/conftest.py
"""Configuración de pytest para el módulo Editor (Equipo Rojo)."""

import sys
from pathlib import Path

MONOREPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parent

if str(MONOREPO_ROOT) not in sys.path:
    sys.path.insert(0, str(MONOREPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
