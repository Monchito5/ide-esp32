import sys
sys.path.insert(0, '.')
from modules.herramientas.backend.herramientas_backend import modulo, routes

print('modulo.router is routes.router:', modulo.router is routes.router)
print()
print('modulo.router.routes:')
for r in modulo.router.routes:
    print(f'  {getattr(r, "path", "?")} - {getattr(r, "methods", "?")}')
print()
print('routes.router.routes:')
for r in routes.router.routes:
    print(f'  {getattr(r, "path", "?")} - {getattr(r, "methods", "?")}')