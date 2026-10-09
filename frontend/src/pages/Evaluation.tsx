import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ModelMetrics from "../components/models/ModelMetrics";
import { generateExplainability } from "../services/explainabilityService";
import { getEvaluation, tuneBestModel } from "../services/modelService";
import type { ModelEvaluationResult } from "../types/model";

const artifactUrl = (path: string) => `http://127.0.0.1:8000${path}`;

export default function Evaluation() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const [evaluation, setEvaluation] = useState<ModelEvaluationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [explaining, setExplaining] = useState(false);
  const [tuning, setTuning] = useState(false);
  useEffect(() => { if (datasetId) void getEvaluation(datasetId).then(setEvaluation).catch(() => setError("No model evaluation is available yet.")); }, [datasetId]);
  async function explain() { if (!datasetId) return; setExplaining(true); setError(null); try { await generateExplainability(datasetId); navigate(`/datasets/${datasetId}/explainability`); } catch { setError("The best model could not be explained."); } finally { setExplaining(false); } }
  async function tune() { if (!datasetId) return; setTuning(true); setError(null); try { await tuneBestModel(datasetId); setEvaluation(await getEvaluation(datasetId)); } catch { setError("Model tuning could not be completed."); } finally { setTuning(false); } }
  if (error && !evaluation) return <main className="page"><p className="error-message">{error}</p></main>;
  if (!evaluation) return <main className="page">Loading model evaluation...</main>;
  const charts = evaluation.charts ?? {};
  return <main className="page evaluation-page"><header className="page-hero"><p className="eyebrow">STAGE 07 · EVALUATION</p><h1>Model Evaluation</h1><p>Observed held-out metrics from leakage-safe training and validation.</p></header>{evaluation.best_model && <section className="best-model card"><span className="status-chip success">Selected best model</span><h2>{evaluation.best_model.model_id.replaceAll("_", " ")}</h2><p>{evaluation.best_model.why_selected}</p></section>}<div className="page-actions"><button type="button" onClick={explain} disabled={!evaluation.best_model || explaining}>{explaining ? "Generating explanation..." : "Explain Best Model"}</button><button type="button" onClick={tune} disabled={!evaluation.best_model || tuning}>{tuning ? "Tuning model..." : "Tune Best Model"}</button><Link className="primary-link" to={`/datasets/${datasetId}/research`}>Run Research Comparison</Link></div>{error && <p className="error-message">{error}</p>}<section className="evaluation-charts">{charts.comparison && <article className="card"><h2>Model comparison</h2><img src={artifactUrl(charts.comparison)} alt="Model comparison chart based on observed evaluation metrics" /></article>}{charts.confusion_matrix && <article className="card"><h2>Confusion matrix</h2><img src={artifactUrl(charts.confusion_matrix)} alt="Confusion matrix for the selected best model" /></article>}</section><h2>Model metrics</h2><div className="evaluation-grid">{evaluation.results.map((result) => <ModelMetrics key={result.model_id} result={result} problemType={evaluation.problem_type} />)}</div></main>;
}
