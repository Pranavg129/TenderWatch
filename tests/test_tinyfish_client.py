"""Offline regression coverage for fast TinyFish Search tender discovery."""
from backend import main, tinyfish_client


def test_search_results_are_normalized_without_inventing_missing_fields(monkeypatch):
    monkeypatch.setenv("TINYFISH_API_KEY", "test-key")
    monkeypatch.setenv(
        "TINYFISH_TENDER_SOURCE_URL",
        "https://eprocure.gov.in/eprocure/app",
    )
    payload = {
        "results": [{
            "position": 1,
            "title": "LED component supply tender",
            "url": "https://eprocure.gov.in/tender/123",
            "snippet": "Supply of LED components. Bid closing date shown in notice.",
        }]
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["timeout"].read == 15.0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get(self, url, **kwargs):
            assert url == tinyfish_client.SEARCH_URL
            assert kwargs["headers"]["X-API-Key"] == "test-key"
            assert "site:eprocure.gov.in" in kwargs["params"]["query"]
            return FakeResponse()

    monkeypatch.setattr(tinyfish_client.httpx, "Client", FakeClient)
    tenders = tinyfish_client.search_tenders("LED supply", limit=1)

    assert len(tenders) == 1
    assert tenders[0]["id"].startswith("TW-LIVE-")
    assert tenders[0]["title"] == "LED component supply tender"
    assert tenders[0]["emd_inr"] is None
    assert tenders[0]["turnover_inr"] is None
    assert tenders[0]["source_url"] == "https://eprocure.gov.in/tender/123"
    assert "TinyFish Search" in tenders[0]["source"]


def test_non_official_search_results_are_excluded():
    source = "https://eprocure.gov.in/eprocure/app"
    tender = tinyfish_client.normalize(
        {"title": "Fake tender", "url": "https://example.com/fake"},
        source,
    )

    assert tender is None


def test_live_tender_with_missing_criteria_stays_review_required(monkeypatch):
    tender = {
        "id": "TW-LIVE-UNKNOWN",
        "title": "Tender with incomplete public details",
        "buyer": "Public buyer",
        "location": "India",
        "category": "Not listed",
        "value_inr": None,
        "deadline": None,
        "emd_inr": None,
        "turnover_inr": None,
        "years_experience": None,
        "description": "See linked notice.",
        "source_url": "https://eprocure.gov.in/tender/unknown",
        "is_live": True,
    }
    monkeypatch.setattr(main, "LIVE_TENDERS", [tender])

    result = main.eligibility(
        tender["id"],
        main.BusinessProfile(
            annual_turnover_inr=10_000_000,
            years_experience=10,
            categories=["Goods", "Services", "Electrical"],
            available_emd_inr=1_000_000,
        ),
    )

    assert result["status"] == "Review required"
    assert result["passed"] == 0
    assert all("Not listed" in check["required"] for check in result["checks"])
