"""TinyFish public tender discovery and official document reader."""
import hashlib
import json
import os
import re
from urllib.parse import urlparse

import httpx

SEARCH_URL = "https://api.search.tinyfish.ai"
FETCH_URL = "https://api.fetch.tinyfish.ai"
DEFAULT_SOURCE_URL = "https://eprocure.gov.in/eprocure/app"
GENERIC_TITLES = (
    "eprocurement system government of india",
    "government eprocurement system",
    "eprocurement system of government",
    "eprocurement system of west bengal",
    "eprocurement system for organisations",
    "eprocurement system for organizations",
    "tenders by organisation",
    "tenders by organization",
    "tenders by closing date",
    "cppp tenders",
    "active tenders",
    "tender search",
    "tenders home",
)


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


def is_generic_page(title, snippet="", url=""):
    title_text = re.sub(r"[^a-z0-9 ]", " ", str(title or "").lower())
    title_text = " ".join(title_text.split())
    if any(title_text == phrase for phrase in GENERIC_TITLES):
        return True
    if "eprocurement system" in title_text or title_text.startswith("tenders by "):
        return True
    if len(title_text) < 100 and any(phrase in title_text for phrase in GENERIC_TITLES):
        return True
    path = urlparse(str(url or "")).path.rstrip("/").lower()
    return path in {"/eprocure/app", "/"} and not re.search(
        r"(tender|bid|corrig)", str(url or ""), re.I
    )


def _boilerplate(text):
    value = " ".join(str(text or "").lower().split())
    return any(phrase in value for phrase in (
        "various search options built in the cpp portal",
        "search active tenders by several parameters",
        "enables the tenderers to download the tender schedule free of cost",
        "tenders by organisation",
        "tenders by organization",
        "latest corrigendums",
    ))


def normalize(row, source):
    if not isinstance(row, dict):
        return None
    title = str(row.get("title") or row.get("tender_title") or "").strip()
    url = str(row.get("url") or row.get("source_url") or "")
    snippet = str(row.get("snippet") or row.get("description") or "").strip()
    if not title or not is_official_url(url) or is_generic_page(title, snippet, url):
        return None
    if _boilerplate(snippet):
        snippet = ""
    native = str(row.get("tender_id") or row.get("id") or "")
    key = hashlib.sha1((native + url + title).encode()).hexdigest()[:10].upper()
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
        "description": snippet[:1200] or "Open the official tender notice for the scope and bid requirements.",
        "source": "TinyFish Search · official details may be incomplete",
        "source_url": url,
        "is_live": True,
        "document_readable": False,
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


def _link_items(page):
    links = page.get("links") or []
    if isinstance(links, dict):
        links = links.get("links", [])
    return links if isinstance(links, list) else []


def _fetch_pages(client, key, urls):
    response = client.post(
        FETCH_URL,
        headers={"X-API-Key": key, "Content-Type": "application/json", "Accept": "application/json"},
        json={"urls": urls[:10], "format": "markdown", "links": True},
    )
    response.raise_for_status()
    return rows(response.json())


def _parse_amount(text, labels):
    label = "|".join(labels)
    match = re.search(
        rf"(?is)(?:{label})[^\d₹]{{0,100}}(?:₹|rs\.?|inr)?\s*([\d][\d,]*(?:\.\d+)?)",
        str(text or ""),
    )
    return number(match.group(1).replace(",", "")) if match else None


def _parse_deadline(text):
    labels = r"bid submission end date|submission end date|bid closing date|closing date|last date (?:for|of) submission|submission deadline"
    match = re.search(
        rf"(?is)(?:{labels})[^\d]{{0,100}}(\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}(?:\s+\d{{1,2}}:\d{{2}}\s*(?:am|pm)?)?|\d{{4}}-\d{{2}}-\d{{2}})",
        str(text or ""),
    )
    return " ".join(match.group(1).split()) if match else None


def _enrich_from_documents(tenders, key):
    urls = [t["source_url"] for t in tenders if is_official_url(t.get("source_url"))][:10]
    if not urls:
        return tenders
    try:
        with httpx.Client(timeout=httpx.Timeout(35.0, connect=8.0)) as client:
            pages = _fetch_pages(client, key, urls)
    except (httpx.HTTPError, json.JSONDecodeError):
        return tenders
    by_url = {}
    for page in pages:
        page_url = str(page.get("final_url") or page.get("url") or "")
        if is_official_url(page_url):
            by_url[page_url] = page
    for tender in tenders:
        page = by_url.get(tender["source_url"])
        if not page:
            continue
        text = str(page.get("text") or "").strip()
        if not text or _boilerplate(text) or is_generic_page(page.get("title"), text[:500], page.get("url")):
            continue
        page_title = str(page.get("title") or "").strip()
        if page_title and not is_generic_page(page_title, "", tender["source_url"]) and len(page_title) > len(tender["title"]):
            tender["title"] = page_title[:240]
        summary = " ".join(text.split())
        if summary:
            tender["description"] = summary[:1200]
            tender["document_readable"] = True
        if tender.get("value_inr") is None:
            tender["value_inr"] = _parse_amount(text, (
                "estimated tender value", "tender value", "estimated cost", "approximate cost"
            ))
        if tender.get("emd_inr") is None:
            tender["emd_inr"] = _parse_amount(text, (
                "emd amount", "earnest money deposit", "bid security amount"
            ))
        if tender.get("turnover_inr") is None:
            tender["turnover_inr"] = _parse_amount(text, (
                "minimum annual turnover", "average annual turnover", "annual turnover requirement"
            ))
        if tender.get("deadline") is None:
            tender["deadline"] = _parse_deadline(text)
        if tender.get("years_experience") is None:
            match = re.search(
                r"(?i)(?:minimum|required|relevant) experience[^.\n]{0,100}?(\d{1,2})\s*years?",
                text,
            )
            if match:
                tender["years_experience"] = number(match.group(1))
        for link in _link_items(page):
            if isinstance(link, dict):
                link_url = str(link.get("url") or link.get("href") or "")
                label = str(link.get("text") or link.get("title") or link.get("label") or "")
                if is_official_url(link_url) and re.search(r"corrig|amend|addend", label + " " + link_url, re.I):
                    tender["corrigendum_url"] = link_url
                    break
    return tenders


def read_tender_documents(tender):
    """Read official tender page and linked corrigendum/addendum documents on demand."""
    key = os.getenv("TINYFISH_API_KEY", "").strip()
    if not key:
        raise RuntimeError("TinyFish is not configured. Add TINYFISH_API_KEY to backend .env.")
    url = str(tender.get("source_url") or "")
    if not is_official_url(url):
        raise RuntimeError("This tender has no verified official document link.")
    try:
        with httpx.Client(timeout=httpx.Timeout(45.0, connect=8.0)) as client:
            notice_pages = _fetch_pages(client, key, [url])
            if not notice_pages:
                raise RuntimeError("TinyFish could not read the official tender page.")
            notice = notice_pages[0]
            corrigenda = []
            for link in _link_items(notice):
                if isinstance(link, str):
                    link_url, label = link, link
                elif isinstance(link, dict):
                    link_url = str(link.get("url") or link.get("href") or "")
                    label = str(link.get("text") or link.get("title") or link.get("label") or link_url)
                else:
                    continue
                if is_official_url(link_url) and re.search(r"corrig|amend|addend", (label + " " + link_url), re.I):
                    corrigenda.append((link_url, label))
            corr_urls = list(dict.fromkeys(link_url for link_url, _ in corrigenda))[:5]
            corr_pages = _fetch_pages(client, key, corr_urls) if corr_urls else []
    except httpx.HTTPStatusError as exc:
        raise RuntimeError("TinyFish document reader returned HTTP " + str(exc.response.status_code) + ".") from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError("Reading the official documents timed out. Open the official notice link directly.") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError("Could not read the official tender documents. Open the official notice link directly.") from exc

    documents = []
    for page, kind in [(notice, "Tender notice")] + [(page, "Corrigendum / amendment") for page in corr_pages]:
        doc_url = str(page.get("final_url") or page.get("url") or url)
        if not is_official_url(doc_url):
            continue
        text = str(page.get("text") or "").strip()
        if is_generic_page(str(page.get("title") or ""), text[:300], doc_url):
            continue
        documents.append({
            "kind": kind,
            "title": str(page.get("title") or kind)[:240],
            "url": doc_url,
            "text": text[:8000],
        })
    if not documents:
        raise RuntimeError("No readable tender notice or corrigendum was returned. Use the official portal link.")
    return {
        "tender_id": tender.get("id"),
        "documents": documents,
        "notice": "Document text is shown for convenience. The official tender notice and latest corrigendum control; verify dates, eligibility, and all bid terms there.",
    }


def search_tenders(query="active tenders", limit=10):
    """Find specific official tender pages and enrich them from their public documents."""
    key = os.getenv("TINYFISH_API_KEY", "").strip()
    if not key:
        raise RuntimeError("TinyFish is not configured. Add TINYFISH_API_KEY to backend .env.")
    source = os.getenv("TINYFISH_TENDER_SOURCE_URL", DEFAULT_SOURCE_URL).strip() or DEFAULT_SOURCE_URL
    if not is_official_url(source):
        raise RuntimeError("Tender source must use an official .gov.in or .nic.in domain.")

    terms = query.strip() or "active tenders"
    # Avoid site:OR syntax here: it was returning broad portal pages and no
    # individual tenders from TinyFish Search. Official-domain allowlisting is
    # applied to each result below instead.
    search_query = (
        f"{terms} current open Indian government public procurement tender notice "
        "tender reference bid closing date EMD"
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
    selected = list(unique.values())[:max(1, min(limit, 10))]
    return _enrich_from_documents(selected, key)
