"""Explainable first-pass tender eligibility checks."""
from typing import Any

def check_eligibility(tender: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {"name": "Annual turnover", "required": tender.get("turnover_inr", 0),
         "provided": profile.get("annual_turnover_inr", 0),
         "pass": profile.get("annual_turnover_inr", 0) >= tender.get("turnover_inr", 0)},
        {"name": "Relevant experience", "required": tender.get("years_experience", 0),
         "provided": profile.get("years_experience", 0),
         "pass": profile.get("years_experience", 0) >= tender.get("years_experience", 0)},
        {"name": "Category match", "required": tender.get("category", ""),
         "provided": profile.get("categories", []),
         "pass": tender.get("category", "").lower() in [c.lower() for c in profile.get("categories", [])]},
        {"name": "EMD capacity", "required": tender.get("emd_inr", 0),
         "provided": profile.get("available_emd_inr", 0),
         "pass": profile.get("available_emd_inr", 0) >= tender.get("emd_inr", 0)},
    ]
    passed = sum(c["pass"] for c in checks)
    return {"checks": checks, "passed": passed, "total": len(checks),
            "status": "Potential match" if passed == len(checks) else "Review required",
            "is_guarantee": False}
