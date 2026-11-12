import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, dashboards, settings
from app.core import database
from app.core.config import get_settings
from app.models import Base
from app.services.bootstrap import bootstrap_first_admin

log = logging.getLogger("it_hub")


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    config = get_settings()
    db_url = config.database_url.strip()
    if db_url:
        database.init_engine(db_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        current_config = get_settings()
        url = current_config.database_url.strip()
        if not url:
            log.warning("DATABASE_URL is not set. Set it in the backend environment.")
            yield
            return

        if database.engine is None:
            database.init_engine(url)

        if database.engine is not None:
            try:
                Base.metadata.create_all(bind=database.engine)
            except Exception as exc:
                log.warning("Could not auto-create tables: %s", exc)

        if database.SessionLocal is not None:
            db = database.SessionLocal()
            try:
                bootstrap_first_admin(db)
            except Exception as exc:
                log.warning("Could not bootstrap first admin: %s", exc)
            finally:
                db.close()
        log.info("IT Hub backend ready (%s, auth=%s)", current_config.environment, current_config.provider)
        yield

    app = FastAPI(title="IT Hub", lifespan=lifespan)
    origins = config.origins or ([config.origin] if config.origin else [])
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
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
        current_config = get_settings()
        has_db = bool(current_config.database_url.strip() and database.engine is not None)
        return {
            "status": "ok",
            "database": "connected" if has_db else "not_configured",
            "auth_provider": current_config.provider,
        }

    app.include_router(auth.router)
    app.include_router(dashboards.router)
    app.include_router(settings.router)
    return app


app = create_app()