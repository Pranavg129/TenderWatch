"""Offline regression coverage for TinyFish search and document reading."""
from backend import main, tinyfish_client


def test_search_results_exclude_generic_portal_pages():
    source = "https://eprocure.gov.in/eprocure/app"
    assert tinyfish_client.normalize(
        {
            "title": "eProcurement System Government of India",
            "url": source,
            "snippet": "Download tender schedules and submit bids online.",
        },
        source,
    ) is None
    assert tinyfish_client.normalize(
        {
            "title": "Tenders by Organisation",
            "url": "https://eprocure.gov.in/eprocure/app?page=org",
        },
        source,
    ) is None


def test_search_results_are_normalized_without_inventing_missing_fields(monkeypatch):
    monkeypatch.setenv("TINYFISH_API_KEY", "test-key")
    monkeypatch.setenv("TINYFISH_TENDER_SOURCE_URL", "https://eprocure.gov.in/eprocure/app")
    payload = {
        "results": [{
            "title": "LED component supply tender",
            "url": "https://eprocure.gov.in/tender/123",
            "snippet": "Supply of LED components. Refer to the tender notice.",
        }]
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get(self, url, **kwargs):
            assert url == tinyfish_client.SEARCH_URL
            assert kwargs["headers"]["X-API-Key"] == "test-key"
            assert "corrigendum" in kwargs["params"]["query"]
            return FakeResponse()

    monkeypatch.setattr(tinyfish_client.httpx, "Client", FakeClient)
    tenders = tinyfish_client.search_tenders("LED supply", limit=1)

    assert len(tenders) == 1
    assert tenders[0]["title"] == "LED component supply tender"
    assert tenders[0]["emd_inr"] is None
    assert tenders[0]["turnover_inr"] is None
    assert tenders[0]["source_url"] == "https://eprocure.gov.in/tender/123"


def test_document_reader_reads_notice_and_linked_corrigendum(monkeypatch):
    monkeypatch.setenv("TINYFISH_API_KEY", "test-key")
    notice_url = "https://eprocure.gov.in/tender/123"
    corrigendum_url = "https://eprocure.gov.in/tender/123/corrigendum.pdf"
    calls = []

    class FakeResponse:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self.data

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, url, **kwargs):
            assert url == tinyfish_client.FETCH_URL
            assert kwargs["headers"]["X-API-Key"] == "test-key"
            urls = kwargs["json"]["urls"]
            calls.append(urls)
            if len(calls) == 1:
                return FakeResponse({"results": [{
                    "title": "Tender notice",
                    "url": notice_url,
                    "text": "Scope: electrical equipment",
                    "links": [{"text": "Corrigendum", "url": corrigendum_url}],
                }]})
            return FakeResponse({"results": [{
                "title": "Corrigendum 1",
                "url": corrigendum_url,
                "text": "Revised bid submission date",
                "links": [],
            }]})

    monkeypatch.setattr(tinyfish_client.httpx, "Client", FakeClient)
    result = tinyfish_client.read_tender_documents({
        "id": "TW-LIVE-123",
        "source_url": notice_url,
    })

    assert calls == [[notice_url], [corrigendum_url]]
    assert [doc["kind"] for doc in result["documents"]] == [
        "Tender notice",
        "Corrigendum / amendment",
    ]
    assert "Revised bid submission date" in result["documents"][1]["text"]


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
