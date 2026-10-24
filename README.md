# TenderWatch

**An AI-assisted tender desk for Indian MSMEs.**

Government tenders are spread across multiple portals. Eligibility rules can be buried in lengthy documents, while corrigenda can change deadlines or requirements. TenderWatch is designed to help small businesses discover relevant opportunities, understand eligibility, track amendments, and prepare bid-document checklists.

## Problem we are solving

Small and medium businesses often lack a dedicated bid team. Manually checking portals and tender documents is time-consuming, and missing a changed deadline or mandatory document can disqualify an otherwise strong bid.

## Intended workflow

1. **Discover** tender opportunities from supported sources.
2. **Extract** key details such as buyer, deadline, estimated value, eligibility, and required documents.
3. **Check eligibility** against a business profile, showing the evidence and any missing information.
4. **Track corrigenda** and flag changes that may affect a saved tender.
5. **Prepare** a practical document checklist before submission.

The exact capabilities available depend on the current implementation and configured data sources. Sample tenders are for demonstration only and must not be mistaken for live government listings.

## Tech stack

- **Backend:** Python and FastAPI
- **HTTP integration:** HTTPX
- **Tender research automation:** TinyFish Web Agent (requires a private API key)
- **Tests:** pytest

The frontend and remaining backend modules will be documented here as they are implemented.

## Getting started

Use Python 3.10 or newer.

```bash
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Copy `.env.example` to `.env` and fill in credentials only if you are using the TinyFish integration. Never commit `.env` or API keys.

Run the API once `backend/main.py` is available:

```bash
uvicorn backend.main:app --reload
```

## Configuration

| Variable | Purpose |
|---|---|
| `TINYFISH_API_KEY` | API key for TinyFish; keep it private |
| `TINYFISH_TENDER_SOURCE_URL` | Public `.gov.in` or `.nic.in` tender page TinyFish should read; defaults to CPPP |
| `APP_ENV` | Environment label, such as `development` |

The backend calls TinyFish's documented Web Agent endpoint. The browser never receives the API key. After setting a key, choose **Fetch live tenders** in the supplier workspace and enter a search phrase in the tender search box. Only public pages are read; login, bid placement, and external submissions are not automated. Extracted fields can be incomplete, so check each linked official notice.

## Development status

This repository is under active development. Do not assume a feature is complete merely because it appears in the intended workflow above. Verify the current code, tests, and configured data sources before presenting a capability as working.


## Demo bid workflow

**Prepare bid** checks the saved business profile and opens a short tender summary, offer amount, technical offer, and document-readiness checklist. **Submit demo bid** stores the record in the running backend's memory and makes it visible in the buyer review workspace. This is a private TenderWatch demonstration record; it is not sent to CPPP, GeM, or another procurement portal. Restarting the backend clears demo bids.

Bidder history is shown only for suppliers who actually submitted a demo bid for the selected tender. When the buyer review loads, the backend uses TinyFish to search the public CPPP Bid Awards index for exact name mentions and displays matching source snippets and links. These are name-only matches: they do not verify the supplier legal identity, prove delivery or quality, or produce a trust rating. CPPP award data can show details such as selected bidder, bid count, award date, and contract value where published. A missing record means unknown, not poor performance. The current demo stores bid submissions in memory and searches CPPP on demand; production use needs official integration approval, stronger legal-entity matching, caching, and a transparent performance-evaluation policy.

## Responsible use

- Display source URLs and retrieval timestamps for sourced tender information wherever possible.
- Distinguish extracted facts from model-generated interpretations.
- Do not make final legal, financial, or bid-submission decisions solely from automated eligibility results.
- Verify deadlines, corrigenda, eligibility, and document requirements on the official tender portal before submission.
- Never store credentials in source code or commit real secrets.

## Project notes

See [SUBMISSION.md](SUBMISSION.md) for the demo-readiness checklist and integrity notes.
