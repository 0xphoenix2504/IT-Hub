import os

os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["CORS_ORIGIN"] = "http://localhost:5173"
os.environ["AUTH_PROVIDER"] = "local"
os.environ["COOKIE_SECURE"] = "false"
os.environ["COOKIE_SAMESITE"] = "lax"
os.environ["LOGIN_MAX_ATTEMPTS"] = "3"
os.environ["LOGIN_LOCKOUT_MINUTES"] = "15"
os.environ["PASSWORD_ITERATIONS"] = "2000"
os.environ["SESSION_TTL_HOURS"] = "8"
os.environ["FIRST_ADMIN_USERNAME"] = "admin"
os.environ["FIRST_ADMIN_PASSWORD"] = "correct-horse-1"
os.environ["FIRST_ADMIN_DISPLAY_NAME"] = "Hub Admin"
os.environ["STATS_CACHE_SECONDS"] = "60"
os.environ["TICKETING_APP_BASE_URL"] = ""
os.environ["ASSETS_APP_BASE_URL"] = ""
os.environ["TRUST_PROXY"] = ""

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core import database  # noqa: E402
from app.core.lockout import clear_all  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.services.bootstrap import bootstrap_first_admin  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(database.engine)
    Base.metadata.create_all(database.engine)
    clear_all()
    if database.SessionLocal is None:
        raise RuntimeError("Database engine not initialized")
    db = database.SessionLocal()
    try:
        bootstrap_first_admin(db)
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    if database.SessionLocal is None:
        raise RuntimeError("Database engine not initialized")
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()
