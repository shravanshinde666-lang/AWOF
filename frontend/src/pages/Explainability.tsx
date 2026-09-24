import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import FeatureImportance from "../components/explainability/FeatureImportance";
import ShapChart from "../components/explainability/ShapChart";
import { generateBusinessPriority } from "../services/businessService";
import { generateExplainability, getExplainability, getLocalExplanation } from "../services/explainabilityService";
import type { ExplainabilityResult, LocalExplanation } from "../types/explainability";

export default function Explainability() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<ExplainabilityResult | null>(null);
  const [local, setLocal] = useState<LocalExplanation | null>(null);
  const [rowIndex, setRowIndex] = useState("0");
  const [error, setError] = useState<string | null>(null);
  const [generatingBusiness, setGeneratingBusiness] = useState(false);

  useEffect(() => { if (datasetId) void getExplainability(datasetId).catch(() => generateExplainability(datasetId)).then((value) => { setResult(value); setLocal(value.local_explanations[0] ?? null); }).catch(() => setError("Explainability is unavailable. Train a best model first.")); }, [datasetId]);
  async function loadLocal() {
    if (!datasetId || !Number.isInteger(Number(rowIndex)) || Number(rowIndex) < 0) return;
    try { setLocal(await getLocalExplanation(datasetId, Number(rowIndex))); setError(null); }
    catch { setError("That row index cannot be explained."); }
  }
  async function business() {
    if (!datasetId) return;
    setGeneratingBusiness(true); setError(null);
    try { await generateBusinessPriority(datasetId); navigate(`/datasets/${datasetId}/business`); }
    catch { setError("Business priorities could not be generated."); }
    finally { setGeneratingBusiness(false); }
  }
  if (error && !result) return <main className="page"><p className="error-message">{error}</p></main>;
  if (!result) return <main className="page">Generating model explanation...</main>;
  return <main className="page"><h1>Explainability</h1><p>Best Model: {result.model_id} · Problem Type: {result.problem_type}</p><p>Explanation Method: {result.explanation_method}</p>{result.warnings.map((warning) => <p className="configuration-warning" key={warning}>{warning}</p>)}<FeatureImportance items={result.global_importance} />{result.problem_type !== "clustering" && <section><h2>Explain a Row</h2><label className="select-field">Row index<input type="number" min="0" value={rowIndex} onChange={(event) => setRowIndex(event.target.value)} /></label><button type="button" onClick={loadLocal}>Explain Row</button></section>}{local && <ShapChart explanation={local} />}{result.problem_type === "clustering" ? <p>Business prioritization is not applicable to this workflow.</p> : <button type="button" onClick={business} disabled={generatingBusiness}>{generatingBusiness ? "Generating business priorities..." : "Generate Business Priorities"}</button>}{error && <p className="error-message">{error}</p>}</main>;
}
