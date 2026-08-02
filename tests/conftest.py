import os
from pathlib import Path
os.environ["DATABASE_URL"] = "sqlite:///./test_orchestrix.db"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine

@pytest.fixture(scope="session", autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.main import seed
    seed()
    yield
    Base.metadata.drop_all(bind=engine)
    Path("test_orchestrix.db").unlink(missing_ok=True)

@pytest.fixture
def client():
    return TestClient(app)
