from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.errors import AppError
from app.core.security import generate_request_id
from app.database.session import init_db
from app.api.v1 import health, courses, modules, presentations, slides, jobs, qa
from app.api.v1 import auth
from app.api import websocket


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
        title="Wizape Presentation Studio API",
        description="AI-Native Backend for Educational PowerPoint Generation",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    @app.middleware("http")
    async def request_id_and_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or generate_request_id()
        request.state.request_id = request_id
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            if isinstance(exc, AppError):
                body = exc.to_dict(request_id)
                return JSONResponse(status_code=exc.status_code, content=body, headers={"X-Request-Id": request_id})
            body = AppError(str(exc)).to_dict(request_id)
            return JSONResponse(status_code=500, content=body, headers={"X-Request-Id": request_id})
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
        return {"service": "wizape-presentation-studio", "version": "0.1.0", "docs": "/docs"}

    return app


app = create_app()
