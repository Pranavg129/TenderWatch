import { formatMoney } from "../api.js";

function initials(name) {
  return String(name || "Bidder").trim().split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0].toUpperCase()).join("") || "B";
}

function BidderHistoryEvidence({ entry, synthetic, checkedAt }) {
  if (!entry) return <section className="bidder-history"><strong>Bidder history</strong><p>History details are not available for this bidder.</p></section>;

  if (synthetic) return <section className="bidder-history" aria-label="Fictional bidder history example">
    <div className="history-heading"><strong>Example history</strong><span className="history-badge">Fictional · not verified</span></div>
    <div className="history-facts">
      <span><strong>{entry.contract_count}</strong> sample contracts</span>
      <span><strong>{entry.completed_count}/{entry.contract_count}</strong> completed</span>
      <span><strong>{entry.on_time_count}</strong> on time</span>
      <span><strong>{entry.delayed_count}</strong> delayed</span>
    </div>
    <p className="history-verdict"><strong>Trustworthiness:</strong> Not assessed from fictional data.</p>
    <details className="bidder-history-records">
      <summary>View fictional record examples</summary>
      <ul>{(entry.contracts || []).map(item => <li key={item}>{item}</li>)}</ul>
    </details>
  </section>;

  const awards = entry.award_records || [];
  const lookupUnavailable = Boolean(entry.lookup_error);
  const lookupLabel = lookupUnavailable
    ? "Lookup unavailable"
    : awards.length
      ? `${awards.length} public name match${awards.length === 1 ? "" : "es"}`
      : "No matching public record found";
  const lookupMessage = lookupUnavailable
    ? entry.lookup_error.toLowerCase().includes("not configured")
      ? "TinyFish is not configured on this backend."
      : "TinyFish could not complete this lookup. Retry later or check the CPPP source directly."
    : awards.length
      ? "These are name-only mentions. They do not verify legal identity, delivery, or performance."
      : "Treat this as unknown information, not a negative performance finding.";

  return <section className="bidder-history" aria-label="Public bidder history lookup">
    <div className="history-heading"><strong>Public history</strong><span className={`history-badge${lookupUnavailable ? " history-badge-muted" : ""}`}>{lookupLabel}</span></div>
    <p>{lookupMessage}</p>
    <p className="history-verdict"><strong>Trustworthiness:</strong> Not determined by this lookup.</p>
    {awards.map((record, index) => <details className="bidder-history-records" key={(record.url || record.title) + index}>
      <summary>{record.title || "CPPP award record mention"}</summary>
      <p>{record.evidence || "No excerpt was returned. Open the source record to review it."}</p>
      {record.url && <a href={record.url} target="_blank" rel="noopener noreferrer">Open CPPP source</a>}
      <small>{record.match_method || "Name-only search match; identity is not verified."}</small>
    </details>)}
    {checkedAt && <small className="history-checked">TinyFish lookup checked {new Date(checkedAt).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}</small>}
  </section>;
}

function SubmittedBids({ bids, history, onStatusChange, synthetic }) {
  if (!bids.length) return <div className="bidder-empty">
    <span className="bidder-empty-icon" aria-hidden="true">✦</span>
    <div><strong>No demo bids yet</strong><p>Preview the review screen with fictional bidder examples.</p></div>
    <p className="id">Example bidders load automatically when there are no demo submissions.</p>
  </div>;

  return <div className="bidder-grid">
    {bids.map((bid, index) => {
      const documents = bid.prepared_documents || [];
      const historyEntry = (history?.bidders || []).find(item => item.bidder_id === bid.bid_id || item.name === bid.bidder_name);
      return <article className="bidder-card" key={bid.bid_id}>
        <div className="bidder-card-topline"><span>{synthetic ? "ILLUSTRATIVE BIDDER" : `BID ${String(index + 1).padStart(2, "0")}`}</span><span className="bidder-card-mark" aria-hidden="true">↗</span></div>
        <div className="bidder-card-identity">
          <span className="bidder-avatar" aria-hidden="true">{initials(bid.bidder_name)}</span>
          <div className="bidder-card-name"><strong>{bid.bidder_name}</strong><small>{synthetic ? "Fictional example" : bid.bid_id}</small></div>
        </div>
        <div className="bidder-offer">
          <span>Quoted amount</span>
          <strong>{bid.offer_amount_inr == null ? "Not shown" : formatMoney(bid.offer_amount_inr)}</strong>
        </div>
        <div className="bidder-card-bottom">
          <div className="bidder-doc-count"><span className="document-glyph" aria-hidden="true">▤</span><span><strong>{documents.length}</strong> documents listed</span></div>
          <label className="bidder-review-control"><span>Review status</span>
            {synthetic ? <em>Fictional</em> : <select aria-label={`Review status for ${bid.bidder_name}`} value={bid.status} onChange={event => onStatusChange(bid.bid_id, event.target.value)}>
              {["Received (demo)", "Under review", "Clarification needed", "Evaluated"].map(status => <option key={status}>{status}</option>)}
            </select>}
          </label>
        </div>
        <BidderHistoryEvidence entry={historyEntry} synthetic={synthetic} checkedAt={history?.checked_at} />
        <details className="bidder-details">
          <summary>Bid summary and checklist</summary>
          <p>{bid.technical_summary || "No technical summary provided."}</p>
          <p><strong>Documents listed:</strong> {documents.join(", ") || "None listed"}</p>
        </details>
      </article>;
    })}
  </div>;
}

export default function BuyerWorkspace({ tenders, tenderId, onTenderChange, history, bids, status, onRefresh, onLoadSamples, onStatusChange }) {
  return <section className="buyer-workspace" aria-labelledby="buyer-title">
    <div className="buyer-heading">
      <div><h2 id="buyer-title">Bidder review</h2><p className="buyer-intro">A clear view of offers received for the selected tender.</p></div>
      <span className="demo-warning">TenderWatch demo · no portal submission</span>
    </div>
    <div className="history-toolbar buyer-selector">
      <label htmlFor="buyer-tender" className="id">Select tender</label>
      <select id="buyer-tender" value={tenderId} onChange={event => onTenderChange(event.target.value)}>
        {tenders.map(item => <option key={item.id} value={item.id}>{item.id} · {item.title}</option>)}
      </select>
      <button type="button" onClick={() => onRefresh()}>Refresh</button>
      <span className="id" aria-live="polite">{status}</span>
    </div>

    <section className="bidder-review-panel" aria-labelledby="submitted-bids-title">
      <div className="bidder-list-title">
        <div><span className="bidder-section-kicker">TENDER RESPONSE</span><h3 id="submitted-bids-title">Submitted bids</h3></div>
        <div className="bidder-panel-actions">
          <span className="bidder-total"><strong>{bids.length}</strong><span>{bids.length === 1 ? "bid received" : "bids received"}</span></span>
          {!history?.is_synthetic && <button type="button" className="secondary-button bidder-sample-button" onClick={onLoadSamples}>Load fictional examples</button>}
        </div>
      </div>
      <p className="buyer-intro">Review each offer against the tender’s published criteria. Expand a card only when you need the technical summary or checklist.</p>
      {history?.is_synthetic && <div className="review-summary">The bidders and offers shown are fictional examples; they are not real submissions.</div>}
      <SubmittedBids bids={bids} history={history} onStatusChange={onStatusChange} synthetic={Boolean(history?.is_synthetic)} />
    </section>

    <p className="review-disclaimer">TinyFish searches public CPPP award records by bidder name only. No trustworthiness score is produced; verify the legal entity and source records. A human reviewer remains responsible for the decision. Bid status changes are temporary and reset when the demo backend restarts.</p>
  </section>;
}

