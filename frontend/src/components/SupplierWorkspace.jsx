import TenderCard from "./TenderCard.jsx";
import EligibilityPanel from "./EligibilityPanel.jsx";

export default function SupplierWorkspace(props) {
  const filtered = props.tenders.filter(tender => {
    const queryMatch = [tender.title, tender.buyer, tender.location, tender.desc].join(" ").toLowerCase().includes(props.query.toLowerCase());
    const categoryMatch = props.category === "All" || tender.category === props.category;
    const result = props.results[tender.id];
    const eligibilityMatch = props.eligibilityFilter === "All results" || result?.status === props.eligibilityFilter;
    return queryMatch && categoryMatch && eligibilityMatch;
  });
  return <section>
    <div className="stats">
      <div className="stat"><strong>{filtered.length}</strong><span>Displayed opportunities</span></div>
      <div className="stat"><strong>4</strong><span>Eligibility signals checked</span></div>
      <div className="stat"><strong>₹0</strong><span>Cost to explore this demo</span></div>
    </div>
    <div className="toolbar">
      <input value={props.query} onChange={e => props.setQuery(e.target.value)} placeholder="Search by tender, buyer or location…" aria-label="Search tenders" />
      <select value={props.category} onChange={e => props.setCategory(e.target.value)} aria-label="Filter by category">
        {["All", "Goods", "Services", "Electrical"].map(x => <option key={x}>{x}</option>)}
      </select>
      <button type="button" className="secondary-button" onClick={props.resetFilters}>Reset filters</button>
    </div>
    <div className="eligibility-tools">
      <button type="button" onClick={props.onCheckAll} disabled={props.checkingAll}>{props.checkingAll ? "Checking…" : "Check all eligibility"}</button>
      <label htmlFor="eligibility-filter" className="id">Show:</label>
      <select id="eligibility-filter" value={props.eligibilityFilter} onChange={e => props.setEligibilityFilter(e.target.value)}>
        {["All results", "Potential match", "Review required", "Likely not eligible"].map(x => <option key={x}>{x}</option>)}
      </select>
      <button type="button" className="secondary-button" onClick={props.onFetchLive} disabled={props.fetchingLive}>{props.fetchingLive ? "Fetching…" : "Fetch live tenders"}</button>
      <span className="id" aria-live="polite">{props.progress}</span>
      <span className="id alert-copy" aria-live="polite">{props.alertMessage}</span>
    </div>
    <div className="grid">
      <section className="list" aria-live="polite">
        {filtered.length ? filtered.map(tender => <TenderCard
          key={tender.id}
          tender={tender}
          result={props.results[tender.id]}
          bidSubmitted={props.userBids.some(bid => bid.tender_id === tender.id)}
          alertOn={props.alerts.includes(tender.id)}
          onCheck={props.onCheck}
          onPrepareBid={props.onPrepareBid}
          onToggleAlert={props.onToggleAlert}
        />) : <div className="empty">No tenders match those filters. Try another search or result filter.</div>}
      </section>
      <EligibilityPanel profile={props.profile} onChange={props.onProfileChange} result={props.selectedResult} selectedTender={props.selectedTender} />
    </div>
  </section>;
}
