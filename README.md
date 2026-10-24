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
- **Tender research automation:** TinyFish integration (requires a configured API endpoint and key)
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
| `TINYFISH_API_URL` | Base URL or endpoint required by the TinyFish client |
| `APP_ENV` | Environment label, such as `development` |

Confirm the required TinyFish endpoint and request format against the API documentation and the implementation before running live requests.

## Development status

This repository is under active development. Do not assume a feature is complete merely because it appears in the intended workflow above. Verify the current code, tests, and configured data sources before presenting a capability as working.

## Responsible use

- Display source URLs and retrieval timestamps for sourced tender information wherever possible.
- Distinguish extracted facts from model-generated interpretations.
- Do not make final legal, financial, or bid-submission decisions solely from automated eligibility results.
- Verify deadlines, corrigenda, eligibility, and document requirements on the official tender portal before submission.
- Never store credentials in source code or commit real secrets.

## Project notes

See [SUBMISSION.md](SUBMISSION.md) for the demo-readiness checklist and integrity notes.
