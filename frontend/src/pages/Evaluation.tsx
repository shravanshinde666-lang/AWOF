import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import ModelMetrics from "../components/models/ModelMetrics";
import { generateExplainability } from "../services/explainabilityService";
import { getEvaluation } from "../services/modelService";
import type { ModelEvaluationResult } from "../types/model";

export default function Evaluation() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const [evaluation, setEvaluation] = useState<ModelEvaluationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [explaining, setExplaining] = useState(false);
  useEffect(() => { if (datasetId) void getEvaluation(datasetId).then(setEvaluation).catch(() => setError("No model evaluation is available yet.")); }, [datasetId]);
  async function explain() {
    if (!datasetId) return;
    setExplaining(true); setError(null);
    try { await generateExplainability(datasetId); navigate(`/datasets/${datasetId}/explainability`); }
    catch { setError("The best model could not be explained."); }
    finally { setExplaining(false); }
  }
  if (error && !evaluation) return <main className="page"><p className="error-message">{error}</p></main>;
  if (!evaluation) return <main className="page">Loading model evaluation...</main>;
  return <main className="page"><h1>Model Evaluation</h1><p>AMRA Score is a pre-training suitability estimate. The metrics below are observed after leakage-safe training.</p>{evaluation.best_model && <section className="card"><h2>Selected Best Model</h2><p>{evaluation.best_model.model_id}</p><p>{evaluation.best_model.why_selected}</p><p>AMRA suitability: {evaluation.best_model.amra_score === undefined ? "Not available" : `${(evaluation.best_model.amra_score * 100).toFixed(0)}%`}</p>{evaluation.best_model.artifact_filename && <p>Saved artifact: {evaluation.best_model.artifact_filename}</p>}</section>}<button type="button" onClick={explain} disabled={!evaluation.best_model || explaining}>{explaining ? "Generating explanation..." : "Explain Best Model"}</button><Link className="primary-link" to={`/datasets/${datasetId}/research`}>Run Research Comparison</Link>{error && <p className="error-message">{error}</p>}<h2>Model Metrics</h2>{evaluation.results.map((result) => <ModelMetrics key={result.model_id} result={result} problemType={evaluation.problem_type} />)}</main>;
}
