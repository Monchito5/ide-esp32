import sys
sys.path.insert(0, '.')
from fastapi import FastAPI
from modules.herramientas.backend.herramientas_backend import modulo

app = FastAPI()
print('App before registrar:')
for route in app.routes:
    path = getattr(route, 'path', '?')
    print(f'  {path}')

modulo.registrar(app)

print('App after registrar:')
for route in app.routes:
    path = getattr(route, 'path', '?')
    methods = getattr(route, 'methods', 'NONE')
    print(f'  {path} - methods={methods}')