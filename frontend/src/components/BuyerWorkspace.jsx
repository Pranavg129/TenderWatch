import { formatMoney } from "../api.js";

function BidderHistory({ data }) {
  const bidders = data?.bidders || [];
  if (!bidders.length) return <div className="empty">No bidders have submitted for this tender yet, so no bidder history is shown.</div>;
  return <>
    {data.notice && <div className="review-summary">{data.notice}</div>}
    <div className="history-grid">
      {bidders.map(bidder => {
        const awards = bidder.award_records || [];
        if (data.is_synthetic) return <article className="history-card" key={bidder.bidder_id}>
          <h3>{bidder.name}</h3><div className="history-rating"><strong>{Number(bidder.history_rating_out_of_5 || 0).toFixed(1)} / 5</strong><span>illustrative only</span></div>
          <p>{bidder.contract_count} sample contracts · {bidder.completed_count} completed · {bidder.on_time_count} on time</p>
          <span className="coverage">Fictional sample record</span>
          <ul>{(bidder.contracts || []).map(item => <li key={item}>{item}</li>)}</ul>
        </article>;
        return <article className="history-card" key={bidder.bidder_id}>
          <h3>{bidder.name}</h3><span className="coverage">{bidder.coverage}</span>
          <p>Public award records found: <strong>{awards.length}</strong>. No performance rating is assigned.</p>
          {awards.length ? awards.map((record, index) => <div className="history-record" key={record.url + index}>
            <strong>{record.title}</strong><p>{record.evidence}</p>
            <a href={record.url} target="_blank" rel="noopener noreferrer">Open CPPP source</a>
            <small>{record.match_method}</small>
          </div>) : <p className="history-record">No matching public CPPP award result was found. This is unknown information, not a negative performance finding.</p>}
        </article>;
      })}
    </div>
  </>;
}

function SubmittedBids({ bids, onStatusChange }) {
  if (!bids.length) return <div className="empty">No demo bids yet for this tender. Switch to Supplier readiness → Prepare bid to create one.</div>;
  return <div className="bid-submissions">
    {bids.map(bid => <article className="submitted-bid" key={bid.bid_id}>
      <div className="submitted-bid-top">
        <div><b>{bid.bidder_name}</b><div className="id">{bid.bid_id} · {bid.status}</div></div>
        <strong>{bid.offer_amount_inr == null ? "Quote not shown" : formatMoney(bid.offer_amount_inr)}</strong>
      </div>
      <p>{bid.technical_summary}</p>
      <p className="id">Prepared documents: {(bid.prepared_documents || []).join(", ") || "Not listed"}</p>
      <label className="review-status">Buyer review status
        <select value={bid.status} onChange={event => onStatusChange(bid.bid_id, event.target.value)}>
          {["Received (demo)", "Under review", "Clarification needed", "Evaluated"].map(status => <option key={status}>{status}</option>)}
        </select>
      </label>
    </article>)}
  </div>;
}

export default function BuyerWorkspace({ tenders, tenderId, onTenderChange, history, bids, status, onRefresh, onLoadSamples, onStatusChange }) {
  const tender = tenders.find(item => item.id === tenderId);
  return <section className="buyer-workspace" aria-labelledby="buyer-title">
    <div className="buyer-heading"><h2 id="buyer-title">Buyer review workspace</h2><span className="demo-warning">Demo bids · public award lookup is informational only</span></div>
    <p className="buyer-intro">Choose a tender to review bids submitted in TenderWatch. CPPP award matches are name-only and are not a supplier rating or award recommendation.</p>
    <div className="history-toolbar">
      <label htmlFor="buyer-tender" className="id">Tender:</label>
      <select id="buyer-tender" value={tenderId} onChange={e => onTenderChange(e.target.value)}>
        {tenders.map(item => <option key={item.id} value={item.id}>{item.id} · {item.title}</option>)}
      </select>
      <button type="button" onClick={onRefresh}>Refresh tender view</button>
      <span className="id" aria-live="polite">{status}</span>
    </div>
    <div className="history-toolbar"><button type="button" className="secondary-button" onClick={onLoadSamples}>Load illustrative bidder comparison</button><span className="id">Fictional bidders, bids and scores.</span></div>
    <h3 className="section-title">Submitted bids</h3>
    <p className="buyer-intro">Review each demo submission against the criteria published in its tender. Status changes stay in the running demo backend.</p>
    <SubmittedBids bids={bids} onStatusChange={onStatusChange} />
    <h3 className="section-title">CPPP public award records</h3>
    <p className="buyer-intro">Awards are not proof of completion or quality. Confirm the bidder’s legal identity and review the official source.</p>
    <BidderHistory data={history} />
    <div className="review-summary">Review reminders: apply the tender’s published and verifiable criteria consistently, record evidence gaps, and keep a human decision-maker responsible for evaluation.</div>
    <p className="review-disclaimer">All TenderWatch bids shown here are demo records, not real government portal submissions. A production deployment needs authenticated roles, secure document storage, audit logs, an authorized source, and legally approved tender-specific rules.</p>
  </section>;
}
