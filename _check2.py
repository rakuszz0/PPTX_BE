import sys, traceback
sys.path.insert(0, '/Users/mat-ila/pptx/backend')
errors = []
try:
    from app.core.config import get_settings
    s = get_settings()
    print('[OK] config: CORS list =', s.cors_origins_list)
    for u in ['http://localhost:3007','http://127.0.0.1:3007','http://localhost:3000','https://evil.com']:
        print(f'     is_cors_allowed({u}) =', s.is_cors_origin_allowed(u))
except Exception:
    errors.append(('config', traceback.format_exc()))
try:
    from app.core.auth_store import get_or_create_oauth_user
    print('[OK] auth_store: fn exists =', callable(get_or_create_oauth_user))
except Exception:
    errors.append(('auth_store', traceback.format_exc()))
try:
    from app.api.v1.auth import router
    paths = sorted({r.path for r in router.routes})
    print('[OK] auth.router paths:', paths)
except Exception:
    errors.append(('auth.api.v1', traceback.format_exc()))
try:
    import app.core.config as cm
    cm.get_settings.cache_clear()
    from app.main import create_app
    app = create_app()
    # route collection lives in app.router.routes (iterable APIRoute)
    routes = list(getattr(app, 'routes') or []) + list(getattr(app.router, 'routes', []))
    rpaths = set()
    for r in routes:
        p = getattr(r, 'path', None)
        if p:
            rpaths.add(p)
    hits = sorted([p for p in rpaths if 'auth' in p])
    print('[OK] main.create_app — auth routes:', hits)
except Exception:
    errors.append(('main', traceback.format_exc()))

# Coba dummy Request untuk test CORS manual
try:
    from starlette.requests import Request as StarReq
    from app.core.config import get_settings as gs
    s2 = gs()
    def _simulate_origin(origin):
        return (
            s2.is_cors_origin_allowed(origin)
            or bool(__import__('re').compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$").match(origin or ''))
        )
    tests = [
        ('http://localhost:3007', True),
        ('http://127.0.0.1:3007', True),
        ('https://localhost', True),
        ('http://localhost:3000', True),
        ('http://otherhost:3000', False),
        ('https://evil.com', False),
    ]
    all_pass = True
    for origin, want in tests:
        got = _simulate_origin(origin)
        mark = 'OK' if got == want else 'FAIL'
        if got != want: all_pass = False
        print(f'  CORS {mark}: origin={origin!r:35s}  want={want}  got={got}')
    if all_pass:
        print('[OK] ALL CORS ASSERTIONS PASSED')
    else:
        errors.append(('cors_check', 'assertions failed'))
except Exception:
    errors.append(('cors_check', traceback.format_exc()))

if errors:
    print('\n== ERRORS ==')
    for n, tb in errors:
        print('---', n, '---')
        print(tb)
    sys.exit(1)
print('\nALL BACKEND CHECKS PASSED')
