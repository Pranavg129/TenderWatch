"""TinyFish public tender discovery client; reads public listings only."""
import hashlib
import json
import os
from urllib.parse import urlparse
import httpx

AGENT_URL = "https://agent.tinyfish.ai/v1/automation/run-sse"
DEFAULT_SOURCE_URL = "https://eprocure.gov.in/eprocure/app"

def status():
    ready = bool(os.getenv("TINYFISH_API_KEY", "").strip())
    return {"configured": ready, "live_extraction_enabled": ready,
            "source_url": os.getenv("TINYFISH_TENDER_SOURCE_URL", DEFAULT_SOURCE_URL),
            "message": "Ready" if ready else "Set TINYFISH_API_KEY in backend .env."}

def number(value):
    if value is None or value == "": return None
    if isinstance(value, (int, float)): return value
    digits = "".join(c for c in str(value) if c.isdigit() or c == ".")
    try: return float(digits) if digits else None
    except ValueError: return None

def normalize(row, source):
    if not isinstance(row, dict): return None
    title = str(row.get("title") or row.get("tender_title") or "").strip()
    if not title: return None
    url = str(row.get("source_url") or row.get("url") or source)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not ((parsed.hostname or "").endswith(".gov.in") or (parsed.hostname or "").endswith(".nic.in")):
        url = source
    native = str(row.get("tender_id") or row.get("id") or "")
    key = hashlib.sha1((native + url + title).encode()).hexdigest()[:10].upper()
    return {"id": native or "TW-LIVE-" + key, "title": title[:240],
            "buyer": str(row.get("buyer") or row.get("organization") or "Buyer not listed"),
            "location": str(row.get("location") or "Location not listed"),
            "category": str(row.get("category") or "Other"),
            "value_inr": number(row.get("value_inr") or row.get("estimated_value")),
            "deadline": row.get("deadline") or row.get("submission_deadline"),
            "emd_inr": number(row.get("emd_inr") or row.get("emd")),
            "turnover_inr": number(row.get("turnover_inr") or row.get("minimum_turnover")),
            "years_experience": number(row.get("years_experience") or row.get("experience_years")),
            "description": str(row.get("description") or row.get("scope") or "See official notice."),
            "source": "TinyFish extraction · verify official notice", "source_url": url, "is_live": True}

def rows(result):
    if isinstance(result, str):
        try: result = json.loads(result)
        except json.JSONDecodeError: return []
    if isinstance(result, list): return result
    if isinstance(result, dict):
        for key in ("tenders", "items", "results", "data"):
            if isinstance(result.get(key), list): return result[key]
    return []

def search_tenders(query="active tenders", limit=10):
    key = os.getenv("TINYFISH_API_KEY", "").strip()
    if not key: raise RuntimeError("TinyFish is not configured. Add TINYFISH_API_KEY to backend .env.")
    source = os.getenv("TINYFISH_TENDER_SOURCE_URL", DEFAULT_SOURCE_URL).strip() or DEFAULT_SOURCE_URL
    parsed = urlparse(source)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or not (parsed.hostname.endswith(".gov.in") or parsed.hostname.endswith(".nic.in")):
        raise RuntimeError("Tender source must use an official .gov.in or .nic.in domain.")
    schema = {"tenders": [{"tender_id": "string|null", "title": "string", "buyer": "string|null", "location": "string|null", "category": "string|null", "estimated_value": "number|string|null", "submission_deadline": "string|null", "emd": "number|string|null", "minimum_turnover": "number|string|null", "experience_years": "number|string|null", "description": "string|null", "source_url": "string"}]}
    goal = "Search this public e-procurement site for active tenders matching " + json.dumps(query[:160]) + ". Read public pages only. Do not log in, enter credentials, submit forms, or place bids. Return at most " + str(max(1, min(limit, 15))) + " tenders as ONLY JSON matching " + json.dumps(schema) + ". Use null if a field is not explicitly shown; do not infer."
    try:
        with httpx.Client(timeout=httpx.Timeout(180.0, connect=20.0)) as client:
            with client.stream("POST", AGENT_URL, headers={"X-API-Key": key, "Content-Type": "application/json", "Accept": "text/event-stream"}, json={"url": source, "goal": goal}) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line.startswith("data:"): continue
                    event = json.loads(line[5:].strip())
                    if event.get("type") == "COMPLETE":
                        if event.get("status") != "COMPLETED": raise RuntimeError("TinyFish could not complete the tender search.")
                        result = event.get("resultJson", {})
                        data = [normalize(item, source) for item in rows(result)]
                        return [item for item in data if item]
    except httpx.HTTPStatusError as exc:
        raise RuntimeError("TinyFish returned HTTP " + str(exc.response.status_code) + ". Check API key and account limits.") from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError("TinyFish search timed out. Try a narrower search.") from exc
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        raise RuntimeError("Could not read TinyFish response. Check backend network access.") from exc
    raise RuntimeError("TinyFish ended without a completed result.")
