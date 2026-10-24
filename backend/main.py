"""TenderWatch MVP API: demo tender discovery and eligibility checks."""
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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
    return {"status": "healthy", "tinyfish_configured": False,
            "note": "TinyFish credentials and endpoint must be configured before live extraction."}

@app.get("/api/tenders")
def list_tenders(q: str = "", category: str = "All"):
    items = DEMO_TENDERS
    if q.strip():
        needle = q.strip().lower()
        items = [t for t in items if needle in (t["title"] + " " + t["buyer"] + " " + t["location"] + " " + t["description"]).lower()]
    if category != "All":
        items = [t for t in items if t["category"].lower() == category.lower()]
    return {"items": items, "count": len(items), "demo": True}

@app.post("/api/eligibility/{tender_id}")
def eligibility(tender_id: str, profile: BusinessProfile):
    tender = next((t for t in DEMO_TENDERS if t["id"] == tender_id), None)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    checks = [
        {"name": "Annual turnover", "required": f"₹{tender['turnover_inr']:,.0f}",
         "provided": f"₹{profile.annual_turnover_inr:,.0f}",
         "pass": profile.annual_turnover_inr >= tender["turnover_inr"]},
        {"name": "Relevant experience", "required": f"{tender['years_experience']} years",
         "provided": f"{profile.years_experience} years",
         "pass": profile.years_experience >= tender["years_experience"]},
        {"name": "Category match", "required": tender["category"],
         "provided": ", ".join(profile.categories),
         "pass": any(c.lower() == tender["category"].lower() for c in profile.categories)},
        {"name": "EMD capacity", "required": f"₹{tender['emd_inr']:,.0f}",
         "provided": f"₹{profile.available_emd_inr:,.0f}",
         "pass": profile.available_emd_inr >= tender["emd_inr"]},
    ]
    passed = sum(1 for c in checks if c["pass"])
    return {"tender_id": tender_id, "checks": checks, "passed": passed,
            "total": len(checks), "status": "Potential match" if passed == len(checks) else "Review required",
            "notice": "Preliminary screening only. Official tender documents and amendments take precedence."}

@app.get("/api/tinyfish/status")
def tinyfish_status():
    # Do not expose secrets. Live integration requires verified API docs and configured credentials.
    import os
    return {"configured": bool(os.getenv("TINYFISH_API_KEY") and os.getenv("TINYFISH_API_URL")),
            "mode": "integration-ready", "live_extraction_enabled": False}
