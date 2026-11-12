import sys
sys.path.insert(0, '.')
from fastapi import FastAPI
from modules.herramientas.backend.herramientas_backend import modulo

app = FastAPI()
print('Routes BEFORE registrar:')
for route in app.routes:
    path = getattr(route, 'path', '?')
    methods = getattr(route, 'methods', 'NONE')
    print(f'  {methods} {path}')

print('\nCalling modulo.registrar(app)...')
modulo.registrar(app)

print('\nRoutes AFTER registrar:')
for route in app.routes:
    path = getattr(route, 'path', '?')
    methods = getattr(route, 'methods', 'NONE')
    print(f'  {methods} {path}')