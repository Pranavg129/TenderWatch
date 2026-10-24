"""Offline regression coverage for TinyFish tender extraction."""
import json

from backend import main, tinyfish_client


def test_tinyfish_stream_is_normalized_without_inventing_missing_fields(monkeypatch):
    monkeypatch.setenv("TINYFISH_API_KEY", "test-key")
    monkeypatch.setenv(
        "TINYFISH_TENDER_SOURCE_URL",
        "https://eprocure.gov.in/eprocure/app",
    )
    extracted = {
        "tenders": [{
            "title": "LED component supply",
            "tender_id": "REF-123",
            "source_url": "https://eprocure.gov.in/tender/123",
            "estimated_value": "₹6,20,000",
            "emd": None,
        }]
    }
    event = {"type": "COMPLETE", "status": "COMPLETED", "resultJson": extracted}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def raise_for_status(self):
            pass

        def iter_lines(self):
            yield "data: " + json.dumps(event)

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def stream(self, method, url, **kwargs):
            assert method == "POST"
            assert url == tinyfish_client.AGENT_URL
            assert kwargs["headers"]["X-API-Key"] == "test-key"
            assert kwargs["json"]["url"].startswith("https://eprocure.gov.in/")
            return FakeResponse()

    monkeypatch.setattr(tinyfish_client.httpx, "Client", FakeClient)
    tenders = tinyfish_client.search_tenders("LED supply", limit=1)

    assert len(tenders) == 1
    assert tenders[0]["id"].startswith("TW-LIVE-")
    assert tenders[0]["reference_id"] == "REF-123"
    assert tenders[0]["value_inr"] == 620000
    assert tenders[0]["emd_inr"] is None
    assert tenders[0]["turnover_inr"] is None
    assert tenders[0]["source_url"] == "https://eprocure.gov.in/tender/123"


def test_non_official_extracted_link_falls_back_to_configured_official_source():
    source = "https://eprocure.gov.in/eprocure/app"
    tender = tinyfish_client.normalize(
        {"title": "Sample tender", "source_url": "https://example.com/fake"},
        source,
    )

    assert tender["source_url"] == source
    assert tender["id"].startswith("TW-LIVE-")


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
