import { useState } from "react";
import { api, formatMoney } from "../api.js";

function ResultBadge({ result }) {
  if (!result) return <span className="id">Preliminary screening available</span>;
  const tone = result.status === "Potential match" ? "status-potential" : result.status === "Likely not eligible" ? "status-ineligible" : "status-review";
  return <span><span className={"status " + tone}>{result.status}</span><span className="id"> {result.passed} of {result.total} checks</span></span>;
}

export default function TenderCard({ tender, result, bidSubmitted, alertOn, onCheck, onPrepareBid, onToggleAlert }) {
  const [docsOpen, setDocsOpen] = useState(false);
  const [docs, setDocs] = useState(null);
  const [docError, setDocError] = useState("");
  const [docLoading, setDocLoading] = useState(false);

  async function readDocuments() {
    if (docs) { setDocsOpen(!docsOpen); return; }
    setDocsLoading(true);
  }

  async function setDocsLoading(value) {
    setDocLoading(value);
    if (!value) return;
    setDocError("");
    try {
      const data = await api("/tenders/" + encodeURIComponent(tender.id) + "/documents");
      setDocs(data);
      setDocsOpen(true);
    } catch (error) {
      setDocError(error.message);
      setDocsOpen(true);
    } finally {
      setDocLoading(false);
    }
  }

  return (
    <article className="tender">
      <div className="tender-top">
        <div><div className="id">{tender.id} · {tender.buyer}</div><h3>{tender.title}</h3></div>
        <div className="amount">{formatMoney(tender.value)}</div>
      </div>
      <div className="meta"><span>⌖ {tender.location}</span><span>◷ Deadline: {tender.deadline}</span><span>EMD: {formatMoney(tender.emd)}</span></div>
      <p className="tender-description">{tender.desc}</p>
      <details className="tender-guide">
        <summary>What will I be bidding for?</summary>
        <p><b>Purpose:</b> {tender.purpose}</p><p><b>Work:</b> {tender.work}</p>
        <p><b>Illustrative requirements:</b> {tender.requirements}</p><p><b>Procedure:</b> {tender.procedure}</p>
      </details>
      {tender.isLive && <section className="official-docs">
        <button className="link-button" type="button" onClick={readDocuments} disabled={docLoading}>
          {docLoading ? "Reading official documents…" : "Read tender notice & corrigenda"}
        </button>
        {docsOpen && <div className="document-reader">
          {docError && <p className="history-error">{docError}</p>}
          {docs?.documents?.map((doc, index) => <details key={doc.url + index} open={index === 0}>
            <summary>{doc.kind}: {doc.title}</summary>
            <p><a href={doc.url} target="_blank" rel="noopener noreferrer">Open original on official portal</a></p>
            <pre>{doc.text || "No readable text returned. Use the official portal link."}</pre>
          </details>)}
          {docs?.notice && <small>{docs.notice}</small>}
        </div>}
      </section>}
      <div className="chips">
        <span className="chip">{tender.category}</span>
        <span className="chip">Turnover: {formatMoney(tender.turnover)}</span>
        <span className="chip">Experience: {tender.experience == null ? "Not listed" : tender.experience + "+ yrs"}</span>
        <span className="chip">{tender.isLive ? "TinyFish extraction · verify official notice" : "Illustrative data"}</span>
        {tender.source_url && <a className="chip" href={tender.source_url} target="_blank" rel="noopener noreferrer">Official source</a>}
      </div>
      <div className="tender-actions">
        <span className="id">{bidSubmitted ? "Demo bid submitted" : <ResultBadge result={result} />}</span>
        <div className="tender-buttons">
          <button type="button" onClick={() => onCheck(tender)}>Check eligibility →</button>
          <button type="button" className="secondary-button" onClick={() => onPrepareBid(tender)}>Prepare bid</button>
          <button type="button" className="secondary-button" onClick={() => onToggleAlert(tender)}>{alertOn ? "Alerts on" : "Set alert"}</button>
        </div>
      </div>
    </article>
  );
}
