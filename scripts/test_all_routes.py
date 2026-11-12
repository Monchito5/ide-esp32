import sys
sys.path.insert(0, '.')
from ide_core.config.registro_modulos import registrar_modulos
from fastapi import FastAPI

app = FastAPI()
registrar_modulos(app)

# Check all routes
print('=== Todas las rutas despues de registrar_modulos ===')
for route in app.routes:
    methods = getattr(route, 'methods', None)
    path = getattr(route, 'path', '?')
    if methods is not None:
        print(f'  {methods} {path}')
    else:
        print(f'  (sin methods) {path}')