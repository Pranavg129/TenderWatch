import { formatMoney } from "../api.js";

function initials(name) {
  return String(name || "Bidder").trim().split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0].toUpperCase()).join("") || "B";
}

function BidderHistory({ data }) {
  const bidders = data?.bidders || [];
  if (!bidders.length) return <div className="empty">No bidder history is available for this tender.</div>;

  return <div className="evidence-list">
    {bidders.map(bidder => {
      const awards = bidder.award_records || [];
      if (data.is_synthetic) return <article className="evidence-row" key={bidder.bidder_id}>
        <strong>{bidder.name}</strong>
        <span className="coverage">Fictional example</span>
        <p>{bidder.contract_count} sample contracts · {bidder.completed_count} completed · {bidder.on_time_count} on time</p>
        <p>Illustrative score: {Number(bidder.history_rating_out_of_5 || 0).toFixed(1)} / 5</p>
        <ul>{(bidder.contracts || []).map(item => <li key={item}>{item}</li>)}</ul>
      </article>;

      return <article className="evidence-row" key={bidder.bidder_id}>
        <strong>{bidder.name}</strong>
        <p>{awards.length} public name match{awards.length === 1 ? "" : "es"}. No performance rating is assigned.</p>
        {awards.length ? awards.map((record, index) => <details className="award-record" key={record.url + index}>
          <summary>{record.title}</summary>
          <p>{record.evidence}</p>
          <a href={record.url} target="_blank" rel="noopener noreferrer">Open CPPP source</a>
          <small>{record.match_method}</small>
        </details>) : <p className="id">No matching result found. This is unknown information, not a negative finding.</p>}
      </article>;
    })}
  </div>;
}

function SubmittedBids({ bids, onStatusChange, onLoadSamples, synthetic }) {
  if (!bids.length) return <div className="bidder-empty">
    <span className="bidder-empty-icon" aria-hidden="true">✦</span>
    <div><strong>No demo bids yet</strong><p>Preview the review screen with fictional bidder examples.</p></div>
    <button type="button" className="secondary-button" onClick={onLoadSamples}>Load example bidders</button>
  </div>;

  return <div className="bidder-grid">
    {bids.map((bid, index) => {
      const documents = bid.prepared_documents || [];
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
      <SubmittedBids bids={bids} onStatusChange={onStatusChange} onLoadSamples={onLoadSamples} synthetic={Boolean(history?.is_synthetic)} />
    </section>

    <details className="evidence-disclosure">
      <summary>{history?.is_synthetic ? "View fictional comparison details" : "Optional context: public CPPP award records"}</summary>
      {history?.is_synthetic
        ? <div className="review-summary">Fictional scores and outcomes are illustrative only. They must not be used to assign a tender.</div>
        : <div className="review-summary">CPPP results are name-only matches. They do not verify legal identity, contract completion, delivery quality, or supplier performance. No match means unknown.</div>}
      <BidderHistory data={history} />
    </details>

    <p className="review-disclaimer">Bid status changes are temporary and reset when the demo backend restarts. A human reviewer remains responsible for the decision.</p>
  </section>;
}
