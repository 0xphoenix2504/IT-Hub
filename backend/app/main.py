import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, dashboards, settings
from app.core import database
from app.core.config import get_settings
from app.services.bootstrap import bootstrap_first_admin

log = logging.getLogger("it_hub")


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    config = get_settings()
    if not config.database_url.strip():
        raise RuntimeError("DATABASE_URL is empty. Set it in the backend environment.")
    database.init_engine(config.database_url.strip())

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if database.SessionLocal is None:
            raise RuntimeError("Database is not initialized")
        db = database.SessionLocal()
        try:
            bootstrap_first_admin(db)
        finally:
            db.close()
        log.info("IT Hub backend ready (%s, auth=%s)", config.environment, config.provider)
        yield

    app = FastAPI(title="IT Hub", lifespan=lifespan)
    if config.origin:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[config.origin],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Content-Type"],
        )

    @app.middleware("http")
    async def protect_responses(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(dashboards.router)
    app.include_router(settings.router)
    return app


app = create_app()
