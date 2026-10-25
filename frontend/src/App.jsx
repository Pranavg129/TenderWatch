import { useEffect, useMemo, useState } from "react";
import { api, fromLiveTender, loadSavedProfile } from "./api.js";
import { demoTenders } from "./data/demoTenders.js";
import SupplierWorkspace from "./components/SupplierWorkspace.jsx";
import BuyerWorkspace from "./components/BuyerWorkspace.jsx";
import BidDialog from "./components/BidDialog.jsx";

function readAlerts() {
  try { return JSON.parse(localStorage.getItem("tenderwatch-alerts") || "[]").map(item => item.tender_id); }
  catch { return []; }
}

function fallbackScreen(tender, profile) {
  const checks = [
    { name: "Annual turnover", required: tender.turnover == null ? "Not listed" : "₹" + tender.turnover.toLocaleString("en-IN"), pass: tender.turnover != null && profile.annual_turnover_inr >= tender.turnover },
    { name: "Relevant experience", required: tender.experience == null ? "Not listed" : tender.experience + " years", pass: tender.experience != null && profile.years_experience >= tender.experience },
    { name: "Category match", required: tender.category || "Not listed", pass: Boolean(tender.category) && profile.categories.some(category => category.toLowerCase() === tender.category.toLowerCase()) },
    { name: "EMD capacity", required: tender.emd == null ? "Not listed" : "₹" + tender.emd.toLocaleString("en-IN"), pass: tender.emd != null && profile.available_emd_inr >= tender.emd }
  ];
  const passed = checks.filter(check => check.pass).length;
  const known = tender.turnover != null && tender.experience != null && tender.emd != null && Boolean(tender.category);
  return { checks, passed, total: checks.length, status: passed === 4 ? "Potential match" : passed === 0 && known ? "Likely not eligible" : "Review required" };
}

export default function App() {
  const [tenders, setTenders] = useState(demoTenders);
  const [profile, setProfile] = useState(loadSavedProfile);
  const [results, setResults] = useState({});
  const [selectedTenderId, setSelectedTenderId] = useState("");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [eligibilityFilter, setEligibilityFilter] = useState("All results");
  const [mode, setMode] = useState("supplier");
  const [checkingAll, setCheckingAll] = useState(false);
  const [fetchingLive, setFetchingLive] = useState(false);
  const [progress, setProgress] = useState("");
  const [userBids, setUserBids] = useState([]);
  const [alerts, setAlerts] = useState(readAlerts);
  const [alertMessage, setAlertMessage] = useState("Alerts are stored on this device; automatic live changes are not connected.");
  const [buyerTenderId, setBuyerTenderId] = useState("TW-2026-003");
  const [history, setHistory] = useState(null);
  const [buyerBids, setBuyerBids] = useState([]);
  const [buyerStatus, setBuyerStatus] = useState("Choose a tender and refresh its review.");
  const [buyerLoading, setBuyerLoading] = useState(false);
  const [dialogTender, setDialogTender] = useState(null);

  const selectedTender = tenders.find(tender => tender.id === selectedTenderId) || null;
  const selectedResult = selectedTender ? results[selectedTender.id] : null;

  useEffect(() => {
    localStorage.setItem("tenderwatch-business-profile", JSON.stringify(profile));
  }, [profile]);

  useEffect(() => {
    api("/bids").then(data => setUserBids(data.items || [])).catch(() => {});
  }, []);

  const visibleTenders = useMemo(() => tenders.filter(tender => {
    const textMatches = [tender.title, tender.buyer, tender.location, tender.desc].join(" ").toLowerCase().includes(query.toLowerCase());
    const categoryMatches = category === "All" || tender.category.toLowerCase() === category.toLowerCase();
    const result = results[tender.id];
    const eligibilityMatches = eligibilityFilter === "All results" || result?.status === eligibilityFilter;
    return textMatches && categoryMatches && eligibilityMatches;
  }), [tenders, query, category, eligibilityFilter, results]);

  async function checkTender(tender) {
    setSelectedTenderId(tender.id);
    const body = {
      annual_turnover_inr: Number(profile.annual_turnover_inr),
      years_experience: Number(profile.years_experience),
      available_emd_inr: Number(profile.available_emd_inr),
      categories: profile.categories
    };
    let result;
    try {
      result = await api("/eligibility/" + encodeURIComponent(tender.id), { method: "POST", body: JSON.stringify(body) });
    } catch {
      result = fallbackScreen(tender, body);
    }
    setResults(previous => ({ ...previous, [tender.id]: result }));
    return result;
  }

  async function checkAll() {
    if (checkingAll || !visibleTenders.length) return;
    setCheckingAll(true);
    setProgress("Screening " + visibleTenders.length + " displayed tenders…");
    await Promise.all(visibleTenders.map(checkTender));
    setProgress("Screened " + visibleTenders.length + " tenders.");
    setCheckingAll(false);
  }

  async function fetchLive() {
    setFetchingLive(true);
    setProgress("Searching official tender listings with TinyFish…");
    try {
      const data = await api("/tenders/refresh", {
        method: "POST",
        body: JSON.stringify({ query: query.trim() || "active tenders India", limit: 10 })
      });
      const live = (data.items || []).map(fromLiveTender);
      setTenders(previous => [...previous.filter(tender => !tender.isLive), ...live]);
      setProgress(data.notice || (live.length ? "Fetched " + live.length + " live tenders." : "No matching live tenders found."));
    } catch (error) {
      setProgress(error.message);
    } finally {
      setFetchingLive(false);
    }
  }

  function toggleAlert(tender) {
    const next = alerts.includes(tender.id) ? alerts.filter(id => id !== tender.id) : [...alerts, tender.id];
    setAlerts(next);
    localStorage.setItem("tenderwatch-alerts", JSON.stringify(next.map(tender_id => ({ tender_id }))));
    setAlertMessage(next.includes(tender.id) ? "Alert saved on this device for " + tender.id + "." : "Alert removed for " + tender.id + ".");
    if (next.includes(tender.id) && "Notification" in window && Notification.permission === "default") {
      Notification.requestPermission().catch(() => {});
    }
  }

  async function loadBuyerTender(tenderId = buyerTenderId) {
    if (buyerLoading || !tenderId) return;
    setBuyerLoading(true);
    setBuyerStatus("Loading bidder history and tender responses…");
    try {
      const [historyData, bidData] = await Promise.all([
        api("/bidders/history/" + encodeURIComponent(tenderId)),
        api("/bids?tender_id=" + encodeURIComponent(tenderId))
      ]);
      const actualBids = bidData.items || [];
      if (actualBids.length) {
        setHistory(historyData);
        setBuyerBids(actualBids);
        const unavailableLookups = (historyData.bidders || []).filter(bidder => bidder.lookup_error).length;
        setBuyerStatus(unavailableLookups
          ? `TinyFish history unavailable for ${unavailableLookups} bidder${unavailableLookups === 1 ? "" : "s"}.`
          : "CPPP name searches loaded · verify each source record.");
      } else {
        const examples = await api("/demo/buyer-scenario/" + encodeURIComponent(tenderId));
        setHistory(examples);
        setBuyerBids(examples.bids || []);
        setBuyerStatus("Showing fictional history examples · no real bids submitted.");
      }
    } catch (error) {
      setBuyerStatus(error.message);
      setHistory(null);
      setBuyerBids([]);
    } finally {
      setBuyerLoading(false);
    }
  }

  function switchMode(next) {
    setMode(next);
    if (next === "buyer") loadBuyerTender();
  }

  async function loadSampleEvaluation() {
    setBuyerStatus("Loading fictional comparison…");
    try {
      const data = await api("/demo/buyer-scenario/" + encodeURIComponent(buyerTenderId));
      setHistory(data);
      setBuyerBids(data.bids || []);
      setBuyerStatus("Fictional comparison · not verified");
    } catch (error) {
      setBuyerStatus(error.message);
    }
  }

  async function changeBidStatus(bidId, status) {
    try {
      const bid = await api("/bids/" + encodeURIComponent(bidId) + "/status", {
        method: "PATCH",
        body: JSON.stringify({ status })
      });
      setBuyerBids(previous => previous.map(item => item.bid_id === bidId ? bid : item));
      setUserBids(previous => previous.map(item => item.bid_id === bidId ? bid : item));
    } catch (error) {
      setBuyerStatus(error.message);
    }
  }

  async function reloadBids() {
    const data = await api("/bids");
    setUserBids(data.items || []);
    if (mode === "buyer") await loadBuyerTender();
  }

  return <>
    <header><div><div className="logo">Tender<span>Watch</span></div><div className="tag">A clearer path to public procurement for MSMEs</div></div><div className="tag">HACKATHON MVP · TEAM APEX AGNI</div></header>
    <main className="wrap">
      <section className="hero"><div><div className="eyebrow">Procurement, made clearer</div><h1>Find tenders your business can actually pursue.</h1><p>Explore opportunities, compare key requirements, and run a first-pass eligibility check before investing time in a bid.</p></div><span className="pill">⚠ Demo dataset · not live tenders</span></section>
      <div className="mode-tabs" role="tablist" aria-label="TenderWatch workspace">
        <button type="button" role="tab" aria-selected={mode === "supplier"} aria-pressed={mode === "supplier"} onClick={() => switchMode("supplier")}>Supplier readiness</button>
        <button type="button" role="tab" aria-selected={mode === "buyer"} aria-pressed={mode === "buyer"} onClick={() => switchMode("buyer")}>Buyer review workspace</button>
      </div>
      {mode === "supplier" ? <SupplierWorkspace
        tenders={tenders} query={query} setQuery={setQuery} category={category} setCategory={setCategory}
        eligibilityFilter={eligibilityFilter} setEligibilityFilter={setEligibilityFilter} results={results}
        profile={profile} onProfileChange={setProfile} selectedResult={selectedResult} selectedTender={selectedTender}
        userBids={userBids} alerts={alerts} progress={progress} alertMessage={alertMessage}
        checkingAll={checkingAll} fetchingLive={fetchingLive} onCheck={checkTender} onCheckAll={checkAll}
        onFetchLive={fetchLive} onPrepareBid={setDialogTender} onToggleAlert={toggleAlert}
        resetFilters={() => { setQuery(""); setCategory("All"); setEligibilityFilter("All results"); }}
      /> : <BuyerWorkspace
        tenders={tenders} tenderId={buyerTenderId} onTenderChange={id => { setBuyerTenderId(id); setHistory(null); setBuyerBids([]); loadBuyerTender(id); }}
        history={history} bids={buyerBids} status={buyerStatus} onRefresh={loadBuyerTender}
        onLoadSamples={loadSampleEvaluation} onStatusChange={changeBidStatus}
      />}
    </main>
    {dialogTender && <BidDialog tender={dialogTender} onClose={() => setDialogTender(null)} onSubmitted={reloadBids} />}
    <footer>TenderWatch · Built for MSMEs · Live public tender discovery is optional through TinyFish. Verify all details in official tender documents.</footer>
  </>;
}

