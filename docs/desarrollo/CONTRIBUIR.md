# Guia de Contribucion

1. Rama `feature/*`, `fix/*` o `docs/*`.
2. Si agregas un modulo, seguir la seccion "Como agregar un nuevo modulo" del
   README raiz.
3. **Dependencias**: si necesitas una libreria nueva, agrgala a
   `requirements.txt` (RAIZ) y ejecuta `pip install -r requirements-dev.txt`.
4. Ejecutar pruebas locales (con el venv de la raiz activado):
   ```bash
   # Core
   cd core/backend && pytest pruebas/ -v

   # Modulo
   cd modules/herramientas/backend && pytest pruebas/ -v

   # Frontend
   cd apps/ide && flutter test
   ```
5. Pull Request con la plantilla.
6. Para convenciones de codigo (sin `__init__.py`, imports absolutamente centralizados,
   black/isort/formato, dependencias en root `requirements.txt`), consultar
   `docs/desarrollo/CONVENCIONES_CODIGO.md`.