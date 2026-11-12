import sys
sys.path.insert(0, '.')
from modules.herramientas.backend.herramientas_backend import modulo

# Check router
print('modulo.router:', modulo.router)
print('type:', type(modulo.router))

# Check if it has include_router
has_method = hasattr(modulo.router, 'include_router')
print('has include_router:', has_method)

# Check routes count
routes_count = len(modulo.router.routes)
print('routes count:', routes_count)

# List routes
print('routes:')
for r in modulo.router.routes:
    path = getattr(r, 'path', '?')
    methods = getattr(r, 'methods', '?')
    print(f'  {methods} {path}')