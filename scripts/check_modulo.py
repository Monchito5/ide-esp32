import sys
sys.path.insert(0, '.')
from modules.herramientas.backend.herramientas_backend import modulo

print('modulo.registrar:', modulo.registrar)
print('modulo.router:', modulo.router)
print('modulo.router.routes count:', len(modulo.router.routes))
for r in modulo.router.routes:
    print(f'  {getattr(r, "path", "?")} - {getattr(r, "methods", "?")}')