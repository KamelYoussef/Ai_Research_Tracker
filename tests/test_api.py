import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.response import AIResponse


# Create a new session for testing
@pytest.fixture(scope="module")
def db_session():
    # Create tables in the test database
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    # Drop tables after testing
    Base.metadata.drop_all(bind=engine)


# Create a test client for FastAPI app
client = TestClient(app)


def test_submit_query(db_session):
    # Test the query submission endpoint
    query_data = {"query": "What is AI?", "ai_platform": "ChatGPT"}
    response = client.post("/query/", json=query_data)

    assert response.status_code == 200
    assert "query" in response.json()
    assert "response" in response.json()
    assert "keywords" in response.json()

    # Check if the query is saved in the database
    db_response = db_session.query(AIResponse).filter(AIResponse.query == query_data["query"]).first()
    assert db_response is not None
    assert db_response.query == query_data["query"]
    assert db_response.ai_platform == query_data["ai_platform"]


def test_get_query_response(db_session):
    # Test the query retrieval endpoint
    # Assuming that a query is already stored in the database
    ai_response = db_session.query(AIResponse).first()

    if ai_response:
        response = client.get(f"/query/{ai_response.id}")
        assert response.status_code == 200
        assert "query" in response.json()
        assert "response" in response.json()
        assert "keywords" in response.json()
    else:
        pytest.skip("No data to test retrieval.")
