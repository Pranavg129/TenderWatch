from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_demo_tenders_are_returned():
    response = client.get("/api/tenders")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo"] is True
    assert payload["count"] >= 1

def test_search_filters_tenders():
    response = client.get("/api/tenders", params={"q": "networking"})
    assert response.status_code == 200
    assert response.json()["count"] == 1

def test_eligibility_screening():
    response = client.post("/api/eligibility/TW-2026-001", json={
        "annual_turnover_inr": 3000000,
        "years_experience": 2,
        "categories": ["Goods"],
        "available_emd_inr": 50000
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["passed"] == 4
    assert payload["status"] == "Potential match"

def test_unknown_tender_returns_404():
    response = client.post("/api/eligibility/not-real", json={})
    assert response.status_code == 404
