# Cómo subir el módulo Azul al monorepo

1. Crea una rama `feature/modulo-azul-menu-log` desde `develop` (o la rama base acordada).
2. Descomprime este ZIP en la **raíz** del repositorio, conservando `modules/`, `shared/` y `sql/`.
3. Revisa los cambios antes de confirmarlos. **No sobrescribas** archivos del equipo Gris ni registros centrales.
4. Sube tu rama y abre un Pull Request hacia la rama acordada.

```powershell
git switch develop
git pull origin develop
git switch -c feature/modulo-azul-menu-log
# Descomprimir este ZIP en la carpeta raíz del repositorio
git add modules/azul shared/contratos/azul sql/02_schema_azul.sql README_INTEGRACION_AZUL.md SUBIR_A_GITHUB.md
git commit -m "feat(azul): preparar menu y log Flutter FastAPI"
git push -u origin feature/modulo-azul-menu-log
```

**Pendiente:** registrar el módulo en el backend y frontend reales, instalar dependencias y conectar el adaptador de compilación del equipo Sketch. El archivo `panel_azul.dart` es un widget y **todavía no implementa** el contrato `ModuloIde` del repositorio. El código no ha sido validado dentro del monorepo oficial.
