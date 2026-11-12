import sys
sys.path.insert(0, '.')
from modules.herramientas.backend.herramientas_backend import routes
from ide_core.config.constants import PREFIJO_API

print('PREFIJO_API:', PREFIJO_API)
print('routes.router.prefix:', routes.router.prefix)
print('routes.router.routes:', len(routes.router.routes))
for r in routes.router.routes:
    print(f'  {getattr(r, "path", "?")} - {getattr(r, "methods", "?")}')