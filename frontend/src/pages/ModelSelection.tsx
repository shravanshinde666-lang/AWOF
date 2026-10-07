import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ModelRecommendation from "../components/models/ModelRecommendation";
import { getRecommendations, getTrainingJob, recommendModels, startTrainingJob } from "../services/modelService";
import type { AMRAResult, TrainingJobStatus } from "../types/model";

export default function ModelSelection() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState<AMRAResult | null>(null);
  const [job, setJob] = useState<TrainingJobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!datasetId) return;
    void getRecommendations(datasetId).catch(() => recommendModels(datasetId)).then(setRecommendations).catch(() => setError("Recommendations are unavailable. Complete execution first."));
    void getTrainingJob(datasetId).then(setJob).catch(() => undefined);
  }, [datasetId]);

  useEffect(() => {
    if (!datasetId || !job || !["queued", "running"].includes(job.status)) return;
    const timer = window.setInterval(() => {
      void getTrainingJob(datasetId).then((next) => {
        setJob(next);
        if (next.status === "completed") navigate(`/datasets/${datasetId}/evaluation`);
      }).catch(() => setError("Unable to read model-training progress."));
    }, 1500);
    return () => window.clearInterval(timer);
  }, [datasetId, job?.status, navigate]);

  async function train() {
    if (!datasetId) return;
    setError(null);
    try { setJob(await startTrainingJob(datasetId)); }
    catch { setError("Training could not be started. Check the workflow prerequisites and try again."); }
  }

  if (error && !recommendations) return <main className="page"><p className="error-message">{error}</p></main>;
  if (!recommendations) return <main className="page">Generating adaptive model recommendations...</main>;
  const recommended = recommendations.models.filter((model) => model.decision === "recommended");
  const other = recommendations.models.filter((model) => model.decision !== "recommended");
  const training = job?.status === "queued" || job?.status === "running";
  const progress = job && job.total_models ? Math.round(job.completed_models / job.total_models * 100) : 0;

  return <main className="page models-page"><header className="page-hero"><p className="eyebrow">STAGE 06 · AMRA</p><h1>Adaptive Model Recommendation</h1><p>Suitability is scored from your dataset and workflow signals before any model is trained.</p></header><section className="stage-kpis"><article><span>Problem type</span><strong>{recommendations.problem_type}</strong><small>Configured objective</small></article><article><span>Models evaluated</span><strong>{recommendations.summary.models_evaluated}</strong><small>Available candidates</small></article><article><span>Recommended</span><strong>{recommendations.summary.models_recommended}</strong><small>Selected for training</small></article></section><p className="info-callout">AMRA scores are suitability estimates. Observed metrics are shown only after leakage-safe training.</p><h2>Recommended Models</h2><div className="model-grid">{recommended.map((model) => <ModelRecommendation key={model.model_id} model={model} />)}</div>{training && job && <section className="training-progress" aria-live="polite"><div><strong>{job.message}</strong><span>{job.completed_models} of {job.total_models} models complete</span></div><div className="capability-bar"><span style={{ width: `${progress}%` }} /></div></section>}<button type="button" onClick={train} disabled={training}>{training ? "Training in progress…" : "Train Recommended Models"}</button>{job?.status === "failed" && <p className="error-message">{job.error ?? job.message}</p>}{error && <p className="error-message">{error}</p>}<h2 className="section-spacer">Not Selected by AMRA</h2><div className="model-grid muted-grid">{other.map((model) => <ModelRecommendation key={model.model_id} model={model} />)}</div></main>;
}
