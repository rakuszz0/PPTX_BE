from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response as PlainResponse
from contextlib import asynccontextmanager
import re

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.errors import AppError
from app.core.security import generate_request_id
from app.database.session import init_db
from app.api.v1 import health, courses, modules, presentations, slides, jobs, qa
from app.api.v1 import auth
from app.api import websocket


# Regex yang selalu diizinkan di dev mode: setiap port localhost / 127.0.0.1
_LOCALHOST_REGEX = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$", re.IGNORECASE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    init_db()
    from pathlib import Path
    for d in ["data", "cache", "output", "assets", "prompts", "themes", "tests"]:
        Path(d).mkdir(parents=True, exist_ok=True)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="SlideForge Studio API",
        description="AI-Native Backend for PowerPoint Generation — forge beautiful educational presentations from any article URL.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Starlette/Fastapi CORSMiddleware di versi lama **tidak menerima callable** di
    # allow_origins (hanya list[str]). Jadi kita gunakan 2 strategi:
    #   1. allow_origins = list yang dikasih user (exact match + "*")
    #   2. allow_origin_regex = localhost/127.0.0.1 port bebas (selalu aktif di dev)
    # Jika list user sudah "*" → regex dimatikan karena "*" sudah menerima sembarang.
    use_wildcard = settings.cors_origins_list == ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=None if use_wildcard else _LOCALHOST_REGEX.pattern,
        allow_credentials=False if use_wildcard else True,  # "*" + allow_credentials tidak diijinkan CORS spec
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id", "Content-Disposition", "Content-Length"],
    )

    @app.middleware("http")
    async def request_id_and_cors_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or generate_request_id()
        request.state.request_id = request_id

        # Backup handler preflight / CORS headers: kalau origin user adalah localhost
        # tapi tidak tertangkap CORSMiddleware, kita inject header secara manual.
        origin = request.headers.get("origin")
        allowed = origin and (
            use_wildcard or settings.is_cors_origin_allowed(origin) or bool(_LOCALHOST_REGEX.match(origin))
        )

        # Tangani OPTIONS preflight yang gagal di CORSMiddleware karena credentials + origin list
        if request.method == "OPTIONS" and allowed and origin:
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,PATCH,OPTIONS",
                "Access-Control-Allow-Headers": request.headers.get(
                    "access-control-request-headers", "Content-Type,Authorization,Accept,X-Requested-With"
                ),
                "Access-Control-Allow-Credentials": "true" if not use_wildcard else "false",
                "Access-Control-Max-Age": "86400",
                "X-Request-Id": request_id,
            }
            return PlainResponse(status_code=204, headers=headers)

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            if isinstance(exc, AppError):
                body = exc.to_dict(request_id)
                resp = JSONResponse(status_code=exc.status_code, content=body)
            else:
                body = AppError(str(exc)).to_dict(request_id)
                resp = JSONResponse(status_code=500, content=body)
            if allowed and origin:
                resp.headers["Access-Control-Allow-Origin"] = origin
                if not use_wildcard:
                    resp.headers["Access-Control-Allow-Credentials"] = "true"
                resp.headers["Vary"] = "Origin"
            resp.headers["X-Request-Id"] = request_id
            return resp

        # Inject CORS headers ke response normal (menambahkan jika CORSMiddleware lewat)
        if allowed and origin:
            acao = response.headers.get("access-control-allow-origin")
            if not acao or acao == "*":
                response.headers["Access-Control-Allow-Origin"] = origin
                if not use_wildcard:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
        response.headers["X-Request-Id"] = request_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        rid = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(rid),
            headers={"X-Request-Id": rid or generate_request_id()},
        )

    v1_prefix = "/api/v1"
    app.include_router(health.router, prefix=v1_prefix)
    app.include_router(courses.router, prefix=v1_prefix)
    app.include_router(modules.router, prefix=v1_prefix)
    app.include_router(presentations.router, prefix=v1_prefix)
    app.include_router(slides.router, prefix=v1_prefix)
    app.include_router(jobs.router, prefix=v1_prefix)
    app.include_router(auth.router, prefix=v1_prefix)
    app.include_router(qa.router, prefix=v1_prefix)
    app.include_router(websocket.router)

    @app.get("/")
    async def root():
        return {"service": "slideforge-studio", "version": "0.1.0", "docs": "/docs"}

    return app


app = create_app()
