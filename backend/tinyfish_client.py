"""TinyFish public tender discovery client; reads public listings only."""
import hashlib
import json
import os
from urllib.parse import urlparse

import httpx

SEARCH_URL = "https://api.search.tinyfish.ai"
DEFAULT_SOURCE_URL = "https://eprocure.gov.in/eprocure/app"


def status():
    ready = bool(os.getenv("TINYFISH_API_KEY", "").strip())
    return {
        "configured": ready,
        "live_extraction_enabled": ready,
        "source_url": os.getenv("TINYFISH_TENDER_SOURCE_URL", DEFAULT_SOURCE_URL),
        "message": "Ready" if ready else "Set TINYFISH_API_KEY in backend .env.",
    }


def number(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return value
    digits = "".join(c for c in str(value) if c.isdigit() or c == ".")
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def is_official_url(value):
    parsed = urlparse(str(value or ""))
    host = (parsed.hostname or "").lower()
    return parsed.scheme in {"http", "https"} and (
        host.endswith(".gov.in") or host.endswith(".nic.in")
    )


def normalize(row, source):
    if not isinstance(row, dict):
        return None
    title = str(row.get("title") or row.get("tender_title") or "").strip()
    if not title:
        return None
    url = str(row.get("url") or row.get("source_url") or "")
    if not is_official_url(url):
        return None
    native = str(row.get("tender_id") or row.get("id") or "")
    key = hashlib.sha1((native + url + title).encode()).hexdigest()[:10].upper()
    snippet = str(row.get("snippet") or row.get("description") or "").strip()
    # Search snippets do not reliably contain qualification figures. Keep those
    # unknown so eligibility screening reports "Review required" instead of guessing.
    return {
        "id": "TW-LIVE-" + key,
        "title": title[:240],
        "buyer": str(row.get("buyer") or row.get("organization") or "Buyer not listed"),
        "location": str(row.get("location") or "Location not listed"),
        "category": str(row.get("category") or "Not listed"),
        "value_inr": number(row.get("value_inr") or row.get("estimated_value")),
        "deadline": row.get("deadline") or row.get("submission_deadline"),
        "emd_inr": number(row.get("emd_inr") or row.get("emd")),
        "turnover_inr": number(row.get("turnover_inr") or row.get("minimum_turnover")),
        "years_experience": number(row.get("years_experience") or row.get("experience_years")),
        "reference_id": native or None,
        "description": snippet[:1200] or "Open the official notice for complete tender details.",
        "source": "TinyFish Search · verify official notice",
        "source_url": url,
        "is_live": True,
    }


def rows(result):
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        for key in ("tenders", "items", "results", "data"):
            value = result.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = rows(value)
                if nested:
                    return nested
    return []


def search_tenders(query="active tenders", limit=10):
    """Search quickly for official tender listings; do not invent missing criteria."""
    key = os.getenv("TINYFISH_API_KEY", "").strip()
    if not key:
        raise RuntimeError("TinyFish is not configured. Add TINYFISH_API_KEY to backend .env.")
    source = os.getenv("TINYFISH_TENDER_SOURCE_URL", DEFAULT_SOURCE_URL).strip() or DEFAULT_SOURCE_URL
    if not is_official_url(source):
        raise RuntimeError("Tender source must use an official .gov.in or .nic.in domain.")

    terms = query.strip() or "active tenders"
    search_query = (
        f"India active public procurement tenders {terms} "
        "site:eprocure.gov.in OR site:*.gov.in OR site:*.nic.in"
    )
    try:
        with httpx.Client(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            response = client.get(
                SEARCH_URL,
                params={"query": search_query},
                headers={"X-API-Key": key, "Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            "TinyFish Search returned HTTP " + str(exc.response.status_code)
            + ". Check API key and account limits."
        ) from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError("TinyFish Search timed out. Try a narrower search.") from exc
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        raise RuntimeError("Could not read TinyFish Search response. Check backend network access.") from exc

    tenders = [normalize(item, source) for item in rows(payload)]
    unique = {}
    for tender in tenders:
        if tender:
            unique[tender["id"]] = tender
    return list(unique.values())[:max(1, min(limit, 15))]
