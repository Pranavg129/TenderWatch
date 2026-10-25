const API_BASE = "/api";

export async function api(path, options = {}) {
  const response = await fetch(API_BASE + path, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {})
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || payload.notice || "TenderWatch API request failed.");
  }
  return payload;
}

export function formatMoney(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "Not listed";
  return "₹" + Number(value).toLocaleString("en-IN");
}

export function fromLiveTender(tender) {
  return {
    id: tender.id,
    title: tender.title,
    buyer: tender.buyer,
    location: tender.location,
    category: tender.category,
    value: tender.value_inr,
    deadline: tender.deadline || "Not listed",
    emd: tender.emd_inr,
    turnover: tender.turnover_inr,
    experience: tender.years_experience,
    desc: tender.description || "Open the official notice for details.",
    purpose: tender.document_readable ? tender.description : "Scope details were not available in the search listing. Open the official document reader.",
    work: tender.description || "Review the official notice for scope of work.",
    procedure: "Review the tender schedule and every corrigendum. Verify all terms on the official portal before preparing a demo bid.",
    requirements: "Turnover: " + formatMoney(tender.turnover_inr) + " · Experience: " + (tender.years_experience == null ? "Not listed" : tender.years_experience + " years") + " · EMD: " + formatMoney(tender.emd_inr),
    source: tender.source,
    source_url: tender.source_url,
    isLive: true
  };
}

export function loadSavedProfile() {
  const defaults = {
    annual_turnover_inr: 3000000,
    years_experience: 2,
    available_emd_inr: 50000,
    categories: ["Goods", "Services", "Electrical"]
  };
  try {
    const saved = JSON.parse(localStorage.getItem("tenderwatch-business-profile") || "null");
    return saved ? { ...defaults, ...saved } : defaults;
  } catch {
    return defaults;
  }
}
