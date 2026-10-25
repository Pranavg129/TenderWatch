import { formatMoney } from "../api.js";

const categories = ["Goods", "Services", "Electrical"];

export default function EligibilityPanel({ profile, onChange, result, selectedTender }) {
  function changeNumber(field, value) {
    onChange({ ...profile, [field]: Number(value) });
  }
  return (
    <aside className="panel">
      <h2>Eligibility quick-check</h2>
      <p className="sub">Enter your business profile, then select “Check eligibility” on a tender.</p>
      <div className="profile">
        <label>Annual turnover (₹)<input type="number" min="0" value={profile.annual_turnover_inr} onChange={e => changeNumber("annual_turnover_inr", e.target.value)} /></label>
        <label>Years of relevant experience<input type="number" min="0" value={profile.years_experience} onChange={e => changeNumber("years_experience", e.target.value)} /></label>
        <label>Available EMD capacity (₹)<input type="number" min="0" value={profile.available_emd_inr} onChange={e => changeNumber("available_emd_inr", e.target.value)} /></label>
        <fieldset className="category-field"><legend>Business categories</legend>
          {categories.map(category => <label key={category} className="category-option">
            <input type="checkbox" checked={profile.categories.includes(category)} onChange={e => onChange({ ...profile, categories: e.target.checked ? [...profile.categories, category] : profile.categories.filter(x => x !== category) })} />
            {category}
          </label>)}
        </fieldset>
      </div>
      <div className="result">
        {!result || !selectedTender ? "Choose a tender and run the check to see requirement-by-requirement results." : <>
          <strong>{result.status}</strong><p>{result.passed} of {result.total} preliminary checks passed for {selectedTender.id}</p>
          {result.checks?.map(check => <div className="check" key={check.name}>
            <span>{check.name} <small>(required {check.required})</small></span>
            <span className={check.pass ? "ok" : "no"}>{check.pass ? "PASS" : "REVIEW"}</span>
          </div>)}
          <p>Screening only; verify every condition in the official tender documents.</p>
        </>}
      </div>
      <div className="notice"><b>Trust note:</b> This is a prototype using illustrative data. It is not legal or procurement advice. Confirm eligibility, deadlines, EMD and corrigenda against the official tender notice.</div>
    </aside>
  );
}
