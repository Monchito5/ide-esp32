"""Tests automáticos de validación para el módulo Editor (Equipo Rojo).

Verifica modelos de dominio, controladores de edición/formato/búsqueda,
rutas FastAPI y cumplimiento de reglas PEP 420.
"""

import sys
sys.path.insert(0, '.')

def test_editor_models():
    """Test de entidades y modelos del editor."""
    from editor_backend.models import (
        ConfiguracionEditor,
        CoincidenciaArchivo,
        ResultadoBusquedaArchivos,
    )

    cfg = ConfiguracionEditor(tamanio_fuente=16, tamanio_tabulacion=4)
    d = cfg.a_dict()
    assert d['tamanio_fuente'] == 16
    assert d['tamanio_tabulacion'] == 4
    assert d['usar_espacios'] is True

    c = CoincidenciaArchivo('sketch.ino', 10, 5, 'Serial.begin(115200);')
    assert c.linea == 10
    assert c.columna == 5

    res = ResultadoBusquedaArchivos('Serial', 1, 1, [c.a_dict()])
    assert res.total_coincidencias == 1
    print('test_editor_models PASSED')


def test_editor_format():
    """Test del controlador de formato C/C++ (Auto Format - REQ-013)."""
    from editor_backend.controllers.format_controller import formatear_codigo_cpp

    codigo = 'void setup(){\npinMode(2, OUTPUT);\n}'
    resultado = formatear_codigo_cpp(codigo, tab_size=2)
    assert resultado['exitoso'] is True
    assert '  pinMode(2, OUTPUT);' in resultado['codigo_formateado']

    # Prueba con líneas vacías y directivas
    codigo2 = '#include <Arduino.h>\nvoid loop(){\n\n}\n'
    resultado2 = formatear_codigo_cpp(codigo2, tab_size=2)
    assert resultado2['exitoso'] is True
    assert '#include <Arduino.h>' in resultado2['codigo_formateado']
    print('test_editor_format PASSED')


def test_editor_config():
    """Test de persistencia de configuración del editor (REQ-018, REQ-019)."""
    from editor_backend.controllers.config_controller import (
        actualizar_configuracion,
        obtener_configuracion,
    )

    cfg = obtener_configuracion()
    assert 'tamanio_fuente' in cfg

    # Prueba de límites seguros de tamaño de fuente (8 a 36)
    actualizar_configuracion({'tamanio_fuente': 50}) # Debe clamp a 36
    assert obtener_configuracion()['tamanio_fuente'] == 36

    actualizar_configuracion({'tamanio_fuente': 4}) # Debe clamp a 8
    assert obtener_configuracion()['tamanio_fuente'] == 8

    # Restablecer a 14
    actualizar_configuracion({'tamanio_fuente': 14})
    assert obtener_configuracion()['tamanio_fuente'] == 14
    print('test_editor_config PASSED')


def test_editor_search():
    """Test de búsqueda y reemplazo en archivos (REQ-017)."""
    from editor_backend.controllers.search_controller import (
        buscar_en_archivos,
        reemplazar_en_archivos,
    )

    # Búsqueda controlada en un archivo temporal de prueba
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, 'test_sketch.ino')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('void setup() {\n  Serial.begin(115200);\n}\n')

        # Buscar
        res = buscar_en_archivos('Serial', directorio=tmpdir)
        assert res['total_coincidencias'] == 1

        # Reemplazar
        rep = reemplazar_en_archivos('Serial', 'MySerial', directorio=tmpdir)
        assert rep['exitoso'] is True
        assert rep['total_reemplazos'] == 1

        # Verificar contenido modificado
        with open(test_file, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert 'MySerial.begin(115200);' in contenido

    print('test_editor_search PASSED')


def test_editor_modulo_registrar():
    """Test del punto de entrada registrar(app) del módulo Editor."""
    from editor_backend.modulo import NOMBRE_MODULO, VERSION_MODULO, registrar
    from fastapi import FastAPI

    assert NOMBRE_MODULO == 'editor'
    assert VERSION_MODULO == '1.0.0'

    app = FastAPI()
    registrar(app)

    route_paths = []
    for r in app.routes:
        if getattr(r, 'path', ''):
            route_paths.append(getattr(r, 'path', ''))
        if hasattr(r, 'original_router'):
            for sub_r in getattr(r.original_router, 'routes', []):
                if getattr(sub_r, 'path', ''):
                    route_paths.append(getattr(sub_r, 'path', ''))

    assert any('editor' in str(p) for p in route_paths)
    print('test_editor_modulo_registrar PASSED')


def test_ci_cd_signature():
    """Verificación de cumplimiento de ausencia de __init__.py (PEP 420)."""
    import pathlib

    base = pathlib.Path('.')
    init_files = [
        p for p in base.rglob('__init__.py')
        if 'venv' not in p.parts and '.venv' not in p.parts and '.git' not in p.parts and 'build' not in p.parts
    ]
    assert len(init_files) == 0, f"Archivos __init__.py prohibidos encontrados: {init_files}"
    print('test_ci_cd_signature PASSED (0 __init__.py)')


if __name__ == '__main__':
    print('=== Running Editor Module (Equipo Rojo) Automated Tests ===\n')
    tests = [
        test_editor_models,
        test_editor_format,
        test_editor_config,
        test_editor_search,
        test_editor_modulo_registrar,
        test_ci_cd_signature,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f'test {test.__name__} FAILED: {e}')
            failed += 1

    print(f'\n=== Results: {passed} passed, {failed} failed ===')
    if failed > 0:
        sys.exit(1)
    else:
        print('=== ALL EDITOR TESTS PASSED ===')
