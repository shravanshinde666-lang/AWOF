import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import FeatureImportance from "../components/explainability/FeatureImportance";
import ShapChart from "../components/explainability/ShapChart";
import { generateBusinessPriority } from "../services/businessService";
import { generateExplainability, getExplainability, getLocalExplanation } from "../services/explainabilityService";
import type { ExplainabilityResult, LocalExplanation } from "../types/explainability";

const label = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function Explainability() {
  const { datasetId } = useParams<{ datasetId: string }>(); const navigate = useNavigate();
  const [result, setResult] = useState<ExplainabilityResult | null>(null); const [local, setLocal] = useState<LocalExplanation | null>(null); const [rowIndex, setRowIndex] = useState("0"); const [error, setError] = useState<string | null>(null); const [generatingBusiness, setGeneratingBusiness] = useState(false);
  useEffect(() => { if (datasetId) void getExplainability(datasetId).catch(() => generateExplainability(datasetId)).then((value) => { setResult(value); setLocal(value.local_explanations[0] ?? null); }).catch(() => setError("Explainability is unavailable. Train a best model first.")); }, [datasetId]);
  async function loadLocal() { if (!datasetId || !Number.isInteger(Number(rowIndex)) || Number(rowIndex) < 0) return; try { setLocal(await getLocalExplanation(datasetId, Number(rowIndex))); setError(null); } catch { setError("That row index cannot be explained."); } }
  async function business() { if (!datasetId) return; setGeneratingBusiness(true); setError(null); try { await generateBusinessPriority(datasetId); navigate(`/datasets/${datasetId}/business`); } catch { setError("Business priorities could not be generated."); } finally { setGeneratingBusiness(false); } }
  if (error && !result) return <main className="page"><p className="error-message">{error}</p></main>;
  if (!result) return <main className="page route-loading">Generating model explanation...</main>;
  return <main className="page explainability-page"><header className="page-hero explainability-hero"><div><p className="eyebrow">STAGE 08 · EXPLAINABILITY</p><h1>Understand model decisions</h1><p>Inspect the global signals that influence the selected model and explain an individual prediction when needed.</p></div><div className="model-context"><span>Best model</span><strong>{label(result.model_id)}</strong><small>{label(result.problem_type)} · {label(result.explanation_method)}</small></div></header>{result.warnings.map((warning) => <p className="configuration-warning" key={warning}>{warning}</p>)}<FeatureImportance items={result.global_importance} />{result.problem_type !== "clustering" && <section className="card explain-row-form"><div><p className="card-kicker">LOCAL ANALYSIS</p><h2>Explain a specific row</h2><p>Choose a source-row index to inspect the signals behind its prediction.</p></div><label className="select-field" htmlFor="explain-row"><span>Row index</span><input id="explain-row" type="number" min="0" value={rowIndex} onChange={(event) => setRowIndex(event.target.value)} /></label><button type="button" onClick={loadLocal}>Explain row</button></section>}{local && <ShapChart explanation={local} />}<section className="explainability-next"><div><p className="eyebrow">NEXT STEP</p><h2>Turn predictions into action</h2><p>{result.problem_type === "clustering" ? "Business prioritization is not applicable to a clustering workflow." : "Rank entities using the model prediction and the available business signals."}</p></div>{result.problem_type !== "clustering" && <button type="button" onClick={business} disabled={generatingBusiness}>{generatingBusiness ? "Generating priorities..." : "Generate Business Priorities"}</button>}</section>{error && <p className="error-message">{error}</p>}</main>;
}
