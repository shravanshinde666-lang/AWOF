import { AxiosError } from "axios";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { generateCapabilities, getCapabilities } from "../services/capabilityService";
import type { ACSAResult, CapabilityResult } from "../types/capability";
import Loading from "../components/common/Loading";
import { useNavigate } from "react-router-dom";

function message(cause: unknown) {
  return cause instanceof AxiosError ? ((cause.response?.data as { error?: string } | undefined)?.error ?? "Capability analysis failed.") : "Capability analysis failed.";
}
function group(capabilities: CapabilityResult[]) {
  return capabilities.reduce<Record<string, CapabilityResult[]>>((groups, item) => {
    (groups[item.category] ??= []).push(item); return groups;
  }, {});
}
export default function CapabilityScores() {
  const navigate=useNavigate();
  const { datasetId } = useParams<{ datasetId: string }>();
  const [result, setResult] = useState<ACSAResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!datasetId) return;
    getCapabilities(datasetId).then(setResult).catch(() => generateCapabilities(datasetId).then(setResult)).catch((cause) => setError(message(cause))).finally(() => setLoading(false));
  }, [datasetId]);
  if (loading) return <main className="page"><Loading message="Running capability analysis..." /></main>;
  if (error || !result) return <main className="page"><p className="error-message">{error ?? "No capability result is available."}</p></main>;
  return <main className="page capability-page">
    <Link className="back-link" to={`/datasets/${datasetId}/configure`}>← Configure Analysis</Link>
    <p className="eyebrow">AWOF · {result.algorithm_version}</p><h1>ACSA Capability Analysis</h1>
    <p>{result.summary.total_capabilities} capabilities evaluated · RUN: {result.summary.run_count} · OPTIONAL: {result.summary.optional_count} · SKIP: {result.summary.skip_count}</p>
    <button type="button" onClick={()=>datasetId&&navigate(`/datasets/${datasetId}/workflow`)}>Generate Adaptive Workflow</button>
    {Object.entries(group(result.capabilities)).map(([category, items]) => <section key={category}><h2>{category.replaceAll("_", " ")}</h2><div className="capability-grid">{items.map((item) => <article className="capability-card" key={item.id}>
      <h3>{item.label}</h3><p>{item.description}</p><p><strong>Score: {(item.score * 100).toFixed(0)}%</strong> · <span className={`decision ${item.decision}`}>{item.decision.toUpperCase()}</span></p>
      <div className="capability-bar"><span style={{ width: `${item.score * 100}%` }} /></div><h4>Why</h4><ul>{item.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
      <details><summary>Signals</summary><ul>{Object.entries(item.signals).map(([key, value]) => <li key={key}>{key.replaceAll("_", " ")}: {value == null ? "—" : String(value)}</li>)}</ul></details>
    </article>)}</div></section>)}
  </main>;
}
