import sys
sys.path.insert(0, '.')
from fastapi import FastAPI
from modules.herramientas.backend.herramientas_backend import modulo

# Create app and check
app = FastAPI()
print('App before registrar:', len(app.routes), 'routes')

# Get info about modulo.router
print('modulo.router exists:', hasattr(modulo, 'router'))
print('modulo.router type:', type(modulo.router))

# Call registrar
modulo.registrar(app)

# Check results
print('App after registrar:', len(app.routes), 'routes')
print('App routes:')
for route in app.routes:
    if hasattr(route, 'methods'):
        path = getattr(route, 'path', '?')
        print(f'    {path}')