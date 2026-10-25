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

- **Frontend:** React 19 with Vite
- **Backend:** Python and FastAPI
- **HTTP integration:** HTTPX
- **Tender research automation:** TinyFish Web Agent (requires a private API key)
- **Backend tests:** pytest

The frontend is split into React screens and reusable components. API helpers and sample tender data live in separate modules; styles are maintained in a standalone stylesheet.

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


## Demo bid and bidder history workflow

**Prepare bid** checks the saved business profile and opens a short tender summary, offer amount, technical offer, and document-readiness checklist. **Submit demo bid** stores the record in the running backend's memory and makes it visible in the buyer review workspace. This is a private TenderWatch demonstration record; it is not sent to CPPP, GeM, or another procurement portal. Restarting the backend clears demo bids.

When no demo submissions exist, the buyer workspace automatically loads fictional bidder-history examples so the review screen is populated during a presentation. These examples are clearly labeled and do not calculate or imply a trustworthiness rating. Once actual TenderWatch demo submissions exist, the backend uses TinyFish on demand to search the public CPPP Bid Awards index by bidder name and shows the returned source snippets and links beside each bidder. These are name-only matches: they do not verify legal identity, prove delivery or quality, or determine whether a bidder is trustworthy. A missing result means unknown, not poor performance. The current demo stores bid submissions in memory and searches CPPP on demand; production use needs official integration approval, stronger legal-entity matching, caching, and a transparent performance-evaluation policy.

## Responsible use

- Display source URLs and retrieval timestamps for sourced tender information wherever possible.
- Distinguish extracted facts from model-generated interpretations.
- Do not make final legal, financial, or bid-submission decisions solely from automated eligibility results.
- Verify deadlines, corrigenda, eligibility, and document requirements on the official tender portal before submission.
- Never store credentials in source code or commit real secrets.

## Project notes

See [SUBMISSION.md](SUBMISSION.md) for the demo-readiness checklist and integrity notes.


## Run the React frontend

Install Node.js 22 LTS (Vite requires Node.js 20.19+ or 22.12+), then from the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (normally http://127.0.0.1:5173). Keep the FastAPI backend running in a separate terminal on port 8000; Vite forwards `/api` requests to it. The frontend is no longer served by opening `index.html` directly or using `py -m http.server`.

Create a production bundle with `npm run build` from the `frontend` folder. The generated `frontend/dist` directory is build output and should not be edited by hand.

