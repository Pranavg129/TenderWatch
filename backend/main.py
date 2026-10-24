"""TenderWatch MVP API: demo tender discovery and eligibility checks."""
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from backend import tinyfish_client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="TenderWatch API", version="0.1.0",
              description="MVP API for MSME tender discovery and eligibility screening.")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"]
)

DEMO_TENDERS: list[dict[str, Any]] = [
    {
        "id": "TW-2026-001", "title": "Supply of office and computer consumables",
        "buyer": "Demo Public Sector Office", "location": "New Delhi",
        "category": "Goods", "value_inr": 850000, "deadline": "2026-11-12",
        "emd_inr": 17000, "turnover_inr": 2500000, "years_experience": 2,
        "description": "Supply and delivery of office consumables and basic computer accessories.",
        "source": "Demo dataset — not a live tender"
    },
    {
        "id": "TW-2026-002", "title": "Annual maintenance of networking equipment",
        "buyer": "Demo Government IT Department", "location": "Faridabad, Haryana",
        "category": "Services", "value_inr": 1450000, "deadline": "2026-11-18",
        "emd_inr": 29000, "turnover_inr": 5000000, "years_experience": 3,
        "description": "Preventive maintenance and support for routers, switches and LAN infrastructure.",
        "source": "Demo dataset — not a live tender"
    },
    {
        "id": "TW-2026-003", "title": "Supply of LED street-light components",
        "buyer": "Demo Municipal Procurement Unit", "location": "Gurugram, Haryana",
        "category": "Electrical", "value_inr": 620000, "deadline": "2026-11-08",
        "emd_inr": 12400, "turnover_inr": 1800000, "years_experience": 1,
        "description": "Supply of LED drivers, connectors and related street-light components.",
        "source": "Demo dataset — not a live tender"
    }
]


BID_SUBMISSIONS: list[dict[str, Any]] = []
LIVE_TENDERS: list[dict[str, Any]] = []

def find_tender(tender_id: str):
    return next((t for t in DEMO_TENDERS + LIVE_TENDERS if t['id'] == tender_id), None)

class BidSubmission(BaseModel):
    bidder_name: str = Field(min_length=2, max_length=120)
    offer_amount_inr: float = Field(gt=0)
    technical_summary: str = Field(min_length=10, max_length=2000)
    prepared_documents: list[str] = Field(default_factory=list)
    confirms_tender_terms: bool = False

class BidStatusUpdate(BaseModel):
    status: str

class BusinessProfile(BaseModel):
    annual_turnover_inr: float = Field(default=3000000, ge=0)
    years_experience: int = Field(default=2, ge=0)
    categories: list[str] = Field(default_factory=lambda: ["Goods", "Services", "Electrical"])
    available_emd_inr: float = Field(default=50000, ge=0)

@app.get("/")
def root():
    return {"name": "TenderWatch API", "status": "ok", "mode": "demo",
            "notice": "Demo data only; verify all tender details with the official source."}

@app.get("/api/health")
def health():
    return {"status": "healthy", "tinyfish_configured": tinyfish_client.status()["configured"],
            "note": "TinyFish fetches public tenders when configured; bids stay inside this demo backend."}

@app.get("/api/tenders")
def list_tenders(q: str = "", category: str = "All"):
    items = DEMO_TENDERS + LIVE_TENDERS
    if q.strip():
        needle = q.strip().lower()
        items = [t for t in items if needle in (t["title"] + " " + t["buyer"] + " " + t["location"] + " " + t["description"]).lower()]
    if category != "All":
        items = [t for t in items if t["category"].lower() == category.lower()]
    return {"items": items, "count": len(items), "demo": not bool(LIVE_TENDERS), "live_count": len(LIVE_TENDERS)}

class TenderSearch(BaseModel):
    query: str = Field(default="active tenders", max_length=160)
    limit: int = Field(default=10, ge=1, le=15)

@app.post("/api/tenders/refresh")
def refresh_tenders(request: TenderSearch):
    """Fetch public tender listings; bid submission remains internal."""
    global LIVE_TENDERS
    try:
        LIVE_TENDERS = tinyfish_client.search_tenders(request.query, request.limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": LIVE_TENDERS, "count": len(LIVE_TENDERS),
            "source": "TinyFish public extraction",
            "notice": "Extracted tender details may be incomplete or stale. Verify official notices and corrigenda."}

@app.get("/api/tenders/{tender_id}/documents")
def tender_documents(tender_id: str):
    """Read the public tender notice and linked corrigenda on demand."""
    tender = find_tender(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    try:
        return tinyfish_client.read_tender_documents(tender)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/tinyfish/status")
def tinyfish_status():
    return tinyfish_client.status()

@app.post("/api/eligibility/{tender_id}")
def eligibility(tender_id: str, profile: BusinessProfile):
    tender = find_tender(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    turnover = tender.get("turnover_inr")
    experience = tender.get("years_experience")
    emd = tender.get("emd_inr")
    checks = [
        {"name": "Annual turnover", "required": f"₹{turnover:,.0f}" if turnover is not None else "Not listed in extracted data",
         "provided": f"₹{profile.annual_turnover_inr:,.0f}",
         "pass": turnover is not None and profile.annual_turnover_inr >= turnover},
        {"name": "Relevant experience", "required": f"{experience:g} years" if experience is not None else "Not listed in extracted data",
         "provided": f"{profile.years_experience} years",
         "pass": experience is not None and profile.years_experience >= experience},
        {"name": "Category match", "required": tender.get("category") or "Not listed",
         "provided": ", ".join(profile.categories),
         "pass": bool(tender.get("category")) and any(c.lower() == tender["category"].lower() for c in profile.categories)},
        {"name": "EMD capacity", "required": f"₹{emd:,.0f}" if emd is not None else "Not listed in extracted data",
         "provided": f"₹{profile.available_emd_inr:,.0f}",
         "pass": emd is not None and profile.available_emd_inr >= emd},
    ]
    passed = sum(1 for c in checks if c["pass"])
    return {"tender_id": tender_id, "checks": checks, "passed": passed, "total": len(checks),
            "status": "Potential match" if passed == len(checks) else ("Likely not eligible" if passed == 0 and all("Not listed" not in c["required"] for c in checks) else "Review required"),
            "notice": "Preliminary screening only. Extracted data may be incomplete; official tender documents and amendments take precedence."}


@app.get("/api/bidders/history/{tender_id}")
def bidder_history(tender_id: str):
    """Show history slots only for bidders who actually submitted for this tender."""
    tender = find_tender(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    submitted = [b for b in BID_SUBMISSIONS if b["tender_id"] == tender_id]
    # TinyFish provider seam: connect here after confirming the authorized API schema,
    # credentials, source URLs, and supplier-identity matching requirements.
    # Do not infer performance from a name-only match.
    bidders = [{
        "bidder_id": b["bid_id"],
        "name": b["bidder_name"],
        "contract_count": 0,
        "completed_count": 0,
        "on_time_count": 0,
        "delayed_count": 0,
        "contracts": [],
        "coverage": "No verified history source connected",
    } for b in submitted]
    from datetime import datetime, timezone
    return {
        "tender_id": tender_id,
        "source": "No verified external performance source connected",
        "is_synthetic": False,
        "records_verified": False,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "bidders": bidders,
        "notice": "This endpoint does not fetch real contract-performance records. A missing history record is unknown, not a negative rating.",
    }

@app.get("/api/bids")
def list_bids(tender_id: str | None = None):
    """List demo bid submissions, optionally for one sample tender."""
    items = BID_SUBMISSIONS
    if tender_id:
        items = [b for b in items if b["tender_id"] == tender_id]
    return {"items": items, "count": len(items), "demo": True}

@app.post("/api/bids/{tender_id}")
def submit_bid(tender_id: str, bid: BidSubmission):
    """Store a demo bid in memory; this does not submit to a government portal."""
    if not find_tender(tender_id):
        raise HTTPException(status_code=404, detail="Tender not found")
    if not bid.confirms_tender_terms:
        raise HTTPException(status_code=400, detail="Confirm the sample tender terms before submitting")
    from datetime import datetime, timezone
    bid_id = tender_id + "-BID-" + str(len(BID_SUBMISSIONS) + 1).zfill(3)
    record = {
        "bid_id": bid_id, "tender_id": tender_id, "bidder_name": bid.bidder_name,
        "offer_amount_inr": bid.offer_amount_inr, "technical_summary": bid.technical_summary,
        "prepared_documents": bid.prepared_documents, "status": "Received (demo)",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "is_demo_submission": True,
    }
    BID_SUBMISSIONS.append(record)
    return record

@app.patch("/api/bids/{bid_id}/status")
def update_bid_status(bid_id: str, update: BidStatusUpdate):
    allowed = {"Received (demo)", "Under review", "Clarification needed", "Evaluated"}
    if update.status not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported demo review status")
    bid = next((b for b in BID_SUBMISSIONS if b["bid_id"] == bid_id), None)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    bid["status"] = update.status
    return bid

