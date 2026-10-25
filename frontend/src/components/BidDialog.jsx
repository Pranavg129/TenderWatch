import { useEffect, useState } from "react";
import { api, formatMoney } from "../api.js";

const requiredDocs = ["Business registration proof", "Turnover / financial proof", "Relevant work orders", "EMD / exemption proof", "Technical offer"];

export default function BidDialog({ tender, onClose, onSubmitted }) {
  const [bidderName, setBidderName] = useState("");
  const [amount, setAmount] = useState("");
  const [technicalSummary, setTechnicalSummary] = useState("");
  const [documents, setDocuments] = useState([]);
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setBidderName("");
    setAmount(tender?.value || "");
    setTechnicalSummary("");
    setDocuments([]);
    setConfirmed(false);
    setMessage("");
  }, [tender]);

  if (!tender) return null;

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      await api("/bids/" + encodeURIComponent(tender.id), {
        method: "POST",
        body: JSON.stringify({
          bidder_name: bidderName,
          offer_amount_inr: Number(amount),
          technical_summary: technicalSummary,
          prepared_documents: documents,
          confirms_tender_terms: confirmed
        })
      });
      await onSubmitted();
      onClose();
    } catch (error) {
      setMessage(error.message + " Check that the backend is running and the sample tender terms are confirmed.");
    } finally {
      setBusy(false);
    }
  }

  return <div className="dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="bid-dialog" role="dialog" aria-modal="true" aria-labelledby="bid-dialog-title">
      <form onSubmit={submit}>
        <div className="buyer-heading"><h2 id="bid-dialog-title">Prepare a demo bid</h2><button type="button" className="secondary-button" onClick={onClose}>Close</button></div>
        <p className="buyer-intro">{tender.id} · {tender.title}</p>
        <div className="demo-warning">Demo only: this records a sample bid in TenderWatch. It does not submit to CPPP, GeM, or any government portal.</div>
        <div className="bid-form-grid">
          <label>Business / bidder name<input value={bidderName} onChange={e => setBidderName(e.target.value)} required minLength="2" maxLength="120" /></label>
          <label>Quoted amount (₹)<input type="number" value={amount} onChange={e => setAmount(e.target.value)} min="1" step="0.01" required /></label>
          <label className="wide">Technical offer summary<textarea value={technicalSummary} onChange={e => setTechnicalSummary(e.target.value)} required minLength="10" maxLength="2000" rows="4" placeholder="Describe how your offer meets the tender scope" /></label>
        </div>
        <div className="review-summary"><b>Purpose:</b> {tender.purpose}<br /><b>Work:</b> {tender.work}<br /><b>Requirements:</b> {tender.requirements}<br /><b>EMD:</b> {formatMoney(tender.emd)} · <b>Deadline:</b> {tender.deadline}</div>
        <fieldset className="doc-checklist"><legend>Documents prepared for this demo</legend>
          {requiredDocs.map(doc => <label key={doc}><input type="checkbox" checked={documents.includes(doc)} onChange={e => setDocuments(e.target.checked ? [...documents, doc] : documents.filter(item => item !== doc))} />{doc}</label>)}
          <small>Checklist only; files are not uploaded or stored.</small>
        </fieldset>
        <label className="terms-check"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} required /> I reviewed the sample tender requirements and confirm this demo offer is accurate.</label>
        {message && <p className="history-error" role="alert">{message}</p>}
        <div className="review-actions"><button type="submit" disabled={busy}>{busy ? "Saving demo bid…" : "Submit demo bid"}</button><span className="review-disclaimer">Submissions are stored in backend memory and cleared when it restarts.</span></div>
        <div className="portal-reminders"><b>Before a real portal submission:</b> check the latest corrigendum and deadline, prepare the tender’s exact documents and price schedule, and confirm bidder account and valid DSC work. <a href="https://eprocure.gov.in/eprocure/app?page=HelpForContractors&service=page" target="_blank" rel="noopener noreferrer">Official CPPP bidder help</a></div>
      </form>
    </section>
  </div>;
}
